from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, SaveAckBody, TutorMessage, TutorMessageRequest, TutorSession, TutorSessionCreateRequest, TutorSessionSummary, TutorFeedbackRequest
from app.services.api import created, success
from app.services.auth_service import resolve_session
from app.services.tutor_service import create_tutor_session, get_tutor_session, list_tutor_sessions, save_tutor_feedback, send_tutor_message

router = APIRouter(prefix="/api/v1/tutor", tags=["Tutor"])


@router.get(
    "/sessions",
    response_model=ApiEnvelope[list[TutorSessionSummary]],
    summary="List Tutor Sessions",
    description="Return tutor session summaries linked to lessons and clips.",
)
async def sessions(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_tutor_sessions(db, context.user), message="success")


@router.post(
    "/sessions",
    response_model=ApiEnvelope[TutorSession],
    summary="Create Tutor Session",
    description="Create or reuse a tutor session grounded in a specific lesson and clip.",
)
async def create_session(payload: TutorSessionCreateRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return created(await create_tutor_session(db, context.user, payload), message="session created")


@router.get(
    "/sessions/{session_id}",
    response_model=ApiEnvelope[TutorSession],
    summary="Tutor Session Detail",
    description="Return the full tutor workspace, context summary, messages, and quick actions.",
)
async def session_detail(session_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_tutor_session(db, context.user, session_id), message="success")


@router.post(
    "/message",
    response_model=ApiEnvelope[TutorMessage],
    summary="Send Tutor Message",
    description="Persist a learner message, inject lesson context, and return the assistant reply.",
)
async def message(payload: TutorMessageRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return created(await send_tutor_message(db, context.user, payload), message="message sent")


@router.post(
    "/feedback",
    response_model=ApiEnvelope[SaveAckBody],
    summary="Save Tutor Feedback",
    description="Store tutor quality feedback for a session.",
)
async def feedback(payload: TutorFeedbackRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await save_tutor_feedback(db, context.user, payload), message="feedback saved")


@router.get(
    "/conversations",
    response_model=ApiEnvelope[list[TutorSessionSummary]],
    summary="Legacy Tutor Conversations Alias",
    description="Compatibility alias for older frontend paths that still read tutor conversations.",
)
async def conversations(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_tutor_sessions(db, context.user), message="success")


@router.get(
    "/conversations/{session_id}",
    response_model=ApiEnvelope[TutorSession],
    summary="Legacy Tutor Conversation Detail Alias",
    description="Compatibility alias for older frontend paths that still read a tutor conversation by id.",
)
async def conversation_detail(session_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_tutor_session(db, context.user, session_id), message="success")
