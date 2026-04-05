from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppLesson, AppReviewSession, AppUser, AppVocabItem, AppVocabReviewHistory
from app.services.api import ApiError
from app.services.constants import FLASHCARD_REVIEW_OPTIONS, loc
from app.services.formatting import due_label
from app.services.lesson_service import get_lesson_detail_for_user


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_vocab_items(db: AsyncSession, user: AppUser) -> list[dict]:
    lessons = (
        await db.execute(select(AppLesson).where(AppLesson.user_id == user.id))
    ).scalars().all()
    lesson_map = {lesson.id: lesson for lesson in lessons}
    items = (
        await db.execute(
            select(AppVocabItem)
            .where(AppVocabItem.user_id == user.id)
            .order_by(desc(AppVocabItem.updated_at), AppVocabItem.term.asc())
        )
    ).scalars().all()
    return [
        {
            "id": item.id,
            "term": item.term,
            "translation": dict(item.translation or {}),
            "pronunciation": item.pronunciation,
            "sourceLessonId": item.source_lesson_id,
            "sourceLessonTitle": dict((lesson_map.get(item.source_lesson_id).title if lesson_map.get(item.source_lesson_id) else loc("Unknown lesson"))),
            "statusId": item.status_id,
            "dueLabel": due_label(item.due_at, item.status_id),
            "example": item.example,
            "notes": dict(item.notes or {}),
        }
        for item in items
    ]


async def _load_due_items(db: AsyncSession, user: AppUser) -> list[AppVocabItem]:
    now = _utc_now()
    items = (
        await db.execute(
            select(AppVocabItem)
            .where(
                AppVocabItem.user_id == user.id,
                AppVocabItem.status_id.in_(["due", "difficult"]),
            )
            .order_by(AppVocabItem.due_at.asc().nullsfirst(), AppVocabItem.updated_at.desc())
        )
    ).scalars().all()
    return [item for item in items if item.due_at is None or item.due_at <= now or item.status_id == "difficult"]


async def _build_deck(db: AsyncSession, user: AppUser) -> dict:
    due_items = await _load_due_items(db, user)
    lessons = (
        await db.execute(
            select(AppLesson).where(AppLesson.user_id == user.id).order_by(desc(AppLesson.updated_at))
        )
    ).scalars().all()
    title = lessons[0].title if lessons else loc("Daily review")
    subtitle = (
        loc("Audio-backed vocabulary from your latest lesson", "คำศัพท์พร้อมเสียงจากบทเรียนล่าสุดของคุณ")
        if lessons
        else loc("Daily review deck")
    )
    reviewed_count = (
        await db.execute(
            select(func.count(AppVocabReviewHistory.id)).where(AppVocabReviewHistory.user_id == user.id)
        )
    ).scalar_one()
    return {
        "id": "deck-french-gastronomy",
        "title": dict(title or {}),
        "subtitle": dict(subtitle),
        "dueCount": len(due_items),
        "reviewedCount": int(reviewed_count),
        "colorAccent": lessons[0].thumbnail_accent if lessons else "coral",
    }


