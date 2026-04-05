from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, ProfileUpdateRequest, UserProfile
from app.services.api import success
from app.services.auth_service import resolve_session
from app.services.profile_service import get_profile, update_profile

router = APIRouter(prefix="/api/v1", tags=["Profile"])


@router.get(
    "/profile",
    response_model=ApiEnvelope[UserProfile],
    summary="Get Profile",
    description="Return the authenticated learner profile and learning preferences.",
)
async def profile(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_profile(context.user), message="success")


@router.patch(
    "/profile",
    response_model=ApiEnvelope[UserProfile],
    summary="Update Profile",
    description="Update profile settings, learning preferences, and notification toggles.",
)
async def profile_update(payload: ProfileUpdateRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await update_profile(db, context.user, payload), message="profile updated")
