from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, LineConfigBody, LineLoginBody, LineProfile, LineStatus, LineWebhookBody
from app.services.api import created, success
from app.services.auth_service import resolve_session
from app.services.line_service import (
    accept_webhook,
    get_line_config,
    get_line_profile,
    get_line_status,
    start_line_login,
    verify_line_signature,
)

router = APIRouter(prefix="/api/v1/line", tags=["LINE"])


@router.get("/config", response_model=ApiEnvelope[LineConfigBody], summary="LINE Frontend Config")
async def line_config():
    return success(get_line_config(), message="success")


@router.get("/status", response_model=ApiEnvelope[LineStatus], summary="LINE Connection Status")
async def line_status(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_line_status(db, context.user), message="success")


@router.post("/login", response_model=ApiEnvelope[LineLoginBody], summary="Start LINE Login")
async def line_login():
    return created(start_line_login(), message="line login started")


@router.post("/webhook", response_model=ApiEnvelope[LineWebhookBody], summary="Receive LINE Webhook")
async def line_webhook(request: Request, x_line_signature: str | None = Header(default=None), db: AsyncSession = Depends(ensure_seeded_db)):
    body = await request.body()
    verify_line_signature(x_line_signature, body)
    return success(accept_webhook(), message="webhook accepted")


@router.get("/profile", response_model=ApiEnvelope[LineProfile], summary="LINE Profile")
async def line_profile(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_line_profile(db, context.user), message="success")
