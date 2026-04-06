from __future__ import annotations

from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")
LocalizedText = Dict[str, str]


class ApiEnvelope(BaseModel, Generic[T]):
    code: str
    message: str
    body: Optional[T]
    meta: Optional[Dict[str, Any]] = None


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="ignore")


class SelectOption(BaseModel):
    id: str
    value: str
    labelKey: str
    descriptionKey: Optional[str] = None
    icon: Optional[str] = None
    accent: Optional[str] = None


class BottomTabItem(BaseModel):
    id: str
    labelKey: str
    href: str
    icon: str


class AuthProvider(BaseModel):
    id: str
    labelKey: str
    connected: bool
    primary: bool
    type: Literal["email", "oauth"]
    detailKey: Optional[str] = None
    icon: Optional[str] = None


class NotificationPreferences(BaseModel):
    practiceReminders: bool
    weeklyDigest: bool
    tutorFollowUps: bool


class TutorPreferences(BaseModel):
    voiceId: str
    modeId: str
    autoPlayPronunciation: bool


class UserProfile(BaseModel):
    id: str
    fullName: str
    email: str
    avatarInitials: str
    membershipTier: Literal["starter", "plus"]
    nativeLanguageId: str
    targetLanguageId: str
    levelId: str
    weeklyFocusId: str
    interests: List[str]
    streakDays: int
    dailyGoalMinutes: int
    timezone: str
    appLocale: str
    goalSummary: LocalizedText
    notificationPreferences: NotificationPreferences
    tutorPreferences: TutorPreferences


class AuthSession(BaseModel):
    loggedIn: bool
    accessToken: str
    refreshToken: str
    currentRole: str
    redirectTo: str
    user: UserProfile


class BootstrapBody(BaseModel):
    appName: str
    locale: str
    featureFlags: Dict[str, bool]
    session: AuthSession
    navTabs: List[BottomTabItem]


class RefreshSession(BaseModel):
    accessToken: str
    refreshToken: str
    expiresInSeconds: int


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"username": "alex", "password": "sorbet-demo"}}
    )

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class LogoutBody(BaseModel):
    loggedOut: bool


class OnboardingIllustration(BaseModel):
    style: Literal["video", "laptop", "robot"]
    note: str


class OnboardingSlide(BaseModel):
    id: str
    step: int
    badge: LocalizedText
    title: LocalizedText
    description: LocalizedText
    ctaKey: str
    theme: Literal["coral", "sky", "mint"]
    illustration: OnboardingIllustration


class PersonalizationOptions(BaseModel):
    nativeLanguageOptionsEndpoint: str
    targetLanguageOptionsEndpoint: str
    levelOptionsEndpoint: str
    voiceOptionsEndpoint: str
    tutorModeOptionsEndpoint: str
    weeklyFocusOptions: List[SelectOption]
    interestOptions: List[SelectOption]


class PersonalizationSubmitRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nativeLanguageId": "thai",
                "targetLanguageId": "english",
                "levelId": "intermediate",
                "weeklyFocusId": "steady",
                "voiceId": "sorbet",
                "tutorModeId": "coach",
                "interests": ["conversation", "listening"],
            }
        }
    )

    nativeLanguageId: Optional[str] = None
    targetLanguageId: Optional[str] = None
    levelId: Optional[str] = None
    weeklyFocusId: Optional[str] = None
    voiceId: Optional[str] = None
    tutorModeId: Optional[str] = None
    interests: List[str] = Field(default_factory=list)


class PersonalizationSubmitBody(BaseModel):
    saved: bool
    nextRoute: str


class ProgressPoint(BaseModel):
    label: str
    minutes: int
    active: bool


class HomeQuickAction(BaseModel):
    id: str
    labelKey: str
    description: LocalizedText
    href: str
    icon: str


class HomeActivityItem(BaseModel):
    id: str
    title: LocalizedText
    detail: LocalizedText
    timeLabel: str


class HomeRecommendation(BaseModel):
    id: str
    title: LocalizedText
    subtitle: LocalizedText
    durationLabel: str
    levelId: str
    phraseCount: int
    accent: Literal["coral", "sky", "mint"]


