alter table public.tbl_youtube_transaction_details
    add translate text;

alter table public.tbl_youtube_transaction_details
    add to_lang varchar(20);
