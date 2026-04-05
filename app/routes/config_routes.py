from __future__ import annotations

from fastapi import APIRouter

from app.schemas import ApiEnvelope, SelectOption
from app.services.api import success
from app.services.config_service import (
    get_languages,
    get_lesson_categories,
    get_lesson_sorts,
    get_lesson_statuses,
    get_levels,
    get_tutor_modes,
    get_vocab_statuses,
    get_voices,
)

router = APIRouter(prefix="/api/v1/config", tags=["Config"])


@router.get("/languages", response_model=ApiEnvelope[list[SelectOption]], summary="Languages")
async def languages():
    return success(get_languages(), message="success")


@router.get("/levels", response_model=ApiEnvelope[list[SelectOption]], summary="Levels")
async def levels():
    return success(get_levels(), message="success")


@router.get("/lesson-categories", response_model=ApiEnvelope[list[SelectOption]], summary="Lesson Categories")
async def lesson_categories():
    return success(get_lesson_categories(), message="success")


@router.get("/lesson-statuses", response_model=ApiEnvelope[list[SelectOption]], summary="Lesson Statuses")
async def lesson_statuses():
    return success(get_lesson_statuses(), message="success")


@router.get("/lesson-sorts", response_model=ApiEnvelope[list[SelectOption]], summary="Lesson Sorts")
async def lesson_sorts():
    return success(get_lesson_sorts(), message="success")


@router.get("/voices", response_model=ApiEnvelope[list[SelectOption]], summary="Voices")
async def voices():
    return success(get_voices(), message="success")


@router.get("/tutor-modes", response_model=ApiEnvelope[list[SelectOption]], summary="Tutor Modes")
async def tutor_modes():
    return success(get_tutor_modes(), message="success")


@router.get("/vocab-statuses", response_model=ApiEnvelope[list[SelectOption]], summary="Vocab Statuses")
async def vocab_statuses():
    return success(get_vocab_statuses(), message="success")
