from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
try:
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
    _SQLALCHEMY_14_COMPAT = False
except ImportError:  # SQLAlchemy 1.4 compatibility
    from sqlalchemy.orm import declarative_base, relationship

    DeclarativeBase = declarative_base()  # type: ignore[assignment]
    _SQLALCHEMY_14_COMPAT = True

    class _MappedCompat:
        def __class_getitem__(cls, _item):
            return Any

    Mapped = _MappedCompat  # type: ignore[assignment]

    def mapped_column(*args, **kwargs):
        return Column(*args, **kwargs)

if _SQLALCHEMY_14_COMPAT:
    Base = DeclarativeBase
else:
    class Base(DeclarativeBase):
        pass


class YoutubeTransaction(Base):
    __tablename__ = "tbl_youtube_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    youtube_link: Mapped[str] = mapped_column(Text, nullable=False)
    user_id_token: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_auto_caption: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    split_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tolerance_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    process_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    process_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default="0")
    source_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default="0")
    clip_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    clip_error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    lastest_seq: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default="0")

    details = relationship("YoutubeTransactionDetail", back_populates="transaction")
    lesson = relationship("AppLesson", back_populates="youtube_transaction", uselist=False)


class YoutubeTransactionDetail(Base):
    __tablename__ = "tbl_youtube_transaction_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_transaction_id: Mapped[int] = mapped_column(ForeignKey("tbl_youtube_transaction.id"))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    start_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    end_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    clip_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    transaction = relationship("YoutubeTransaction", back_populates="details")


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_initials: Mapped[str] = mapped_column(String(8), nullable=False)
    membership_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="starter")
    native_language_id: Mapped[str] = mapped_column(String(40), nullable=False)
    target_language_id: Mapped[str] = mapped_column(String(40), nullable=False)
    level_id: Mapped[str] = mapped_column(String(40), nullable=False)
    weekly_focus_id: Mapped[str] = mapped_column(String(40), nullable=False)
    interests: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    app_locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    goal_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notification_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tutor_preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions = relationship("AppUserSession", back_populates="user")
    line_account = relationship("AppLineAccount", back_populates="user", uselist=False)
    lessons = relationship("AppLesson", back_populates="user")
    tutor_sessions = relationship("AppTutorSession", back_populates="user")
    vocab_items = relationship("AppVocabItem", back_populates="user")
    review_sessions = relationship("AppReviewSession", back_populates="user")


class AppUserSession(Base):
    __tablename__ = "app_user_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    access_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    current_role: Mapped[str] = mapped_column(String(40), nullable=False, default="learner")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("AppUser", back_populates="sessions")


class AppLineAccount(Base):
    __tablename__ = "app_line_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, unique=True)
    line_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    picture_accent: Mapped[str] = mapped_column(String(40), nullable=False, default="coral")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("AppUser", back_populates="line_account")


class AppLesson(Base):
    __tablename__ = "app_lessons"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    youtube_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("tbl_youtube_transaction.id"), nullable=True, unique=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    subtitle: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status_id: Mapped[str] = mapped_column(String(40), nullable=False, default="ready")
    status_label: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    extracted_vocab_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[str] = mapped_column(String(40), nullable=False)
    thumbnail_accent: Mapped[str] = mapped_column(String(20), nullable=False, default="coral")
    clip_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_label: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    learning_objectives: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tabs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_language_id: Mapped[str] = mapped_column(String(40), nullable=False)
    target_language_id: Mapped[str] = mapped_column(String(40), nullable=False)
    voice_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    auto_detect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("AppUser", back_populates="lessons")
    youtube_transaction = relationship("YoutubeTransaction", back_populates="lesson")
    clips = relationship("AppLessonClip", back_populates="lesson")
    transcript_blocks = relationship("AppLessonTranscriptBlock", back_populates="lesson")
    lesson_vocabularies = relationship("AppLessonVocabulary", back_populates="lesson")
    tutor_sessions = relationship("AppTutorSession", back_populates="lesson")
    vocab_items = relationship("AppVocabItem", back_populates="lesson")
    video = relationship("AppVideo", back_populates="lesson", uselist=False)


