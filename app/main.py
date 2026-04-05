from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_settings
from app.routes.ai import router as ai_router
from app.routes.auth import router as auth_router
from app.routes.bootstrap import router as bootstrap_router
from app.routes.config_routes import router as config_router
from app.routes.flashcards import router as flashcards_router
from app.routes.health import router as health_router
from app.routes.home import router as home_router
from app.routes.lessons import router as lessons_router
from app.routes.line import router as line_router
from app.routes.onboarding import router as onboarding_router
from app.routes.profile import router as profile_router
from app.routes.storage import router as storage_router
from app.routes.tutor import router as tutor_router
from app.routes.vocab import router as vocab_router
from app.routes.youtube import router as youtube_router
from app.services.api import (
    ApiError,
    api_error_handler,
    envelope,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)

settings = load_settings()
allowed_origins = [
    origin
    for origin in {
        settings.public_base_url(),
        settings.Core.nextPublicApiBaseURL if settings.Core else "",
        "http://localhost:3000",
    }
    if origin
]

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Language-learning API for YouTube lesson import, tutor sessions, vocabulary review, "
        "profile settings, and LINE-ready integration flows."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health_router)
app.include_router(storage_router)
app.include_router(auth_router)
app.include_router(bootstrap_router)
app.include_router(onboarding_router)
app.include_router(config_router)
app.include_router(home_router)
app.include_router(lessons_router)
app.include_router(tutor_router)
app.include_router(vocab_router)
app.include_router(flashcards_router)
app.include_router(profile_router)
app.include_router(line_router)
app.include_router(ai_router)
app.include_router(youtube_router)


@app.get("/", tags=["Meta"])
async def root():
    return envelope(
        {
            "service": settings.app_name,
            "env": settings.env,
            "publicBaseURL": settings.public_base_url(),
        }
    )
