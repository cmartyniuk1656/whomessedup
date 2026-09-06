"""Heroic Sszorak Tempest contacts and successful dispels."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Set

import requests

from ..api import Fight, fetch_events_grouped, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _fight_roster_from_metadata,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
    compute_death_cutoffs,
    compute_fight_duration_ms,
)

REPORT_DEFAULT_FIGHT = "Sszorak"
TEMPEST_ABILITY_ID = 1287083
TEMPEST_ABILITY_NAME = "Tempest"
CONTACT_EVENT_TYPES = frozenset({"applydebuff", "applydebuffstack", "refreshdebuff"})
DISPEL_ABILITY_NAMES = {
    4987: "Cleanse",
    88423: "Nature's Cure",
    218164: "Detox",
    374251: "Cauterizing Flame",
    383015: "Poison Cleansing",
}


@dataclass
class SszorakTempestEvent:
    source_report_code: Optional[str]
    player: str
    target: str
    event_type: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    stack: Optional[int] = None
    dispel_ability_id: Optional[int] = None
    dispel_ability_name: Optional[str] = None
    credited_from_pet: Optional[str] = None
    pull_duration_ms: Optional[float] = None


@dataclass
class SszorakTempestEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    contacts: int
    dispels: int
    contacts_per_pull: float
    dispels_per_pull: float
    events: List[SszorakTempestEvent] = field(default_factory=list)


@dataclass
class SszorakTempestSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    total_contacts: int
    total_dispels: int
    pet_dispels: int
    entries: List[SszorakTempestEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[SszorakTempestEvent]]
    source_reports: List[str] = field(default_factory=list)


def fetch_sszorak_tempest_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> SszorakTempestSummary:
    primary_code = _sanitize_report_code(report_code)
    normalized_fight_ids = [int(fight_id) for fight_id in fight_ids] if fight_ids else None
    summaries = [
        _fetch_single_summary(
            report_code=primary_code,
            fight_name=fight_name or REPORT_DEFAULT_FIGHT,
            fight_ids=normalized_fight_ids,
            difficulty=difficulty,
            ignore_after_deaths=ignore_after_deaths,
            token=token,
            client_id=client_id,
            client_secret=client_secret,
        )
    ]
    seen = {primary_code}
    for candidate in extra_report_codes or []:
        if not candidate:
            continue
        try:
            code = _sanitize_report_code(candidate)
        except ValueError:
            continue
        if code in seen:
            continue
        seen.add(code)
        summaries.append(
            _fetch_single_summary(
                report_code=code,
                fight_name=fight_name or REPORT_DEFAULT_FIGHT,
                fight_ids=normalized_fight_ids,
                difficulty=difficulty,
                ignore_after_deaths=ignore_after_deaths,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    return summaries[0] if len(summaries) == 1 else _merge_summaries(summaries)


def _fetch_single_summary(
    *,
    report_code: str,
    fight_name: str,
    fight_ids: Optional[List[int]],
    difficulty: Optional[str | int],
    ignore_after_deaths: Optional[int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> SszorakTempestSummary:
    load_env()
    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    chosen_ids = [fight.id for fight in chosen]
    known_players = {
        name for actor_id, name in actor_names.items() if name and actor_classes.get(actor_id)
    }

    details = fetch_player_details(session, bearer, code=report_code, fight_ids=chosen_ids)
    player_roles, player_specs = _infer_player_roles(details)
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    participants_by_fight: Dict[int, Set[str]] = {}
    for fight in chosen:
        roster = _fight_roster_from_metadata(fight, actor_names, actor_classes)
        if roster is None:
            fight_details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
            fight_roles, fight_specs = _infer_player_roles(fight_details)
            participants = {
                player for player in _players_from_details(fight_details) if player in known_players
            }
        else:
            participants, fight_roles, fight_specs = roster
            participants = {player for player in participants if player in known_players}
        for player, role in fight_roles.items():
            if player_roles.get(player) in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
        for player, spec in fight_specs.items():
            if not player_specs.get(player):
                player_specs[player] = spec
        participants_by_fight[fight.id] = participants
        for player in participants:
            pulls_by_player[player] += 1

    death_limit = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    death_cutoffs = compute_death_cutoffs(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        actor_names=actor_names,
        max_deaths=death_limit,
    )
    player_classes = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name in known_players
    }
    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    events_by_player: DefaultDict[str, List[SszorakTempestEvent]] = defaultdict(list)
    debuffs_by_fight = fetch_events_grouped(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        fights=chosen,
        ability_id=TEMPEST_ABILITY_ID,
        actor_names=actor_names,
    )
    dispels_by_fight = fetch_events_grouped(
        session,
        bearer,
        code=report_code,
        data_type="Dispels",
        fights=chosen,
        actor_names=actor_names,
    )
    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else float(fight.end)
        for event in _collect_fight_events(
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            actor_owners=actor_owners,
            known_players=known_players,
            participants=participants_by_fight.get(fight.id, set()),
            pull_index=pull_index_by_fight[fight.id],
            raw_debuffs=debuffs_by_fight.get(fight.id, ()),
            raw_dispels=dispels_by_fight.get(fight.id, ()),
        ):
            events_by_player[event.player].append(event)

    players = set(pulls_by_player) | set(events_by_player)
    entries = _build_entries(
        players=players,
        events_by_player=events_by_player,
        pulls_by_player=pulls_by_player,
        player_roles=player_roles,
        player_classes=player_classes,
    )
    return _build_summary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=fight_ids,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        entries=entries,
        player_classes={player: player_classes.get(player) for player in players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players},
        player_specs={player: player_specs.get(player) for player in players},
        source_reports=[report_code],
    )


def _collect_fight_events(
    *,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
    known_players: Set[str],
    participants: Set[str],
    pull_index: int,
    raw_debuffs: Iterable[dict],
    raw_dispels: Iterable[dict],
) -> List[SszorakTempestEvent]:
    pull_duration_ms = compute_fight_duration_ms(fight)
    filtered_debuffs = (
        event
        for event in raw_debuffs
        if (_event_timestamp(event) is not None and _event_timestamp(event) <= event_end)
    )
    contacts = _collapse_tempest_contacts(filtered_debuffs)
    results: List[SszorakTempestEvent] = []
    for event in contacts:
        player = _target_name(event)
        timestamp = _event_timestamp(event)
        if not _player_in_scope(player, known_players, participants) or timestamp is None:
            continue
        results.append(
            SszorakTempestEvent(
                source_report_code=report_code,
                player=player,
                target=player,
                event_type="contact",
                fight_id=fight.id,
                fight_name=fight.name,
                pull_index=pull_index,
                timestamp=timestamp,
                offset_ms=timestamp - float(fight.start),
                stack=_stack(event),
                pull_duration_ms=pull_duration_ms,
            )
        )

    for event in raw_dispels:
        if str(event.get("type") or "").lower() != "dispel":
            continue
        if _extra_ability_id(event) != TEMPEST_ABILITY_ID:
            continue
        timestamp = _event_timestamp(event)
        if timestamp is not None and timestamp > event_end:
            continue
        target = _target_name(event)
        credited_player, pet_name = _credited_dispeller(event, actor_names, actor_owners)
        if timestamp is None or not _player_in_scope(credited_player, known_players, participants):
            continue
        results.append(
            SszorakTempestEvent(
                source_report_code=report_code,
                player=credited_player,
                target=target or "Unknown",
                event_type="dispel",
                fight_id=fight.id,
                fight_name=fight.name,
                pull_index=pull_index,
                timestamp=timestamp,
                offset_ms=timestamp - float(fight.start),
                dispel_ability_id=_ability_id(event),
                dispel_ability_name=_ability_name(event),
                credited_from_pet=pet_name,
                pull_duration_ms=pull_duration_ms,
            )
        )
    return sorted(results, key=lambda item: (item.timestamp, item.event_type, item.player))


def _collapse_tempest_contacts(events: Iterable[dict]) -> List[dict]:
    """Return one contact for each player/timestamp, preferring stack-bearing events."""
    contacts: Dict[tuple[str, int], dict] = {}
    for event in events:
        if _ability_id(event) != TEMPEST_ABILITY_ID:
            continue
        if str(event.get("type") or "").lower() not in CONTACT_EVENT_TYPES:
            continue
        player = _target_name(event)
        timestamp = _event_timestamp(event)
        if not player or timestamp is None:
            continue
        key = (player, int(round(timestamp)))
        current = contacts.get(key)
        if current is None or (_stack(event) or 0) > (_stack(current) or 0):
            contacts[key] = event
    return sorted(contacts.values(), key=lambda event: (_event_timestamp(event) or 0.0, _target_name(event) or ""))


def _credited_dispeller(
    event: dict,
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
) -> tuple[Optional[str], Optional[str]]:
    source_id = _actor_id(event, "source")
    source_name = _source_name(event)
    owner_id = actor_owners.get(source_id) if source_id is not None else None
    owner_name = actor_names.get(owner_id) if owner_id is not None else None
    if owner_name:
        return owner_name, source_name
    return source_name, None


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[SszorakTempestEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[SszorakTempestEntry]:
    entries: List[SszorakTempestEntry] = []
    for player in players:
        events = sorted(events_by_player.get(player, []), key=lambda item: (item.source_report_code or "", item.timestamp))
        contacts = sum(event.event_type == "contact" for event in events)
        dispels = sum(event.event_type == "dispel" for event in events)
        pulls = pulls_by_player.get(player, 0) or 1
        entries.append(
            SszorakTempestEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                contacts=contacts,
                dispels=dispels,
                contacts_per_pull=contacts / pulls,
                dispels_per_pull=dispels / pulls,
                events=events,
            )
        )
    return sorted(
        entries,
        key=lambda entry: (
            -entry.contacts,
            -entry.dispels,
            ROLE_PRIORITY.get(entry.role, ROLE_PRIORITY[ROLE_UNKNOWN]),
            entry.player.lower(),
        ),
    )


def _merge_summaries(summaries: List[SszorakTempestSummary]) -> SszorakTempestSummary:
    primary = summaries[0]
    classes: Dict[str, Optional[str]] = {}
    roles: Dict[str, str] = {}
    specs: Dict[str, Optional[str]] = {}
    pulls: DefaultDict[str, int] = defaultdict(int)
    events: DefaultDict[str, List[SszorakTempestEvent]] = defaultdict(list)
    source_reports: List[str] = []
    for summary in summaries:
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for player, value in summary.player_classes.items():
            if player not in classes or classes[player] is None:
                classes[player] = value
        for player, value in summary.player_roles.items():
            if roles.get(player) in (None, ROLE_UNKNOWN):
                roles[player] = value or ROLE_UNKNOWN
        for player, value in summary.player_specs.items():
            if player not in specs or specs[player] is None:
                specs[player] = value
        for entry in summary.entries:
            pulls[entry.player] += entry.pulls
            events[entry.player].extend(entry.events)
    players = set(pulls) | set(events)
    entries = _build_entries(
        players=players,
        events_by_player=events,
        pulls_by_player=pulls,
        player_roles=roles,
        player_classes=classes,
    )
    return _build_summary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=sum(summary.pull_count for summary in summaries),
        ignore_after_deaths=primary.ignore_after_deaths,
        entries=entries,
        player_classes=classes,
        player_roles=roles,
        player_specs=specs,
        source_reports=source_reports,
    )


def _build_summary(
    *,
    report_code: str,
    fight_filter: Optional[str],
    fight_ids: Optional[List[int]],
    pull_count: int,
    ignore_after_deaths: Optional[int],
    entries: List[SszorakTempestEntry],
    player_classes: Dict[str, Optional[str]],
    player_roles: Dict[str, str],
    player_specs: Dict[str, Optional[str]],
    source_reports: List[str],
) -> SszorakTempestSummary:
    return SszorakTempestSummary(
        report_code=report_code,
        fight_filter=fight_filter,
        fight_ids=fight_ids,
        pull_count=pull_count,
        ignore_after_deaths=ignore_after_deaths,
        total_contacts=sum(entry.contacts for entry in entries),
        total_dispels=sum(entry.dispels for entry in entries),
        pet_dispels=sum(event.credited_from_pet is not None for entry in entries for event in entry.events),
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        player_events={entry.player: entry.events for entry in entries},
        source_reports=source_reports,
    )


def _player_in_scope(player: Optional[str], known_players: Set[str], participants: Set[str]) -> bool:
    return bool(player and player in known_players and (not participants or player in participants))


def _event_timestamp(event: dict) -> Optional[float]:
    try:
        return float(event.get("timestamp"))
    except (TypeError, ValueError):
        return None


def _ability_id(event: dict) -> Optional[int]:
    raw = event.get("abilityGameID")
    if raw is None and isinstance(event.get("ability"), dict):
        raw = event["ability"].get("id") or event["ability"].get("gameID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _extra_ability_id(event: dict) -> Optional[int]:
    raw = event.get("extraAbilityGameID")
    if raw is None and isinstance(event.get("extraAbility"), dict):
        raw = event["extraAbility"].get("id") or event["extraAbility"].get("gameID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _ability_name(event: dict) -> Optional[str]:
    ability = event.get("ability")
    if isinstance(ability, dict) and ability.get("name"):
        return str(ability["name"])
    # Dispels returned by Warcraft Logs do not always include master-data names.
    return DISPEL_ABILITY_NAMES.get(_ability_id(event))


def _target_name(event: dict) -> Optional[str]:
    value = event.get("targetName")
    if not value and isinstance(event.get("target"), dict):
        value = event["target"].get("name")
    return str(value) if value else None


def _source_name(event: dict) -> Optional[str]:
    value = event.get("sourceName")
    if not value and isinstance(event.get("source"), dict):
        value = event["source"].get("name")
    return str(value) if value else None


def _actor_id(event: dict, prefix: str) -> Optional[int]:
    raw = event.get(f"{prefix}ID")
    nested = event.get(prefix)
    if raw is None and isinstance(nested, dict):
        raw = nested.get("id")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _stack(event: dict) -> Optional[int]:
    try:
        return int(event["stack"]) if event.get("stack") is not None else 1
    except (TypeError, ValueError):
        return None


__all__ = [
    "TEMPEST_ABILITY_ID",
    "TEMPEST_ABILITY_NAME",
    "SszorakTempestEntry",
    "SszorakTempestEvent",
    "SszorakTempestSummary",
    "fetch_sszorak_tempest_summary",
]
