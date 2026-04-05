from __future__ import annotations

from app.config import load_settings
from app.services.auth_service import build_auth_session
from app.services.constants import FEATURE_FLAGS, NAV_TABS


def build_bootstrap(user, session) -> dict:
    settings = load_settings()
    locale = user.app_locale if user else (settings.Core.defaultLocale if settings.Core else "en")
    return {
        "appName": "Fluid Scholar",
        "locale": locale,
        "featureFlags": FEATURE_FLAGS,
        "session": build_auth_session(user, session).model_dump(),
        "navTabs": NAV_TABS,
    }