class HomeBody(BaseModel):
    userName: str
    welcome: LocalizedText
    subtitle: LocalizedText
    newWordsCount: int
    continueDeckId: str
    dailyGoalMinutes: int
    studyMinutesToday: int
    streakDays: int
    activity: List[ProgressPoint]
    quickActions: List[HomeQuickAction]
    recentActivity: List[HomeActivityItem]
    recentLesson: HomeRecommendation
    recommendations: List[HomeRecommendation]


class DailyProgressBody(BaseModel):
    streakDays: int
    goalMinutes: int
    minutesCompleted: int
    newWordsLearned: int


class FlashcardDeck(BaseModel):
    id: str
    title: LocalizedText
    subtitle: LocalizedText
    dueCount: int
    reviewedCount: int
    colorAccent: str


class FlashcardReviewOption(BaseModel):
    id: str
    labelKey: str
    etaLabel: str
    tone: Literal["error", "coral", "sky", "mint"]


class FlashcardSession(BaseModel):
    id: str
    deckId: str
    deckTitle: LocalizedText
    progressCurrent: int
    progressTotal: int
    sourceLabel: str
    prompt: str
    translation: str
    note: LocalizedText
    reviewOptions: List[FlashcardReviewOption]


class FlashcardStartRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"deckId": "deck-french-gastronomy"}})

    deckId: Optional[str] = None


class FlashcardStartBody(BaseModel):
    sessionId: str
    nextRoute: str


class FlashcardAnswerRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"sessionId": "review-abc123", "answer": "good"}}
    )

    sessionId: str
    answer: str


class FlashcardAnswerBody(BaseModel):
    saved: bool
    nextCardId: Optional[str] = None


class FlashcardFinishRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"sessionId": "review-abc123"}})

    sessionId: str


class FlashcardFinishSummary(BaseModel):
    cardsReviewed: int
    retention: int


class FlashcardFinishBody(BaseModel):
    saved: bool
    summary: FlashcardFinishSummary


class ClipItem(BaseModel):
    id: str
    sourceUrl: str
    title: LocalizedText
    channel: str
    durationLabel: str
    transcriptStatus: Literal["ready", "processing"]


class LessonSummary(BaseModel):
    id: str
    clipId: str
    title: LocalizedText
    subtitle: LocalizedText
    durationLabel: str
    progressPercent: int
    statusId: str
    statusLabel: LocalizedText
    extractedVocabCount: int
    categoryId: str
    lastActivityLabel: LocalizedText
    thumbnailAccent: Literal["coral", "sky", "mint"]
    clipCount: int
    sourceLabel: LocalizedText


class LessonTranscriptBlock(BaseModel):
    id: str
    timestamp: str
    source: str
    translated: str
    explanation: LocalizedText


class LessonVocabulary(BaseModel):
    id: str
    term: str
    pronunciation: str
    meaning: LocalizedText


class LessonTab(BaseModel):
    id: str
    label: LocalizedText


class RecommendedAction(BaseModel):
    id: str
    labelKey: str
    href: str


class LessonDetail(LessonSummary):
    learningObjectives: List[LocalizedText]
    transcriptBlocks: List[LessonTranscriptBlock]
    vocabulary: List[LessonVocabulary]
    tabs: List[LessonTab]
    recommendedActions: List[RecommendedAction]


class LessonCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://youtube.com/watch?v=abc123xyz00",
                "sourceLanguageId": "english",
                "targetLanguageId": "thai",
                "categoryId": "travel",
                "voiceId": "sorbet",
                "autoDetect": True,
            }
        }
    )

    url: str
    sourceLanguageId: str
    targetLanguageId: str
    categoryId: str
    voiceId: str
    autoDetect: bool = True


class LessonCreateBody(BaseModel):
    lessonId: str
    clipId: str
    status: str
    nextRoute: str


class VideoQuizOption(BaseModel):
    id: str
    label: LocalizedText
    correct: bool


class VideoQuizQuestion(BaseModel):
    id: str
    prompt: LocalizedText
    options: List[VideoQuizOption]
    rationale: LocalizedText


