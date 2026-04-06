# API Usage Guide

This document is the human-readable companion to Swagger UI.

## Discovery

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Access Model

- The backend is open by default.
- Requests do not need a prior login session to be accepted.
- If a bearer token or auth cookies are missing, the backend resolves a deterministic compatibility learner account.
- This keeps direct API calls working now and allows Kong to map real identity later.
- If Kong injects user identity in a future phase, backend auth/session resolution can be tightened without changing route shapes.

## Response Envelope

Most JSON endpoints return:

```json
{
  "code": "OK",
  "message": "success",
  "body": {}
}
```

Created responses use:

```json
{
  "code": "CREATED",
  "message": "resource created",
  "body": {}
}
```

Error example:

```json
{
  "code": "INVALID_REQUEST",
  "message": "body.url: Field required",
  "body": null
}
```

Exceptions:

- `GET /healthz` returns a raw liveness payload.
- `GET /file` streams binary content instead of JSON.
- Legacy `/youtube/*` endpoints keep their original response shapes.

## Core Capabilities

- Import YouTube videos into lesson workspaces
- Poll clip/transcript processing results
- Load home dashboard and lesson detail pages
- Run lesson-grounded tutor sessions
- Manage spaced-repetition vocab review and flashcards
- Read and update learner profile/preferences
- Bootstrap LIFF / LINE login and sync LINE profile state
- Generate TTS / STT / AI utility responses

## Route Reference

### Meta / Infra

- `GET /`
  - Returns service name, environment, and public base URL.
- `GET /healthz`
  - Liveness probe for containers, gateways, and uptime checks.
- `GET /file?key=<object-key>`
  - Streams MinIO-backed files such as generated clips and audio.

### Bootstrap / Auth

- `GET /api/v1/bootstrap`
  - Returns app shell data: app name, locale, feature flags, session, nav tabs.
- `POST /api/v1/auth/login`
  - Creates a backend session from username/password.
  - Useful for admin tools, local QA, or manual session creation.
- `POST /api/v1/auth/logout`
  - Invalidates the current session if present.
- `GET /api/v1/auth/me`
  - Returns the resolved learner profile.
- `GET|POST /api/v1/auth/refresh`
  - Rotates access/refresh tokens.
- `GET /api/v1/auth/providers`
  - Returns sign-in provider metadata such as LINE, Google, and email.

Login request example:

```json
{
  "username": "alex",
  "password": "sorbet-demo"
}
```

### Onboarding / Config

- `GET /api/v1/onboarding/slides`
  - Returns onboarding slide content.
- `GET /api/v1/personalization/options`
  - Returns endpoints and option lists for setup forms.
- `POST /api/v1/personalization/submit`
  - Accepts onboarding choices and returns the next route.
- `GET /api/v1/config/languages`
- `GET /api/v1/config/levels`
- `GET /api/v1/config/lesson-categories`
- `GET /api/v1/config/lesson-statuses`
- `GET /api/v1/config/lesson-sorts`
- `GET /api/v1/config/voices`
- `GET /api/v1/config/tutor-modes`
- `GET /api/v1/config/vocab-statuses`
  - These endpoints power frontend dropdowns and filter controls.

### Home

- `GET /api/v1/home`
  - Returns greeting, progress, streak, quick actions, recent lesson, recommendations.
- `GET /api/v1/recommendations`
  - Returns lesson recommendations without the rest of the dashboard payload.
- `GET /api/v1/daily-progress`
  - Returns daily minutes, streak, and new-word progress.

### Lessons / Clips / Videos

- `POST /api/v1/lessons`
  - Imports a YouTube URL into a lesson workspace.
  - Starts the background transcript and clip pipeline.
- `GET /api/v1/lessons`
  - Lists lesson summaries for the resolved learner.
- `GET /api/v1/lessons/{lessonId}`
  - Returns transcript blocks, vocab, tabs, actions, and lesson summary state.
- `GET /api/v1/clip`
  - Lists clip import records and transcript state.
- `GET /api/v1/clip/{clipId}`
  - Returns one clip record.
- `GET /api/v1/videos`
  - Lists media/video detail records linked to lessons.
- `GET /api/v1/videos/{videoId}`
  - Returns one video detail record.

Lesson import request example:

```json
{
  "url": "https://youtube.com/watch?v=abc123xyz00",
  "sourceLanguageId": "english",
  "targetLanguageId": "thai",
  "categoryId": "travel",
  "voiceId": "sorbet",
  "autoDetect": true
}
```

### Tutor

- `GET /api/v1/tutor/sessions`
  - Lists tutor sessions linked to lessons and clips.
- `POST /api/v1/tutor/sessions`
  - Creates or reuses a tutor session grounded in a lesson clip.
- `GET /api/v1/tutor/sessions/{sessionId}`
  - Returns full tutor workspace content including messages and waveform.
- `POST /api/v1/tutor/message`
  - Persists learner message and returns assistant reply.
- `POST /api/v1/tutor/feedback`
  - Stores quality feedback for tutor answers.
- `GET /api/v1/tutor/conversations`
- `GET /api/v1/tutor/conversations/{sessionId}`
  - Legacy aliases kept for older clients.

