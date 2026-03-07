from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

from app.config import load_settings


_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_VTT_TIME_RE = re.compile(r"(\d+):(\d+):(\d+\.\d+)\s+-->\s+(\d+):(\d+):(\d+\.\d+)")


def extract_video_id(url_or_id: str) -> str:
    if _ID_RE.match(url_or_id):
        return url_or_id
    try:
        u = urlparse(url_or_id)
        if u.netloc in {"youtu.be"}:
            vid = u.path.strip("/").split("/")[0]
            if _ID_RE.match(vid):
                return vid
        if "youtube.com" in u.netloc:
            if u.path == "/watch":
                qs = parse_qs(u.query)
                vid = (qs.get("v") or [None])[0]
                if vid and _ID_RE.match(vid):
                    return vid
            parts = [p for p in u.path.split("/") if p]
            if parts and parts[0] in {"shorts", "embed"} and len(parts) >= 2:
                vid = parts[1]
                if _ID_RE.match(vid):
                    return vid
    except Exception:
        pass
    raise ValueError("invalid youtube url")


def clean_transcript_text(text: str) -> str:
    t = html.unescape(text or "")
    t = t.replace("\n", " ").replace("\r", " ")
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""

    # Remove duplicate trailing punctuation like "!!" or ".."
    t = re.sub(r"([.!?])\1+", r"\1", t)

    # Remove consecutive duplicate sentences
    sentences = _SENT_SPLIT_RE.split(t)
    cleaned = []
    prev = None
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        key = s.lower()
        if key == prev:
            continue
        cleaned.append(s)
        prev = key
    t = " ".join(cleaned).strip()

    # Remove duplicated full text (A A)
    parts = t.split(" ")
    if len(parts) >= 4:
        mid = len(parts) // 2
        if parts[:mid] == parts[mid:]:
            t = " ".join(parts[:mid])

    return t


def get_transcript_from_youtube_api(video_id: str, languages: List[str] | None = None) -> List[Dict]:
    raw = YouTubeTranscriptApi.get_transcript(video_id, languages=languages or ["en"])
    segments: List[Dict] = []
    prev_text = None
    for item in raw:
        text = clean_transcript_text(item.get("text", ""))
        if not text:
            continue
        if text == prev_text:
            continue
        start_s = float(item.get("start", 0.0))
        duration = float(item.get("duration", 0.0))
        end_s = start_s + duration
        segments.append({"start_s": start_s, "end_s": end_s, "text": text})
        prev_text = text
    return segments


def _run(cmd: List[str], cwd: Optional[str] = None) -> None:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDERR:\n{p.stderr}")


def clean_vtt_text(text: str) -> str:
    t = text or ""
    t = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", t)
    t = re.sub(r"</?c[^>]*>", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = t.replace("\n", " ").replace("\r", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return clean_transcript_text(t)


def download_vtt(youtube_url: str, out_dir: str, lang: str = "en") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    _run(
        [
            "yt-dlp",
            "--extractor-args",
            "youtube:player_client=android",
            "--sleep-requests",
            "1",
            "--retries",
            "3",
            "--skip-download",
            "--write-auto-subs",
            "--sub-langs",
            lang,
            "--sub-format",
            "vtt",
            "-o",
            str(out / "%(id)s.%(ext)s"),
            youtube_url,
        ],
        cwd=out_dir,
    )

    vtts = list(out.glob("*.vtt"))
    if not vtts:
        raise RuntimeError("No VTT subtitle found (auto subs).")
    return vtts[0]

def _collapse_progressive(lines: List[str]) -> str:
    if not lines:
        return ""
    if len(lines) == 1:
        return lines[0]
    prev = lines[0]
    progressive = True
    for line in lines[1:]:
        if not line.startswith(prev):
            progressive = False
            break
        prev = line
    if progressive:
        return lines[-1]
    return " ".join(lines)


def vtt_to_segments(vtt_path: str) -> List[Dict]:
    text = Path(vtt_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    segments: List[Dict] = []
    i = 0
    while i < len(text):
        line = text[i].strip()
        m = _VTT_TIME_RE.search(line)
        if not m:
            i += 1
            continue

        sh, sm, ss, eh, em, es = m.groups()
        start_s = int(sh) * 3600 + int(sm) * 60 + float(ss)
        end_s = int(eh) * 3600 + int(em) * 60 + float(es)

        i += 1
        caption_lines = []
        while i < len(text) and text[i].strip() != "":
            caption_lines.append(text[i].strip())
            i += 1

        collapsed = _collapse_progressive(caption_lines)
        caption = clean_vtt_text(collapsed)
        if caption:
            segments.append({"start_s": start_s, "end_s": end_s, "text": caption})
        i += 1

    return segments


def download_audio(youtube_url: str, out_dir: str, filename: str = "audio.mp3") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    template = str(out / "audio.%(ext)s")

    _run(
        [
            "yt-dlp",
            "--extractor-args",
            "youtube:player_client=android",
            "--sleep-requests",
            "1",
            "--retries",
            "3",
            "-x",
            "--audio-format",
            "mp3",
            "-o",
            template,
            youtube_url,
        ],
        cwd=out_dir,
    )

    candidates = list(out.glob("audio.*"))
    if not candidates:
        raise RuntimeError("Audio download failed")

    src = candidates[0]
    final = out / filename

    if src != final:
        src.replace(final)

    return final

def _get_audio_duration_s(audio_path: str) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nokey=1:noprint_wrappers=1",
        audio_path,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return 0.0
    try:
        return float(p.stdout.strip())
    except Exception:
        return 0.0


def _text_to_segments(text: str, duration_s: float) -> List[Dict]:
    cleaned = clean_transcript_text(text)
    if not cleaned:
        return []
    sentences = _SENT_SPLIT_RE.split(cleaned)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return []
    if duration_s <= 0:
        duration_s = max(1.0, len(sentences) * 2.0)
    per = max(0.5, duration_s / len(sentences))
    segments = []
    start = 0.0
    for s in sentences:
        end = min(duration_s, start + per)
        segments.append({"start_s": start, "end_s": end, "text": s})
        start = end
    if segments:
        segments[-1]["end_s"] = duration_s
    return segments


def transcribe_with_openai(audio_path: str) -> Tuple[List[Dict], int]:
    settings = load_settings()
    if not settings.OpenAI or not settings.OpenAI.apiKey:
        raise RuntimeError("OpenAI apiKey missing")

    client = OpenAI(api_key=settings.OpenAI.apiKey)
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
            response_format="json",
        )

    text = getattr(resp, "text", "") or ""
    usage = getattr(resp, "usage", None)
    token_usage = 0
    if usage and getattr(usage, "total_tokens", None) is not None:
        token_usage = int(usage.total_tokens)
    # Some API responses may not include usage; default to 0 in that case.

    duration_s = _get_audio_duration_s(audio_path)
    segments = _text_to_segments(text, duration_s)
    return segments, token_usage
