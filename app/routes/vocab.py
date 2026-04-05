from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, VocabDashboard, VocabItem, VocabReviewAnswerBody, VocabReviewAnswerRequest
from app.services.api import success
from app.services.auth_service import resolve_session
from app.services.vocab_service import build_vocab_dashboard, list_vocab_items, record_review_answer

router = APIRouter(prefix="/api/v1/vocab", tags=["Vocab"])


@router.get(
    "/items",
    response_model=ApiEnvelope[list[VocabItem]],
    summary="List Vocab Items",
    description="Return saved and extracted vocabulary items linked back to lessons.",
)
async def items(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_vocab_items(db, context.user), message="success")


@router.get(
    "/review",
    response_model=ApiEnvelope[VocabDashboard],
    summary="Vocab Review Dashboard",
    description="Return the daily review metrics and the active review session card.",
)
async def review(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await build_vocab_dashboard(db, context.user), message="success")


@router.post(
    "/review/answer",
    response_model=ApiEnvelope[VocabReviewAnswerBody],
    summary="Record Review Answer",
    description="Store a spaced-repetition answer and return the next due label.",
)
async def review_answer(payload: VocabReviewAnswerRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await record_review_answer(db, context.user, payload.sessionId, payload.answer), message="review recorded")
