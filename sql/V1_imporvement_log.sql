ALTER TABLE tbl_youtube_transaction
ADD COLUMN process_step TEXT;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN process_log TEXT;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN started_at TIMESTAMP;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN finished_at TIMESTAMP;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN error_code TEXT;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN retry_count INTEGER DEFAULT 0;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN source_transcript TEXT;

ALTER TABLE tbl_youtube_transaction
ADD COLUMN token_usage INTEGER;