from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.routes.deps import ensure_seeded_db
from app.schemas import ApiEnvelope, ClipItem, LessonCreateBody, LessonCreateRequest, LessonDetail, LessonSummary, VideoDetail
from app.services.api import created, success
from app.services.auth_service import resolve_session
from app.services.lesson_service import (
    create_lesson_from_import,
    get_clip_for_user,
    get_lesson_detail_for_user,
    get_video_for_user,
    list_clips_for_user,
    list_lessons_for_user,
    list_videos_for_user,
)
from app.services.youtube_jobs import process_youtube_job

router = APIRouter(prefix="/api/v1", tags=["Lessons"])


@router.post(
    "/lessons",
    response_model=ApiEnvelope[LessonCreateBody],
    summary="Import Lesson",
    description="Create a new lesson workspace from a YouTube URL and start transcript processing in the background.",
)
async def create_lesson(payload: LessonCreateRequest, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    lesson, clip, job = await create_lesson_from_import(db, context.user, payload)
    asyncio.create_task(process_youtube_job(job.id, None))
    return created(
        {
            "lessonId": lesson.id,
            "clipId": clip.id,
            "status": "processing",
            "nextRoute": f"/learn/{lesson.id}",
        },
        message="lesson created",
    )


@router.get(
    "/lessons",
    response_model=ApiEnvelope[list[LessonSummary]],
    summary="List Lessons",
    description="Return lesson summaries for the authenticated learner.",
)
async def list_lessons(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_lessons_for_user(db, context.user), message="success")


@router.get(
    "/lessons/{lesson_id}",
    response_model=ApiEnvelope[LessonDetail],
    summary="Lesson Detail",
    description="Return the full lesson detail payload including transcript blocks, vocabulary, tabs, and actions.",
)
async def lesson_detail(lesson_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_lesson_detail_for_user(db, context.user, lesson_id), message="success")


@router.get(
    "/clip",
    response_model=ApiEnvelope[list[ClipItem]],
    summary="List Clips",
    description="Return imported clip records and transcript processing state.",
)
async def list_clips(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_clips_for_user(db, context.user), message="success")


@router.get(
    "/clip/{clip_id}",
    response_model=ApiEnvelope[ClipItem],
    summary="Clip Detail",
    description="Return a single imported clip record.",
)
async def clip_detail(clip_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_clip_for_user(db, context.user, clip_id), message="success")


@router.get(
    "/videos",
    response_model=ApiEnvelope[list[VideoDetail]],
    summary="List Videos",
    description="Return video quiz/media entries linked to lessons.",
)
async def list_videos(request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await list_videos_for_user(db, context.user), message="success")


@router.get(
    "/videos/{video_id}",
    response_model=ApiEnvelope[VideoDetail],
    summary="Video Detail",
    description="Return a single video quiz/media entry linked to a lesson.",
)
async def video_detail(video_id: str, request: Request, db: AsyncSession = Depends(ensure_seeded_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(await get_video_for_user(db, context.user, video_id), message="success")