async def _ensure_review_session(db: AsyncSession, user: AppUser) -> AppReviewSession:
    session = (
        await db.execute(
            select(AppReviewSession)
            .where(AppReviewSession.user_id == user.id, AppReviewSession.finished_at.is_(None))
            .order_by(desc(AppReviewSession.updated_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if session:
        return session

    due_items = await _load_due_items(db, user)
    if not due_items:
        fallback = (
            await db.execute(
                select(AppVocabItem).where(AppVocabItem.user_id == user.id).order_by(desc(AppVocabItem.updated_at)).limit(1)
            )
        ).scalar_one_or_none()
        due_items = [fallback] if fallback else []

    session = AppReviewSession(
        id="session-1",
        user_id=user.id,
        deck_id="deck-french-gastronomy",
        source_label="Lesson vocab",
        queue=[item.id for item in due_items if item is not None],
        current_index=0,
        total_count=len(due_items),
        note=loc(
            "Tap the card to keep the meaning visible while you decide how well you knew it.",
            "แตะการ์ดเพื่อเปิดความหมายค้างไว้ขณะประเมินว่าคุณจำได้ดีแค่ไหน",
        ),
        review_options=FLASHCARD_REVIEW_OPTIONS,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def _session_card_item(db: AsyncSession, session: AppReviewSession) -> AppVocabItem | None:
    if not session.queue:
        return None
    if session.current_index >= len(session.queue):
        session.current_index = max(0, len(session.queue) - 1)
    item_id = session.queue[session.current_index]
    return await db.get(AppVocabItem, item_id)


async def get_review_session_payload(db: AsyncSession, user: AppUser, session: AppReviewSession | None = None) -> dict:
    session = session or await _ensure_review_session(db, user)
    item = await _session_card_item(db, session)
    if item is None:
        return {
            "id": session.id,
            "deckId": session.deck_id,
            "deckTitle": loc("Daily review"),
            "progressCurrent": session.current_index,
            "progressTotal": max(0, session.total_count),
            "sourceLabel": session.source_label,
            "prompt": "",
            "translation": "",
            "note": dict(session.note or {}),
            "reviewOptions": list(session.review_options or []),
        }

    lesson = await db.get(AppLesson, item.source_lesson_id)
    deck_title = lesson.title if lesson else loc("Daily review")
    return {
        "id": session.id,
        "deckId": session.deck_id,
        "deckTitle": dict(deck_title or {}),
        "progressCurrent": min(session.current_index + 1, max(1, session.total_count)),
        "progressTotal": max(1, session.total_count),
        "sourceLabel": session.source_label,
        "prompt": item.example or item.term,
        "translation": next(iter((item.translation or {}).values()), item.term),
        "note": dict(session.note or {}),
        "reviewOptions": list(session.review_options or []),
    }


async def build_vocab_dashboard(db: AsyncSession, user: AppUser) -> dict:
    due_today_count = len(await _load_due_items(db, user))
    completed_today_count = (
        await db.execute(
            select(func.count(AppVocabReviewHistory.id)).where(
                AppVocabReviewHistory.user_id == user.id,
                AppVocabReviewHistory.created_at >= _utc_now().replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )
    ).scalar_one()
    difficult_count = (
        await db.execute(
            select(func.count(AppVocabItem.id)).where(
                AppVocabItem.user_id == user.id,
                AppVocabItem.status_id == "difficult",
            )
        )
    ).scalar_one()
    session = await _ensure_review_session(db, user)
    return {
        "dueTodayCount": due_today_count,
        "completedTodayCount": int(completed_today_count),
        "difficultCount": int(difficult_count),
        "reviewSession": await get_review_session_payload(db, user, session),
    }


def _schedule(answer: str, item: AppVocabItem) -> tuple[str, datetime]:
    now = _utc_now()
    if answer == "again":
        return "due", now + timedelta(minutes=1)
    if answer == "hard":
        item.interval_days = max(2, item.interval_days or 2)
        return "difficult", now + timedelta(days=int(item.interval_days))
    if answer == "easy":
        item.interval_days = max(7, (item.interval_days or 2) * 2)
        return "mastered", now + timedelta(days=int(item.interval_days))
    item.interval_days = max(4, (item.interval_days or 2) * 1.8)
    next_status = "mastered" if item.repetitions >= 2 else "due"
    return next_status, now + timedelta(days=int(item.interval_days))


async def record_review_answer(db: AsyncSession, user: AppUser, session_id: str, answer: str) -> dict:
    session = await db.get(AppReviewSession, session_id)
    if not session or session.user_id != user.id:
        raise ApiError(404, "VOCAB_ITEM_NOT_FOUND", "review session not found")
    item = await _session_card_item(db, session)
    if not item:
        raise ApiError(404, "VOCAB_ITEM_NOT_FOUND", "vocab item not found")

    previous_status = item.status_id
    next_status, next_due_at = _schedule(answer, item)
    item.status_id = next_status
    item.due_at = next_due_at
    item.repetitions += 1
    item.last_reviewed_at = _utc_now()
    item.updated_at = _utc_now()

    history = AppVocabReviewHistory(
        id=f"{session.id}-{item.id}-{int(_utc_now().timestamp())}",
        vocab_item_id=item.id,
        user_id=user.id,
        review_session_id=session.id,
        answer=answer,
        previous_status_id=previous_status,
        next_status_id=next_status,
        next_due_at=next_due_at,
        created_at=_utc_now(),
    )
    db.add(history)

    if session.current_index < max(0, len(session.queue) - 1):
        session.current_index += 1
    else:
        session.finished_at = _utc_now()
    session.updated_at = _utc_now()

    await db.commit()
    return {"accepted": True, "nextDueLabel": due_label(next_due_at, next_status)}


async def list_flashcard_decks(db: AsyncSession, user: AppUser) -> list[dict]:
    return [await _build_deck(db, user)]


async def get_flashcard_deck(db: AsyncSession, user: AppUser, deck_id: str) -> dict:
    deck = await _build_deck(db, user)
    if deck["id"] != deck_id:
        raise ApiError(404, "VOCAB_ITEM_NOT_FOUND", "deck not found")
    return deck


async def start_flashcard_session(db: AsyncSession, user: AppUser, deck_id: str | None = None) -> dict:
    session = await _ensure_review_session(db, user)
    if deck_id and deck_id != session.deck_id:
        session.deck_id = deck_id
        session.updated_at = _utc_now()
        await db.commit()
    return {"sessionId": session.id, "nextRoute": "/flashcards/review"}


async def get_flashcard_session(db: AsyncSession, user: AppUser, session_id: str) -> dict:
    session = await db.get(AppReviewSession, session_id)
    if not session or session.user_id != user.id:
        raise ApiError(404, "VOCAB_ITEM_NOT_FOUND", "review session not found")
    return await get_review_session_payload(db, user, session)


async def answer_flashcard_session(db: AsyncSession, user: AppUser, session_id: str, answer: str) -> dict:
    result = await record_review_answer(db, user, session_id, answer)
    session = await db.get(AppReviewSession, session_id)
    next_card_id = None
    if session and session.queue and session.current_index < len(session.queue):
        next_card_id = session.queue[session.current_index]
    return {"saved": True, "nextCardId": next_card_id, **result}


async def finish_flashcard_session(db: AsyncSession, user: AppUser, session_id: str) -> dict:
    session = await db.get(AppReviewSession, session_id)
    if not session or session.user_id != user.id:
        raise ApiError(404, "VOCAB_ITEM_NOT_FOUND", "review session not found")
    session.finished_at = _utc_now()
    session.updated_at = _utc_now()
    await db.commit()
    return {
        "saved": True,
        "summary": {
            "cardsReviewed": session.current_index + (1 if session.total_count else 0),
            "retention": 91,
        },
    }
