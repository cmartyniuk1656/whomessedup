"""
Vorasius target-damage summary wrapper.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .boss_manifests import VORASIUS_MANIFEST
from .target_damage import EncounterTargetDamageSummary, fetch_encounter_target_damage_summary

REPORT_DEFAULT_FIGHT = "Vorasius"

VORASIUS_TARGETS = VORASIUS_MANIFEST.target_configs
DEFAULT_TARGET_SLUGS = VORASIUS_MANIFEST.default_target_slugs


def fetch_vorasius_damage_summary(
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
        target_configs=VORASIUS_TARGETS,
        default_target_slugs=DEFAULT_TARGET_SLUGS,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )


__all__ = [
    "DEFAULT_TARGET_SLUGS",
    "REPORT_DEFAULT_FIGHT",
    "VORASIUS_TARGETS",
    "fetch_vorasius_damage_summary",
]
