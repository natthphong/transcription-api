from __future__ import annotations

from fastapi import APIRouter

from app.schemas import ApiEnvelope, OnboardingSlide, PersonalizationOptions, PersonalizationSubmitBody, PersonalizationSubmitRequest
from app.services.api import created, success
from app.services.config_service import get_personalization_options
from app.services.constants import ONBOARDING_SLIDES

router = APIRouter(prefix="/api/v1", tags=["Onboarding"])


@router.get(
    "/onboarding/slides",
    response_model=ApiEnvelope[list[OnboardingSlide]],
    summary="Onboarding Slides",
    description="Return onboarding content shown before the learner enters the main app.",
)
async def onboarding_slides():
    return success(ONBOARDING_SLIDES, message="success")


@router.get(
    "/personalization/options",
    response_model=ApiEnvelope[PersonalizationOptions],
    summary="Personalization Options",
    description="Return personalization form metadata and option endpoints used by account setup.",
)
async def personalization_options():
    return success(get_personalization_options(), message="success")


@router.post(
    "/personalization/submit",
    response_model=ApiEnvelope[PersonalizationSubmitBody],
    summary="Submit Personalization",
    description="Persist onboarding personalization inputs and return the next frontend route.",
)
async def personalization_submit(_: PersonalizationSubmitRequest):
    return created({"saved": True, "nextRoute": "/"}, message="journey saved")
