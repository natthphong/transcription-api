from __future__ import annotations

import asyncio
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import load_settings
from app.db import SessionLocal
from sqlalchemy import select
from app.models import YoutubeTransaction, YoutubeTransactionDetail
from app.services.youtube import download_video
from app.services.splitter import build_clips_from_segments, cut_clip_ffmpeg
from app.services.storage import upload_file
from app.core.logger import log_event
from app.services.transcript import (
    extract_video_id,
    get_transcript_from_youtube_api,
    transcribe_with_openai,
    download_audio,
    download_vtt,
    vtt_to_segments,
)

WORK_DIR = "/tmp/ytjobs"


def _clip_key(prefix: str, clip_id: str) -> str:
    safe_prefix = (prefix or "youtube").strip("/")
    return f"{safe_prefix}/{clip_id}.mp4"


async def _set_step(job_id: int, step: str, log: Optional[str] = None) -> None:
    async with SessionLocal() as db:
        job = await db.get(YoutubeTransaction, job_id)
        if not job:
            return
        job.process_step = step
        if log:
            job.process_log = log
        await db.commit()


def _map_error_code(msg: str) -> str:
    text = (msg or "").lower()
    if "transcript_not_available" in text:
        return "TRANSCRIPT_NOT_AVAILABLE"
    if "too many requests" in text or "429" in text:
        return "YTDLP_TOO_MANY_REQUESTS"
    if "video unavailable" in text:
        return "YTDLP_VIDEO_UNAVAILABLE"
    if "no vtt subtitle" in text or "subtitle" in text:
        return "YTDLP_SUBTITLE_UNAVAILABLE"
    if "openai" in text:
        return "OPENAI_TRANSCRIBE_FAILED"
    if "youtube" in text:
        return "YOUTUBE_API_NOT_AVAILABLE"
    return "UNKNOWN_ERROR"


def _map_clip_error_code(msg: str) -> str:
    text = (msg or "").lower()
    if "please sign in" in text:
        return "YTDLP_SIGN_IN_REQUIRED"
    if "precondition check failed" in text:
        return "YTDLP_PRECONDITION_FAILED"
    if "video unavailable" in text:
        return "YTDLP_VIDEO_UNAVAILABLE"
    if "ffmpeg" in text:
        return "FFMPEG_FAILED"
    if "minio" in text or "upload" in text:
        return "MINIO_UPLOAD_FAILED"
    return "VIDEO_DOWNLOAD_FAILED"


