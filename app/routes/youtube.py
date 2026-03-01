from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db import get_db
from app.models import YoutubeTransaction, YoutubeTransactionDetail
from app.schemas import CreateYoutubeJobReq, YoutubeJobRes, YoutubeJobDetailRes, ClipDetailRes
from app.services.youtube import download_vtt, vtt_to_segments
from app.services.splitter import build_clips_from_segments
from pathlib import Path

router = APIRouter(prefix="/youtube", tags=["youtube"])

WORK_DIR = "/tmp/ytjobs"

@router.post("/jobs", response_model=YoutubeJobRes)
async def create_job(req: CreateYoutubeJobReq, db: AsyncSession = Depends(get_db)):
    # if req.split_seconds not in (5, 10, 15):
    #     raise HTTPException(status_code=400, detail="split_seconds must be 5, 10, or 15")

    job = YoutubeTransaction(
        title=None,
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

    # Process immediately (simple MVP). Later you can move to background worker/queue.
    try:
        job_dir = str(Path(WORK_DIR) / str(job.id))
        vtt_path, is_auto = download_vtt(req.youtube_link, out_dir=job_dir, lang=req.lang)
        segments = vtt_to_segments(str(vtt_path))
        clips = build_clips_from_segments(segments, req.split_seconds, req.tolerance_seconds)

        # insert details
        for c in clips:
            start_ms = int(c["start_s"] * 1000)
            end_ms = int(c["end_s"] * 1000)
            d = YoutubeTransactionDetail(
                youtube_transaction_id=job.id,
                message=c["text"] or "",
                seq=c["seq"],
                start_ms=start_ms,
                end_ms=end_ms,
            )
            db.add(d)

        # update job status
        job.is_auto_caption = is_auto
        job.status = "done"
        await db.commit()

    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"process failed: {e}")

    return YoutubeJobRes(id=job.id, status=job.status)

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
        ))

    return YoutubeJobDetailRes(
        id=job.id,
        youtube_link=job.youtube_link,
        title=job.title,
        status=job.status or "unknown",
        details=details
    )