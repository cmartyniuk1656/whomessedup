"""Heroic and Mythic Entombed Sentinels death summary wrapper."""
from __future__ import annotations

from typing import Iterable, Optional

from .boss_manifest_types import normalize_manifest_difficulty
from .boss_manifests import (
    ENTOMBED_SENTINELS_HEROIC_MANIFEST,
    ENTOMBED_SENTINELS_MYTHIC_MANIFEST,
)
from .death_reports import DeathReportSummary, fetch_death_report_summary

REPORT_DEFAULT_FIGHT = "Entombed Sentinels"


def fetch_entombed_sentinels_death_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ignore_after_deaths: Optional[int] = None,
    ignore_unavoidable_after_healer_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DeathReportSummary:
    manifest = (
        ENTOMBED_SENTINELS_MYTHIC_MANIFEST
        if normalize_manifest_difficulty(difficulty) == "mythic"
        else ENTOMBED_SENTINELS_HEROIC_MANIFEST
    )
    return fetch_death_report_summary(
        report_code=report_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        ignore_after_deaths=ignore_after_deaths,
        ignore_unavoidable_after_healer_deaths=ignore_unavoidable_after_healer_deaths,
        extra_report_codes=extra_report_codes,
        boss_manifest=manifest,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "fetch_entombed_sentinels_death_summary",
]
