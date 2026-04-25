"""
Shared helpers for building v2 UI-facing report models.
"""
from __future__ import annotations

from typing import Optional

from ..common import ROLE_UNKNOWN


def class_color_token(class_name: Optional[str]) -> Optional[str]:
    if not class_name:
        return None
    return class_name.replace(" ", "").lower()


def role_tone(role: Optional[str]) -> str:
    normalized = (role or ROLE_UNKNOWN).strip().lower()
    return normalized if normalized else ROLE_UNKNOWN.lower()


def format_offset_seconds(value_ms: Optional[float]) -> str:
    if value_ms is None:
        return "?"
    try:
        numeric = float(value_ms)
    except (TypeError, ValueError):
        return "?"
    return f"{numeric / 1000.0:.2f}s"


def format_duration(value_ms: Optional[float]) -> Optional[str]:
    if value_ms is None:
        return None
    try:
        numeric = float(value_ms)
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    total_seconds = int(numeric // 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def build_pull_link(report_code: Optional[str], fight_id: Optional[int]) -> Optional[str]:
    if not report_code:
        return None
    try:
        numeric_fight_id = int(fight_id)
    except (TypeError, ValueError):
        return None
    return f"https://www.warcraftlogs.com/reports/{report_code}#fight={numeric_fight_id}"


def merged_reports_label(source_reports: list[str]) -> Optional[str]:
    extra_count = max(len(source_reports) - 1, 0)
    if extra_count <= 0:
        return None
    if extra_count == 1:
        return "Merged 1 additional report"
    return f"Merged {extra_count} additional reports"


__all__ = [
    "build_pull_link",
    "class_color_token",
    "format_duration",
    "format_offset_seconds",
    "merged_reports_label",
    "role_tone",
]
