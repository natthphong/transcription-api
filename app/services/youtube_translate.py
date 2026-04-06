from __future__ import annotations

import json
from datetime import datetime, timezone

from openai import OpenAI
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_settings
from app.core.logger import log_event
from app.models import YoutubeTransaction, YoutubeTransactionDetail
from app.services.api import ApiError


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _translation_model() -> str:
    settings = load_settings()
    if settings.OpenAI and settings.OpenAI.modelChat:
        return settings.OpenAI.modelChat
    return "gpt-4o-mini"


def _translation_client() -> OpenAI:
    settings = load_settings()
    if not settings.OpenAI or not settings.OpenAI.apiKey:
        raise ApiError(400, "OPENAI_CONFIG_MISSING", "openai config missing")
    return OpenAI(api_key=settings.OpenAI.apiKey)


def _normalize_lang(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ApiError(400, "INVALID_REQUEST", "to_lang is required")
    if len(normalized) > 20:
        raise ApiError(400, "INVALID_REQUEST", "to_lang must be 20 characters or fewer")
    return normalized


class _TranslationRecord(BaseModel):
    id: int
    translate: str


def _build_translation_prompt(details: list[YoutubeTransactionDetail], from_lang: str | None, to_lang: str) -> str:
    source_label = from_lang or "auto-detected source language"
    payload = [
        {
            "id": detail.id,
            "message": detail.message,
        }
        for detail in details
    ]
    return (
        f"Source language: {source_label}\n"
        f"Target language: {to_lang}\n"
        "Translate every item.\n"
        "Return only a JSON array.\n"
        'Each item must have exactly: {"id": <number>, "translate": <string>}.\n'
        "Do not omit or add ids. Do not add explanations or markdown.\n"
        f"Input items:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def _validate_translation_payload(content: str, expected_ids: set[int]) -> list[_TranslationRecord]:
    try:
        decoded = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ApiError(502, "INTERNAL_ERROR", f"translation returned invalid json: {exc.msg}") from exc

    try:
        rows = TypeAdapter(list[_TranslationRecord]).validate_python(decoded)
    except ValidationError as exc:
        raise ApiError(502, "INTERNAL_ERROR", f"translation schema validation failed: {exc}") from exc

    returned_ids = [row.id for row in rows]
    if len(returned_ids) != len(set(returned_ids)):
        raise ApiError(502, "INTERNAL_ERROR", "translation response contains duplicate ids")
    if set(returned_ids) != expected_ids:
        raise ApiError(502, "INTERNAL_ERROR", "translation response ids do not match requested details")
    return rows


def _translate_batch(
    client: OpenAI,
    model: str,
    details: list[YoutubeTransactionDetail],
    from_lang: str | None,
    to_lang: str,
) -> list[_TranslationRecord]:
    if not details:
        return []

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a translation engine for transcript snippets. "
                    "Return strict JSON only. "
                    "Preserve the source record ids exactly. "
                    "Translate naturally into the target language without commentary."
                ),
            },
            {
                "role": "user",
                "content": _build_translation_prompt(details, from_lang, to_lang),
            },
        ],
    )
    content = response.choices[0].message.content if response.choices else ""
    raw_payload = (content or "").strip()
    if not raw_payload:
        raise ApiError(502, "INTERNAL_ERROR", "translation returned empty content")
    return _validate_translation_payload(raw_payload, expected_ids={detail.id for detail in details})


def _serialize_detail(detail: YoutubeTransactionDetail, base_url: str | None) -> dict:
    url_video = None
    if base_url and detail.clip_path:
        url_video = f"{base_url.rstrip('/')}/file?key={detail.clip_path}"
    return {
        "id": detail.id,
        "seq": detail.seq or 0,
        "start_s": (detail.start_ms or 0) / 1000.0,
        "end_s": (detail.end_ms or 0) / 1000.0,
        "message": detail.message,
        "clip_path": detail.clip_path,
        "has_clip": bool(detail.clip_path),
        "url_video": url_video,
        "translate": detail.translate,
        "to_lang": detail.to_lang,
    }