async def process_youtube_job(job_id: int, type_of_transcription:str | None) -> None:
    settings = load_settings()

    async with SessionLocal() as db:
        job = await db.get(YoutubeTransaction, job_id)
        if not job:
            return
        job_data = {
            "youtube_link": job.youtube_link,
            "lang": job.language or "en",
            "split_seconds": job.split_seconds or 5,
            "tolerance_seconds": job.tolerance_seconds or 1,
        }

    job_dir = Path(WORK_DIR) / str(job_id)
    try:
        await _set_step(job_id, "JOB_PROCESS_START", "processing started")
        log_event("JOB_PROCESS_START", job_id=job_id, youtube_link=job_data["youtube_link"])

        await _set_step(job_id, "TRANSCRIPT_FETCH", "fetch transcript")
        video_id = extract_video_id(job_data["youtube_link"])

        segments = []
        source_transcript = "youtube_api"
        token_usage = 0
        is_transcription_youtube = True
        if type_of_transcription is not None and type_of_transcription != "youtube":
            is_transcription_youtube = False
        if is_transcription_youtube:
            try:
                await _set_step(job_id, "TRANSCRIPT_SOURCE_YOUTUBE_API", "youtube transcript api")
                log_event("TRANSCRIPT_SOURCE_YOUTUBE_API_START", job_id=job_id)
                segments = await asyncio.to_thread(
                    get_transcript_from_youtube_api, video_id, [job_data["lang"]]
                )
                log_event("TRANSCRIPT_SOURCE_YOUTUBE_API_DONE", job_id=job_id, segments=len(segments))
            except Exception as e:
                log_event("TRANSCRIPT_SOURCE_YOUTUBE_API_DONE", job_id=job_id, error=str(e))

            if not segments:
                try:
                    source_transcript = "yt_dlp_vtt"
                    await _set_step(job_id, "TRANSCRIPT_SOURCE_YTDLP", "yt-dlp vtt")
                    log_event("TRANSCRIPT_SOURCE_YTDLP_START", job_id=job_id)
                    vtt_path = await asyncio.to_thread(
                        download_vtt, job_data["youtube_link"], str(job_dir), job_data["lang"]
                    )
                    segments = await asyncio.to_thread(vtt_to_segments, str(vtt_path))
                    log_event("TRANSCRIPT_SOURCE_YTDLP_DONE", job_id=job_id, segments=len(segments))
                except Exception as e:
                    log_event("TRANSCRIPT_SOURCE_YTDLP_DONE", job_id=job_id, error=str(e))

        if not segments:
            source_transcript = "openai_transcribe"
            await _set_step(job_id, "TRANSCRIPT_SOURCE_OPENAI", "openai transcribe")
            log_event("TRANSCRIPT_SOURCE_OPENAI_START", job_id=job_id)
            try:
                audio_path = await asyncio.to_thread(
                    download_audio, job_data["youtube_link"], str(job_dir), "audio.mp3"
                )
                segments, token_usage = await asyncio.to_thread(
                    transcribe_with_openai,
                    str(audio_path),
                    int(job_data["split_seconds"]),
                    job_id,
                )
                log_event(
                    "TRANSCRIPT_SOURCE_OPENAI_DONE",
                    job_id=job_id,
                    segments=len(segments),
                    token_usage=token_usage,
                )
            except Exception as e:
                log_event("TRANSCRIPT_SOURCE_OPENAI_DONE", job_id=job_id, error=str(e))
                raise RuntimeError("TRANSCRIPT_NOT_AVAILABLE")

        if not segments:
            raise RuntimeError("TRANSCRIPT_NOT_AVAILABLE")

        await _set_step(job_id, "SEGMENT_BUILD", "build segments")
        log_event("SEGMENT_BUILD_START", job_id=job_id)
        if source_transcript == "openai_transcribe":
            clips = [
                {
                    "seq": idx + 1,
                    "start_s": seg["start_s"],
                    "end_s": seg["end_s"],
                    "text": seg["text"],
                }
                for idx, seg in enumerate(segments)
            ]
        else:
            clips = build_clips_from_segments(
                segments, job_data["split_seconds"], job_data["tolerance_seconds"]
            )
        log_event("SEGMENT_BUILD_DONE", job_id=job_id, segments=len(segments))
        if not clips:
            raise RuntimeError("no clips generated from subtitles")

        await _set_step(job_id, "TRANSCRIPT_SAVE", "save transcript details")
        log_event("TRANSCRIPT_SAVE_START", job_id=job_id, rows=len(clips))
        detail_ids: List[int] = []
        async with SessionLocal() as db:
            job = await db.get(YoutubeTransaction, job_id)
            if not job:
                return
            for c in clips:
                d = YoutubeTransactionDetail(
                    youtube_transaction_id=job_id,
                    message=c["text"] or "",
                    seq=c["seq"],
                    start_ms=int(c["start_s"] * 1000),
                    end_ms=int(c["end_s"] * 1000),
                )
                db.add(d)
            job.source_transcript = source_transcript
            job.token_usage = token_usage
            if segments and not job.title:
                job.title = (segments[0].get("text") or "")[:25]
            await db.commit()

            rows = (await db.execute(
                select(YoutubeTransactionDetail.id).where(
                    YoutubeTransactionDetail.youtube_transaction_id == job_id
                )
            )).scalars().all()
            detail_ids = list(rows)
        log_event("TRANSCRIPT_SAVE_DONE", job_id=job_id, rows=len(detail_ids))

        await _set_step(job_id, "VIDEO_DOWNLOAD", "download video")
        log_event("VIDEO_DOWNLOAD_START", job_id=job_id, youtube_link=job_data["youtube_link"])
        try:
            video_path = await asyncio.to_thread(
                download_video, job_data["youtube_link"], str(job_dir), "video.mp4"
            )
            log_event("VIDEO_DOWNLOAD_DONE", job_id=job_id, path=str(video_path))
        except Exception as e:
            async with SessionLocal() as db:
                job = await db.get(YoutubeTransaction, job_id)
                if job:
                    job.status = "done_transcript_only"
                    job.clip_error_message = str(e)
                    job.clip_error_code = _map_clip_error_code(str(e))
                    job.process_step = "DONE"
                    job.finished_at = datetime.now(timezone.utc)
                    await db.commit()
            log_event("VIDEO_DOWNLOAD_FAILED_NON_FATAL", job_id=job_id, error=str(e))
            log_event("JOB_COMPLETED_TRANSCRIPT_ONLY", job_id=job_id)
            return

        try:
            await _set_step(job_id, "CLIP_CUT", "cut clips")
            log_event("CLIP_PROCESS_START", job_id=job_id, clips=len(clips))
            clip_updates: List[Dict[str, Any]] = []
            for c in clips:
                clip_id = str(uuid.uuid4())
                out_path = job_dir / f"{clip_id}.mp4"
                await asyncio.to_thread(
                    cut_clip_ffmpeg,
                    str(video_path),
                    str(out_path),
                    c["start_s"],
                    c["end_s"],
                )
                log_event("CLIP_CREATED", job_id=job_id, seq=c["seq"], start=c["start_s"], end=c["end_s"])
                key = _clip_key(settings.prefixTTSVoice, clip_id)
                await _set_step(job_id, "UPLOAD", "upload clips")
                log_event("UPLOAD_START", job_id=job_id, key=key)
                await asyncio.to_thread(upload_file, str(out_path), key, "video/mp4")
                log_event("UPLOAD_DONE", job_id=job_id, key=key)
                clip_updates.append({"seq": c["seq"], "clip_path": key})

            async with SessionLocal() as db:
                job = await db.get(YoutubeTransaction, job_id)
                if not job:
                    return
                for u in clip_updates:
                    await db.execute(
                        YoutubeTransactionDetail.__table__.update()
                        .where(
                            (YoutubeTransactionDetail.youtube_transaction_id == job_id)
                            & (YoutubeTransactionDetail.seq == u["seq"])
                        )
                        .values(clip_path=u["clip_path"])
                    )
                job.status = "done"
                job.clip_error_code = None
                job.clip_error_message = None
                job.process_step = "DONE"
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()
            log_event("CLIP_PROCESS_DONE", job_id=job_id, clips=len(clip_updates))
        except Exception as e:
            async with SessionLocal() as db:
                job = await db.get(YoutubeTransaction, job_id)
                if job:
                    job.status = "done_transcript_only"
                    job.clip_error_message = str(e)
                    job.clip_error_code = _map_clip_error_code(str(e))
                    job.process_step = "DONE"
                    job.finished_at = datetime.now(timezone.utc)
                    await db.commit()
            log_event("CLIP_PROCESS_FAILED_NON_FATAL", job_id=job_id, error=str(e))
            log_event("JOB_COMPLETED_TRANSCRIPT_ONLY", job_id=job_id)
            return

        duration = None
        async with SessionLocal() as db:
            job = await db.get(YoutubeTransaction, job_id)
            if job and job.started_at and job.finished_at:
                duration = (job.finished_at - job.started_at).total_seconds()
        log_event("DETAIL_INSERT_DONE", job_id=job_id, clips=len(clips))
        log_event("JOB_COMPLETED", job_id=job_id, clips=len(clips), duration_s=duration)

    except Exception as e:
        async with SessionLocal() as db:
            job = await db.get(YoutubeTransaction, job_id)
            if job:
                job.status = "error"
                job.error_message = str(e)
                job.error_code = _map_error_code(str(e))
                job.process_step = "FAILED"
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()
        log_event("JOB_FAILED", job_id=job_id, level="error", error=str(e))
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)
        log_event("TMP_CLEANUP_DONE", job_id=job_id, path=str(job_dir))


async def process_job(job_id: int) -> None:
    await process_youtube_job(job_id)
