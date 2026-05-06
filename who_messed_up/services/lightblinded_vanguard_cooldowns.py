"""
Lightblinded Vanguard cooldown-usage report entry point.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .cooldown_usage import CooldownUsageSummary, fetch_cooldown_usage_summary


REPORT_DEFAULT_FIGHT = "Lightblinded Vanguard"
LIGHTBLINDED_VANGUARD_ENCOUNTER_ID = 3180
LIGHTBLINDED_VANGUARD_DIFFICULTY = "mythic"


def fetch_lightblinded_vanguard_cooldown_summary(
    *,
    report_code: str,
    reminder_text: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    tolerance_seconds: float = 7.5,
    ignore_after_deaths: Optional[int] = None,
    ignore_after_healer_death: bool = False,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> CooldownUsageSummary:
    return fetch_cooldown_usage_summary(
        report_code=report_code,
        reminder_text=reminder_text,
        expected_encounter_id=LIGHTBLINDED_VANGUARD_ENCOUNTER_ID,
        expected_difficulty=LIGHTBLINDED_VANGUARD_DIFFICULTY,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty or LIGHTBLINDED_VANGUARD_DIFFICULTY,
        extra_report_codes=extra_report_codes,
        tolerance_seconds=tolerance_seconds,
        ignore_after_deaths=ignore_after_deaths,
        ignore_after_healer_death=ignore_after_healer_death,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )


__all__ = [
    "LIGHTBLINDED_VANGUARD_DIFFICULTY",
    "LIGHTBLINDED_VANGUARD_ENCOUNTER_ID",
    "REPORT_DEFAULT_FIGHT",
    "fetch_lightblinded_vanguard_cooldown_summary",
]
