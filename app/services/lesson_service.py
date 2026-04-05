from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AppLesson,
    AppLessonClip,
    AppLessonTranscriptBlock,
    AppLessonVocabulary,
    AppUser,
    AppVideo,
    AppVocabItem,
    YoutubeTransaction,
    YoutubeTransactionDetail,
)
from app.schemas import LessonCreateRequest
from app.services.api import ApiError
from app.services.constants import loc, status_label
from app.services.formatting import format_duration_label, humanize_relative
from app.services.transcript import extract_video_id

_COMMON_WORDS = {
    "this",
    "that",
    "with",
    "from",
    "about",
    "their",
    "there",
    "would",
    "could",
    "should",
    "today",
    "video",
    "lesson",
    "hello",
    "bonjour",
    "please",
    "price",
    "about",
    "together",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _localized_last_activity(lesson: AppLesson) -> dict:
    label = humanize_relative(lesson.last_activity_at or lesson.updated_at or lesson.created_at)
    if "ago" in label:
        return loc(f"Reviewed {label}", f"ทบทวนล่าสุดเมื่อ {label}")
    if label == "Yesterday":
        return loc("Completed yesterday", "เรียนจบเมื่อวาน")
    return loc("Imported today", "นำเข้าแล้ววันนี้")


def _serialize_lesson_summary(lesson: AppLesson, primary_clip_id: str | None = None) -> dict:
    clip_id = primary_clip_id or f"clip-{lesson.id}"
    return {
        "id": lesson.id,
        "clipId": clip_id,
        "title": dict(lesson.title or {}),
        "subtitle": dict(lesson.subtitle or {}),
        "durationLabel": format_duration_label(lesson.duration_seconds),
        "progressPercent": lesson.progress_percent,
        "statusId": lesson.status_id,
        "statusLabel": dict(lesson.status_label or status_label(lesson.status_id)),
        "extractedVocabCount": lesson.extracted_vocab_count,
        "categoryId": lesson.category_id,
        "lastActivityLabel": _localized_last_activity(lesson),
        "thumbnailAccent": lesson.thumbnail_accent,
        "clipCount": lesson.clip_count,
        "sourceLabel": dict(lesson.source_label or loc("YouTube import", "นำเข้าจาก YouTube")),
    }


def _timestamp_from_ms(value: int | None) -> str:
    if value is None:
        return "00:00"
    total_seconds = max(0, int(value / 1000))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _naive_translation(text: str) -> str:
    return text


def _naive_explanation(text: str) -> dict:
    return loc(
        f"This line came from an imported lesson. Review it with the tutor for a deeper explanation: {text[:80]}",
        f"บรรทัดนี้มาจากบทเรียนที่นำเข้าใหม่ ลองถามติวเตอร์เพื่อขอคำอธิบายเชิงลึกเพิ่มเติม: {text[:80]}",
    )


def _extract_vocab_candidates(lines: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for line in lines:
        for match in re.findall(r"[A-Za-zÀ-ÿ']{4,}", line):
            token = match.lower()
            if token in _COMMON_WORDS:
                continue
            counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ranked[:5]]


async def sync_lesson_from_job(db: AsyncSession, lesson: AppLesson) -> None:
    if not lesson.youtube_transaction_id:
        return

    job = await db.get(YoutubeTransaction, lesson.youtube_transaction_id)
    if not job:
        return

    details = (
        await db.execute(
            select(YoutubeTransactionDetail)
            .where(YoutubeTransactionDetail.youtube_transaction_id == job.id)
            .order_by(YoutubeTransactionDetail.seq.asc(), YoutubeTransactionDetail.id.asc())
        )
    ).scalars().all()

    clip = (
        await db.execute(
            select(AppLessonClip)
            .where(AppLessonClip.lesson_id == lesson.id)
            .order_by(AppLessonClip.seq.asc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if clip:
        clip.transcript_status = "ready" if job.status in {"done", "done_transcript_only"} else "processing"
        clip.clip_path = clip.clip_path or (details[0].clip_path if details else None)
        clip.updated_at = _utc_now()

    if job.title and not lesson.title.get("en"):
        lesson.title = loc(job.title)
    if details:
        lesson.duration_seconds = int(max((row.end_ms or 0) for row in details) / 1000)
        lesson.clip_count = len(details)
        lesson.last_activity_at = job.finished_at or job.created_at or _utc_now()
        if job.status in {"done", "done_transcript_only"}:
            lesson.status_id = "ready" if lesson.progress_percent == 0 else lesson.status_id
            lesson.status_label = status_label(lesson.status_id)

    existing_blocks = (
        await db.execute(
            select(AppLessonTranscriptBlock).where(AppLessonTranscriptBlock.lesson_id == lesson.id)
        )
    ).scalars().all()
    if details and not existing_blocks:
        for row in details:
            seq = row.seq or row.id
            db.add(
                AppLessonTranscriptBlock(
                    id=f"{lesson.id}-block-{seq}",
                    lesson_id=lesson.id,
                    clip_id=clip.id if clip else None,
                    seq=seq,
                    timestamp_label=_timestamp_from_ms(row.start_ms),
                    source=row.message,
                    translated=_naive_translation(row.message),
                    explanation=_naive_explanation(row.message),
                    created_at=_utc_now(),
                    updated_at=_utc_now(),
                )
            )

    existing_vocab = (
        await db.execute(select(AppLessonVocabulary).where(AppLessonVocabulary.lesson_id == lesson.id))
    ).scalars().all()
    if details and not existing_vocab:
        candidates = _extract_vocab_candidates([row.message for row in details if row.message])
        for idx, token in enumerate(candidates, start=1):
            db.add(
                AppLessonVocabulary(
                    id=f"{lesson.id}-vocab-{idx}",
                    lesson_id=lesson.id,
                    term=token,
                    pronunciation=f"/{token}/",
                    meaning=loc(f"Key term from the imported lesson: {token}", f"คำสำคัญจากบทเรียนที่นำเข้า: {token}"),
                    created_at=_utc_now(),
                    updated_at=_utc_now(),
                )
            )
        lesson.extracted_vocab_count = len(candidates)

        existing_user_vocab = (
            await db.execute(
                select(AppVocabItem).where(
                    AppVocabItem.user_id == lesson.user_id,
                    AppVocabItem.source_lesson_id == lesson.id,
                )
            )
        ).scalars().all()
        if not existing_user_vocab:
            for idx, token in enumerate(candidates, start=1):
                example = next((row.message for row in details if token in row.message.lower()), token)
                db.add(
                    AppVocabItem(
                        id=f"{lesson.id}-saved-vocab-{idx}",
                        user_id=lesson.user_id,
                        source_lesson_id=lesson.id,
                        term=token,
                        translation=loc(token),
                        pronunciation=f"/{token}/",
                        status_id="due",
                        due_at=_utc_now(),
                        example=example,
                        notes=loc(
                            f"Extracted from the lesson transcript for review: {token}",
                            f"ดึงมาจากทรานสคริปต์ของบทเรียนเพื่อทบทวน: {token}",
                        ),
                        interval_days=1,
                        repetitions=0,
                        created_at=_utc_now(),
                        updated_at=_utc_now(),
                    )
                )

    await db.commit()


async def create_lesson_from_import(
    db: AsyncSession,
    user: AppUser,
    payload: LessonCreateRequest,
) -> tuple[AppLesson, AppLessonClip, YoutubeTransaction]:
    try:
        video_id = extract_video_id(payload.url)
    except Exception as exc:
        raise ApiError(400, "INVALID_YOUTUBE_URL", "invalid youtube url") from exc

    lesson_id = f"lesson-{video_id}"
    existing = await db.get(AppLesson, lesson_id)
    if existing:
        clip = (
            await db.execute(
                select(AppLessonClip)
                .where(AppLessonClip.lesson_id == existing.id)
                .order_by(AppLessonClip.seq.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        job = None
        if existing.youtube_transaction_id:
            job = await db.get(YoutubeTransaction, existing.youtube_transaction_id)
        if clip and job:
            return existing, clip, job

    lesson_title = loc(f"Imported lesson {video_id}", f"บทเรียนที่นำเข้า {video_id}")
    lesson_subtitle = loc("Transcript is being prepared.", "กำลังเตรียมทรานสคริปต์")
    job = YoutubeTransaction(
        title=lesson_title["en"],
        youtube_link=payload.url,
        user_id_token=user.id[:36],
        status="processing",
        language=next(
            (option["value"] for option in [{"id": "english", "value": "en"}, {"id": "thai", "value": "th"}, {"id": "french", "value": "fr"}, {"id": "japanese", "value": "ja"}] if option["id"] == payload.sourceLanguageId),
            "en",
        ),
        split_seconds=15,
        tolerance_seconds=1,
        process_step="JOB_CREATED",
        process_log="created from lessons api",
        started_at=_utc_now(),
        created_at=_utc_now(),
    )
    db.add(job)
    await db.flush()

    lesson = AppLesson(
        id=lesson_id,
        user_id=user.id,
        youtube_transaction_id=job.id,
        source_url=payload.url,
        title=lesson_title,
        subtitle=lesson_subtitle,
        duration_seconds=0,
        progress_percent=0,
        status_id="ready",
        status_label=status_label("ready"),
        extracted_vocab_count=0,
        category_id=payload.categoryId,
        thumbnail_accent="sky",
        clip_count=1,
        source_label=loc("YouTube import", "นำเข้าจาก YouTube"),
        learning_objectives=[
            loc("Import the video and wait for transcript alignment to finish.", "นำเข้าวิดีโอและรอให้การจัดแนวทรานสคริปต์เสร็จสิ้น"),
        ],
        tabs=[
            {"id": "source", "label": loc("Source", "ต้นฉบับ")},
            {"id": "translated", "label": loc("Translated", "แปล")},
            {"id": "dual", "label": loc("Dual", "สองภาษา")},
        ],
        recommended_actions=[
            {
                "id": "to-tutor",
                "labelKey": "common.actions.askTutor",
                "href": f"/tutor?lessonId={lesson_id}",
            },
            {
                "id": "to-vocab",
                "labelKey": "common.actions.extractVocab",
                "href": f"/vocab?lessonId={lesson_id}",
            },
        ],
        source_language_id=payload.sourceLanguageId,
        target_language_id=payload.targetLanguageId,
        voice_id=payload.voiceId,
        auto_detect=payload.autoDetect,
        last_activity_at=_utc_now(),
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(lesson)

    clip = AppLessonClip(
        id=f"clip-{video_id}",
        lesson_id=lesson_id,
        source_url=payload.url,
        title=lesson_title,
        channel="YouTube",
        duration_seconds=0,
        transcript_status="processing",
        seq=1,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(clip)

    video = AppVideo(
        id=f"video-{video_id}",
        lesson_id=lesson_id,
        title=lesson_title,
        thumbnail_accent="sky",
        duration_seconds=0,
        summary=loc("This imported lesson will gain AI quiz content after transcript processing finishes."),
        quiz=[],
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(video)

    await db.commit()
    await db.refresh(lesson)
    await db.refresh(clip)
    await db.refresh(job)
    return lesson, clip, job


async def list_lessons_for_user(db: AsyncSession, user: AppUser) -> list[dict]:
    lessons = (
        await db.execute(
            select(AppLesson).where(AppLesson.user_id == user.id).order_by(AppLesson.updated_at.desc())
        )
    ).scalars().all()
    items: list[dict] = []
    for lesson in lessons:
        await sync_lesson_from_job(db, lesson)
        clip = (
            await db.execute(
                select(AppLessonClip)
                .where(AppLessonClip.lesson_id == lesson.id)
                .order_by(AppLessonClip.seq.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        items.append(_serialize_lesson_summary(lesson, clip.id if clip else None))
    return items


async def get_lesson_detail_for_user(db: AsyncSession, user: AppUser, lesson_id: str) -> dict:
    lesson = (
        await db.execute(
            select(AppLesson).where(AppLesson.id == lesson_id, AppLesson.user_id == user.id).limit(1)
        )
    ).scalar_one_or_none()
    if not lesson:
        raise ApiError(404, "LESSON_NOT_FOUND", "lesson not found")

    await sync_lesson_from_job(db, lesson)
    clip = (
        await db.execute(
            select(AppLessonClip)
            .where(AppLessonClip.lesson_id == lesson.id)
            .order_by(AppLessonClip.seq.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    summary = _serialize_lesson_summary(lesson, clip.id if clip else None)
    transcript_blocks = (
        await db.execute(
            select(AppLessonTranscriptBlock)
            .where(AppLessonTranscriptBlock.lesson_id == lesson.id)
            .order_by(AppLessonTranscriptBlock.seq.asc())
        )
    ).scalars().all()
    vocabulary = (
        await db.execute(
            select(AppLessonVocabulary)
            .where(AppLessonVocabulary.lesson_id == lesson.id)
            .order_by(AppLessonVocabulary.term.asc())
        )
    ).scalars().all()
    return {
        **summary,
        "learningObjectives": list(lesson.learning_objectives or []),
        "transcriptBlocks": [
            {
                "id": row.id,
                "timestamp": row.timestamp_label,
                "source": row.source,
                "translated": row.translated,
                "explanation": dict(row.explanation or {}),
            }
            for row in transcript_blocks
        ],
        "vocabulary": [
            {
                "id": row.id,
                "term": row.term,
                "pronunciation": row.pronunciation,
                "meaning": dict(row.meaning or {}),
            }
            for row in vocabulary
        ],
        "tabs": list(lesson.tabs or []),
        "recommendedActions": list(lesson.recommended_actions or []),
    }


async def list_clips_for_user(db: AsyncSession, user: AppUser) -> list[dict]:
    clips = (
        await db.execute(
            select(AppLessonClip)
            .join(AppLesson, AppLesson.id == AppLessonClip.lesson_id)
            .where(AppLesson.user_id == user.id)
            .order_by(AppLessonClip.updated_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": clip.id,
            "sourceUrl": clip.source_url,
            "title": dict(clip.title or {}),
            "channel": clip.channel,
            "durationLabel": format_duration_label(clip.duration_seconds),
            "transcriptStatus": clip.transcript_status,
        }
        for clip in clips
    ]


async def get_clip_for_user(db: AsyncSession, user: AppUser, clip_id: str) -> dict:
    clip = (
        await db.execute(
            select(AppLessonClip)
            .join(AppLesson, AppLesson.id == AppLessonClip.lesson_id)
            .where(AppLesson.user_id == user.id, AppLessonClip.id == clip_id)
            .limit(1)
        )
    ).scalar_one_or_none()
    if not clip:
        raise ApiError(404, "CLIP_NOT_FOUND", "clip not found")
    return {
        "id": clip.id,
        "sourceUrl": clip.source_url,
        "title": dict(clip.title or {}),
        "channel": clip.channel,
        "durationLabel": format_duration_label(clip.duration_seconds),
        "transcriptStatus": clip.transcript_status,
    }


async def list_videos_for_user(db: AsyncSession, user: AppUser) -> list[dict]:
    rows = (
        await db.execute(
            select(AppVideo)
            .join(AppLesson, AppLesson.id == AppVideo.lesson_id)
            .where(AppLesson.user_id == user.id)
            .order_by(AppVideo.updated_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": row.id,
            "lessonId": row.lesson_id,
            "title": dict(row.title or {}),
            "thumbnailAccent": row.thumbnail_accent,
            "durationLabel": format_duration_label(row.duration_seconds),
            "summary": dict(row.summary or {}),
            "quiz": list(row.quiz or []),
        }
        for row in rows
    ]


async def get_video_for_user(db: AsyncSession, user: AppUser, video_id: str) -> dict:
    row = (
        await db.execute(
            select(AppVideo)
            .join(AppLesson, AppLesson.id == AppVideo.lesson_id)
            .where(AppLesson.user_id == user.id, AppVideo.id == video_id)
            .limit(1)
        )
    ).scalar_one_or_none()
    if not row:
        raise ApiError(404, "VIDEO_NOT_FOUND", "video not found")
    return {
        "id": row.id,
        "lessonId": row.lesson_id,
        "title": dict(row.title or {}),
        "thumbnailAccent": row.thumbnail_accent,
        "durationLabel": format_duration_label(row.duration_seconds),
        "summary": dict(row.summary or {}),
        "quiz": list(row.quiz or []),
    }


async def regenerate_lesson_from_transcript(db: AsyncSession, user: AppUser, lesson_id: str) -> int:
    lesson = (
        await db.execute(
            select(AppLesson).where(AppLesson.id == lesson_id, AppLesson.user_id == user.id).limit(1)
        )
    ).scalar_one_or_none()
    if not lesson:
        raise ApiError(404, "LESSON_NOT_FOUND", "lesson not found")

    blocks = (
        await db.execute(
            select(AppLessonTranscriptBlock)
            .where(AppLessonTranscriptBlock.lesson_id == lesson.id)
            .order_by(AppLessonTranscriptBlock.seq.asc())
        )
    ).scalars().all()
    if not blocks:
        raise ApiError(409, "TRANSCRIPT_NOT_READY", "transcript not ready")

    await db.execute(delete(AppLessonVocabulary).where(AppLessonVocabulary.lesson_id == lesson.id))
    await db.execute(
        delete(AppVocabItem).where(
            AppVocabItem.user_id == user.id,
            AppVocabItem.source_lesson_id == lesson.id,
        )
    )
    await db.commit()
    lesson.extracted_vocab_count = 0
    await db.commit()

    lines = [block.source for block in blocks]
    candidates = _extract_vocab_candidates(lines)
    for idx, token in enumerate(candidates, start=1):
        db.add(
            AppLessonVocabulary(
                id=f"{lesson.id}-regen-vocab-{idx}",
                lesson_id=lesson.id,
                term=token,
                pronunciation=f"/{token}/",
                meaning=loc(f"Key term from the lesson transcript: {token}"),
                created_at=_utc_now(),
                updated_at=_utc_now(),
            )
        )
        example = next((line for line in lines if token in line.lower()), token)
        db.add(
            AppVocabItem(
                id=f"{lesson.id}-regen-saved-{idx}",
                user_id=user.id,
                source_lesson_id=lesson.id,
                term=token,
                translation=loc(token),
                pronunciation=f"/{token}/",
                status_id="due",
                due_at=_utc_now(),
                example=example,
                notes=loc(f"Generated from lesson {lesson.id}"),
                interval_days=1,
                repetitions=0,
                created_at=_utc_now(),
                updated_at=_utc_now(),
            )
        )
    lesson.extracted_vocab_count = len(candidates)
    lesson.updated_at = _utc_now()
    await db.commit()
    return len(candidates)