class AppLessonClip(Base):
    __tablename__ = "app_lesson_clips"
    __table_args__ = (UniqueConstraint("lesson_id", "seq", name="uq_app_lesson_clips_lesson_seq"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("app_lessons.id"), nullable=False, index=True)
    youtube_transaction_detail_id: Mapped[int | None] = mapped_column(
        ForeignKey("tbl_youtube_transaction_details.id"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    channel: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transcript_status: Mapped[str] = mapped_column(String(40), nullable=False, default="processing")
    start_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    end_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    clip_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson = relationship("AppLesson", back_populates="clips")


class AppLessonTranscriptBlock(Base):
    __tablename__ = "app_lesson_transcript_blocks"
    __table_args__ = (
        UniqueConstraint("lesson_id", "seq", name="uq_app_lesson_transcript_blocks_lesson_seq"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("app_lessons.id"), nullable=False, index=True)
    clip_id: Mapped[str | None] = mapped_column(ForeignKey("app_lesson_clips.id"), nullable=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_label: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    translated: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson = relationship("AppLesson", back_populates="transcript_blocks")


class AppLessonVocabulary(Base):
    __tablename__ = "app_lesson_vocabularies"
    __table_args__ = (UniqueConstraint("lesson_id", "term", name="uq_app_lesson_vocabularies_term"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("app_lessons.id"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    pronunciation: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    meaning: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson = relationship("AppLesson", back_populates="lesson_vocabularies")


class AppTutorSession(Base):
    __tablename__ = "app_tutor_sessions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("app_lessons.id"), nullable=False, index=True)
    clip_id: Mapped[str] = mapped_column(ForeignKey("app_lesson_clips.id"), nullable=False, index=True)
    title: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    lesson_label: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_message_preview: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    mode_id: Mapped[str] = mapped_column(String(40), nullable=False, default="coach")
    context_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    selected_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quick_prompts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    waveform: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    available_actions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("AppUser", back_populates="tutor_sessions")
    lesson = relationship("AppLesson", back_populates="tutor_sessions")
    messages = relationship("AppTutorMessage", back_populates="session")
    feedback_rows = relationship("AppTutorFeedback", back_populates="session")


class AppTutorMessage(Base):
    __tablename__ = "app_tutor_messages"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("app_tutor_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_label: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session = relationship("AppTutorSession", back_populates="messages")


class AppTutorFeedback(Base):
    __tablename__ = "app_tutor_feedback"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("app_tutor_sessions.id"), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session = relationship("AppTutorSession", back_populates="feedback_rows")


class AppVocabItem(Base):
    __tablename__ = "app_vocab_items"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    source_lesson_id: Mapped[str] = mapped_column(ForeignKey("app_lessons.id"), nullable=False, index=True)
    lesson_vocabulary_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_lesson_vocabularies.id"), nullable=True
    )
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    translation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    pronunciation: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status_id: Mapped[str] = mapped_column(String(40), nullable=False, default="due")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    example: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    interval_days: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("AppUser", back_populates="vocab_items")
    lesson = relationship("AppLesson", back_populates="vocab_items")
    review_history = relationship("AppVocabReviewHistory", back_populates="vocab_item")


class AppReviewSession(Base):
    __tablename__ = "app_review_sessions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    deck_id: Mapped[str] = mapped_column(String(80), nullable=False)
    source_label: Mapped[str] = mapped_column(String(120), nullable=False, default="Lesson vocab")
    queue: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    current_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    review_options: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("AppUser", back_populates="review_sessions")


class AppVocabReviewHistory(Base):
    __tablename__ = "app_vocab_review_history"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    vocab_item_id: Mapped[str] = mapped_column(ForeignKey("app_vocab_items.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    review_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("app_review_sessions.id"), nullable=True
    )
    answer: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_status_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    next_status_id: Mapped[str] = mapped_column(String(40), nullable=False)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    vocab_item = relationship("AppVocabItem", back_populates="review_history")


class AppVideo(Base):
    __tablename__ = "app_videos"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("app_lessons.id"), nullable=False, unique=True)
    title: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    thumbnail_accent: Mapped[str] = mapped_column(String(20), nullable=False, default="coral")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    quiz: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson = relationship("AppLesson", back_populates="video")
