"""
Event-level filters for ability metadata that cannot be represented by spell ID alone.
"""
from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, Optional

import requests

from ..api import fetch_events
from .boss_manifest_types import BossAbilityMetadata

AvoidableExclusionEvents = Dict[str, Dict[str, List[float]]]


def collect_avoidable_exclusion_events(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    event_end: Optional[float] = None,
) -> AvoidableExclusionEvents:
    configured = [
        ability
        for ability in abilities
        if ability.game_id is not None and ability.avoidable_exclusion_debuff_ability_id is not None
    ]
    if not configured:
        return {}

    by_debuff_id: DefaultDict[int, List[BossAbilityMetadata]] = defaultdict(list)
    for ability in configured:
        assert ability.avoidable_exclusion_debuff_ability_id is not None
        by_debuff_id[int(ability.avoidable_exclusion_debuff_ability_id)].append(ability)

    exclusions: Dict[str, DefaultDict[str, List[float]]] = {
        _ability_key(ability): defaultdict(list)
        for ability in configured
    }
    end_time = event_end if event_end is not None else fight.end
    for debuff_id, abilities_for_debuff in by_debuff_id.items():
        allowed_types = {
            event_type.strip().lower()
            for ability in abilities_for_debuff
            for event_type in ability.avoidable_exclusion_debuff_event_types
            if event_type
        }
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=end_time,
            ability_id=debuff_id,
            actor_names=actor_names,
        ):
            event_type = str(event.get("type") or "").lower()
            if allowed_types and event_type not in allowed_types:
                continue
            timestamp = _event_timestamp(event)
            target_name = _target_name_from_event(event)
            if timestamp is None or not target_name:
                continue
            for ability in abilities_for_debuff:
                ability_allowed_types = {
                    candidate.strip().lower()
                    for candidate in ability.avoidable_exclusion_debuff_event_types
                    if candidate
                }
                if ability_allowed_types and event_type not in ability_allowed_types:
                    continue
                exclusions[_ability_key(ability)][target_name].append(timestamp)

    return {ability_key: dict(targets) for ability_key, targets in exclusions.items()}


def is_avoidable_event_excluded(
    ability: Optional[BossAbilityMetadata],
    event: Dict[str, object],
    target_name: Optional[str],
    exclusions: AvoidableExclusionEvents,
) -> bool:
    if not ability or not target_name or ability.game_id is None:
        return False
    window_ms = float(ability.avoidable_exclusion_debuff_window_ms or 0)
    if window_ms < 0:
        return False
    timestamp = _event_timestamp(event)
    if timestamp is None:
        return False
    target_exclusions = exclusions.get(_ability_key(ability), {}).get(target_name, ())
    return any(abs(timestamp - excluded_timestamp) <= window_ms for excluded_timestamp in target_exclusions)


def _ability_key(ability: BossAbilityMetadata) -> str:
    return str(int(ability.game_id)) if ability.game_id is not None else ability.name.strip().lower()


def _event_timestamp(event: Dict[str, object]) -> Optional[float]:
    timestamp = event.get("timestamp")
    if timestamp is None:
        return None
    try:
        return float(timestamp)
    except (TypeError, ValueError):
        return None


def _target_name_from_event(event: Dict[str, object]) -> Optional[str]:
    target_name = event.get("targetName")
    if not target_name and isinstance(event.get("target"), dict):
        target_name = event["target"].get("name")
    return str(target_name) if target_name else None


__all__ = [
    "AvoidableExclusionEvents",
    "collect_avoidable_exclusion_events",
    "is_avoidable_event_excluded",
]
