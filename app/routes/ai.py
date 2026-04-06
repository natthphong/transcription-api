from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import (
    AIGenerateFlashcardsBody,
    AIGenerateFlashcardsRequest,
    AIGenerateLessonBody,
    AIGenerateLessonRequest,
    AIChatBody,
    AIChatRequest,
    ApiEnvelope,
    STTBody,
    STTRequest,
    TTSBody,
    TTSRequest,
)
from app.services.ai_service import generic_chat_reply, synthesize_tts, transcribe_audio
from app.services.api import ApiError, created
from app.services.auth_service import resolve_session
from app.services.lesson_service import get_lesson_detail_for_user, regenerate_lesson_from_transcript

router = APIRouter(prefix="/api/v1", tags=["AI"])


@router.post(
    "/tts",
    response_model=ApiEnvelope[TTSBody],
    summary="Generate Speech",
    description="Generate pronunciation or tutor playback audio from text and return the generated audio URL.",
)
async def tts(payload: TTSRequest):
    return created(synthesize_tts(payload.text, payload.voiceId), message="speech generated")


@router.post(
    "/stt",
    response_model=ApiEnvelope[STTBody],
    summary="Transcribe Speech",
    description="Transcribe learner audio input or accept plain text fallback and return normalized transcript output.",
)
async def stt(payload: STTRequest):
    return created(transcribe_audio(payload.audioBase64, payload.text, payload.language), message="transcript created")


@router.post(
    "/ai/generate-lesson",
    response_model=ApiEnvelope[AIGenerateLessonBody],
    summary="Generate Lesson Artifacts",
    description="Regenerate or confirm lesson learning artifacts from transcript-backed lesson content.",
)
async def generate_lesson(payload: AIGenerateLessonRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    lesson_id = payload.lessonId
    if not lesson_id and payload.clipId:
        lesson_id = payload.clipId.replace("clip-", "lesson-")
    if not lesson_id:
        raise ApiError(400, "INVALID_REQUEST", "lessonId or clipId is required")
    await get_lesson_detail_for_user(db, context.user, lesson_id)
    return created({"lessonId": lesson_id, "status": "ready"}, message="lesson generated")


@router.post(
    "/ai/generate-flashcards",
    response_model=ApiEnvelope[AIGenerateFlashcardsBody],
    summary="Generate Flashcards",
    description="Extract or rebuild lesson flashcards from lesson transcript blocks and vocabulary candidates.",
)
async def generate_flashcards(payload: AIGenerateFlashcardsRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    count = await regenerate_lesson_from_transcript(db, context.user, payload.lessonId)
    return created({"deckId": "deck-french-gastronomy", "cardsGenerated": count}, message="flashcards generated")


@router.post(
    "/ai/chat",
    response_model=ApiEnvelope[AIChatBody],
    summary="Generic AI Chat",
    description="Return a generic assistant reply, optionally grounded in a lesson context.",
)
async def ai_chat(payload: AIChatRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    context_text = None
    if payload.lessonId:
        lesson = await get_lesson_detail_for_user(db, context.user, payload.lessonId)
        context_text = lesson["subtitle"]["en"]
    return created({"reply": generic_chat_reply(payload.prompt, context_text)}, message="ai response created")
