"""
Event-level filters for ability metadata that cannot be represented by spell ID alone.
"""
from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, Mapping, Optional, Tuple

import requests

from ..api import Fight, fetch_events_grouped
from .boss_manifest_types import BossAbilityMetadata

AvoidableExclusionEvents = Dict[str, Dict[str, List[float]]]
AvoidableRequirementWindows = Dict[str, Dict[str, List[Tuple[float, float]]]]
AvoidableActiveExclusionWindows = AvoidableRequirementWindows
AvoidableExclusionEventsByFight = Dict[int, AvoidableExclusionEvents]
AvoidableRequirementWindowsByFight = Dict[int, AvoidableRequirementWindows]


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
    return collect_avoidable_exclusion_events_by_fight(
        session,
        bearer,
        report_code=report_code,
        fights=[fight],
        actor_names=actor_names,
        abilities=abilities,
        event_ends={fight.id: event_end} if event_end is not None else None,
    ).get(fight.id, {})


def collect_avoidable_exclusion_events_by_fight(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[Fight],
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    event_ends: Optional[Mapping[int, float]] = None,
) -> AvoidableExclusionEventsByFight:
    selected_fights = list(fights)
    configured = [
        ability
        for ability in abilities
        if ability.game_id is not None and ability.avoidable_exclusion_debuff_ability_id is not None
    ]
    if not configured:
        return {fight.id: {} for fight in selected_fights}

    by_debuff_id: DefaultDict[int, List[BossAbilityMetadata]] = defaultdict(list)
    for ability in configured:
        assert ability.avoidable_exclusion_debuff_ability_id is not None
        by_debuff_id[int(ability.avoidable_exclusion_debuff_ability_id)].append(ability)

    events_by_fight = fetch_events_grouped(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        fights=selected_fights,
        extra_filter=_ability_id_filter(by_debuff_id),
        actor_names=actor_names,
    )
    result: AvoidableExclusionEventsByFight = {}
    for fight in selected_fights:
        exclusions: Dict[str, DefaultDict[str, List[float]]] = {
            _ability_key(ability): defaultdict(list)
            for ability in configured
        }
        end_time = float(event_ends.get(fight.id, fight.end)) if event_ends else float(fight.end)
        for event in events_by_fight.get(fight.id, ()):
            timestamp = _event_timestamp(event)
            if timestamp is None or timestamp > end_time:
                continue
            abilities_for_debuff = by_debuff_id.get(_event_ability_id(event) or -1, ())
            if not abilities_for_debuff:
                continue
            event_type = str(event.get("type") or "").lower()
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
        result[fight.id] = {
            ability_key: dict(targets) for ability_key, targets in exclusions.items()
        }
    return result


def is_avoidable_event_excluded(
    ability: Optional[BossAbilityMetadata],
    event: Dict[str, object],
    target_name: Optional[str],
    exclusions: AvoidableExclusionEvents,
    active_exclusions: Optional[AvoidableActiveExclusionWindows] = None,
) -> bool:
    if not ability or not target_name or ability.game_id is None:
        return False
    window_ms = float(ability.avoidable_exclusion_debuff_window_ms or 0)
    if window_ms < 0:
        return False
    timestamp = _event_timestamp(event)
    if timestamp is None:
        return False
    ability_key = _ability_key(ability)
    target_exclusions = exclusions.get(ability_key, {}).get(target_name, ())
    if any(abs(timestamp - excluded_timestamp) <= window_ms for excluded_timestamp in target_exclusions):
        return True
    if ability.avoidable_excludes_active_debuff_ability_id is None:
        return False
    windows = (active_exclusions or {}).get(ability_key, {}).get(target_name, ())
    return any(start <= timestamp <= end for start, end in windows)


def collect_avoidable_active_exclusion_windows(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    event_end: Optional[float] = None,
) -> AvoidableActiveExclusionWindows:
    return collect_avoidable_active_exclusion_windows_by_fight(
        session,
        bearer,
        report_code=report_code,
        fights=[fight],
        actor_names=actor_names,
        abilities=abilities,
        event_ends={fight.id: event_end} if event_end is not None else None,
    ).get(fight.id, {})


def collect_avoidable_active_exclusion_windows_by_fight(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[Fight],
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    event_ends: Optional[Mapping[int, float]] = None,
) -> AvoidableRequirementWindowsByFight:
    return _collect_active_debuff_windows_by_fight(
        session,
        bearer,
        report_code=report_code,
        fights=fights,
        actor_names=actor_names,
        abilities=abilities,
        ability_id_attribute="avoidable_excludes_active_debuff_ability_id",
        event_ends=event_ends,
    )


def collect_avoidable_requirement_windows(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    event_end: Optional[float] = None,
) -> AvoidableRequirementWindows:
    return collect_avoidable_requirement_windows_by_fight(
        session,
        bearer,
        report_code=report_code,
        fights=[fight],
        actor_names=actor_names,
        abilities=abilities,
        event_ends={fight.id: event_end} if event_end is not None else None,
    ).get(fight.id, {})


def collect_avoidable_requirement_windows_by_fight(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[Fight],
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    event_ends: Optional[Mapping[int, float]] = None,
) -> AvoidableRequirementWindowsByFight:
    return _collect_active_debuff_windows_by_fight(
        session,
        bearer,
        report_code=report_code,
        fights=fights,
        actor_names=actor_names,
        abilities=abilities,
        ability_id_attribute="avoidable_requires_active_debuff_ability_id",
        event_ends=event_ends,
    )


