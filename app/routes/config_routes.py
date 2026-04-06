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


@router.get(
    "/languages",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Languages",
    description="Return language options for source language, target language, and profile preferences.",
)
async def languages():
    return success(get_languages(), message="success")


@router.get(
    "/levels",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Levels",
    description="Return learner proficiency level options used by onboarding and profile settings.",
)
async def levels():
    return success(get_levels(), message="success")


@router.get(
    "/lesson-categories",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Lesson Categories",
    description="Return lesson category options for YouTube import and lesson filtering.",
)
async def lesson_categories():
    return success(get_lesson_categories(), message="success")


@router.get(
    "/lesson-statuses",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Lesson Statuses",
    description="Return lesson processing and learning-status options for UI badges and filters.",
)
async def lesson_statuses():
    return success(get_lesson_statuses(), message="success")


@router.get(
    "/lesson-sorts",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Lesson Sorts",
    description="Return lesson sort options for frontend list ordering controls.",
)
async def lesson_sorts():
    return success(get_lesson_sorts(), message="success")


@router.get(
    "/voices",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Voices",
    description="Return voice options used by tutor playback, pronunciation playback, and TTS generation.",
)
async def voices():
    return success(get_voices(), message="success")


@router.get(
    "/tutor-modes",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Tutor Modes",
    description="Return tutor interaction mode options such as coach, grammar, or pronunciation support.",
)
async def tutor_modes():
    return success(get_tutor_modes(), message="success")


@router.get(
    "/vocab-statuses",
    response_model=ApiEnvelope[list[SelectOption]],
    summary="Vocab Statuses",
    description="Return vocabulary mastery and scheduling status options for filters and labels.",
)
async def vocab_statuses():
    return success(get_vocab_statuses(), message="success")
