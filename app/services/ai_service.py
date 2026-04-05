from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

from openai import OpenAI

from app.config import load_settings
from app.services.api import ApiError
from app.services.constants import VOICE_MODEL_MAP
from app.services.storage import upload_file


def _client() -> OpenAI | None:
    settings = load_settings()
    if not settings.OpenAI or not settings.OpenAI.apiKey:
        return None
    return OpenAI(api_key=settings.OpenAI.apiKey)


def _chat_model() -> str:
    settings = load_settings()
    return settings.OpenAI.modelChat if settings.OpenAI else "gpt-4o-mini"


def _tts_model() -> str:
    settings = load_settings()
    return settings.OpenAI.modelTTS if settings.OpenAI else "gpt-4o-mini-tts"


def _stt_model() -> str:
    settings = load_settings()
    return settings.OpenAI.modelSTT if settings.OpenAI else "gpt-4o-mini-transcribe"


def generate_tutor_reply(prompt: str, context: str, mode_id: str) -> str:
    client = _client()
    if client:
        response = client.chat.completions.create(
            model=_chat_model(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise language tutor. Use the lesson context, explain clearly, "
                        "and keep answers compact and practical."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Mode: {mode_id}\nContext: {context}\nQuestion: {prompt}",
                },
            ],
        )
        content = response.choices[0].message.content if response.choices else ""
        if content:
            return content.strip()

    return (
        f"{mode_id.title()} reply: {prompt}\n\n"
        f"Use this lesson context while reviewing: {context[:220]}"
    )


def generic_chat_reply(prompt: str, context: str | None = None) -> str:
    client = _client()
    if client:
        response = client.chat.completions.create(
            model=_chat_model(),
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a language-learning product."},
                {"role": "user", "content": f"{context or ''}\n\n{prompt}".strip()},
            ],
        )
        content = response.choices[0].message.content if response.choices else ""
        if content:
            return content.strip()
    return f"A natural answer would be: {prompt}"


def synthesize_tts(text: str, voice_id: str | None = None) -> dict:
    client = _client()
    model = _tts_model()
    if client:
        voice = VOICE_MODEL_MAP.get(voice_id or "", "alloy")
        response = client.audio.speech.create(model=model, voice=voice, input=text)
        fd, temp_path = tempfile.mkstemp(prefix="tts-", suffix=".mp3")
        os.close(fd)
        Path(temp_path).unlink(missing_ok=True)
        Path(temp_path).write_bytes(response.read())
        settings = load_settings()
        if settings.Minio:
            key = upload_file(temp_path, f"tts/{Path(temp_path).name}", "audio/mpeg")
            Path(temp_path).unlink(missing_ok=True)
            return {"audioUrl": f"{settings.public_base_url().rstrip('/')}/file?key={key}", "model": model}
        Path(temp_path).unlink(missing_ok=True)
    return {"audioUrl": "/mock/audio/tts-lesson.mp3", "model": model}


def transcribe_audio(audio_base64: str | None = None, text: str | None = None, language: str | None = None) -> dict:
    model = _stt_model()
    if text:
        return {"text": text, "confidence": 1.0, "model": model}

    if not audio_base64:
        raise ApiError(400, "INVALID_REQUEST", "audioBase64 or text is required")

    client = _client()
    if not client:
        raise ApiError(400, "OPENAI_CONFIG_MISSING", "openai config missing")

    data = base64.b64decode(audio_base64)
    with tempfile.NamedTemporaryFile(prefix="stt-", suffix=".webm", delete=False) as handle:
        handle.write(data)
        temp_path = handle.name
    with open(temp_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language=language,
            response_format="json",
        )
    Path(temp_path).unlink(missing_ok=True)
    return {
        "text": getattr(response, "text", "") or "",
        "confidence": 0.97,
        "model": model,
    }
