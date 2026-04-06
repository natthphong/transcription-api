# Frontend Task: LINE / LIFF Login Bridge

Goal: move the LINE entry flow on `/page/webhook-line` from mock inspection into a real LIFF login bridge that persists the LINE profile to backend.

## Required env

- `NEXT_PUBLIC_LINE_LIFF_ID`
- `NEXT_PUBLIC_API_BASE_URL`

Use `NEXT_PUBLIC_LINE_LIFF_ID` as the primary frontend env. Backend already exposes the same value from `/api/v1/line/config`.

## Required frontend behavior

On the LINE login entry flow, and especially on `/page/webhook-line`, run LIFF init first and force LINE login when needed:

```ts
await liff.init({ liffId: process.env.NEXT_PUBLIC_LINE_LIFF_ID as string });
setStatus("init");
if (!liff.isLoggedIn()) {
  setStatus("login");
  liff.login();
}
const profile = await liff.getProfile();
if (!profile) {
  throw new Error(t(I18N_KEYS.LINE_ERROR_NO_PROFILE));
}
```

After `liff.getProfile()` succeeds, call backend immediately:

`POST /api/v1/line/profile`

Request body:

```json
{
  "userId": "Uxxxxxxxx",
  "displayName": "Alex on LINE",
  "statusMessage": "Hello",
  "pictureUrl": "https://profile.line-scdn.net/...",
  "language": "th",
  "liffId": "165xxxxxxxxx-xxxxxxx"
}
```

## Expected backend response

Backend returns envelope shape:

```json
{
  "code": "CREATED",
  "message": "line profile synced",
  "body": {
    "connected": true,
    "redirectTo": "/home",
    "profile": {
      "userId": "Uxxxxxxxx",
      "displayName": "Alex on LINE",
      "statusMessage": "Hello",
      "pictureAccent": "sky",
      "language": "th"
    },
    "session": {
      "loggedIn": true,
      "accessToken": "...",
      "refreshToken": "...",
      "currentRole": "learner",
      "redirectTo": "/home",
      "user": {}
    }
  }
}
```

The backend also sets auth cookies, so after success frontend should route to `/home` and refetch bootstrap/profile as needed.

## Integration notes

- Keep using `GET /api/v1/line/config` as the first source of truth for `enabled`, `liffId`, `redirectUri`, and `mockMode`.
- Keep `POST /api/v1/line/login` for the old start-login action if the login screen still needs it.
- Do not use `POST /api/v1/line/webhook` for LIFF profile sync. That route is for LINE Messaging API webhook verification only.
- `/page/webhook-line` should behave as the real LIFF bridge page, not only a debug page.
- If `/api/v1/line/config` returns `enabled: false`, stay in mock/dev fallback mode.

## What backend now guarantees

- Stores LINE `userId` in backend table `app_line_accounts.line_user_id`
- Updates display name, status message, language, and sync timestamp
- Creates backend learner/session if this LINE user is new
- Keeps `LINE_CHANNEL_SECRET` and `LINE_BOT_CHANNEL_ACCESS_TOKEN` server-side for future notification flows
