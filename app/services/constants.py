from __future__ import annotations

from typing import Any


def loc(en: str, th: str | None = None) -> dict[str, str]:
    return {"en": en, "th": th or en}


NAV_TABS = [
    {"id": "home", "labelKey": "common.nav.home", "href": "/home", "icon": "house"},
    {"id": "learn", "labelKey": "common.nav.learn", "href": "/learn", "icon": "book-open"},
    {"id": "tutor", "labelKey": "common.nav.tutor", "href": "/tutor", "icon": "sparkles"},
    {"id": "vocab", "labelKey": "common.nav.vocab", "href": "/vocab", "icon": "layers-3"},
    {"id": "profile", "labelKey": "common.nav.profile", "href": "/profile", "icon": "user-round"},
]

FEATURE_FLAGS = {
    "lineLogin": True,
    "aiTutorVoice": True,
    "videoImport": True,
}

LANGUAGE_OPTIONS = [
    {"id": "english", "value": "en", "labelKey": "dropdowns.languages.english"},
    {"id": "thai", "value": "th", "labelKey": "dropdowns.languages.thai"},
    {"id": "japanese", "value": "ja", "labelKey": "dropdowns.languages.japanese"},
    {"id": "french", "value": "fr", "labelKey": "dropdowns.languages.french"},
]

LEVEL_OPTIONS = [
    {"id": "beginner", "value": "beginner", "labelKey": "dropdowns.levels.beginner"},
    {"id": "intermediate", "value": "intermediate", "labelKey": "dropdowns.levels.intermediate"},
    {"id": "advanced", "value": "advanced", "labelKey": "dropdowns.levels.advanced"},
]

LESSON_CATEGORY_OPTIONS = [
    {"id": "conversation", "value": "conversation", "labelKey": "dropdowns.lessonCategories.conversation"},
    {"id": "listening", "value": "listening", "labelKey": "dropdowns.lessonCategories.listening"},
    {"id": "school", "value": "school", "labelKey": "dropdowns.lessonCategories.school"},
    {"id": "travel", "value": "travel", "labelKey": "dropdowns.lessonCategories.travel"},
    {"id": "work", "value": "work", "labelKey": "dropdowns.lessonCategories.work"},
]

LESSON_STATUS_OPTIONS = [
    {"id": "all", "value": "all", "labelKey": "dropdowns.lessonStatuses.all"},
    {"id": "ready", "value": "ready", "labelKey": "dropdowns.lessonStatuses.ready"},
    {"id": "in_progress", "value": "in_progress", "labelKey": "dropdowns.lessonStatuses.in_progress"},
    {"id": "completed", "value": "completed", "labelKey": "dropdowns.lessonStatuses.completed"},
]

LESSON_SORT_OPTIONS = [
    {"id": "recent", "value": "recent", "labelKey": "dropdowns.lessonSorts.recent"},
    {"id": "progress", "value": "progress", "labelKey": "dropdowns.lessonSorts.progress"},
    {"id": "vocab", "value": "vocab", "labelKey": "dropdowns.lessonSorts.vocab"},
]

VOICE_OPTIONS = [
    {"id": "breeze", "value": "breeze", "labelKey": "dropdowns.voices.breeze"},
    {"id": "sorbet", "value": "sorbet", "labelKey": "dropdowns.voices.sorbet"},
    {"id": "atelier", "value": "atelier", "labelKey": "dropdowns.voices.atelier"},
]

TUTOR_MODE_OPTIONS = [
    {"id": "coach", "value": "coach", "labelKey": "dropdowns.tutorModes.coach"},
    {"id": "grammar", "value": "grammar", "labelKey": "dropdowns.tutorModes.grammar"},
    {"id": "pronunciation", "value": "pronunciation", "labelKey": "dropdowns.tutorModes.pronunciation"},
]

VOCAB_STATUS_OPTIONS = [
    {"id": "all", "value": "all", "labelKey": "dropdowns.vocabStatuses.all"},
    {"id": "due", "value": "due", "labelKey": "dropdowns.vocabStatuses.due"},
    {"id": "mastered", "value": "mastered", "labelKey": "dropdowns.vocabStatuses.mastered"},
    {"id": "difficult", "value": "difficult", "labelKey": "dropdowns.vocabStatuses.difficult"},
]

WEEKLY_FOCUS_OPTIONS = [
    {"id": "bite", "value": "bite", "labelKey": "dropdowns.weeklyFocus.bite", "icon": "zap"},
    {"id": "steady", "value": "steady", "labelKey": "dropdowns.weeklyFocus.steady", "icon": "flame"},
    {"id": "deep", "value": "deep", "labelKey": "dropdowns.weeklyFocus.deep", "icon": "brain"},
]

INTEREST_OPTIONS = [
    {
        "id": "conversation",
        "value": "conversation",
        "labelKey": "dropdowns.lessonCategories.conversation",
        "icon": "messages-square",
        "accent": "coral",
    },
    {
        "id": "listening",
        "value": "listening",
        "labelKey": "dropdowns.lessonCategories.listening",
        "icon": "headphones",
        "accent": "sky",
    },
    {
        "id": "school",
        "value": "school",
        "labelKey": "dropdowns.lessonCategories.school",
        "icon": "graduation-cap",
        "accent": "mint",
    },
    {
        "id": "travel",
        "value": "travel",
        "labelKey": "dropdowns.lessonCategories.travel",
        "icon": "plane",
        "accent": "coral",
    },
    {
        "id": "work",
        "value": "work",
        "labelKey": "dropdowns.lessonCategories.work",
        "icon": "briefcase",
        "accent": "sky",
    },
]

