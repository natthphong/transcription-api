from __future__ import annotations

from app.services.constants import (
    INTEREST_OPTIONS,
    LANGUAGE_OPTIONS,
    LESSON_CATEGORY_OPTIONS,
    LESSON_SORT_OPTIONS,
    LESSON_STATUS_OPTIONS,
    LEVEL_OPTIONS,
    TUTOR_MODE_OPTIONS,
    VOCAB_STATUS_OPTIONS,
    VOICE_OPTIONS,
    WEEKLY_FOCUS_OPTIONS,
    personalization_options,
)


def get_languages() -> list[dict]:
    return LANGUAGE_OPTIONS


def get_levels() -> list[dict]:
    return LEVEL_OPTIONS


def get_lesson_categories() -> list[dict]:
    return LESSON_CATEGORY_OPTIONS


def get_lesson_statuses() -> list[dict]:
    return LESSON_STATUS_OPTIONS


def get_lesson_sorts() -> list[dict]:
    return LESSON_SORT_OPTIONS


def get_voices() -> list[dict]:
    return VOICE_OPTIONS


def get_tutor_modes() -> list[dict]:
    return TUTOR_MODE_OPTIONS


def get_vocab_statuses() -> list[dict]:
    return VOCAB_STATUS_OPTIONS


def get_weekly_focus() -> list[dict]:
    return WEEKLY_FOCUS_OPTIONS


def get_interests() -> list[dict]:
    return INTEREST_OPTIONS


def get_personalization_options() -> dict:
    return personalization_options()
