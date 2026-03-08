import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import update

from app.db import get_db
from app.models import YoutubeTransaction, YoutubeTransactionDetail
from app.schemas import CreateYoutubeJobReq, YoutubeJobRes, YoutubeJobDetailRes, ClipDetailRes, YoutubeJobListItemRes, \
    JobTrackRequest
from app.services.youtube_jobs import process_youtube_job
from app.config import load_settings
from typing import Optional
from app.core.logger import log_event

router = APIRouter(prefix="/youtube", tags=["youtube"])

settings = load_settings()


def _build_url(base_url: Optional[str], clip_path: Optional[str]) -> Optional[str]:
    if not base_url or not clip_path:
        return None
    return f"{base_url.rstrip('/')}/file?key={clip_path}"


def _has_clip(clip_path: Optional[str]) -> bool:
    return bool(clip_path)


def _progress_for_step(step: Optional[str]) -> int:
    if not step:
        return 0
    table = {
        "VIDEO_DOWNLOAD": 10,
        "TRANSCRIPT_FETCH": 20,
        "TRANSCRIPT_SOURCE_YOUTUBE_API": 20,
        "TRANSCRIPT_SOURCE_YTDLP": 20,
        "TRANSCRIPT_SOURCE_OPENAI": 20,
        "OPENAI_TRANSCRIBE": 20,
        "SEGMENT_BUILD": 40,
        "CLIP_CUT": 70,
        "UPLOAD": 90,
        "DONE": 100,
        "FAILED": 100,
    }
    return table.get(step, 0)

@router.post("/job/track", response_model=YoutubeJobRes)
async def track_job(req: JobTrackRequest, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        update(YoutubeTransaction)
        .where(YoutubeTransaction.id == req.job_id)
        .values(lastest_seq=req.seq)
        .returning(YoutubeTransaction)
    )

    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=404, detail="job not found or not updated")

    await db.commit()
    return YoutubeJobRes(id=job.id, status=job.status or "processing")
@router.post("/jobs", response_model=YoutubeJobRes)
async def create_job(req: CreateYoutubeJobReq, db: AsyncSession = Depends(get_db)):
    # if req.split_seconds not in (5, 10, 15):
    #     raise HTTPException(status_code=400, detail="split_seconds must be 5, 10, or 15")

    job = YoutubeTransaction(
        title=req.title,
        youtube_link=req.youtube_link,
        user_id_token=req.user_id_token,
        status="processing",
        language=req.lang,
        split_seconds=req.split_seconds,
        tolerance_seconds=req.tolerance_seconds,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    job.process_step = "JOB_CREATED"
    job.process_log = "created"
    job.started_at = datetime.now(timezone.utc)
    await db.commit()
    log_event("JOB_CREATED", job_id=job.id)

    asyncio.create_task(process_youtube_job(job.id,req.type_of_transcription))

    return YoutubeJobRes(id=job.id, status=job.status or "processing")


@router.get("/jobs", response_model=list[YoutubeJobListItemRes])
async def list_jobs(user_id_token: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(YoutubeTransaction)
        .where(YoutubeTransaction.user_id_token == user_id_token)
        .order_by(YoutubeTransaction.created_at.desc())
    )).scalars().all()

    items = []
    for r in rows:
        title = r.title
        if not title:
            first_detail = (await db.execute(
                select(YoutubeTransactionDetail.message)
                .where(YoutubeTransactionDetail.youtube_transaction_id == r.id)
                .order_by(YoutubeTransactionDetail.seq.asc())
                .limit(1)
            )).scalar_one_or_none()
            if first_detail:
                title = str(first_detail)[:25]
        items.append(
            YoutubeJobListItemRes(
                id=r.id,
                created_at=str(r.created_at) if r.created_at else None,
                title=title,
                lastest_seq=r.lastest_seq
            )
        )
    return items

@router.get("/jobs/{job_id}", response_model=YoutubeJobDetailRes)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = (await db.execute(select(YoutubeTransaction).where(YoutubeTransaction.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    rows = (await db.execute(
        select(YoutubeTransactionDetail).where(YoutubeTransactionDetail.youtube_transaction_id == job_id).order_by(YoutubeTransactionDetail.seq.asc())
    )).scalars().all()

    details = []
    for r in rows:
        details.append(ClipDetailRes(
            id=r.id,
            seq=r.seq or 0,
            start_s=(r.start_ms or 0)/1000.0,
            end_s=(r.end_ms or 0)/1000.0,
            message=r.message,
            clip_path=r.clip_path,
            has_clip=_has_clip(r.clip_path),
            url_video=_build_url(settings.BaseURL, r.clip_path) if r.clip_path else None,
        ))

    return YoutubeJobDetailRes(
        id=job.id,
        youtube_link=job.youtube_link,
        title=job.title,
        status=job.status or "unknown",
        created_at=str(job.created_at) if job.created_at else None,
        process_step=job.process_step,
        progress=_progress_for_step(job.process_step),
        source_transcript=job.source_transcript,
        token_usage=job.token_usage or 0,
        clip_error_code=job.clip_error_code,
        clip_error_message=job.clip_error_message,
        details=details
    )