ONBOARDING_SLIDES = [
    {
        "id": "onboarding-1",
        "step": 1,
        "badge": loc("Learning mode", "โหมดการเรียน"),
        "title": loc("Turn any YouTube video into a lesson.", "เปลี่ยนวิดีโอ YouTube ใด ๆ ให้เป็นบทเรียนได้ทันที"),
        "description": loc(
            "Paste a link and get interactive transcripts in two languages.",
            "วางลิงก์แล้วรับบทถอดเสียงแบบโต้ตอบได้สองภาษา",
        ),
        "ctaKey": "common.actions.next",
        "theme": "coral",
        "illustration": {"style": "video", "note": "Laptop and play button visual"},
    },
    {
        "id": "onboarding-2",
        "step": 2,
        "badge": loc("Immersive learning", "การเรียนแบบดื่มด่ำ"),
        "title": loc(
            "Study with audio, transcripts, and instant context.",
            "เรียนด้วยเสียง บทถอดเสียง และคำอธิบายทันที",
        ),
        "description": loc(
            "Each line unlocks pronunciation, translation, and AI explanations.",
            "แต่ละบรรทัดมีการออกเสียง คำแปล และคำอธิบายจาก AI",
        ),
        "ctaKey": "common.actions.next",
        "theme": "sky",
        "illustration": {"style": "laptop", "note": "Transcript on warm display"},
    },
    {
        "id": "onboarding-3",
        "step": 3,
        "badge": loc("Daily habit", "นิสัยประจำวัน"),
        "title": loc("Master it with daily practice.", "เชี่ยวชาญได้ด้วยการฝึกทุกวัน"),
        "description": loc(
            "Take AI-generated quizzes and get personalized review lessons based on your weak spots.",
            "ทำควิซจาก AI และรับบทเรียนทบทวนเฉพาะจุดอ่อนของคุณ",
        ),
        "ctaKey": "common.actions.getStarted",
        "theme": "mint",
        "illustration": {"style": "robot", "note": "Friendly AI robot companion"},
    },
]

FLASHCARD_REVIEW_OPTIONS = [
    {"id": "again", "labelKey": "common.labels.reviewAgain", "etaLabel": "< 1m", "tone": "error"},
    {"id": "hard", "labelKey": "common.labels.reviewHard", "etaLabel": "2d", "tone": "coral"},
    {"id": "good", "labelKey": "common.labels.reviewGood", "etaLabel": "4d", "tone": "sky"},
    {"id": "easy", "labelKey": "common.labels.reviewEasy", "etaLabel": "7d", "tone": "mint"},
]

TUTOR_ACTIONS = [
    {
        "id": "action-explain",
        "value": "explain",
        "labelKey": "common.actions.explain",
        "icon": "sparkles",
        "promptText": loc(
            "Explain this line in simple English and Thai.",
            "ช่วยอธิบายบรรทัดนี้ด้วยภาษาอังกฤษและภาษาไทยแบบง่าย ๆ",
        ),
    },
    {
        "id": "action-summarize",
        "value": "summarize",
        "labelKey": "common.actions.summarize",
        "icon": "book-open",
        "promptText": loc(
            "Summarize the clip and highlight the important vocabulary.",
            "สรุปคลิปและเน้นคำศัพท์สำคัญ",
        ),
    },
    {
        "id": "action-quiz",
        "value": "quiz",
        "labelKey": "common.actions.quizMe",
        "icon": "brain",
        "promptText": loc(
            "Quiz me on the key phrases from this lesson.",
            "ช่วยตั้งคำถามจากวลีสำคัญของบทเรียนนี้ให้หน่อย",
        ),
    },
    {
        "id": "action-vocab",
        "value": "extract-vocab",
        "labelKey": "common.actions.extractVocab",
        "icon": "layers-3",
        "promptText": loc(
            "Extract the most useful vocab from this clip.",
            "ช่วยดึงคำศัพท์ที่มีประโยชน์ที่สุดจากคลิปนี้",
        ),
    },
    {
        "id": "action-translate",
        "value": "translate",
        "labelKey": "common.actions.translateAction",
        "icon": "graduation-cap",
        "promptText": loc(
            "Translate the selected excerpt naturally.",
            "แปลประโยคที่เลือกให้เป็นธรรมชาติ",
        ),
    },
]

VOICE_MODEL_MAP = {
    "breeze": "alloy",
    "sorbet": "nova",
    "atelier": "fable",
}


def status_label(status_id: str) -> dict[str, str]:
    table = {
        "ready": loc("Ready", "พร้อมเรียน"),
        "in_progress": loc("In progress", "กำลังเรียน"),
        "completed": loc("Completed", "เสร็จแล้ว"),
        "processing": loc("Processing", "กำลังประมวลผล"),
        "due": loc("Due", "ถึงกำหนด"),
        "mastered": loc("Mastered", "คล่องแล้ว"),
        "difficult": loc("Difficult", "ยาก"),
    }
    return table.get(status_id, loc(status_id.replace("_", " ").title()))


def personalization_options() -> dict[str, Any]:
    return {
        "nativeLanguageOptionsEndpoint": "/api/v1/config/languages",
        "targetLanguageOptionsEndpoint": "/api/v1/config/languages",
        "levelOptionsEndpoint": "/api/v1/config/levels",
        "voiceOptionsEndpoint": "/api/v1/config/voices",
        "tutorModeOptionsEndpoint": "/api/v1/config/tutor-modes",
        "weeklyFocusOptions": WEEKLY_FOCUS_OPTIONS,
        "interestOptions": INTEREST_OPTIONS,
    }
