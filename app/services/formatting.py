from __future__ import annotations

from datetime import datetime, timezone


def format_duration_label(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def humanize_relative(target: datetime | None, now: datetime | None = None) -> str:
    if target is None:
        return "Recently"
    now = now or datetime.now(timezone.utc)
    delta = now - target
    seconds = max(0, int(delta.total_seconds()))
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    if minutes < 1:
        return "Now"
    if minutes < 60:
        return f"{minutes}m ago"
    if hours < 24:
        return f"{hours}h ago"
    if days == 1:
        return "Yesterday"
    return f"{days}d ago"


def due_label(due_at: datetime | None, status_id: str, now: datetime | None = None) -> str:
    if status_id == "mastered":
        return "Completed"
    if due_at is None:
        return "Today"
    now = now or datetime.now(timezone.utc)
    diff_days = (due_at.date() - now.date()).days
    if diff_days <= 0:
        return "Today"
    if diff_days == 1:
        return "Tomorrow"
    return f"{diff_days}d"
