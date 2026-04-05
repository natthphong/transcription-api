from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import load_settings
from app.models import AppLineAccount, AppUser
from app.services.api import ApiError
from app.services.constants import loc
from app.services.formatting import humanize_relative
from app.services.security import generate_token


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_line_config() -> dict:
    settings = load_settings()
    enabled = bool(settings.Line and settings.Line.channelId and settings.Line.channelSecret)
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
