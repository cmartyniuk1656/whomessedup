"""
Imperator Averzian target-damage summary wrapper.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from .target_damage import (
    EncounterTargetBucket,
    EncounterTargetConfig,
    EncounterTargetDamageSummary,
    fetch_encounter_target_damage_summary,
)

REPORT_DEFAULT_FIGHT = "Imperator Averzian"

IMPERATOR_AVERZIAN_TARGETS: Dict[str, EncounterTargetConfig] = {
    "imperator_averzian": EncounterTargetConfig(
        slug="imperator_averzian",
        label="Imperator Averzian",
        enemy_name="Imperator Averzian",
        bucket=EncounterTargetBucket.BOSS,
    ),
    "abyssal_voidshaper": EncounterTargetConfig(
        slug="abyssal_voidshaper",
        label="Abyssal Voidshaper",
        enemy_name="Abyssal Voidshaper",
        bucket=EncounterTargetBucket.PRIORITY_ADD,
    ),
    "abyssal_annihilator": EncounterTargetConfig(
        slug="abyssal_annihilator",
        label="Voidbound Annihilator",
        enemy_name="Voidbound Annihilator",
        bucket=EncounterTargetBucket.PAD_ADD,
    ),
    "abyssal_malus": EncounterTargetConfig(
        slug="abyssal_malus",
        label="Abyssal Malus",
        enemy_name="Abyssal Malus",
        bucket=EncounterTargetBucket.PAD_ADD,
    ),
    "voidmaw": EncounterTargetConfig(
        slug="voidmaw",
        label="Voidmaw",
        enemy_name="Voidmaw",
        bucket=EncounterTargetBucket.PAD_ADD,
    ),
}
DEFAULT_TARGET_SLUGS = (
    "imperator_averzian",
    "abyssal_voidshaper",
    "abyssal_annihilator",
    "abyssal_malus",
    "voidmaw",
)


def fetch_imperator_averzian_damage_summary(
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
    return fetch_encounter_target_damage_summary(
        report_code=report_code,
        fight_name=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
        targets=targets,
        extra_report_codes=extra_report_codes,
        kill_only=kill_only,
        omit_dead_players=omit_dead_players,
        target_configs=IMPERATOR_AVERZIAN_TARGETS,
        default_target_slugs=DEFAULT_TARGET_SLUGS,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )


__all__ = [
    "DEFAULT_TARGET_SLUGS",
    "IMPERATOR_AVERZIAN_TARGETS",
    "REPORT_DEFAULT_FIGHT",
    "fetch_imperator_averzian_damage_summary",
]