def _collect_active_debuff_windows_by_fight(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[Fight],
    actor_names: Dict[int, str],
    abilities: Iterable[BossAbilityMetadata],
    ability_id_attribute: str,
    event_ends: Optional[Mapping[int, float]] = None,
) -> AvoidableRequirementWindowsByFight:
    selected_fights = list(fights)
    configured = [
        ability
        for ability in abilities
        if ability.game_id is not None and getattr(ability, ability_id_attribute) is not None
    ]
    if not configured:
        return {fight.id: {} for fight in selected_fights}

    by_debuff_id: DefaultDict[int, List[BossAbilityMetadata]] = defaultdict(list)
    for ability in configured:
        debuff_id = getattr(ability, ability_id_attribute)
        assert debuff_id is not None
        by_debuff_id[int(debuff_id)].append(ability)

    events_by_fight = fetch_events_grouped(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        fights=selected_fights,
        extra_filter=_ability_id_filter(by_debuff_id),
        actor_names=actor_names,
    )
    results: AvoidableRequirementWindowsByFight = {}
    for fight in selected_fights:
        result: Dict[str, DefaultDict[str, List[Tuple[float, float]]]] = {
            _ability_key(ability): defaultdict(list)
            for ability in configured
        }
        end_time = float(event_ends.get(fight.id, fight.end)) if event_ends else float(fight.end)
        events_by_debuff: DefaultDict[int, List[Dict[str, object]]] = defaultdict(list)
        for event in events_by_fight.get(fight.id, ()):
            timestamp = _event_timestamp(event)
            debuff_id = _event_ability_id(event)
            if timestamp is not None and timestamp <= end_time and debuff_id in by_debuff_id:
                events_by_debuff[debuff_id].append(event)
        for debuff_id, abilities_for_debuff in by_debuff_id.items():
            active_since: Dict[str, float] = {}
            for event in sorted(
                events_by_debuff.get(debuff_id, ()),
                key=lambda item: float(item.get("timestamp") or 0),
            ):
                event_type = str(event.get("type") or "").strip().lower()
                timestamp = _event_timestamp(event)
                target_name = _target_name_from_event(event)
                if timestamp is None or not target_name:
                    continue

                if event_type in {"applydebuff", "applydebuffstack"}:
                    active_since.setdefault(target_name, timestamp)
                    continue

                if event_type in {"refreshdebuff", "refreshdebuffstack"}:
                    start = active_since.get(target_name)
                    if start is not None:
                        for ability in abilities_for_debuff:
                            result[_ability_key(ability)][target_name].append((start, timestamp))
                    active_since[target_name] = timestamp
                    continue

                if event_type in {"removedebuff", "removedebuffstack"}:
                    start = active_since.pop(target_name, None)
                    if start is None:
                        continue
                    for ability in abilities_for_debuff:
                        result[_ability_key(ability)][target_name].append((start, timestamp))

            for target_name, start in active_since.items():
                for ability in abilities_for_debuff:
                    result[_ability_key(ability)][target_name].append((start, end_time))

        results[fight.id] = {
            ability_key: dict(targets)
            for ability_key, targets in result.items()
        }
    return results


def is_avoidable_event_requirement_met(
    ability: Optional[BossAbilityMetadata],
    event: Dict[str, object],
    target_name: Optional[str],
    requirements: AvoidableRequirementWindows,
) -> bool:
    if not ability or ability.avoidable_requires_active_debuff_ability_id is None:
        return True
    if not target_name or ability.game_id is None:
        return False
    timestamp = _event_timestamp(event)
    if timestamp is None:
        return False
    minimum_age_ms = max(float(ability.avoidable_requires_active_debuff_min_age_ms or 0), 0.0)
    windows = requirements.get(_ability_key(ability), {}).get(target_name, ())
    return any(
        start + minimum_age_ms < timestamp <= end
        for start, end in windows
    )


def _ability_key(ability: BossAbilityMetadata) -> str:
    return str(int(ability.game_id)) if ability.game_id is not None else ability.name.strip().lower()


def _ability_id_filter(abilities_by_id: Mapping[int, object]) -> str:
    return " or ".join(
        f"(ability.id = {ability_id} or abilityGameID = {ability_id})"
        for ability_id in sorted(abilities_by_id)
    )


def _event_ability_id(event: Dict[str, object]) -> Optional[int]:
    candidate = event.get("abilityGameID")
    if candidate is None and isinstance(event.get("ability"), dict):
        candidate = event["ability"].get("guid") or event["ability"].get("id")
    try:
        return int(candidate) if candidate is not None else None
    except (TypeError, ValueError):
        return None


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
    "AvoidableActiveExclusionWindows",
    "AvoidableExclusionEvents",
    "AvoidableRequirementWindows",
    "collect_avoidable_active_exclusion_windows",
    "collect_avoidable_active_exclusion_windows_by_fight",
    "collect_avoidable_exclusion_events",
    "collect_avoidable_exclusion_events_by_fight",
    "collect_avoidable_requirement_windows",
    "collect_avoidable_requirement_windows_by_fight",
    "is_avoidable_event_excluded",
    "is_avoidable_event_requirement_met",
]
