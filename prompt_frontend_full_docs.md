# Frontend Integration Guide

## Base URL

- Backend API base: `PUBLIC_BASE_URL` from backend config.
- Frontend server-side base: `NEXT_PUBLIC_API_BASE_URL`.
- All app endpoints live under `/api/v1`.
- Media files remain on `/file?key=<minio-object-key>`.

## Envelope

Every API response uses the same envelope:

```json
{
  "code": "OK",
  "message": "success",
  "body": {}
}
```

Error example:

```json
{
  "code": "UNAUTHORIZED",
  "message": "missing or invalid session",
  "body": null
}
```

## Auth And Session Flow

1. `POST /api/v1/auth/login`
2. Backend returns `AuthSession` in the envelope and sets `fluid_access_token` and `fluid_refresh_token` cookies.
3. `GET /api/v1/bootstrap` returns app bootstrap state for authenticated screens.
4. `POST /api/v1/auth/logout` clears the cookies and invalidates the active session.
5. `GET|POST /api/v1/auth/refresh` rotates the token pair.

## Important SSR Compatibility Note

- The current frontend server-side fetch layer does not forward browser auth cookies to the backend explicitly.
- To keep the existing frontend working in real mode, the backend supports a development compatibility fallback: if no auth token is present, it uses the most recently active backend session.
- This is intended for the current frontend integration path and local/dev use.
- For stricter multi-user production mode later, forward cookies or bearer tokens from the frontend server runtime.

## Route Groups

### Bootstrap / Auth

- `GET /api/v1/bootstrap`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET|POST /api/v1/auth/refresh`
- `GET /api/v1/auth/providers`

### Onboarding / Personalization

- `GET /api/v1/onboarding/slides`
- `GET /api/v1/personalization/options`
- `POST /api/v1/personalization/submit`

### Home

- `GET /api/v1/home`
- `GET /api/v1/recommendations`
- `GET /api/v1/daily-progress`

### Learn / Media

- `POST /api/v1/lessons`
- `GET /api/v1/lessons`
- `GET /api/v1/lessons/{id}`
- `GET /api/v1/clip`
- `GET /api/v1/clip/{id}`
- `GET /api/v1/videos`
- `GET /api/v1/videos/{id}`

### Tutor

- `GET /api/v1/tutor/sessions`
- `POST /api/v1/tutor/sessions`
- `GET /api/v1/tutor/sessions/{id}`
- `POST /api/v1/tutor/message`
- `POST /api/v1/tutor/feedback`
- Legacy aliases:
- `GET /api/v1/tutor/conversations`
- `GET /api/v1/tutor/conversations/{id}`

### Vocab / Flashcards

- `GET /api/v1/vocab/items`
- `GET /api/v1/vocab/review`
- `POST /api/v1/vocab/review/answer`
- `GET /api/v1/flashcards/decks`
- `GET /api/v1/flashcards/decks/{id}`
- `POST /api/v1/flashcards/session/start`
- `GET /api/v1/flashcards/session/{id}`
- `POST /api/v1/flashcards/session/answer`
- `POST /api/v1/flashcards/session/finish`

### Profile / Config

- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `GET /api/v1/config/languages`
- `GET /api/v1/config/levels`
- `GET /api/v1/config/lesson-categories`
- `GET /api/v1/config/lesson-statuses`
- `GET /api/v1/config/lesson-sorts`
- `GET /api/v1/config/voices`
- `GET /api/v1/config/tutor-modes`
- `GET /api/v1/config/vocab-statuses`

### LINE / LIFF

- `GET /api/v1/line/config`
- `GET /api/v1/line/status`
- `POST /api/v1/line/login`
- `POST /api/v1/line/webhook`
- `GET /api/v1/line/profile`

### AI / Speech

- `POST /api/v1/tts`
- `POST /api/v1/stt`
- `POST /api/v1/ai/generate-lesson`
- `POST /api/v1/ai/generate-flashcards`
- `POST /api/v1/ai/chat`

## Request Examples

### Login

```json
{
  "username": "alex",
  "password": "sorbet-demo"
}
```

### Create Lesson

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

### Tutor Message

```json
{
  "sessionId": "session-paris-bistro",
  "lessonId": "lesson-paris-bistro",
  "prompt": "Explain this line in simple English and Thai."
}
```

### Vocab Review Answer

```json
{
  "sessionId": "session-1",
  "answer": "good"
}
```

### Profile Patch

```json
{
  "nativeLanguageId": "thai",
  "targetLanguageId": "french",
  "levelId": "intermediate",
  "weeklyFocusId": "steady",
  "voiceId": "atelier",
  "tutorModeId": "grammar",
  "practiceReminders": true,
  "weeklyDigest": true,
  "tutorFollowUps": true,
  "autoPlayPronunciation": true
}
```

## Field Semantics

- `LocalizedText`: `{ "en": "...", "th": "..." }`
- Config endpoints return option metadata only. Frontend should still resolve `labelKey` with its own dictionary layer.
- Content endpoints return already localized content payloads where the UI expects direct text.
- Lesson/tutor/vocab entities keep explicit linkage:
- `lessonId` -> lesson workspace
- `clipId` -> imported clip / primary clip
- `sourceLessonId` -> vocab traceability
- Tutor sessions are lesson-grounded, not generic chat rooms.

## Vocab Review / Flashcards

- `GET /api/v1/vocab/review` returns dashboard metrics and the active review card.
- `POST /api/v1/vocab/review/answer` updates due scheduling.
- Supported answer ids: `again`, `hard`, `good`, `easy`
- Backend scheduling behavior:
- `again` -> near-immediate retry
- `hard` -> difficult queue
- `good` -> standard spaced repetition
- `easy` -> longer mastered interval
- Flashcard endpoints are backed by the same review-session domain.

## LINE / LIFF Notes

- `GET /api/v1/line/config` is safe for frontend use and should be the source of truth for LIFF enablement.
- `POST /api/v1/line/webhook` verifies `x-line-signature` with `LINE_CHANNEL_SECRET`.
- If LINE config is missing, `line/config` reports `enabled: false` and `mockMode: true`.

## Real Mode Migration

1. Disable frontend mock mode.
2. Point `NEXT_PUBLIC_API_BASE_URL` to the FastAPI server.
3. Keep using the existing typed contracts in `src/lib/api/types.ts`.
4. Keep using the same endpoint constants in `src/lib/api/endpoints.ts`.
5. Handle non-`OK` / non-`CREATED` `code` values from the response envelope.

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

## Current Backend Assumptions

- The backend seeds a default `alex / sorbet-demo` learner and baseline lesson data when the app tables are empty.
- New YouTube imports create real lesson records and also start the existing background transcript pipeline.
- Imported lesson transcript blocks and extracted vocab are synchronized from the YouTube job when lesson endpoints are fetched after processing finishes.

## Production Hardening Follow-Ups

- Forward cookies or bearer tokens in frontend SSR to remove the latest-active-session compatibility fallback.
- Add a real migration runner and deployment migration step.
- Replace naive fallback AI/TTS/STT behavior with fully configured OpenAI or vendor-specific production paths.
- Add rate limiting and Redis-backed session/cache support if traffic grows.
