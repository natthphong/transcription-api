import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

VTT_TIME_RE = re.compile(r"(\d+):(\d+):(\d+\.\d+)\s+-->\s+(\d+):(\d+):(\d+\.\d+)")

def _run(cmd: List[str], cwd: Optional[str] = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDERR:\n{p.stderr}")
    return p.stdout

def list_subs(youtube_url: str) -> str:
    return _run(["yt-dlp", "--list-subs", youtube_url])

def download_video(youtube_url: str, out_dir: str, filename: str = "video.mp4") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    template = str(out / "video.%(ext)s")
    _run([
        "yt-dlp",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", template,
        youtube_url,
    ], cwd=out_dir)
    candidates = list(out.glob("video.*"))
    if not candidates:
        raise RuntimeError("Video download failed: no output file")
    # Prefer mp4 if available
    mp4 = next((p for p in candidates if p.suffix.lower() == ".mp4"), None)
    src = mp4 or candidates[0]
    final_path = out / filename
    if src != final_path:
        src.replace(final_path)
    return final_path

def download_vtt(youtube_url: str, out_dir: str, lang: str = "en") -> Tuple[Path, bool]:
    """
    Returns (vtt_path, is_auto_caption)
    Prefer manual subs first, fallback to auto subs.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1) Try manual subtitles
    try:
        _run([
            "yt-dlp",
            "--skip-download",
            "--write-subs",
            "--sub-langs", lang,
            "--sub-format", "vtt",
            "-o", str(out / "%(id)s.%(ext)s"),
            youtube_url,
        ], cwd=out_dir)
        # find vtt
        vtts = list(out.glob("*.vtt"))
        if vtts:
            return vtts[0], False
    except Exception:
        pass

    # 2) Fallback auto subtitles
    _run([
        "yt-dlp",
        "--skip-download",
        "--write-auto-subs",
        "--sub-langs", lang,
        "--sub-format", "vtt",
        "-o", str(out / "%(id)s.%(ext)s"),
        youtube_url,
    ], cwd=out_dir)

    vtts = list(out.glob("*.vtt"))
    if not vtts:
        raise RuntimeError("No VTT subtitle found (manual/auto).")
    return vtts[0], True

def vtt_to_segments(vtt_path: str) -> List[Dict]:
    """
    Parses .vtt into segments:
    [{start_s, end_s, text}, ...]
    """
    text = Path(vtt_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    segments: List[Dict] = []
    i = 0
    while i < len(text):
        line = text[i].strip()
        m = VTT_TIME_RE.search(line)
        if not m:
            i += 1
            continue

        sh, sm, ss, eh, em, es = m.groups()
        start_s = int(sh) * 3600 + int(sm) * 60 + float(ss)
        end_s = int(eh) * 3600 + int(em) * 60 + float(es)

        # next lines until blank -> caption text
        i += 1
        caption_lines = []
        while i < len(text) and text[i].strip() != "":
            caption_lines.append(text[i].strip())
            i += 1

        caption = " ".join(caption_lines).strip()
        if caption:
            segments.append({"start_s": start_s, "end_s": end_s, "text": caption})
        i += 1

    return segments
