"""
Imperator Averzian target-damage summary wrapper.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from .target_damage import (
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
    ),
    "abyssal_voidshaper": EncounterTargetConfig(
        slug="abyssal_voidshaper",
        label="Abyssal Voidshaper",
        enemy_name="Abyssal Voidshaper",
    ),
    "abyssal_annihilator": EncounterTargetConfig(
        slug="abyssal_annihilator",
        label="Voidbound Annihilator",
        enemy_name="Voidbound Annihilator",
    ),
}
DEFAULT_TARGET_SLUGS = (
    "imperator_averzian",
    "abyssal_voidshaper",
    "abyssal_annihilator",
)


def fetch_imperator_averzian_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    targets: Optional[Iterable[str]] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
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
