"""
Shared avoidable-damage report helpers.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

import requests

from ..api import fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    is_avoidable_ability,
    is_avoidable_for_role,
)
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
    compute_death_cutoffs,
    compute_fight_duration_ms,
)
from .death_reports import resolve_damage_ability, resolve_damage_amount


@dataclass
class AvoidableDamageEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    ability_id: Optional[int]
    ability_label: Optional[str]
    damage_amount: float
    ability_description: Optional[str] = None
    ability_url: Optional[str] = None
    ability_tags: Tuple[str, ...] = ()
    pull_duration_ms: Optional[float] = None


@dataclass
class AvoidableDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float
    events: List[AvoidableDamageEvent]


@dataclass
class AvoidableDamageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    total_damage: float
    avg_damage_per_pull: float
    entries: List[AvoidableDamageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[AvoidableDamageEvent]]
    abilities: List[BossAbilityMetadata]
    source_reports: List[str] = field(default_factory=list)


def fetch_avoidable_damage_summary(
    *,
    report_code: str,
    boss_manifest: BossManifest,
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
    primary_code = _sanitize_report_code(report_code)
    selected_abilities = resolve_avoidable_manifest_abilities(boss_manifest, ability_keys=ability_keys)
    primary_summary = _fetch_single_avoidable_damage_summary(
        report_code=primary_code,
        boss_manifest=boss_manifest,
        selected_abilities=selected_abilities,
        fight_name=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
        ignore_after_deaths=ignore_after_deaths,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )

    extra_codes: List[str] = []
    if extra_report_codes:
        for candidate in extra_report_codes:
            if not candidate:
                continue
            try:
                normalized = _sanitize_report_code(candidate)
            except ValueError:
                continue
            if normalized == primary_code or normalized in extra_codes:
                continue
            extra_codes.append(normalized)

    if not extra_codes:
        return primary_summary

    summaries = [primary_summary]
    for code in extra_codes:
        summaries.append(
            _fetch_single_avoidable_damage_summary(
                report_code=code,
                boss_manifest=boss_manifest,
                selected_abilities=selected_abilities,
                fight_name=fight_name,
                fight_ids=fight_ids,
                difficulty=difficulty,
                ignore_after_deaths=ignore_after_deaths,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    return _merge_avoidable_damage_summaries(summaries)


def resolve_avoidable_manifest_abilities(
    boss_manifest: BossManifest,
    *,
    ability_keys: Optional[Iterable[str]] = None,
) -> List[BossAbilityMetadata]:
    avoidable = [ability for ability in boss_manifest.abilities if is_avoidable_ability(ability)]
    if ability_keys is None:
        return avoidable
    selected = {str(key) for key in ability_keys}
    return [ability for ability in avoidable if ability_manifest_key(ability) in selected]


def ability_manifest_key(ability: BossAbilityMetadata) -> str:
    if ability.game_id is not None:
        return str(int(ability.game_id))
    return _normalize_ability_name(ability.name)


def _fetch_single_avoidable_damage_summary(
    *,
    report_code: str,
    boss_manifest: BossManifest,
    selected_abilities: List[BossAbilityMetadata],
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ignore_after_deaths: Optional[int] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> AvoidableDamageSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)

    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    known_players = {
        name
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    fight_id_list = [fight.id for fight in chosen]

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(aggregated_details)

    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    participants_by_fight: Dict[int, Set[str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = {name for name in _players_from_details(details) if name in known_players}
        participants_by_fight[fight.id] = participants
        for name in participants:
            pulls_by_player[name] += 1

    death_limit = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    death_cutoffs = compute_death_cutoffs(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        actor_names=actor_names,
        max_deaths=death_limit,
    )

    ability_labels = {
        int(ability.game_id): ability.name
        for ability in selected_abilities
        if ability.game_id is not None
    }
    pull_index_by_fight: Dict[int, int] = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    events_by_player: DefaultDict[str, List[AvoidableDamageEvent]] = defaultdict(list)
    damage_totals: DefaultDict[str, float] = defaultdict(float)

    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else fight.end
        pull_duration = compute_fight_duration_ms(fight)
        participants = participants_by_fight.get(fight.id, set())
        fight_roles = roles_by_fight.get(fight.id, player_roles)
        for ability in selected_abilities:
            for event in fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="DamageTaken",
                start=fight.start,
                end=event_end,
                ability_id=ability.game_id,
                ability_name=None if ability.game_id is not None else ability.name,
                actor_names=actor_names,
            ):
                timestamp = event.get("timestamp")
                if timestamp is None:
                    continue
                try:
                    ts_val = float(timestamp)
                except (TypeError, ValueError):
                    continue
                if cutoff is not None and ts_val > cutoff:
                    continue

                target_name = _target_name_from_event(event)
                if not target_name or target_name not in known_players:
                    continue
                if participants and target_name not in participants:
                    continue

                damage_amount = resolve_damage_amount(event)
                if damage_amount is None or damage_amount <= 0:
                    continue

                ability_id, ability_label = resolve_damage_ability(event, ability_labels)
                metadata = boss_manifest.ability_for(
                    ability_id=ability_id,
                    ability_name=ability_label or ability.name,
                ) or ability
                target_role = fight_roles.get(target_name) or player_roles.get(target_name)
                if not is_avoidable_for_role(metadata, target_role):
                    continue
                event_model = AvoidableDamageEvent(
                    source_report_code=report_code,
                    player=target_name,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index_by_fight.get(fight.id, 0),
                    timestamp=ts_val,
                    offset_ms=ts_val - float(fight.start),
                    ability_id=ability_id,
                    ability_label=ability_label or metadata.name,
                    damage_amount=damage_amount,
                    ability_description=metadata.description,
                    ability_url=metadata.url,
                    ability_tags=tuple(metadata.tags),
                    pull_duration_ms=pull_duration,
                )
                events_by_player[target_name].append(event_model)
                damage_totals[target_name] += damage_amount

    player_classes: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name and name in known_players:
            player_classes[name] = actor_classes.get(actor_id)

    all_players = set(pulls_by_player.keys()) | set(events_by_player.keys())
    entries: List[AvoidableDamageEntry] = []
    for player in sorted(
        all_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -damage_totals.get(name, 0.0),
            name.lower(),
        ),
    ):
        pulls = pulls_by_player.get(player, len(chosen))
        if pulls <= 0:
            pulls = len(chosen) or 1
        role = player_roles.get(player) or ROLE_UNKNOWN
        total_damage = float(damage_totals.get(player, 0.0))
        entries.append(
            AvoidableDamageEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=total_damage / pulls if pulls else 0.0,
                events=sorted(events_by_player.get(player, []), key=lambda item: item.timestamp),
            )
        )

    total_damage_amount = sum(entry.total_damage for entry in entries)
    pull_count = len(chosen)

    return AvoidableDamageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=pull_count,
        ignore_after_deaths=death_limit,
        total_damage=total_damage_amount,
        avg_damage_per_pull=total_damage_amount / pull_count if pull_count else 0.0,
        entries=entries,
        player_classes={player: player_classes.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        player_events={player: list(events) for player, events in events_by_player.items()},
        abilities=selected_abilities,
        source_reports=[report_code],
    )


def _merge_avoidable_damage_summaries(summaries: List[AvoidableDamageSummary]) -> AvoidableDamageSummary:
    primary = summaries[0]
    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_damage: DefaultDict[str, float] = defaultdict(float)
    combined_events: DefaultDict[str, List[AvoidableDamageEvent]] = defaultdict(list)
    combined_pull_count = 0
    source_reports: List[str] = []

    for summary in summaries:
        combined_pull_count += summary.pull_count
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for player, class_name in summary.player_classes.items():
            if player not in combined_player_classes or combined_player_classes[player] is None:
                combined_player_classes[player] = class_name
        for player, role in summary.player_roles.items():
            current_role = combined_player_roles.get(player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if player not in combined_player_specs or combined_player_specs[player] is None:
                combined_player_specs[player] = spec
        for entry in summary.entries:
            combined_pulls[entry.player] += entry.pulls
            combined_damage[entry.player] += entry.total_damage
            combined_events[entry.player].extend(entry.events)
            if combined_player_classes.get(entry.player) is None:
                combined_player_classes[entry.player] = entry.class_name
            current_role = combined_player_roles.get(entry.player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[entry.player] = entry.role or ROLE_UNKNOWN

    players = sorted(
        set(combined_pulls.keys()) | set(combined_damage.keys()) | set(combined_events.keys()),
        key=lambda name: (
            ROLE_PRIORITY.get(combined_player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -combined_damage.get(name, 0.0),
            name.lower(),
        ),
    )

    entries: List[AvoidableDamageEntry] = []
    player_events: Dict[str, List[AvoidableDamageEvent]] = {}
    for player in players:
        pulls = combined_pulls.get(player, combined_pull_count)
        if pulls <= 0:
            pulls = combined_pull_count or 1
        events = sorted(combined_events.get(player, []), key=lambda item: (item.source_report_code or "", item.timestamp))
        player_events[player] = events
        total_damage = float(combined_damage.get(player, 0.0))
        entries.append(
            AvoidableDamageEntry(
                player=player,
                role=combined_player_roles.get(player) or ROLE_UNKNOWN,
                class_name=combined_player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=total_damage / pulls if pulls else 0.0,
                events=events,
            )
        )

    total_damage_amount = sum(entry.total_damage for entry in entries)

    return AvoidableDamageSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=combined_pull_count,
        ignore_after_deaths=primary.ignore_after_deaths,
        total_damage=total_damage_amount,
        avg_damage_per_pull=total_damage_amount / combined_pull_count if combined_pull_count else 0.0,
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        player_events=player_events,
        abilities=primary.abilities,
        source_reports=source_reports,
    )


def _target_name_from_event(event: Dict[str, object]) -> Optional[str]:
    target_name = event.get("targetName")
    if not target_name and isinstance(event.get("target"), dict):
        target_name = event["target"].get("name")
    return str(target_name) if target_name else None


def _normalize_ability_name(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


__all__ = [
    "AvoidableDamageEntry",
    "AvoidableDamageEvent",
    "AvoidableDamageSummary",
    "ability_manifest_key",
    "fetch_avoidable_damage_summary",
    "is_avoidable_ability",
    "resolve_avoidable_manifest_abilities",
]
