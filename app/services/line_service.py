from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_settings
from app.models import AppLineAccount, AppUser, AppUserSession
from app.schemas import LineProfileSyncRequest
from app.services.auth_service import build_auth_session, create_session
from app.services.api import ApiError
from app.services.constants import loc
from app.services.formatting import humanize_relative
from app.services.security import generate_token, hash_password


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_line_config() -> dict:
    settings = load_settings()
    enabled = bool(settings.Line and settings.Line.liffId and settings.Line.channelId and settings.Line.channelSecret)
    redirect_uri = settings.Line.loginRedirectURI if settings.Line and settings.Line.loginRedirectURI else "/page/webhook-line"
    return {
        "enabled": enabled,
        "liffId": settings.Line.liffId if settings.Line else "",
        "redirectUri": redirect_uri,
        "webhookPath": "/api/v1/line/webhook",
        "mockMode": not enabled,
    }


async def get_line_status(db: AsyncSession, user: AppUser) -> dict:
    account = (
        await db.execute(select(AppLineAccount).where(AppLineAccount.user_id == user.id).limit(1))
    ).scalar_one_or_none()
    if not account:
        return {
            "connected": False,
            "displayName": user.full_name,
            "providerLabel": "LINE Login",
            "liffReady": False,
            "lastSyncedLabel": "Not linked",
            "note": loc(
                "Connect LINE to unlock future LIFF sign-in and messaging flows.",
                "เชื่อมต่อ LINE เพื่อใช้งาน LIFF และเวิร์กโฟลว์การส่งข้อความในอนาคต",
            ),
        }
    return {
        "connected": True,
        "displayName": account.display_name,
        "providerLabel": "LINE Login",
        "liffReady": True,
        "lastSyncedLabel": humanize_relative(account.last_synced_at),
        "note": loc(
            "LINE account is connected and ready for future LIFF-based sign-in flows.",
            "บัญชี LINE เชื่อมต่อแล้วและพร้อมสำหรับขั้นตอนลงชื่อเข้าใช้ด้วย LIFF ในอนาคต",
        ),
    }


async def get_line_profile(db: AsyncSession, user: AppUser) -> dict:
    account = (
        await db.execute(select(AppLineAccount).where(AppLineAccount.user_id == user.id).limit(1))
    ).scalar_one_or_none()
    if not account:
        raise ApiError(404, "PROFILE_NOT_FOUND", "line profile not found")
    return {
        "userId": account.line_user_id,
        "displayName": account.display_name,
        "statusMessage": account.status_message,
        "pictureAccent": account.picture_accent,
        "language": account.language,
    }


def start_line_login() -> dict:
    settings = load_settings()
    config = get_line_config()
    state = generate_token("line-state")
    if not config["enabled"]:
        return {"redirectUrl": f"{config['redirectUri']}?mode=mock", "state": state}
    params = urlencode(
        {
            "response_type": "code",
            "client_id": settings.Line.channelId,
            "redirect_uri": settings.Line.loginRedirectURI,
            "state": state,
            "scope": "profile openid",
        }
    )
    return {"redirectUrl": f"https://access.line.me/oauth2/v2.1/authorize?{params}", "state": state}


def _line_picture_accent(line_user_id: str) -> str:
    accents = ["coral", "sky", "mint"]
    digest = hashlib.sha256(line_user_id.encode("utf-8")).hexdigest()
    return accents[int(digest[:2], 16) % len(accents)]


