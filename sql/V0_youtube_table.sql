CREATE TABLE tbl_youtube_transaction (
      id            serial PRIMARY KEY,
      title varchar(255) null,
      youtube_link text,
      user_id_token VARCHAR(36) NOT NULL,
      created_at    TIMESTAMP DEFAULT now()
);


CREATE TABLE tbl_youtube_transaction_details (
      id            serial PRIMARY KEY,
      youtube_transaction_id int ,
      message text,
      start_timestamp TIMESTAMPTZ ,
      end_timestamp TIMESTAMPTZ ,
      created_at    TIMESTAMPTZ DEFAULT now(),
      updated_at    TIMESTAMPTZ
);


ALTER TABLE tbl_youtube_transaction
ADD COLUMN status varchar(20) DEFAULT 'queued',
ADD COLUMN language varchar(10),
ADD COLUMN is_auto_caption boolean,
ADD COLUMN split_seconds int,
ADD COLUMN tolerance_seconds int,
ADD COLUMN error_message text;

ALTER TABLE tbl_youtube_transaction_details
ADD COLUMN seq int,
ADD COLUMN start_ms bigint,
ADD COLUMN end_ms bigint,
ADD COLUMN clip_path text;