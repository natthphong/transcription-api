from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppLesson, AppTutorSession, AppUser, AppVocabItem, AppVocabReviewHistory, AppVideo
from app.services.constants import loc
from app.services.formatting import format_duration_label, humanize_relative
from app.services.lesson_service import list_lessons_for_user


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def build_recommendations(db: AsyncSession, user: AppUser) -> list[dict]:
    videos = (
        await db.execute(
            select(AppVideo)
            .join(AppLesson, AppLesson.id == AppVideo.lesson_id)
            .where(AppLesson.user_id == user.id)
            .order_by(AppVideo.updated_at.desc())
        )
    ).scalars().all()
    if videos:
        return [
            {
                "id": row.id,
                "title": dict(row.title or {}),
                "subtitle": dict(row.summary or {}),
                "durationLabel": format_duration_label(row.duration_seconds),
                "levelId": user.level_id,
                "phraseCount": max(1, len(row.quiz or [])),
                "accent": row.thumbnail_accent if row.thumbnail_accent in {"coral", "sky", "mint"} else "sky",
            }
            for row in videos
        ]

    lessons = await list_lessons_for_user(db, user)
    return [
        {
            "id": lesson["id"],
            "title": lesson["title"],
            "subtitle": lesson["subtitle"],
            "durationLabel": lesson["durationLabel"],
            "levelId": user.level_id,
            "phraseCount": lesson["extractedVocabCount"],
            "accent": lesson["thumbnailAccent"],
        }
        for lesson in lessons[:3]
    ]