class VideoDetail(BaseModel):
    id: str
    lessonId: str
    title: LocalizedText
    thumbnailAccent: str
    durationLabel: str
    summary: LocalizedText
    quiz: List[VideoQuizQuestion]


class TutorMessage(BaseModel):
    id: str
    role: Literal["assistant", "user"]
    text: str
    timestampLabel: str


class TutorAction(BaseModel):
    id: str
    value: str
    labelKey: str
    icon: Optional[str] = None
    promptText: Optional[LocalizedText] = None


class TutorSessionSummary(BaseModel):
    id: str
    lessonId: str
    clipId: str
    title: LocalizedText
    lessonLabel: LocalizedText
    lastMessagePreview: LocalizedText
    updatedAtLabel: str
    modeId: str


class TutorSession(TutorSessionSummary):
    contextSummary: LocalizedText
    selectedExcerpt: str
    quickPrompts: List[str]
    waveform: List[int]
    messages: List[TutorMessage]
    availableActions: List[TutorAction]


class TutorSessionCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lessonId": "lesson-paris-bistro",
                "clipId": "clip-youtube-paris",
                "modeId": "coach",
            }
        }
    )

    lessonId: str
    clipId: str
    modeId: str


class TutorMessageRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sessionId": "session-paris-bistro",
                "lessonId": "lesson-paris-bistro",
                "prompt": "Explain this line in simple English and Thai.",
            }
        }
    )

    sessionId: str
    lessonId: str
    prompt: str


class TutorFeedbackRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sessionId": "session-paris-bistro",
                "rating": "helpful",
                "note": "Clear explanation with Thai support.",
            }
        }
    )

    sessionId: str
    rating: str
    note: Optional[str] = None


class SaveAckBody(BaseModel):
    saved: bool


class LineConfigBody(BaseModel):
    enabled: bool
    liffId: str
    redirectUri: str
    webhookPath: str
    mockMode: bool


class LineStatus(BaseModel):
    connected: bool
    displayName: str
    providerLabel: str
    liffReady: bool
    lastSyncedLabel: str
    note: LocalizedText


class LineProfile(BaseModel):
    userId: str
    displayName: str
    statusMessage: str
    pictureAccent: str
    language: str


class LineLoginBody(BaseModel):
    redirectUrl: str
    state: str


class LineProfileSyncRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "userId": "Uxxxxxxxx",
                "displayName": "Alex on LINE",
                "statusMessage": "Hello from LINE",
                "pictureUrl": "https://profile.line-scdn.net/...",
                "language": "th",
                "liffId": "165xxxxxxxxx-xxxxxxx",
            }
        }
    )

    userId: str
    displayName: str
    statusMessage: str | None = None
    pictureUrl: str | None = None
    language: str | None = None
    liffId: str | None = None


class LineProfileSyncBody(BaseModel):
    connected: bool
    redirectTo: str
    profile: LineProfile
    session: AuthSession


class LineWebhookBody(BaseModel):
    accepted: bool


class VocabItem(BaseModel):
    id: str
    term: str
    translation: LocalizedText
    pronunciation: str
    sourceLessonId: str
    sourceLessonTitle: LocalizedText
    statusId: str
    dueLabel: str
    example: str
    notes: LocalizedText


class VocabDashboard(BaseModel):
    dueTodayCount: int
    completedTodayCount: int
    difficultCount: int
    reviewSession: FlashcardSession


class VocabReviewAnswerRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"sessionId": "review-abc123", "answer": "good"}}
    )

    sessionId: str
    answer: str


class VocabReviewAnswerBody(BaseModel):
    accepted: bool
    nextDueLabel: str


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nativeLanguageId": "thai",
                "targetLanguageId": "english",
                "levelId": "intermediate",
                "weeklyFocusId": "steady",
                "voiceId": "atelier",
                "tutorModeId": "grammar",
                "appLocale": "th",
                "dailyGoalMinutes": 20,
                "interests": ["travel", "conversation"],
                "practiceReminders": True,
                "weeklyDigest": True,
                "tutorFollowUps": True,
                "autoPlayPronunciation": True,
            }
        }
    )

    nativeLanguageId: Optional[str] = None
    targetLanguageId: Optional[str] = None
    levelId: Optional[str] = None
    weeklyFocusId: Optional[str] = None
    voiceId: Optional[str] = None
    tutorModeId: Optional[str] = None
    appLocale: Optional[str] = None
    dailyGoalMinutes: Optional[int] = None
    interests: Optional[List[str]] = None
    practiceReminders: Optional[bool] = None
    weeklyDigest: Optional[bool] = None
    tutorFollowUps: Optional[bool] = None
    autoPlayPronunciation: Optional[bool] = None


class TTSRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Bonjour, comment ça va ?",
                "voiceId": "sorbet",
                "lessonId": "lesson-paris-bistro",
                "clipId": "clip-youtube-paris",
            }
        }
    )

    text: str
    voiceId: Optional[str] = None
    lessonId: Optional[str] = None
    clipId: Optional[str] = None


class TTSBody(BaseModel):
    audioUrl: str
    model: str


class STTRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audioBase64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
                "language": "en",
            }
        }
    )

    audioBase64: Optional[str] = None
    text: Optional[str] = None
    language: Optional[str] = None


class STTBody(BaseModel):
    text: str
    confidence: float
    model: str


class AIGenerateLessonRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lessonId": "lesson-paris-bistro",
                "transcript": "Bonjour tout le monde...",
            }
        }
    )

    lessonId: Optional[str] = None
    clipId: Optional[str] = None
    transcript: Optional[str] = None


class AIGenerateLessonBody(BaseModel):
    lessonId: str
    status: str


class AIGenerateFlashcardsRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"lessonId": "lesson-paris-bistro"}})

    lessonId: str


class AIGenerateFlashcardsBody(BaseModel):
    deckId: str
    cardsGenerated: int


class AIChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Summarize the lesson in Thai and extract three travel phrases.",
                "lessonId": "lesson-paris-bistro",
                "sessionId": "session-paris-bistro",
            }
        }
    )

    prompt: str
    lessonId: Optional[str] = None
    sessionId: Optional[str] = None


class AIChatBody(BaseModel):
    reply: str


class CreateYoutubeJobReq(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "youtube_link": "https://www.youtube.com/watch?v=7IyiKqFQAnk",
                "user_id_token": "device-123",
                "lang": "en",
                "split_seconds": 15,
                "tolerance_seconds": 1,
                "title": "Travel Listening Practice",
                "type_of_transcription": "openai_transcribe",
            }
        }
    )

    youtube_link: str
    user_id_token: str = Field(min_length=1, max_length=36)
    lang: str = "en"
    split_seconds: int = 5
    tolerance_seconds: int = 1
    title: str | None = None
    type_of_transcription: str | None = None


class TranslateYoutubeJobReq(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"youtube_transaction_id": 42, "to_lang": "th"}}
    )

    youtube_transaction_id: int
    to_lang: str = Field(min_length=2, max_length=20)


class JobTrackRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"job_id": 42, "seq": 5}})

    job_id: int
    seq: int


class YoutubeJobRes(BaseModel):
    id: int
    status: str


class ClipDetailRes(BaseModel):
    id: int
    seq: int
    start_s: float
    end_s: float
    message: str
    clip_path: Optional[str] = None
    has_clip: bool = False
    url_video: Optional[str] = None
    translate: Optional[str] = None
    to_lang: Optional[str] = None


class YoutubeJobDetailRes(BaseModel):
    id: int
    youtube_link: str
    title: Optional[str]
    status: str
    created_at: Optional[str] = None
    process_step: Optional[str] = None
    progress: Optional[int] = None
    source_transcript: Optional[str] = None
    token_usage: Optional[int] = None
    clip_error_code: Optional[str] = None
    clip_error_message: Optional[str] = None
    details: List[ClipDetailRes]


class YoutubeTranslateRes(BaseModel):
    youtube_transaction_id: int
    from_lang: Optional[str] = None
    to_lang: str
    translated_count: int
    skipped_count: int
    details: List[ClipDetailRes]


class YoutubeJobListItemRes(BaseModel):
    id: int
    created_at: Optional[str] = None
    title: Optional[str] = None
    lastest_seq: Optional[int] = None
