from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppLesson, AppLessonClip, AppTutorFeedback, AppTutorMessage, AppTutorSession, AppUser
from app.schemas import TutorFeedbackRequest, TutorMessageRequest, TutorSessionCreateRequest
from app.services.ai_service import generate_tutor_reply
from app.services.api import ApiError
from app.services.constants import TUTOR_ACTIONS, loc
from app.services.formatting import humanize_relative


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def _get_session(db: AsyncSession, user: AppUser, session_id: str) -> AppTutorSession:
    session = (
        await db.execute(
            select(AppTutorSession)
            .where(AppTutorSession.id == session_id, AppTutorSession.user_id == user.id)
            .limit(1)
        )
    ).scalar_one_or_none()
    if not session:
        raise ApiError(404, "TUTOR_SESSION_NOT_FOUND", "tutor session not found")
    return session


async def list_tutor_sessions(db: AsyncSession, user: AppUser) -> list[dict]:
    rows = (
        await db.execute(
            select(AppTutorSession)
            .where(AppTutorSession.user_id == user.id)
            .order_by(desc(AppTutorSession.updated_at))
        )
    ).scalars().all()
    return [
        {
            "id": row.id,
            "lessonId": row.lesson_id,
            "clipId": row.clip_id,
            "title": dict(row.title or {}),
            "lessonLabel": dict(row.lesson_label or {}),
            "lastMessagePreview": dict(row.last_message_preview or {}),
            "updatedAtLabel": humanize_relative(row.updated_at),
            "modeId": row.mode_id,
        }
        for row in rows
    ]


async def get_tutor_session(db: AsyncSession, user: AppUser, session_id: str) -> dict:
    row = await _get_session(db, user, session_id)
    messages = (
        await db.execute(
            select(AppTutorMessage)
            .where(AppTutorMessage.session_id == row.id)
            .order_by(AppTutorMessage.created_at.asc())
        )
    ).scalars().all()
    return {
        "id": row.id,
        "lessonId": row.lesson_id,
        "clipId": row.clip_id,
        "title": dict(row.title or {}),
        "lessonLabel": dict(row.lesson_label or {}),
        "lastMessagePreview": dict(row.last_message_preview or {}),
        "updatedAtLabel": humanize_relative(row.updated_at),
        "modeId": row.mode_id,
        "contextSummary": dict(row.context_summary or {}),
        "selectedExcerpt": row.selected_excerpt,
        "quickPrompts": list(row.quick_prompts or []),
        "waveform": list(row.waveform or []),
        "messages": [
            {
                "id": item.id,
                "role": item.role,
                "text": item.text,
                "timestampLabel": item.timestamp_label,
            }
            for item in messages
        ],
        "availableActions": list(row.available_actions or []),
    }


async def create_tutor_session(db: AsyncSession, user: AppUser, payload: TutorSessionCreateRequest) -> dict:
    existing = (
        await db.execute(
            select(AppTutorSession)
            .where(
                AppTutorSession.user_id == user.id,
                AppTutorSession.lesson_id == payload.lessonId,
                AppTutorSession.clip_id == payload.clipId,
                AppTutorSession.mode_id == payload.modeId,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing:
        return await get_tutor_session(db, user, existing.id)

    lesson = await db.get(AppLesson, payload.lessonId)
    clip = await db.get(AppLessonClip, payload.clipId)
    if not lesson:
        raise ApiError(404, "LESSON_NOT_FOUND", "lesson not found")
    if not clip:
        raise ApiError(404, "CLIP_NOT_FOUND", "clip not found")

    session = AppTutorSession(
        id=f"session-{payload.lessonId}",
        user_id=user.id,
        lesson_id=lesson.id,
        clip_id=clip.id,
        title=loc(f"{lesson.title.get('en', 'Lesson')} tutor"),
        lesson_label=dict(lesson.title or {}),
        last_message_preview=loc("Start a tutor conversation for this lesson."),
        mode_id=payload.modeId,
        context_summary=loc(
            f"This tutor session is grounded in {lesson.title.get('en', 'the selected lesson')}.",
            f"เซสชันติวเตอร์นี้อิงตาม {lesson.title.get('th', 'บทเรียนที่เลือก')}.",
        ),
        selected_excerpt=lesson.subtitle.get("en", ""),
        quick_prompts=[
            "Explain the key line",
            "Quiz me on the lesson",
            "Translate the excerpt naturally",
        ],
        waveform=[4, 7, 10, 13, 8, 6, 3],
        available_actions=TUTOR_ACTIONS,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return await get_tutor_session(db, user, session.id)


async def send_tutor_message(db: AsyncSession, user: AppUser, payload: TutorMessageRequest) -> dict:
    session = await _get_session(db, user, payload.sessionId)
    lesson = await db.get(AppLesson, session.lesson_id)
    context = lesson.subtitle.get("en", "") if lesson else ""
    user_message = AppTutorMessage(
        id=f"user-{int(_utc_now().timestamp())}",
        session_id=session.id,
        role="user",
        text=payload.prompt,
        timestamp_label="Now",
        created_at=_utc_now(),
    )
    db.add(user_message)

    reply = generate_tutor_reply(payload.prompt, context, session.mode_id)
    assistant_message = AppTutorMessage(
        id=f"assistant-{int(_utc_now().timestamp())}",
        session_id=session.id,
        role="assistant",
        text=reply,
        timestamp_label="Sorbet AI",
        created_at=_utc_now(),
    )
    db.add(assistant_message)

    session.last_message_preview = loc(reply[:90], reply[:90])
    session.updated_at = _utc_now()
    await db.commit()
    return {
        "id": assistant_message.id,
        "role": assistant_message.role,
        "text": assistant_message.text,
        "timestampLabel": assistant_message.timestamp_label,
    }


async def save_tutor_feedback(db: AsyncSession, user: AppUser, payload: TutorFeedbackRequest) -> dict:
    session = await _get_session(db, user, payload.sessionId)
    db.add(
        AppTutorFeedback(
            id=f"feedback-{session.id}-{int(_utc_now().timestamp())}",
            session_id=session.id,
            rating=payload.rating,
            note=payload.note,
            created_at=_utc_now(),
        )
    )
    await db.commit()
    return {"saved": True}
