"""Heroic The Coiled Altar avoidable-damage summary wrapper."""
from __future__ import annotations

from typing import Iterable, Optional

from .avoidable_damage import AvoidableDamageSummary, fetch_avoidable_damage_summary
from .boss_manifests import THE_COILED_ALTAR_HEROIC_MANIFEST

REPORT_DEFAULT_FIGHT = "The Coiled Altar"


def fetch_the_coiled_altar_avoidable_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ability_keys: Optional[Iterable[str]] = None,
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> AvoidableDamageSummary:
    return fetch_avoidable_damage_summary(
        report_code=report_code,
        boss_manifest=THE_COILED_ALTAR_HEROIC_MANIFEST,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        ability_keys=ability_keys,
        ignore_after_deaths=ignore_after_deaths,
        extra_report_codes=extra_report_codes,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )


__all__ = ["REPORT_DEFAULT_FIGHT", "fetch_the_coiled_altar_avoidable_damage_summary"]
