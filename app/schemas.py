from pydantic import BaseModel, Field
from typing import Optional, List

class CreateYoutubeJobReq(BaseModel):
    youtube_link: str
    user_id_token: str = Field(min_length=1, max_length=36)
    lang: str = "en"
    split_seconds: int = 5   # 5/10/15
    tolerance_seconds: int = 1
    title: str | None = None
    type_of_transcription: str | None = None

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
