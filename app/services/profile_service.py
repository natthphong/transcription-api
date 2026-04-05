from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppUser
from app.schemas import ProfileUpdateRequest
from app.services.auth_service import build_user_profile


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_profile(user: AppUser) -> dict:
    return build_user_profile(user).model_dump()


async def update_profile(db: AsyncSession, user: AppUser, payload: ProfileUpdateRequest) -> dict:
    if payload.nativeLanguageId is not None:
        user.native_language_id = payload.nativeLanguageId
    if payload.targetLanguageId is not None:
        user.target_language_id = payload.targetLanguageId
    if payload.levelId is not None:
        user.level_id = payload.levelId
    if payload.weeklyFocusId is not None:
        user.weekly_focus_id = payload.weeklyFocusId
    if payload.appLocale is not None:
        user.app_locale = payload.appLocale
    if payload.dailyGoalMinutes is not None:
        user.daily_goal_minutes = payload.dailyGoalMinutes
    if payload.interests is not None:
        user.interests = payload.interests

    notifications = dict(user.notification_preferences or {})
    if payload.practiceReminders is not None:
        notifications["practiceReminders"] = payload.practiceReminders
    if payload.weeklyDigest is not None:
        notifications["weeklyDigest"] = payload.weeklyDigest
    if payload.tutorFollowUps is not None:
        notifications["tutorFollowUps"] = payload.tutorFollowUps
    user.notification_preferences = notifications

    tutor_preferences = dict(user.tutor_preferences or {})
    if payload.voiceId is not None:
        tutor_preferences["voiceId"] = payload.voiceId
    if payload.tutorModeId is not None:
        tutor_preferences["modeId"] = payload.tutorModeId
    if payload.autoPlayPronunciation is not None:
        tutor_preferences["autoPlayPronunciation"] = payload.autoPlayPronunciation
    user.tutor_preferences = tutor_preferences

    user.updated_at = _utc_now()
    await db.commit()
    await db.refresh(user)
    return build_user_profile(user).model_dump()
