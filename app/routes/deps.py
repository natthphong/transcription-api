from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import AppUser
from app.services.auth_service import SessionContext, resolve_session
from app.services.seed_service import ensure_seed_data


async def ensure_seeded_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    await ensure_seed_data(db)
    return db


async def get_current_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SessionContext:
    return await resolve_session(db, request, allow_compatibility_fallback=True)


async def get_current_user(
    context: SessionContext = Depends(get_current_context),
) -> AppUser:
    return context.user
