ALTER TABLE tbl_youtube_transaction
ADD COLUMN source_transcript TEXT,
ADD COLUMN token_usage INTEGER DEFAULT 0,
ADD COLUMN process_step TEXT,
ADD COLUMN process_log TEXT,
ADD COLUMN started_at TIMESTAMPTZ,
ADD COLUMN finished_at TIMESTAMPTZ,
ADD COLUMN error_code TEXT,
ADD COLUMN retry_count INTEGER DEFAULT 0,
ADD COLUMN clip_error_message TEXT,
ADD COLUMN clip_error_code TEXT;
