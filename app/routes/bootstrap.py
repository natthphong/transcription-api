from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, BootstrapBody
from app.services.api import success
from app.services.auth_service import resolve_session
from app.services.bootstrap_service import build_bootstrap

router = APIRouter(prefix="/api/v1", tags=["Bootstrap"])


@router.get(
    "/bootstrap",
    response_model=ApiEnvelope[BootstrapBody],
    summary="Bootstrap App",
    description="Return global app bootstrap state including feature flags, session, user, and bottom navigation.",
)
async def bootstrap(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(build_bootstrap(context.user, context.session), message="success")
