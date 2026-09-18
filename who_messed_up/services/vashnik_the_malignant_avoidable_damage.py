"""Heroic and Mythic Vashnik the Malignant avoidable-damage summary wrapper."""
from __future__ import annotations

from typing import Iterable, Optional

from .avoidable_damage import AvoidableDamageSummary, fetch_avoidable_damage_summary
from .boss_manifest_types import normalize_manifest_difficulty
from .boss_manifests import (
    VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST,
    VASHNIK_THE_MALIGNANT_MYTHIC_MANIFEST,
)

REPORT_DEFAULT_FIGHT = "Vashnik the Malignant"


def fetch_vashnik_the_malignant_avoidable_damage_summary(
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
    manifest = (
        VASHNIK_THE_MALIGNANT_MYTHIC_MANIFEST
        if normalize_manifest_difficulty(difficulty) == "mythic"
        else VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST
    )
    return fetch_avoidable_damage_summary(
        report_code=report_code,
        boss_manifest=manifest,
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


__all__ = ["REPORT_DEFAULT_FIGHT", "fetch_vashnik_the_malignant_avoidable_damage_summary"]
