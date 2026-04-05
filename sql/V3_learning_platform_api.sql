CREATE TABLE IF NOT EXISTS app_users (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    avatar_initials VARCHAR(8) NOT NULL,
    membership_tier VARCHAR(20) NOT NULL DEFAULT 'starter',
    native_language_id VARCHAR(40) NOT NULL,
    target_language_id VARCHAR(40) NOT NULL,
    level_id VARCHAR(40) NOT NULL,
    weekly_focus_id VARCHAR(40) NOT NULL,
    interests JSONB NOT NULL DEFAULT '[]'::jsonb,
    streak_days INTEGER NOT NULL DEFAULT 0,
    daily_goal_minutes INTEGER NOT NULL DEFAULT 15,
    timezone VARCHAR(80) NOT NULL DEFAULT 'UTC',
    app_locale VARCHAR(10) NOT NULL DEFAULT 'en',
    goal_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    notification_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    tutor_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_user_sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES app_users(id),
    access_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255) NOT NULL UNIQUE,
    "current_role" VARCHAR(40) NOT NULL DEFAULT 'learner',
    expires_at TIMESTAMPTZ,
    refresh_expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_user_sessions_user_id ON app_user_sessions(user_id);

CREATE TABLE IF NOT EXISTS app_line_accounts (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL UNIQUE REFERENCES app_users(id),
    line_user_id VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    status_message TEXT NOT NULL DEFAULT '',
    picture_accent VARCHAR(40) NOT NULL DEFAULT 'coral',
    language VARCHAR(20) NOT NULL DEFAULT 'en',
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_lessons (
    id VARCHAR(80) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES app_users(id),
    youtube_transaction_id INTEGER UNIQUE REFERENCES tbl_youtube_transaction(id),
    source_url TEXT NOT NULL,
    title JSONB NOT NULL DEFAULT '{}'::jsonb,
    subtitle JSONB NOT NULL DEFAULT '{}'::jsonb,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    progress_percent INTEGER NOT NULL DEFAULT 0,
    status_id VARCHAR(40) NOT NULL DEFAULT 'ready',
    status_label JSONB NOT NULL DEFAULT '{}'::jsonb,
    extracted_vocab_count INTEGER NOT NULL DEFAULT 0,
    category_id VARCHAR(40) NOT NULL,
    thumbnail_accent VARCHAR(20) NOT NULL DEFAULT 'coral',
    clip_count INTEGER NOT NULL DEFAULT 1,
    source_label JSONB NOT NULL DEFAULT '{}'::jsonb,
    learning_objectives JSONB NOT NULL DEFAULT '[]'::jsonb,
    tabs JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommended_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_language_id VARCHAR(40) NOT NULL,
    target_language_id VARCHAR(40) NOT NULL,
    voice_id VARCHAR(40),
    auto_detect BOOLEAN NOT NULL DEFAULT TRUE,
    last_activity_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_lessons_user_id ON app_lessons(user_id);

CREATE TABLE IF NOT EXISTS app_lesson_clips (
    id VARCHAR(80) PRIMARY KEY,
    lesson_id VARCHAR(80) NOT NULL REFERENCES app_lessons(id),
    youtube_transaction_detail_id INTEGER REFERENCES tbl_youtube_transaction_details(id),
    source_url TEXT NOT NULL,
    title JSONB NOT NULL DEFAULT '{}'::jsonb,
    channel VARCHAR(255) NOT NULL DEFAULT '',
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    transcript_status VARCHAR(40) NOT NULL DEFAULT 'processing',
    start_ms BIGINT,
    end_ms BIGINT,
    clip_path TEXT,
    seq INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_app_lesson_clips_lesson_seq UNIQUE (lesson_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_app_lesson_clips_lesson_id ON app_lesson_clips(lesson_id);

CREATE TABLE IF NOT EXISTS app_lesson_transcript_blocks (
    id VARCHAR(80) PRIMARY KEY,
    lesson_id VARCHAR(80) NOT NULL REFERENCES app_lessons(id),
    clip_id VARCHAR(80) REFERENCES app_lesson_clips(id),
    seq INTEGER NOT NULL,
    timestamp_label VARCHAR(20) NOT NULL,
    source TEXT NOT NULL,
    translated TEXT NOT NULL DEFAULT '',
    explanation JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_app_lesson_transcript_blocks_lesson_seq UNIQUE (lesson_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_app_lesson_transcript_blocks_lesson_id ON app_lesson_transcript_blocks(lesson_id);

CREATE TABLE IF NOT EXISTS app_lesson_vocabularies (
    id VARCHAR(80) PRIMARY KEY,
    lesson_id VARCHAR(80) NOT NULL REFERENCES app_lessons(id),
    term VARCHAR(255) NOT NULL,
    pronunciation VARCHAR(255) NOT NULL DEFAULT '',
    meaning JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_app_lesson_vocabularies_term UNIQUE (lesson_id, term)
);
CREATE INDEX IF NOT EXISTS idx_app_lesson_vocabularies_lesson_id ON app_lesson_vocabularies(lesson_id);

CREATE TABLE IF NOT EXISTS app_tutor_sessions (
    id VARCHAR(80) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES app_users(id),
    lesson_id VARCHAR(80) NOT NULL REFERENCES app_lessons(id),
    clip_id VARCHAR(80) NOT NULL REFERENCES app_lesson_clips(id),
    title JSONB NOT NULL DEFAULT '{}'::jsonb,
    lesson_label JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_message_preview JSONB NOT NULL DEFAULT '{}'::jsonb,
    mode_id VARCHAR(40) NOT NULL DEFAULT 'coach',
    context_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    selected_excerpt TEXT NOT NULL DEFAULT '',
    quick_prompts JSONB NOT NULL DEFAULT '[]'::jsonb,
    waveform JSONB NOT NULL DEFAULT '[]'::jsonb,
    available_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_tutor_sessions_user_id ON app_tutor_sessions(user_id);

CREATE TABLE IF NOT EXISTS app_tutor_messages (
    id VARCHAR(80) PRIMARY KEY,
    session_id VARCHAR(80) NOT NULL REFERENCES app_tutor_sessions(id),
    role VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    timestamp_label VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_tutor_messages_session_id ON app_tutor_messages(session_id);

CREATE TABLE IF NOT EXISTS app_tutor_feedback (
    id VARCHAR(80) PRIMARY KEY,
    session_id VARCHAR(80) NOT NULL REFERENCES app_tutor_sessions(id),
    rating VARCHAR(20) NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_vocab_items (
    id VARCHAR(80) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES app_users(id),
    source_lesson_id VARCHAR(80) NOT NULL REFERENCES app_lessons(id),
    lesson_vocabulary_id VARCHAR(80) REFERENCES app_lesson_vocabularies(id),
    term VARCHAR(255) NOT NULL,
    translation JSONB NOT NULL DEFAULT '{}'::jsonb,
    pronunciation VARCHAR(255) NOT NULL DEFAULT '',
    status_id VARCHAR(40) NOT NULL DEFAULT 'due',
    due_at TIMESTAMPTZ,
    example TEXT NOT NULL DEFAULT '',
    notes JSONB NOT NULL DEFAULT '{}'::jsonb,
    interval_days DOUBLE PRECISION NOT NULL DEFAULT 0,
    ease_factor DOUBLE PRECISION NOT NULL DEFAULT 2.5,
    repetitions INTEGER NOT NULL DEFAULT 0,
    last_reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_vocab_items_user_id ON app_vocab_items(user_id);
CREATE INDEX IF NOT EXISTS idx_app_vocab_items_source_lesson_id ON app_vocab_items(source_lesson_id);

CREATE TABLE IF NOT EXISTS app_review_sessions (
    id VARCHAR(80) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES app_users(id),
    deck_id VARCHAR(80) NOT NULL,
    source_label VARCHAR(120) NOT NULL DEFAULT 'Lesson vocab',
    queue JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_index INTEGER NOT NULL DEFAULT 0,
    total_count INTEGER NOT NULL DEFAULT 0,
    note JSONB NOT NULL DEFAULT '{}'::jsonb,
    review_options JSONB NOT NULL DEFAULT '[]'::jsonb,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_review_sessions_user_id ON app_review_sessions(user_id);

CREATE TABLE IF NOT EXISTS app_vocab_review_history (
    id VARCHAR(80) PRIMARY KEY,
    vocab_item_id VARCHAR(80) NOT NULL REFERENCES app_vocab_items(id),
    user_id VARCHAR(64) NOT NULL REFERENCES app_users(id),
    review_session_id VARCHAR(80) REFERENCES app_review_sessions(id),
    answer VARCHAR(20) NOT NULL,
    previous_status_id VARCHAR(40),
    next_status_id VARCHAR(40) NOT NULL,
    next_due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_app_vocab_review_history_user_id ON app_vocab_review_history(user_id);

CREATE TABLE IF NOT EXISTS app_videos (
    id VARCHAR(80) PRIMARY KEY,
    lesson_id VARCHAR(80) NOT NULL UNIQUE REFERENCES app_lessons(id),
    title JSONB NOT NULL DEFAULT '{}'::jsonb,
    thumbnail_accent VARCHAR(20) NOT NULL DEFAULT 'coral',
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    quiz JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
