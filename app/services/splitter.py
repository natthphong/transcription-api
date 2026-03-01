from typing import List, Dict, Tuple
import math
import re
import subprocess
from pathlib import Path

PUNC_END = re.compile(r"[\.!?]$")

def _is_good_boundary(text: str) -> int:
    """
    score boundary by punctuation strength
    """
    t = text.strip()
    if not t:
        return 0
    if PUNC_END.search(t):
        return 3
    if t.endswith(",") or t.endswith(";") or t.endswith(":"):
        return 2
    return 1

def build_clips_from_segments(
    segments: List[Dict],
    split_seconds: int,
    tolerance_seconds: int = 1,
) -> List[Dict]:
    """
    Make clip windows approximately split_seconds.
    Choose cut points near target using caption boundaries.
    Output: [{start_s, end_s, text}]
    """
    if not segments:
        return []

    full_end = max(s["end_s"] for s in segments)
    targets = []
    t = split_seconds
    while t < full_end:
        targets.append(t)
        t += split_seconds

    # candidate cut points are segment end times
    cut_points = []
    for seg in segments:
        cut_points.append((seg["end_s"], seg["text"]))

    chosen = []
    prev_cut = 0.0

    for target in targets:
        lo = target - tolerance_seconds
        hi = target + tolerance_seconds

        best = None  # (score, absDiff, time)
        for cp_time, cp_text in cut_points:
            if cp_time < lo or cp_time > hi:
                continue
            if cp_time <= prev_cut + 1.0:  # avoid ultra short clips
                continue
            score = _is_good_boundary(cp_text)
            diff = abs(cp_time - target)
            cand = (score, -diff, cp_time)  # higher score, closer time
            if best is None or cand > best:
                best = cand

        if best:
            chosen_time = best[2]
        else:
            # fallback exact target
            chosen_time = target

        chosen.append(chosen_time)
        prev_cut = chosen_time

    # build clip list (start/end), then collect text that overlaps
    clip_ranges: List[Tuple[float, float]] = []
    start = 0.0
    for end in chosen:
        clip_ranges.append((start, end))
        start = end
    clip_ranges.append((start, full_end))

    clips = []
    for idx, (cs, ce) in enumerate(clip_ranges, start=1):
        texts = []
        for seg in segments:
            if seg["end_s"] <= cs:
                continue
            if seg["start_s"] >= ce:
                continue
            texts.append(seg["text"])
        merged = " ".join(texts).strip()
        clips.append({"seq": idx, "start_s": cs, "end_s": ce, "text": merged})

    return clips



def cut_clip_ffmpeg(input_path: str, out_path: str, start_s: float, end_s: float) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    dur = max(0.01, end_s - start_s)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_s}",
        "-i", input_path,
        "-t", f"{dur}",
        "-c", "copy",
        out_path,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {p.stderr}")