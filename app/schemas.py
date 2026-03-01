from pydantic import BaseModel, Field
from typing import Optional, List

class CreateYoutubeJobReq(BaseModel):
    youtube_link: str
    user_id_token: str = Field(min_length=1, max_length=36)
    lang: str = "en"
    split_seconds: int = 5   # 5/10/15
    tolerance_seconds: int = 1

class YoutubeJobRes(BaseModel):
    id: int
    status: str

class ClipDetailRes(BaseModel):
    id: int
    seq: int
    start_s: float
    end_s: float
    message: str

class YoutubeJobDetailRes(BaseModel):
    id: int
    youtube_link: str
    title: Optional[str]
    status: str
    details: List[ClipDetailRes]