def _line_user_seed(line_user_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(line_user_id.encode("utf-8")).hexdigest()
    return digest[:12], digest[:24]


def _avatar_initials(display_name: str) -> str:
    parts = [part for part in display_name.strip().split() if part]
    if not parts:
        return "LI"
    return "".join(part[:1] for part in parts[:2]).upper() or "LI"


async def _create_line_user(db: AsyncSession, line_user_id: str, display_name: str, language: str | None) -> AppUser:
    short_id, email_seed = _line_user_seed(line_user_id)
    normalized_name = display_name.strip() or "LINE Learner"
    locale = language or "en"
    user = AppUser(
        id=f"user-line-{short_id}",
        username=f"line-{short_id}",
        password_hash=hash_password(generate_token("line-secret")),
        full_name=normalized_name,
        email=f"line-{email_seed}@line.local",
        avatar_initials=_avatar_initials(normalized_name),
        membership_tier="starter",
        native_language_id="thai",
        target_language_id="english",
        level_id="beginner",
        weekly_focus_id="steady",
        interests=["conversation"],
        streak_days=0,
        daily_goal_minutes=15,
        timezone="Asia/Bangkok",
        app_locale=locale if locale in {"en", "th"} else "en",
        goal_summary=loc(
            "Learn from short LINE-friendly lessons and daily review.",
            "เรียนจากบทเรียนสั้นที่เหมาะกับ LINE และทบทวนทุกวัน",
        ),
        notification_preferences={
            "practiceReminders": True,
            "weeklyDigest": False,
            "tutorFollowUps": True,
        },
        tutor_preferences={
            "voiceId": "sorbet",
            "modeId": "coach",
            "autoPlayPronunciation": True,
        },
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    db.add(user)
    await db.flush()
    return user


async def sync_line_profile(
    db: AsyncSession,
    payload: LineProfileSyncRequest,
    current_user: AppUser | None = None,
) -> tuple[dict, AppUserSession]:
    existing_account = (
        await db.execute(select(AppLineAccount).where(AppLineAccount.line_user_id == payload.userId).limit(1))
    ).scalar_one_or_none()

    if current_user and existing_account and existing_account.user_id != current_user.id:
        raise ApiError(403, "FORBIDDEN", "line account already linked to another learner")

    user = current_user
    if existing_account and user is None:
        user = await db.get(AppUser, existing_account.user_id)
    if user is None:
        user = await _create_line_user(db, payload.userId, payload.displayName, payload.language)

    account = existing_account
    if account is None:
        account = (
            await db.execute(select(AppLineAccount).where(AppLineAccount.user_id == user.id).limit(1))
        ).scalar_one_or_none()
        if account and account.line_user_id != payload.userId:
            raise ApiError(403, "FORBIDDEN", "learner already linked to a different line account")

    if account is None:
        account = AppLineAccount(
            id=generate_token("line-account"),
            user_id=user.id,
            line_user_id=payload.userId,
            display_name=payload.displayName,
            status_message=payload.statusMessage or "",
            picture_accent=_line_picture_accent(payload.userId),
            language=payload.language or "en",
            last_synced_at=_utc_now(),
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        db.add(account)
    else:
        account.line_user_id = payload.userId
        account.display_name = payload.displayName
        account.status_message = payload.statusMessage or ""
        account.language = payload.language or account.language or "en"
        account.picture_accent = account.picture_accent or _line_picture_accent(payload.userId)
        account.last_synced_at = _utc_now()
        account.updated_at = _utc_now()

    if not user.full_name:
        user.full_name = payload.displayName
    user.updated_at = _utc_now()

    await db.commit()
    await db.refresh(user)
    await db.refresh(account)

    session = await create_session(db, user)
    profile = {
        "userId": account.line_user_id,
        "displayName": account.display_name,
        "statusMessage": account.status_message,
        "pictureAccent": account.picture_accent,
        "language": account.language,
    }
    return {
        "connected": True,
        "redirectTo": "/home",
        "profile": profile,
        "session": build_auth_session(user, session).model_dump(),
    }, session


def verify_line_signature(signature: str | None, body: bytes) -> None:
    settings = load_settings()
    if not settings.Line or not settings.Line.channelSecret:
        raise ApiError(400, "LINE_CONFIG_MISSING", "line config missing")
    if not signature:
        raise ApiError(401, "LINE_SIGNATURE_INVALID", "line signature invalid")
    digest = hmac.new(
        settings.Line.channelSecret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    if not hmac.compare_digest(signature, expected):
        raise ApiError(401, "LINE_SIGNATURE_INVALID", "line signature invalid")


def accept_webhook() -> dict:
    return {"accepted": True}
