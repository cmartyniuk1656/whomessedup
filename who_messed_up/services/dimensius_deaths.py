"""
Dimensius death summary helpers.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple, Set

import requests

from ..env import load_env
from ..api import Fight, fetch_events, fetch_fights, fetch_player_details, REPORT_OVERVIEW_QUERY, gql
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _select_fights,
    compute_death_cutoffs,
)

OBLIVION_ID = 1249077
AIRBORNE_ID = 1243609
FISTS_OF_VOIDLORD_ID = 1227665
DEVOUR_ID = 1243373
RECENT_WINDOW_MS = 8000.0

ABILITY_LABELS: Dict[int, str] = {
    OBLIVION_ID: "Oblivion",
    AIRBORNE_ID: "Airborne",
    FISTS_OF_VOIDLORD_ID: "Fists of the Voidlord",
    DEVOUR_ID: "Devour",
}


@dataclass
class DimensiusDeathEvent:
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    ability_id: Optional[int]
    ability_label: Optional[str]


@dataclass
class DimensiusDeathEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    deaths: int
    death_rate: float
    events: List[DimensiusDeathEvent]


@dataclass
class DimensiusDeathSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    total_deaths: int
    entries: List[DimensiusDeathEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[DimensiusDeathEvent]]
    ability_labels: Dict[int, str]


def fetch_dimensius_death_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    ignore_after_deaths: Optional[int] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DimensiusDeathSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)

    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)
    fight_id_list = [fight.id for fight in chosen]

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(aggregated_details)

    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    participants_by_fight: Dict[int, List[str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = _players_from_details(details)
        participants_by_fight[fight.id] = participants
        for name in set(participants):
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

    pull_index_by_fight: Dict[int, int] = {fight.id: idx + 1 for idx, fight in enumerate(chosen)}
    airborne_events = _collect_target_event_times(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        data_type="Debuffs",
        ability_id=AIRBORNE_ID,
        actor_names=actor_names,
        allowed_types={"applydebuff", "applydebuffstack", "refreshdebuff"},
        death_cutoffs=death_cutoffs,
    )
    fists_events = _collect_target_event_times(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        data_type="DamageTaken",
        ability_id=FISTS_OF_VOIDLORD_ID,
        actor_names=actor_names,
        death_cutoffs=death_cutoffs,
    )
    devour_events = _collect_target_event_times(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        data_type="DamageTaken",
        ability_id=DEVOUR_ID,
        actor_names=actor_names,
        death_cutoffs=death_cutoffs,
    )

    events_by_player: DefaultDict[str, List[DimensiusDeathEvent]] = defaultdict(list)
    death_counts: DefaultDict[str, int] = defaultdict(int)
    ability_labels = _fetch_ability_labels(session, bearer, report_code)

    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id) if death_cutoffs else None
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Deaths",
            start=fight.start,
            end=fight.end,
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
            target_name = event.get("targetName")
            if not target_name and isinstance(event.get("target"), dict):
                target_name = event["target"].get("name")
            if not target_name:
                continue
            ability_id = event.get("killingAbilityGameID") or event.get("abilityGameID")
            ability_label = ability_labels.get(ability_id)
            if ability_label is None:
                ability_obj = event.get("ability") or {}
                ability_label = ability_obj.get("name")
                if ability_label and isinstance(ability_id, int):
                    ability_labels[ability_id] = ability_label
            include_death = True
            if ability_id == OBLIVION_ID:
                include_death = _has_recent_event(airborne_events, fight.id, target_name, ts_val) or _has_recent_event(
                    fists_events, fight.id, target_name, ts_val
                ) or _has_recent_event(devour_events, fight.id, target_name, ts_val)
            if not include_death:
                continue
            death_counts[target_name] += 1
            offset_ms = ts_val - float(fight.start)
            events_by_player[target_name].append(
                DimensiusDeathEvent(
                    player=target_name,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index_by_fight.get(fight.id, 0),
                    timestamp=ts_val,
                    offset_ms=offset_ms,
                    ability_id=int(ability_id) if ability_id is not None else None,
                    ability_label=ability_label,
                )
            )

    pull_count = len(chosen)
    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    all_players = set(pulls_by_player.keys()) | set(events_by_player.keys())
    if not all_players and participants_by_fight:
        for participants in participants_by_fight.values():
            all_players.update(participants)

    entries: List[DimensiusDeathEntry] = []
    total_deaths = 0

    for player in sorted(
        all_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -death_counts.get(name, 0),
            name.lower(),
        ),
    ):
        pulls = pulls_by_player.get(player, pull_count)
        if pulls <= 0:
            pulls = pull_count or 1
        deaths = death_counts.get(player, 0)
        total_deaths += deaths
        death_rate = deaths / pulls if pulls else 0.0
        entries.append(
            DimensiusDeathEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=name_to_class.get(player),
                pulls=pulls,
                deaths=deaths,
                death_rate=death_rate,
                events=sorted(events_by_player.get(player, []), key=lambda evt: evt.timestamp),
            )
        )

    return DimensiusDeathSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=pull_count,
        ignore_after_deaths=death_limit,
        total_deaths=total_deaths,
        entries=entries,
        player_classes={player: name_to_class.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        player_events={player: list(events) for player, events in events_by_player.items()},
        ability_labels=ability_labels,
    )


def _collect_target_event_times(
    session: requests.Session,
    bearer: str,
    *,
    fights: Iterable[Fight],
    report_code: str,
    data_type: str,
    ability_id: int,
    actor_names: Dict[int, str],
    allowed_types: Optional[Set[str]] = None,
    death_cutoffs: Optional[Dict[int, float]] = None,
) -> Dict[int, Dict[str, List[float]]]:
    events_by_fight: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for fight in fights:
        cutoff = death_cutoffs.get(fight.id) if death_cutoffs else None
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type=data_type,
            start=fight.start,
            end=fight.end,
            ability_id=ability_id,
            actor_names=actor_names,
        ):
            if allowed_types:
                event_type = (event.get("type") or "").lower()
                if event_type not in allowed_types:
                    continue
            timestamp = event.get("timestamp")
            if timestamp is None:
                continue
            try:
                ts_val = float(timestamp)
            except (TypeError, ValueError):
                continue
            if cutoff is not None and ts_val >= cutoff:
                continue
            target_name = event.get("targetName")
            if not target_name and isinstance(event.get("target"), dict):
                target_name = event["target"].get("name")
            if not target_name:
                continue
            events_by_fight[fight.id][target_name].append(ts_val)
    for fight_map in events_by_fight.values():
        for timestamps in fight_map.values():
            timestamps.sort()
    return events_by_fight


def _has_recent_event(
    events_by_fight: Dict[int, Dict[str, List[float]]],
    fight_id: int,
    player: str,
    timestamp: float,
    window_ms: float = RECENT_WINDOW_MS,
) -> bool:
    fight_events = events_by_fight.get(fight_id)
    if not fight_events:
        return False
    timestamps = fight_events.get(player)
    if not timestamps:
        return False
    cutoff = timestamp - window_ms
    idx = bisect_left(timestamps, cutoff)
    return idx < len(timestamps) and timestamps[idx] <= timestamp


def _fetch_ability_labels(session, bearer: str, report_code: str) -> Dict[int, str]:
    labels = dict(ABILITY_LABELS)
    try:
        data = gql(session, bearer, REPORT_OVERVIEW_QUERY, {"code": report_code})
        abilities = data["reportData"]["report"].get("masterData", {}).get("abilities", []) or []
        for ability in abilities:
            game_id = ability.get("gameID")
            name = ability.get("name")
            if game_id is None or not name:
                continue
            try:
                labels[int(game_id)] = name
            except (TypeError, ValueError):
                continue
    except Exception:
        pass
    return labels


__all__ = [
    "DimensiusDeathEntry",
    "DimensiusDeathEvent",
    "DimensiusDeathSummary",
    "fetch_dimensius_death_summary",
]
