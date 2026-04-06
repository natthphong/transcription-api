from __future__ import annotations

PUBLIC_ACCESS_NOTE = (
    "This backend runs in open-access compatibility mode. Requests do not need a prior login "
    "session. When no bearer token or auth cookies are provided, the service resolves a "
    "deterministic compatibility learner account so the API can still be called directly. "
    "Upstream gateways such as Kong can map real identity later."
)

API_DESCRIPTION = (
    "Language-learning API for YouTube lesson import, tutor sessions, vocabulary review, "
    "profile settings, AI speech utilities, and LINE-ready integration flows.\n\n"
    f"Access model: {PUBLIC_ACCESS_NOTE}\n\n"
    "Docs:\n"
    "- Swagger UI: `/docs`\n"
    "- ReDoc: `/redoc`\n"
    "- OpenAPI JSON: `/openapi.json`"
)

OPENAPI_TAGS = [
    {
        "name": "Meta",
        "description": "Service metadata and entrypoint discovery.",
    },
    {
        "name": "Health",
        "description": "Runtime readiness checks used by infrastructure and probes.",
    },
    {
        "name": "Storage",
        "description": "Binary file streaming for MinIO-backed clip and audio assets.",
    },
    {
        "name": "Bootstrap",
        "description": "Global app bootstrap payload for the frontend shell, tabs, and session state.",
    },
    {
        "name": "Auth",
        "description": "Session bootstrap, credential login, logout, provider discovery, and token refresh.",
    },
    {
        "name": "Onboarding",
        "description": "Pre-home slides and personalization setup metadata.",
    },
    {
        "name": "Config",
        "description": "API-driven dropdown and option catalogs for languages, voices, levels, statuses, and modes.",
    },
    {
        "name": "Home",
        "description": "Dashboard metrics, recommendations, and daily learning progress summaries.",
    },
    {
        "name": "Lessons",
        "description": "YouTube lesson import, lesson summaries, transcript-backed detail pages, clip records, and videos.",
    },
    {
        "name": "Tutor",
        "description": "Lesson-grounded tutor sessions, messages, and feedback flows.",
    },
    {
        "name": "Vocab",
        "description": "Vocabulary inventory and spaced-repetition review dashboard endpoints.",
    },
    {
        "name": "Flashcards",
        "description": "Deck-oriented flashcard session flows built on top of the vocab review domain.",
    },
    {
        "name": "Profile",
        "description": "Learner profile, preferences, notifications, and tutor defaults.",
    },
    {
        "name": "LINE",
        "description": "LIFF config, LINE profile sync, login bootstrap, and webhook verification.",
    },
    {
        "name": "AI",
        "description": "AI convenience endpoints for TTS, STT, lesson regeneration, flashcard generation, and chat.",
    },
    {
        "name": "youtube",
        "description": "Legacy YouTube processing job endpoints used by the original clip pipeline.",
    },
]
