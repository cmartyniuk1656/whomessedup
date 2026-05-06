"""
Lightblinded Vanguard Avenger's Shield dispel summaries.

This report intentionally tracks debuff applications separately from dispel
events: application groups determine the set denominator, while Dispels events
attribute successful removals to the player who actually dispelled them.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

import requests

from ..api import fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
    compute_fight_duration_ms,
)


REPORT_DEFAULT_FIGHT = "Lightblinded Vanguard"
AVENGERS_SHIELD_DEBUFF_ID = 1246502
AVENGERS_SHIELD_SET_SIZE = 4
APPLICATION_SET_WINDOW_MS = 250.0
REVIVAL_ABILITY_ID = 115310


@dataclass(frozen=True)
class DispelCastAbility:
    game_id: int
    name: str


DISPEL_CAST_ABILITIES: Tuple[DispelCastAbility, ...] = (
    DispelCastAbility(88423, "Nature's Cure"),
    DispelCastAbility(115450, "Detox"),
    DispelCastAbility(77130, "Purify Spirit"),
    DispelCastAbility(4987, "Cleanse"),
    DispelCastAbility(360823, "Naturalize"),
)
DISPEL_CAST_ABILITY_IDS = {ability.game_id for ability in DISPEL_CAST_ABILITIES}
DISPEL_CAST_ABILITY_NAMES_BY_ID = {ability.game_id: ability.name for ability in DISPEL_CAST_ABILITIES}


@dataclass
class LightblindedVanguardDispelEvent:
    source_report_code: Optional[str]
    player: str
    target: Optional[str]
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    ability_id: Optional[int]
    ability_label: Optional[str]
    pull_duration_ms: Optional[float] = None
    is_revival: bool = False
    is_multi_dispel: bool = False
    is_non_set: bool = False


@dataclass
class LightblindedVanguardDispelEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    sets: int
    dispel_casts: int
    successful_dispels: int
    set_dispels: int
    average_dispels_per_set: float
    filtered_dispels: int
    events: List[LightblindedVanguardDispelEvent] = field(default_factory=list)
    cast_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class LightblindedVanguardDispelSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    total_sets: int
    excluded_application_groups: int
    excluded_application_count: int
    total_dispel_casts: int
    successful_dispels: int
    set_successful_dispels: int
    filtered_dispels: int
    revival_dispels: int
    multi_dispels: int
    non_set_dispels: int
    avg_dispels_per_set: float
    entries: List[LightblindedVanguardDispelEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[LightblindedVanguardDispelEvent]]
    source_reports: List[str] = field(default_factory=list)
    exclude_revival_dispels: bool = True
    exclude_dead_player_sets: bool = False


def fetch_lightblinded_vanguard_dispel_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    exclude_revival_dispels: bool = True,
    exclude_dead_player_sets: bool = False,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> LightblindedVanguardDispelSummary:
    primary_code = _sanitize_report_code(report_code)
    primary_summary = _fetch_single_lightblinded_vanguard_dispel_summary(
        report_code=primary_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        exclude_revival_dispels=exclude_revival_dispels,
        exclude_dead_player_sets=exclude_dead_player_sets,
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
            _fetch_single_lightblinded_vanguard_dispel_summary(
                report_code=code,
                fight_name=fight_name or REPORT_DEFAULT_FIGHT,
                fight_ids=fight_ids,
                difficulty=difficulty,
                exclude_revival_dispels=exclude_revival_dispels,
                exclude_dead_player_sets=exclude_dead_player_sets,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    return _merge_lightblinded_vanguard_dispel_summaries(summaries)


def _fetch_single_lightblinded_vanguard_dispel_summary(
    *,
    report_code: str,
    fight_name: Optional[str],
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    exclude_revival_dispels: bool,
    exclude_dead_player_sets: bool,
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> LightblindedVanguardDispelSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    fight_id_list = [fight.id for fight in chosen]
    known_players = {
        name
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    participants_by_fight: Dict[int, Set[str]] = {}
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    eligible_players: Set[str] = set()
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = {
            name for name in set(_players_from_details(details)) if name and name in known_players
        }
        participants_by_fight[fight.id] = participants
        for player in participants:
            eligible_players.add(player)
            pulls_by_player[player] += 1

    player_classes: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name and name in known_players:
            player_classes[name] = actor_classes.get(actor_id)

    player_roles: Dict[str, str] = {
        player: role for player, role in player_roles_global.items() if player in known_players
    }
    player_specs: Dict[str, Optional[str]] = {
        player: spec for player, spec in player_specs_global.items() if player in known_players
    }
    for fight_roles in roles_by_fight.values():
        for player, role in fight_roles.items():
            if player not in player_roles or player_roles[player] in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
            player_specs.setdefault(player, player_specs_global.get(player))

    death_timestamps_by_fight = (
        _collect_death_timestamps_by_fight(
            session,
            bearer,
            report_code=report_code,
            fights=chosen,
            actor_names=actor_names,
            known_players=known_players,
        )
        if exclude_dead_player_sets
        else {}
    )

    set_counts_by_player: DefaultDict[str, int] = defaultdict(int)
    total_sets = 0
    excluded_application_groups = 0
    excluded_application_count = 0
    applications_by_fight_target: Dict[int, Dict[str, List[Tuple[float, bool]]]] = {}

    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    pull_duration_by_fight = {fight.id: compute_fight_duration_ms(fight) for fight in chosen}

    for fight in chosen:
        apply_events = _collect_avengers_shield_applications(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            known_players=known_players,
        )
        target_applications: DefaultDict[str, List[Tuple[float, bool]]] = defaultdict(list)
        for group in _group_events_by_timestamp(apply_events, window_ms=APPLICATION_SET_WINDOW_MS):
            group_timestamp = _event_timestamp(group[0])
            is_counted_set = len(group) == AVENGERS_SHIELD_SET_SIZE
            for event in group:
                target_name = _target_name_from_event(event)
                if target_name:
                    target_applications[target_name].append((group_timestamp, is_counted_set))
            if not is_counted_set:
                excluded_application_groups += 1
                excluded_application_count += len(group)
                continue
            total_sets += 1
            for player in participants_by_fight.get(fight.id, set()):
                if exclude_dead_player_sets and _player_was_dead_before(
                    death_timestamps_by_fight.get(fight.id, {}).get(player, []),
                    group_timestamp,
                ):
                    continue
                set_counts_by_player[player] += 1
        applications_by_fight_target[fight.id] = {
            target: sorted(values, key=lambda item: item[0]) for target, values in target_applications.items()
        }

    dispel_cast_counts: DefaultDict[str, int] = defaultdict(int)
    cast_breakdowns: Dict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
    for fight in chosen:
        for ability in DISPEL_CAST_ABILITIES:
            seen_casts: Set[Tuple[object, ...]] = set()
            for event in fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="Casts",
                start=fight.start,
                end=fight.end,
                limit=5000,
                ability_id=ability.game_id,
                actor_names=actor_names,
            ):
                if (event.get("type") or "").lower() != "cast":
                    continue
                source_name = _source_name_from_event(event)
                if not source_name or source_name not in known_players:
                    continue
                key = _event_identity(event)
                if key in seen_casts:
                    continue
                seen_casts.add(key)
                dispel_cast_counts[source_name] += 1
                cast_breakdowns[source_name][ability.name] += 1

    successful_dispels: DefaultDict[str, int] = defaultdict(int)
    set_successful_dispels: DefaultDict[str, int] = defaultdict(int)
    filtered_dispels: DefaultDict[str, int] = defaultdict(int)
    events_by_player: DefaultDict[str, List[LightblindedVanguardDispelEvent]] = defaultdict(list)
    total_revival_dispels = 0
    total_multi_dispels = 0
    total_non_set_dispels = 0

    for fight in chosen:
        raw_dispels = _collect_avengers_shield_dispels(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            known_players=known_players,
        )
        multi_dispel_keys = _multi_dispel_keys(raw_dispels)
        for event in raw_dispels:
            source_name = _source_name_from_event(event)
            if not source_name:
                continue
            ability_id = _ability_id_from_event(event)
            timestamp = _event_timestamp(event)
            is_revival = ability_id == REVIVAL_ABILITY_ID
            is_multi = _dispel_group_key(event) in multi_dispel_keys
            if is_revival:
                total_revival_dispels += 1
            if is_multi:
                total_multi_dispels += 1

            target_name = _target_name_from_event(event)
            is_non_set_dispel = not _matches_counted_application(
                applications_by_fight_target.get(fight.id, {}).get(target_name or "", []),
                timestamp,
            )
            if exclude_revival_dispels and (is_revival or is_multi):
                filtered_dispels[source_name] += 1
                continue

            successful_dispels[source_name] += 1
            if is_non_set_dispel:
                total_non_set_dispels += 1
            else:
                set_successful_dispels[source_name] += 1
            events_by_player[source_name].append(
                LightblindedVanguardDispelEvent(
                    source_report_code=report_code,
                    player=source_name,
                    target=target_name,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index_by_fight.get(fight.id, 0),
                    timestamp=timestamp,
                    offset_ms=timestamp - float(fight.start),
                    ability_id=ability_id,
                    ability_label=_ability_label(ability_id),
                    pull_duration_ms=pull_duration_by_fight.get(fight.id),
                    is_revival=is_revival,
                    is_multi_dispel=is_multi,
                    is_non_set=is_non_set_dispel,
                )
            )

    all_players = (
        eligible_players
        | set(dispel_cast_counts.keys())
        | set(successful_dispels.keys())
        | set(set_successful_dispels.keys())
        | set(filtered_dispels.keys())
    )
    if not all_players:
        all_players = set(player_roles.keys())

    entries: List[LightblindedVanguardDispelEntry] = []
    for player in sorted(
        all_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -successful_dispels.get(name, 0),
            -dispel_cast_counts.get(name, 0),
            name.lower(),
        ),
    ):
        pulls = pulls_by_player.get(player, len(chosen))
        if pulls <= 0:
            pulls = len(chosen) or 1
        sets = set_counts_by_player.get(player, 0)
        dispels = successful_dispels.get(player, 0)
        set_dispels = set_successful_dispels.get(player, 0)
        role = player_roles.get(player) or ROLE_UNKNOWN
        if role != "Healer" and dispels <= 0:
            continue
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, player_specs_global.get(player))
        entries.append(
            LightblindedVanguardDispelEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                sets=sets,
                dispel_casts=dispel_cast_counts.get(player, 0),
                successful_dispels=dispels,
                set_dispels=set_dispels,
                average_dispels_per_set=set_dispels / sets if sets else 0.0,
                filtered_dispels=filtered_dispels.get(player, 0),
                events=sorted(events_by_player.get(player, []), key=lambda item: item.timestamp),
                cast_breakdown=dict(cast_breakdowns.get(player, {})),
            )
        )

    total_successful_dispels = sum(successful_dispels.values())
    total_set_successful_dispels = sum(set_successful_dispels.values())
    total_dispel_casts = sum(dispel_cast_counts.values())
    total_filtered_dispels = sum(filtered_dispels.values())

    return LightblindedVanguardDispelSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=len(chosen),
        total_sets=total_sets,
        excluded_application_groups=excluded_application_groups,
        excluded_application_count=excluded_application_count,
        total_dispel_casts=total_dispel_casts,
        successful_dispels=total_successful_dispels,
        set_successful_dispels=total_set_successful_dispels,
        filtered_dispels=total_filtered_dispels,
        revival_dispels=total_revival_dispels,
        multi_dispels=total_multi_dispels,
        non_set_dispels=total_non_set_dispels,
        avg_dispels_per_set=total_set_successful_dispels / total_sets if total_sets else 0.0,
        entries=entries,
        player_classes={player: player_classes.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        player_events={player: list(events) for player, events in events_by_player.items()},
        source_reports=[report_code],
        exclude_revival_dispels=exclude_revival_dispels,
        exclude_dead_player_sets=exclude_dead_player_sets,
    )


def _merge_lightblinded_vanguard_dispel_summaries(
    summaries: List[LightblindedVanguardDispelSummary],
) -> LightblindedVanguardDispelSummary:
    primary = summaries[0]
    combined_classes: Dict[str, Optional[str]] = {}
    combined_roles: Dict[str, str] = {}
    combined_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_sets: DefaultDict[str, int] = defaultdict(int)
    combined_casts: DefaultDict[str, int] = defaultdict(int)
    combined_successful_dispels: DefaultDict[str, int] = defaultdict(int)
    combined_set_successful_dispels: DefaultDict[str, int] = defaultdict(int)
    combined_filtered_dispels: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[LightblindedVanguardDispelEvent]] = defaultdict(list)
    combined_breakdowns: Dict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
    source_reports: List[str] = []

    pull_count = 0
    total_sets = 0
    excluded_application_groups = 0
    excluded_application_count = 0
    revival_dispels = 0
    multi_dispels = 0
    non_set_dispels = 0

    for summary in summaries:
        pull_count += summary.pull_count
        total_sets += summary.total_sets
        excluded_application_groups += summary.excluded_application_groups
        excluded_application_count += summary.excluded_application_count
        revival_dispels += summary.revival_dispels
        multi_dispels += summary.multi_dispels
        non_set_dispels += summary.non_set_dispels
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for player, class_name in summary.player_classes.items():
            if player not in combined_classes or combined_classes[player] is None:
                combined_classes[player] = class_name
        for player, role in summary.player_roles.items():
            current_role = combined_roles.get(player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if player not in combined_specs or combined_specs[player] is None:
                combined_specs[player] = spec
        for entry in summary.entries:
            combined_pulls[entry.player] += entry.pulls
            combined_sets[entry.player] += entry.sets
            combined_casts[entry.player] += entry.dispel_casts
            combined_successful_dispels[entry.player] += entry.successful_dispels
            combined_set_successful_dispels[entry.player] += entry.set_dispels
            combined_filtered_dispels[entry.player] += entry.filtered_dispels
            combined_events[entry.player].extend(entry.events)
            for ability_name, total in entry.cast_breakdown.items():
                combined_breakdowns[entry.player][ability_name] += total
            if combined_classes.get(entry.player) is None:
                combined_classes[entry.player] = entry.class_name
            current_role = combined_roles.get(entry.player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_roles[entry.player] = entry.role or ROLE_UNKNOWN

    players = sorted(
        set(combined_pulls.keys())
        | set(combined_casts.keys())
        | set(combined_successful_dispels.keys())
        | set(combined_set_successful_dispels.keys())
        | set(combined_filtered_dispels.keys()),
        key=lambda name: (
            ROLE_PRIORITY.get(combined_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -combined_successful_dispels.get(name, 0),
            -combined_casts.get(name, 0),
            name.lower(),
        ),
    )

    entries: List[LightblindedVanguardDispelEntry] = []
    player_events: Dict[str, List[LightblindedVanguardDispelEvent]] = {}
    for player in players:
        events = sorted(
            combined_events.get(player, []),
            key=lambda item: (item.source_report_code or "", item.pull_index, item.fight_id, item.timestamp),
        )
        player_events[player] = events
        sets = combined_sets.get(player, 0)
        dispels = combined_successful_dispels.get(player, 0)
        set_dispels = combined_set_successful_dispels.get(player, 0)
        role = combined_roles.get(player) or ROLE_UNKNOWN
        if role != "Healer" and dispels <= 0:
            continue
        entries.append(
            LightblindedVanguardDispelEntry(
                player=player,
                role=role,
                class_name=combined_classes.get(player),
                pulls=combined_pulls.get(player, pull_count),
                sets=sets,
                dispel_casts=combined_casts.get(player, 0),
                successful_dispels=dispels,
                set_dispels=set_dispels,
                average_dispels_per_set=set_dispels / sets if sets else 0.0,
                filtered_dispels=combined_filtered_dispels.get(player, 0),
                events=events,
                cast_breakdown=dict(combined_breakdowns.get(player, {})),
            )
        )

    total_successful_dispels = sum(combined_successful_dispels.values())
    total_set_successful_dispels = sum(combined_set_successful_dispels.values())
    total_dispel_casts = sum(combined_casts.values())
    total_filtered_dispels = sum(combined_filtered_dispels.values())

    return LightblindedVanguardDispelSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=pull_count,
        total_sets=total_sets,
        excluded_application_groups=excluded_application_groups,
        excluded_application_count=excluded_application_count,
        total_dispel_casts=total_dispel_casts,
        successful_dispels=total_successful_dispels,
        set_successful_dispels=total_set_successful_dispels,
        filtered_dispels=total_filtered_dispels,
        revival_dispels=revival_dispels,
        multi_dispels=multi_dispels,
        non_set_dispels=non_set_dispels,
        avg_dispels_per_set=total_set_successful_dispels / total_sets if total_sets else 0.0,
        entries=entries,
        player_classes=combined_classes,
        player_roles=combined_roles,
        player_specs=combined_specs,
        player_events=player_events,
        source_reports=source_reports,
        exclude_revival_dispels=primary.exclude_revival_dispels,
        exclude_dead_player_sets=primary.exclude_dead_player_sets,
    )


def _collect_avengers_shield_applications(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    known_players: Set[str],
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        start=fight.start,
        end=fight.end,
        limit=5000,
        ability_id=AVENGERS_SHIELD_DEBUFF_ID,
        actor_names=actor_names,
    ):
        if (event.get("type") or "").lower() != "applydebuff":
            continue
        target_name = _target_name_from_event(event)
        if not target_name or target_name not in known_players:
            continue
        events.append(event)
    return sorted(events, key=_event_timestamp)


def _collect_avengers_shield_dispels(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    known_players: Set[str],
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Dispels",
        start=fight.start,
        end=fight.end,
        limit=5000,
        actor_names=actor_names,
    ):
        if (event.get("type") or "").lower() != "dispel":
            continue
        if _extra_ability_id_from_event(event) != AVENGERS_SHIELD_DEBUFF_ID:
            continue
        source_name = _source_name_from_event(event)
        if not source_name or source_name not in known_players:
            continue
        events.append(event)
    return sorted(events, key=_event_timestamp)


def _collect_death_timestamps_by_fight(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[object],
    actor_names: Dict[int, str],
    known_players: Set[str],
) -> Dict[int, Dict[str, List[float]]]:
    deaths_by_fight: Dict[int, Dict[str, List[float]]] = {}
    for fight in fights:
        player_deaths: DefaultDict[str, List[float]] = defaultdict(list)
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Deaths",
            start=fight.start,
            end=fight.end,
            limit=1000,
            actor_names=actor_names,
        ):
            if (event.get("type") or "").lower() not in {"death", "instakill"}:
                continue
            target_name = _target_name_from_event(event)
            if not target_name or target_name not in known_players:
                continue
            player_deaths[target_name].append(_event_timestamp(event))
        deaths_by_fight[fight.id] = {player: sorted(values) for player, values in player_deaths.items()}
    return deaths_by_fight


def _group_events_by_timestamp(
    events: List[Dict[str, object]],
    *,
    window_ms: float,
) -> List[List[Dict[str, object]]]:
    groups: List[List[Dict[str, object]]] = []
    for event in sorted(events, key=_event_timestamp):
        timestamp = _event_timestamp(event)
        if not groups:
            groups.append([event])
            continue
        current_group = groups[-1]
        group_start = _event_timestamp(current_group[0])
        if timestamp - group_start <= window_ms:
            current_group.append(event)
        else:
            groups.append([event])
    return groups


def _multi_dispel_keys(events: List[Dict[str, object]]) -> Set[Tuple[object, ...]]:
    grouped: DefaultDict[Tuple[object, ...], int] = defaultdict(int)
    for event in events:
        grouped[_dispel_group_key(event)] += 1
    return {key for key, count in grouped.items() if count > 1}


def _dispel_group_key(event: Dict[str, object]) -> Tuple[object, ...]:
    return (
        event.get("fight"),
        event.get("sourceID"),
        int(round(_event_timestamp(event))),
    )


def _event_identity(event: Dict[str, object]) -> Tuple[object, ...]:
    return (
        event.get("fight"),
        event.get("sourceID"),
        event.get("targetID"),
        _ability_id_from_event(event),
        int(round(_event_timestamp(event))),
    )


def _player_was_dead_before(death_timestamps: List[float], timestamp: float) -> bool:
    return any(death_timestamp <= timestamp for death_timestamp in death_timestamps)


def _matches_counted_application(applications: List[Tuple[float, bool]], dispel_timestamp: float) -> bool:
    matched: Optional[bool] = None
    for application_timestamp, is_counted_set in applications:
        if application_timestamp <= dispel_timestamp:
            matched = is_counted_set
        else:
            break
    return bool(matched)


def _event_timestamp(event: Dict[str, object]) -> float:
    try:
        return float(event.get("timestamp") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ability_id_from_event(event: Dict[str, object]) -> Optional[int]:
    return _normalize_int(event.get("abilityGameID"))


def _extra_ability_id_from_event(event: Dict[str, object]) -> Optional[int]:
    extra_id = _normalize_int(event.get("extraAbilityGameID"))
    if extra_id is not None:
        return extra_id
    extra_ability = event.get("extraAbility")
    if isinstance(extra_ability, dict):
        return _normalize_int(extra_ability.get("id") or extra_ability.get("gameID"))
    return None


def _normalize_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _source_name_from_event(event: Dict[str, object]) -> Optional[str]:
    source_name = event.get("sourceName")
    if not source_name and isinstance(event.get("source"), dict):
        source_name = event["source"].get("name")
    return str(source_name) if source_name else None


def _target_name_from_event(event: Dict[str, object]) -> Optional[str]:
    target_name = event.get("targetName")
    if not target_name and isinstance(event.get("target"), dict):
        target_name = event["target"].get("name")
    return str(target_name) if target_name else None


def _ability_label(ability_id: Optional[int]) -> Optional[str]:
    if ability_id is None:
        return None
    if ability_id == REVIVAL_ABILITY_ID:
        return "Revival"
    return DISPEL_CAST_ABILITY_NAMES_BY_ID.get(ability_id, f"Spell {ability_id}")


__all__ = [
    "AVENGERS_SHIELD_DEBUFF_ID",
    "DISPEL_CAST_ABILITIES",
    "LightblindedVanguardDispelEntry",
    "LightblindedVanguardDispelEvent",
    "LightblindedVanguardDispelSummary",
    "REPORT_DEFAULT_FIGHT",
    "fetch_lightblinded_vanguard_dispel_summary",
]
