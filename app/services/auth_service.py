from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_settings
from app.models import AppLineAccount, AppUser, AppUserSession
from app.schemas import AuthSession, UserProfile
from app.services.api import ApiError
from app.services.seed_service import ensure_seed_data
from app.services.security import generate_token, hash_password, verify_password

ACCESS_COOKIE_NAME = "fluid_access_token"
REFRESH_COOKIE_NAME = "fluid_refresh_token"


@dataclass
class SessionContext:
    user: AppUser
    session: AppUserSession


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _expires_at(hours: int) -> datetime:
    return _utc_now() + timedelta(hours=hours)


def build_user_profile(user: AppUser) -> UserProfile:
    return UserProfile(
        id=user.id,
        fullName=user.full_name,
        email=user.email,
        avatarInitials=user.avatar_initials,
        membershipTier=user.membership_tier,
        nativeLanguageId=user.native_language_id,
        targetLanguageId=user.target_language_id,
        levelId=user.level_id,
        weeklyFocusId=user.weekly_focus_id,
        interests=list(user.interests or []),
        streakDays=user.streak_days,
        dailyGoalMinutes=user.daily_goal_minutes,
        timezone=user.timezone,
        appLocale=user.app_locale,
        goalSummary=dict(user.goal_summary or {}),
        notificationPreferences=dict(user.notification_preferences or {}),
        tutorPreferences=dict(user.tutor_preferences or {}),
    )


def build_auth_session(user: AppUser, session: AppUserSession, redirect_to: str = "/home") -> AuthSession:
    return AuthSession(
        loggedIn=True,
        accessToken=session.access_token,
        refreshToken=session.refresh_token,
        currentRole=session.current_role,
        redirectTo=redirect_to,
        user=build_user_profile(user),
    )


def _set_session_cookies(response: Response, session: AppUserSession) -> None:
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        session.access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 12,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        session.refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 14,
    )


def set_session_cookies(response: Response, session: AppUserSession) -> None:
    _set_session_cookies(response, session)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)


async def get_or_create_user(db: AsyncSession, username: str, password: str) -> AppUser:
    user = (
        await db.execute(select(AppUser).where(AppUser.username == username).limit(1))
    ).scalar_one_or_none()
    if user:
        if not verify_password(password, user.password_hash):
            raise ApiError(401, "UNAUTHORIZED", "missing or invalid session")
        return user

    base_name = username.strip() or "Learner"
    new_user = AppUser(
        id=f"user-{base_name.lower().replace(' ', '-')}",
        username=base_name,
        password_hash=hash_password(password),
        full_name=base_name if base_name != "alex" else "Alex Rivera",
        email=f"{base_name.lower().replace(' ', '.')}@example.com",
        avatar_initials="".join(part[:1] for part in base_name.split()[:2]).upper() or "FL",
        membership_tier="starter",
        native_language_id="thai",
        target_language_id="english",
        level_id="beginner",
        weekly_focus_id="steady",
        interests=["conversation"],
        streak_days=0,
        daily_goal_minutes=15,
        timezone="UTC",
        app_locale="en",
        goal_summary={
            "en": "Build a steady learning habit from short video lessons.",
            "th": "สร้างนิสัยการเรียนอย่างสม่ำเสมอจากบทเรียนวิดีโอสั้น",
        },
        notification_preferences={
            "practiceReminders": True,
            "weeklyDigest": False,
            "tutorFollowUps": False,
        },
        tutor_preferences={
            "voiceId": "sorbet",
            "modeId": "coach",
            "autoPlayPronunciation": True,
        },
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def create_session(db: AsyncSession, user: AppUser) -> AppUserSession:
    session = AppUserSession(
        id=generate_token("session"),
        user_id=user.id,
        access_token=generate_token("access"),
        refresh_token=generate_token("refresh"),
        current_role="learner",
        expires_at=_expires_at(12),
        refresh_expires_at=_expires_at(24 * 14),
        is_active=True,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def resolve_session(
    db: AsyncSession,
    request: Request,
    allow_compatibility_fallback: bool = True,
) -> SessionContext:
    await ensure_seed_data(db)

    auth_header = request.headers.get("authorization", "")
    access_token = ""
    if auth_header.lower().startswith("bearer "):
        access_token = auth_header[7:].strip()
    if not access_token:
        access_token = request.cookies.get(ACCESS_COOKIE_NAME, "")

    session = None
    if access_token:
        session = (
            await db.execute(
                select(AppUserSession).where(
                    AppUserSession.access_token == access_token,
                    AppUserSession.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()

    settings = load_settings()
    if not session and allow_compatibility_fallback and settings.Core and settings.Core.compatibilityUseLatestSession:
        session = (
            await db.execute(
                select(AppUserSession)
                .where(AppUserSession.is_active.is_(True))
                .order_by(desc(AppUserSession.updated_at), desc(AppUserSession.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()

    if not session:
        raise ApiError(401, "UNAUTHORIZED", "missing or invalid session")

    user = await db.get(AppUser, session.user_id)
    if not user:
        raise ApiError(401, "UNAUTHORIZED", "missing or invalid session")
    return SessionContext(user=user, session=session)


async def refresh_session(db: AsyncSession, session: AppUserSession) -> AppUserSession:
    session.access_token = generate_token("access")
    session.refresh_token = generate_token("refresh")
    session.expires_at = _expires_at(12)
    session.refresh_expires_at = _expires_at(24 * 14)
    session.updated_at = _utc_now()
    await db.commit()
    await db.refresh(session)
    return session


async def logout_session(db: AsyncSession, request: Request) -> None:
    try:
        context = await resolve_session(db, request, allow_compatibility_fallback=False)
    except ApiError:
        return
    context.session.is_active = False
    context.session.updated_at = _utc_now()
    await db.commit()


async def auth_providers(db: AsyncSession, user: AppUser | None) -> list[dict]:
    line_connected = False
    if user:
        line_connected = (
            await db.execute(select(AppLineAccount).where(AppLineAccount.user_id == user.id).limit(1))
        ).scalar_one_or_none() is not None
    return [
        {
            "id": "line",
            "labelKey": "dropdowns.providers.line",
            "connected": line_connected,
            "primary": True,
            "type": "oauth",
            "icon": "message-circle-more",
        },
        {
            "id": "google",
            "labelKey": "dropdowns.providers.google",
            "connected": False,
            "primary": False,
            "type": "oauth",
            "icon": "fingerprint",
        },
        {
            "id": "email",
            "labelKey": "dropdowns.providers.email",
            "connected": user is not None,
            "primary": False,
            "type": "email",
            "icon": "mail",
        },
    ]