async def translate_youtube_transaction(
    db: AsyncSession,
    youtube_transaction_id: int,
    to_lang: str,
) -> dict:
    normalized_to_lang = _normalize_lang(to_lang)
    transaction = (
        await db.execute(
            select(YoutubeTransaction).where(YoutubeTransaction.id == youtube_transaction_id).limit(1)
        )
    ).scalar_one_or_none()
    if transaction is None:
        raise ApiError(404, "VIDEO_NOT_FOUND", "youtube transaction not found")

    details = (
        await db.execute(
            select(YoutubeTransactionDetail)
            .where(YoutubeTransactionDetail.youtube_transaction_id == youtube_transaction_id)
            .order_by(YoutubeTransactionDetail.seq.asc(), YoutubeTransactionDetail.id.asc())
        )
    ).scalars().all()
    if not details:
        raise ApiError(404, "TRANSCRIPT_NOT_READY", "youtube transaction details not found")

    client = _translation_client()
    model = _translation_model()
    translated_count = 0
    skipped_count = 0
    pending_details: list[YoutubeTransactionDetail] = []

    log_event(
        "YOUTUBE_TRANSLATE_START",
        job_id=youtube_transaction_id,
        to_lang=normalized_to_lang,
        from_lang=transaction.language,
        detail_count=len(details),
    )

    for detail in details:
        if detail.to_lang == normalized_to_lang and detail.translate:
            skipped_count += 1
            continue
        pending_details.append(detail)

    translated_rows: list[_TranslationRecord] = []
    try:
        translated_rows = _translate_batch(
            client=client,
            model=model,
            details=pending_details,
            from_lang=transaction.language,
            to_lang=normalized_to_lang,
        )
    except ApiError:
        raise
    except Exception as exc:
        log_event(
            "YOUTUBE_TRANSLATE_BATCH_FAILED",
            job_id=youtube_transaction_id,
            level="error",
            to_lang=normalized_to_lang,
            pending_count=len(pending_details),
            error=str(exc),
        )
        raise ApiError(502, "INTERNAL_ERROR", "translation batch failed")

    translations_by_id = {row.id: row.translate.strip() for row in translated_rows}

    for detail in pending_details:
        translated = translations_by_id.get(detail.id, "")
        if not translated:
            raise ApiError(502, "INTERNAL_ERROR", f"translation missing content for detail {detail.id}")
        detail.translate = translated
        detail.to_lang = normalized_to_lang
        detail.updated_at = _utc_now()
        translated_count += 1

        log_event(
            "YOUTUBE_TRANSLATE_DETAIL_DONE",
            job_id=youtube_transaction_id,
            detail_id=detail.id,
            seq=detail.seq,
            to_lang=normalized_to_lang,
            text_len=len(translated),
        )

    await db.commit()

    refreshed_details = (
        await db.execute(
            select(YoutubeTransactionDetail)
            .where(YoutubeTransactionDetail.youtube_transaction_id == youtube_transaction_id)
            .order_by(YoutubeTransactionDetail.seq.asc(), YoutubeTransactionDetail.id.asc())
        )
    ).scalars().all()

    settings = load_settings()
    log_event(
        "YOUTUBE_TRANSLATE_DONE",
        job_id=youtube_transaction_id,
        to_lang=normalized_to_lang,
        translated_count=translated_count,
        skipped_count=skipped_count,
        model=model,
    )

    return {
        "youtube_transaction_id": youtube_transaction_id,
        "from_lang": transaction.language,
        "to_lang": normalized_to_lang,
        "translated_count": translated_count,
        "skipped_count": skipped_count,
        "details": [_serialize_detail(detail, settings.BaseURL) for detail in refreshed_details],
    }
