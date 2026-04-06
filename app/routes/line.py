from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import (
    ApiEnvelope,
    LineConfigBody,
    LineLoginBody,
    LineProfile,
    LineProfileSyncBody,
    LineProfileSyncRequest,
    LineStatus,
    LineWebhookBody,
)
from app.services.api import ApiError, created, success
from app.services.auth_service import resolve_session, set_session_cookies
from app.services.line_service import (
    accept_webhook,
    get_line_config,
    get_line_profile,
    get_line_status,
    start_line_login,
    sync_line_profile,
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


@router.post(
    "/profile",
    response_model=ApiEnvelope[LineProfileSyncBody],
    summary="Sync LIFF Profile",
    description=(
        "Persist the LIFF profile returned by `liff.getProfile()`, store the LINE user id on the backend, "
        "and issue a backend session so the frontend can continue into authenticated screens."
    ),
)
async def line_profile_sync(
    payload: LineProfileSyncRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(ensure_seeded_db),
):
    context = None
    try:
        context = await resolve_session(db, request, allow_compatibility_fallback=False)
    except ApiError as exc:
        if exc.code != "UNAUTHORIZED":
            raise
        context = None

    body, session = await sync_line_profile(db, payload, current_user=context.user if context else None)
    response = created(body, message="line profile synced")
    set_session_cookies(response, session)
    return response