async def build_home(db: AsyncSession, user: AppUser) -> dict:
    lessons = await list_lessons_for_user(db, user)
    recommendations = await build_recommendations(db, user)
    now = _utc_now()
    start_of_week = now - timedelta(days=6)

    daily_reviews = (
        await db.execute(
            select(
                func.date_trunc("day", AppVocabReviewHistory.created_at).label("day"),
                func.count(AppVocabReviewHistory.id).label("count"),
            )
            .where(
                AppVocabReviewHistory.user_id == user.id,
                AppVocabReviewHistory.created_at >= start_of_week,
            )
            .group_by("day")
            .order_by("day")
        )
    ).all()
    review_map = {row.day.date(): int(row.count) for row in daily_reviews if row.day}
    activity = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        activity.append(
            {
                "label": day.strftime("%a"),
                "minutes": review_map.get(day, 0) * 2,
                "active": day == now.date(),
            }
        )

    due_today_count = (
        await db.execute(
            select(func.count(AppVocabItem.id)).where(
                AppVocabItem.user_id == user.id,
                AppVocabItem.status_id.in_(["due", "difficult"]),
            )
        )
    ).scalar_one()
    completed_today_count = (
        await db.execute(
            select(func.count(AppVocabReviewHistory.id)).where(
                AppVocabReviewHistory.user_id == user.id,
                AppVocabReviewHistory.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )
    ).scalar_one()
    latest_tutor_session = (
        await db.execute(
            select(AppTutorSession)
            .where(AppTutorSession.user_id == user.id)
            .order_by(desc(AppTutorSession.updated_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    latest_lesson = (
        await db.execute(
            select(AppLesson)
            .where(AppLesson.user_id == user.id)
            .order_by(desc(AppLesson.last_activity_at), desc(AppLesson.updated_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    recent_activity = [
        {
            "id": "activity-reviews",
            "title": loc(f"Reviewed {completed_today_count} vocab cards", f"ทบทวนแฟลชการ์ดคำศัพท์ {completed_today_count} ใบ"),
            "detail": loc(
                "Most of them came from your recent lessons.",
                "ส่วนใหญ่มาจากบทเรียนล่าสุดของคุณ",
            ),
            "timeLabel": "Today",
        }
    ]
    if latest_tutor_session:
        recent_activity.append(
            {
                "id": "activity-tutor",
                "title": loc("Asked tutor about a recent lesson", "ถามติวเตอร์เกี่ยวกับบทเรียนล่าสุด"),
                "detail": dict(latest_tutor_session.last_message_preview or {}),
                "timeLabel": humanize_relative(latest_tutor_session.updated_at),
            }
        )
    if latest_lesson:
        recent_activity.append(
            {
                "id": "activity-import",
                "title": loc("Imported a new lesson", "นำเข้าบทเรียนใหม่"),
                "detail": dict(latest_lesson.subtitle or {}),
                "timeLabel": humanize_relative(latest_lesson.created_at),
            }
        )

    recent_lesson_body = (
        {
            "id": latest_lesson.id,
            "title": dict(latest_lesson.title or {}),
            "subtitle": dict(latest_lesson.subtitle or {}),
            "durationLabel": format_duration_label(latest_lesson.duration_seconds),
            "levelId": user.level_id,
            "phraseCount": latest_lesson.extracted_vocab_count,
            "accent": latest_lesson.thumbnail_accent,
        }
        if latest_lesson
        else {
            "id": "lesson-empty",
            "title": loc("No lessons yet"),
            "subtitle": loc("Import a YouTube link to get started."),
            "durationLabel": "00:00",
            "levelId": user.level_id,
            "phraseCount": 0,
            "accent": "coral",
        }
    )

    return {
        "userName": user.full_name.split()[0],
        "welcome": loc(f"Bonjour, {user.full_name.split()[0]}!", f"สวัสดี {user.full_name.split()[0]}!"),
        "subtitle": loc(
            "Ready to expand your lexicon today?",
            "พร้อมขยายคลังคำศัพท์ของคุณวันนี้หรือยัง?",
        ),
        "newWordsCount": due_today_count,
        "continueDeckId": "deck-french-gastronomy",
        "dailyGoalMinutes": user.daily_goal_minutes,
        "studyMinutesToday": completed_today_count * 2,
        "streakDays": user.streak_days,
        "activity": activity,
        "quickActions": [
            {
                "id": "quick-learn",
                "labelKey": "common.nav.learn",
                "description": loc(
                    "Import a new YouTube lesson or reopen one that is already in progress.",
                    "นำเข้าบทเรียน YouTube ใหม่ หรือกลับไปทำบทเรียนที่กำลังเรียนอยู่",
                ),
                "href": "/learn",
                "icon": "book-open",
            },
            {
                "id": "quick-tutor",
                "labelKey": "common.nav.tutor",
                "description": loc(
                    "Ask the tutor to explain the clip you studied most recently.",
                    "ถามติวเตอร์ให้ช่วยอธิบายคลิปที่คุณเพิ่งเรียนล่าสุด",
                ),
                "href": f"/tutor?lessonId={latest_lesson.id}" if latest_lesson else "/tutor",
                "icon": "sparkles",
            },
            {
                "id": "quick-vocab",
                "labelKey": "common.nav.vocab",
                "description": loc(
                    "Clear your due vocab queue and keep your streak alive.",
                    "เคลียร์คิวคำศัพท์ที่ถึงกำหนดและรักษาสตรีคของคุณไว้",
                ),
                "href": "/vocab",
                "icon": "layers-3",
            },
        ],
        "recentActivity": recent_activity,
        "recentLesson": recent_lesson_body,
        "recommendations": recommendations[:2] or [recent_lesson_body],
    }


async def build_daily_progress(db: AsyncSession, user: AppUser) -> dict:
    now = _utc_now()
    completed_today = (
        await db.execute(
            select(func.count(AppVocabReviewHistory.id)).where(
                AppVocabReviewHistory.user_id == user.id,
                AppVocabReviewHistory.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )
    ).scalar_one()
    new_words = (
        await db.execute(
            select(func.count(AppVocabItem.id)).where(AppVocabItem.user_id == user.id)
        )
    ).scalar_one()
    return {
        "streakDays": user.streak_days,
        "goalMinutes": user.daily_goal_minutes,
        "minutesCompleted": completed_today * 2,
        "newWordsLearned": new_words,
    }
