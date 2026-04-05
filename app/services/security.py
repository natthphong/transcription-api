from __future__ import annotations

import hashlib
import secrets

from app.config import load_settings


def hash_password(value: str) -> str:
    settings = load_settings()
    secret = settings.Core.sessionSecret if settings.Core else "dev-session-secret"
    return hashlib.sha256(f"{secret}:{value}".encode("utf-8")).hexdigest()


def verify_password(raw_value: str, hashed_value: str) -> bool:
    return hash_password(raw_value) == hashed_value


def generate_token(prefix: str) -> str:
    return f"{prefix}-{secrets.token_urlsafe(24)}"