Tutor message request example:

```json
{
  "sessionId": "session-paris-bistro",
  "lessonId": "lesson-paris-bistro",
  "prompt": "Explain this line in simple English and Thai."
}
```

### Vocab / Flashcards

- `GET /api/v1/vocab/items`
  - Lists saved or extracted vocab items with lesson traceability.
- `GET /api/v1/vocab/review`
  - Returns daily review counts and the active review card/session.
- `POST /api/v1/vocab/review/answer`
  - Applies spaced-repetition scheduling to the current card.
- `GET /api/v1/flashcards/decks`
  - Lists flashcard decks.
- `GET /api/v1/flashcards/decks/{deckId}`
  - Returns one deck summary.
- `POST /api/v1/flashcards/session/start`
  - Starts a deck review session.
- `GET /api/v1/flashcards/session/{sessionId}`
  - Returns the active card payload and answer options.
- `POST /api/v1/flashcards/session/answer`
  - Saves answer and advances the session.
- `POST /api/v1/flashcards/session/finish`
  - Closes the session and returns review summary.

Review answer example:

```json
{
  "sessionId": "review-abc123",
  "answer": "good"
}
```

Supported answer values:

- `again`
- `hard`
- `good`
- `easy`

### Profile

- `GET /api/v1/profile`
  - Returns learner profile, preferences, and notification settings.
- `PATCH /api/v1/profile`
  - Updates locale, languages, level, weekly focus, tutor defaults, and notification flags.

### LINE / LIFF

- `GET /api/v1/line/config`
  - Returns LIFF enablement, LIFF ID, redirect URI, and webhook path for frontend bootstrapping.
- `GET /api/v1/line/status`
  - Returns whether the resolved learner is linked to LINE.
- `POST /api/v1/line/login`
  - Returns LINE Login redirect URL and state token.
- `GET /api/v1/line/profile`
  - Returns stored LINE profile snapshot for the resolved learner.
- `POST /api/v1/line/profile`
  - Stores LIFF profile data, links or creates learner account, and issues backend auth cookies.
- `POST /api/v1/line/webhook`
  - Verifies `x-line-signature` and accepts Messaging API webhook payloads.

LIFF profile sync example:

```json
{
  "userId": "Uxxxxxxxx",
  "displayName": "Alex on LINE",
  "statusMessage": "Hello from LINE",
  "pictureUrl": "https://profile.line-scdn.net/...",
  "language": "th",
  "liffId": "165xxxxxxxxx-xxxxxxx"
}
```

### AI / Speech

- `POST /api/v1/tts`
  - Generates speech URL for pronunciation playback or tutor narration.
- `POST /api/v1/stt`
  - Transcribes learner audio or normalizes provided transcript text.
- `POST /api/v1/ai/generate-lesson`
  - Confirms or regenerates lesson artifacts from transcript-backed lesson state.
- `POST /api/v1/ai/generate-flashcards`
  - Rebuilds a lesson flashcard deck from transcript/vocab data.
- `POST /api/v1/ai/chat`
  - Returns generic assistant output, optionally grounded in lesson context.

### Legacy YouTube Pipeline

- `POST /youtube/jobs`
  - Creates a legacy processing job and starts asynchronous transcript+clip generation.
- `GET /youtube/jobs?user_id_token=<token>`
  - Lists jobs by external client token.
- `GET /youtube/jobs/{jobId}`
  - Returns job progress, transcript source, token usage, clip details.
- `POST /youtube/job/track`
  - Updates the last known clip sequence for a job.

Legacy job request example:

```json
{
  "youtube_link": "https://www.youtube.com/watch?v=7IyiKqFQAnk",
  "user_id_token": "device-123",
  "lang": "en",
  "split_seconds": 15,
  "tolerance_seconds": 1,
  "title": "Travel Listening Practice",
  "type_of_transcription": "openai_transcribe"
}
```

## Operational Notes

- `POST /api/v1/lessons` and `POST /youtube/jobs` start background work. Poll corresponding detail endpoints for progress.
- `POST /api/v1/line/webhook` requires valid `x-line-signature`.
- `GET /file` is intended for media playback links that already contain object keys returned by other APIs.
- `POST /api/v1/tts` and `POST /api/v1/stt` are utility endpoints and may fall back to configured defaults if upstream AI providers are not fully enabled.

## Error Codes

- `UNAUTHORIZED`
- `FORBIDDEN`
- `INVALID_REQUEST`
- `INVALID_YOUTUBE_URL`
- `LESSON_NOT_FOUND`
- `CLIP_NOT_FOUND`
- `VIDEO_NOT_FOUND`
- `TUTOR_SESSION_NOT_FOUND`
- `VOCAB_ITEM_NOT_FOUND`
- `PROFILE_NOT_FOUND`
- `LINE_CONFIG_MISSING`
- `LINE_SIGNATURE_INVALID`
- `OPENAI_CONFIG_MISSING`
- `TRANSCRIPT_NOT_READY`
- `RATE_LIMITED`
- `INTERNAL_ERROR`
