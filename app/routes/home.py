from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, DailyProgressBody, HomeBody, HomeRecommendation
from app.services.api import success
from app.services.auth_service import resolve_session
from app.services.home_service import build_daily_progress, build_home, build_recommendations

router = APIRouter(prefix="/api/v1", tags=["Home"])


@router.get(
    "/home",
    response_model=ApiEnvelope[HomeBody],
    summary="Home Dashboard",
    description="Return the learner dashboard payload for the home screen.",
)
async def home(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await build_home(db, context.user), message="success")


@router.get(
    "/recommendations",
    response_model=ApiEnvelope[list[HomeRecommendation]],
    summary="Recommendations",
    description="Return recommended lessons or videos for the learner.",
)
async def recommendations(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await build_recommendations(db, context.user), message="success")


@router.get(
    "/daily-progress",
    response_model=ApiEnvelope[DailyProgressBody],
    summary="Daily Progress",
    description="Return summary metrics for the learner's current daily progress.",
)
async def daily_progress(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await build_daily_progress(db, context.user), message="success")
