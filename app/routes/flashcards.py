from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import (
    ApiEnvelope,
    FlashcardAnswerBody,
    FlashcardAnswerRequest,
    FlashcardDeck,
    FlashcardFinishBody,
    FlashcardFinishRequest,
    FlashcardSession,
    FlashcardStartBody,
    FlashcardStartRequest,
)
from app.services.api import created, success
from app.services.auth_service import resolve_session
from app.services.vocab_service import (
    answer_flashcard_session,
    finish_flashcard_session,
    get_flashcard_deck,
    get_flashcard_session,
    list_flashcard_decks,
    start_flashcard_session,
)

router = APIRouter(prefix="/api/v1/flashcards", tags=["Flashcards"])


@router.get(
    "/decks",
    response_model=ApiEnvelope[list[FlashcardDeck]],
    summary="List Flashcard Decks",
    description="Return flashcard decks derived from lesson vocabulary and review state.",
)
async def decks(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_flashcard_decks(db, context.user), message="success")


@router.get(
    "/decks/{deck_id}",
    response_model=ApiEnvelope[FlashcardDeck],
    summary="Flashcard Deck Detail",
    description="Return one flashcard deck summary, including due and reviewed counts.",
)
async def deck_detail(deck_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_flashcard_deck(db, context.user, deck_id), message="success")


@router.post(
    "/session/start",
    response_model=ApiEnvelope[FlashcardStartBody],
    summary="Start Flashcard Session",
    description="Open a review session for a specific deck or the next available deck.",
)
async def session_start(payload: FlashcardStartRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return created(await start_flashcard_session(db, context.user, payload.deckId), message="session started")


@router.get(
    "/session/{session_id}",
    response_model=ApiEnvelope[FlashcardSession],
    summary="Flashcard Session Detail",
    description="Return the active flashcard prompt, translation, and available answer options.",
)
async def session_detail(session_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_flashcard_session(db, context.user, session_id), message="success")


@router.post(
    "/session/answer",
    response_model=ApiEnvelope[FlashcardAnswerBody],
    summary="Save Flashcard Answer",
    description="Record an answer in the flashcard session and move the learner to the next card.",
)
async def session_answer(payload: FlashcardAnswerRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    result = await answer_flashcard_session(db, context.user, payload.sessionId, payload.answer)
    return success({"saved": result["saved"], "nextCardId": result["nextCardId"]}, message="answer saved")


@router.post(
    "/session/finish",
    response_model=ApiEnvelope[FlashcardFinishBody],
    summary="Finish Flashcard Session",
    description="Close a flashcard review session and return a retention summary.",
)
async def session_finish(payload: FlashcardFinishRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await finish_flashcard_session(db, context.user, payload.sessionId), message="session finished")
