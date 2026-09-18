"""Heroic and Mythic Vashnik the Malignant target-damage summary wrapper."""
from __future__ import annotations

from typing import Iterable, Optional

from .boss_manifest_types import normalize_manifest_difficulty
from .boss_manifests import (
    VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST,
    VASHNIK_THE_MALIGNANT_MYTHIC_MANIFEST,
)
from .target_damage import EncounterTargetDamageSummary, fetch_encounter_target_damage_summary

REPORT_DEFAULT_FIGHT = "Vashnik the Malignant"
VASHNIK_THE_MALIGNANT_TARGETS = VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST.target_configs
DEFAULT_TARGET_SLUGS = VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST.default_target_slugs


def fetch_vashnik_the_malignant_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    targets: Optional[Iterable[str]] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    kill_only: bool = False,
    omit_dead_players: bool = False,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> EncounterTargetDamageSummary:
    manifest = (
        VASHNIK_THE_MALIGNANT_MYTHIC_MANIFEST
        if normalize_manifest_difficulty(difficulty) == "mythic"
        else VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST
    )
    return fetch_encounter_target_damage_summary(
        report_code=report_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        targets=targets,
        extra_report_codes=extra_report_codes,
        kill_only=kill_only,
        omit_dead_players=omit_dead_players,
        target_configs=manifest.target_configs,
        default_target_slugs=manifest.default_target_slugs,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )


__all__ = [
    "DEFAULT_TARGET_SLUGS",
    "REPORT_DEFAULT_FIGHT",
    "VASHNIK_THE_MALIGNANT_TARGETS",
    "fetch_vashnik_the_malignant_damage_summary",
]
