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
    deckId: Optional[str] = None


class FlashcardStartBody(BaseModel):
    sessionId: str
    nextRoute: str


class FlashcardAnswerRequest(BaseModel):
    sessionId: str
    answer: str


class FlashcardAnswerBody(BaseModel):
    saved: bool
    nextCardId: Optional[str] = None


class FlashcardFinishRequest(BaseModel):
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
    lessonId: str
    clipId: str
    modeId: str


class TutorMessageRequest(BaseModel):
    sessionId: str
    lessonId: str
    prompt: str


class TutorFeedbackRequest(BaseModel):
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
    sessionId: str
    answer: str


class VocabReviewAnswerBody(BaseModel):
    accepted: bool
    nextDueLabel: str


class ProfileUpdateRequest(BaseModel):
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
    text: str
    voiceId: Optional[str] = None
    lessonId: Optional[str] = None
    clipId: Optional[str] = None


class TTSBody(BaseModel):
    audioUrl: str
    model: str


class STTRequest(BaseModel):
    audioBase64: Optional[str] = None
    text: Optional[str] = None
    language: Optional[str] = None


class STTBody(BaseModel):
    text: str
    confidence: float
    model: str


class AIGenerateLessonRequest(BaseModel):
    lessonId: Optional[str] = None
    clipId: Optional[str] = None
    transcript: Optional[str] = None


class AIGenerateLessonBody(BaseModel):
    lessonId: str
    status: str


class AIGenerateFlashcardsRequest(BaseModel):
    lessonId: str


class AIGenerateFlashcardsBody(BaseModel):
    deckId: str
    cardsGenerated: int


class AIChatRequest(BaseModel):
    prompt: str
    lessonId: Optional[str] = None
    sessionId: Optional[str] = None


class AIChatBody(BaseModel):
    reply: str


class CreateYoutubeJobReq(BaseModel):
    youtube_link: str
    user_id_token: str = Field(min_length=1, max_length=36)
    lang: str = "en"
    split_seconds: int = 5
    tolerance_seconds: int = 1
    title: str | None = None
    type_of_transcription: str | None = None


class JobTrackRequest(BaseModel):
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


class YoutubeJobListItemRes(BaseModel):
    id: int
    created_at: Optional[str] = None
    title: Optional[str] = None
    lastest_seq: Optional[int] = None
