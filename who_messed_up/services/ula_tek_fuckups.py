"""Heroic Ula'tek player-owned mechanic failure report.

This report intentionally starts narrow: every logged Caustic Waves damage
event is one scored failure. Additional mechanics can be added here once their
combat-log signals are precise enough to attribute to a player.
"""
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

REPORT_DEFAULT_FIGHT = "Ula'tek"
CAUSTIC_WAVES_ID = 1292403
CAUSTIC_WAVES_LABEL = "Caustic Waves"
WAVE_CONTACT_RESET_MS = 2_500.0


@dataclass
class UlaTekFuckupEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    ability_id: int
    ability_label: str
    tick_count: int
    amount: float
    absorbed: float
    pull_duration_ms: Optional[float] = None


@dataclass
class UlaTekFuckupEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_fuckups: int
    caustic_waves_hits: int
    fuckups_per_pull: float
    events: List[UlaTekFuckupEvent] = field(default_factory=list)


@dataclass
class UlaTekFuckupSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    total_fuckups: int
    caustic_waves_hits: int
    entries: List[UlaTekFuckupEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[UlaTekFuckupEvent]]
    source_reports: List[str] = field(default_factory=list)

    @property
    def fuckups_per_pull(self) -> float:
        return self.total_fuckups / self.pull_count if self.pull_count else 0.0


def fetch_ula_tek_fuckup_summary(
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
) -> UlaTekFuckupSummary:
    primary_code = _sanitize_report_code(report_code)
    normalized_fight_ids = [int(fight_id) for fight_id in fight_ids] if fight_ids else None
    primary = _fetch_single_summary(
        report_code=primary_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=normalized_fight_ids,
        difficulty=difficulty,
        ignore_after_deaths=ignore_after_deaths,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )

    extra_codes: List[str] = []
    for candidate in extra_report_codes or []:
        if not candidate:
            continue
        try:
            normalized = _sanitize_report_code(candidate)
        except ValueError:
            continue
        if normalized != primary_code and normalized not in extra_codes:
            extra_codes.append(normalized)
    if not extra_codes:
        return primary

    summaries = [primary]
    for code in extra_codes:
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
    return _merge_summaries(summaries)


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
) -> UlaTekFuckupSummary:
    load_env()
    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    chosen_ids = [fight.id for fight in chosen]
    known_players = {
        name for actor_id, name in actor_names.items() if name and actor_classes.get(actor_id)
    }

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=chosen_ids)
    player_roles, player_specs = _infer_player_roles(aggregated_details)
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    participants_by_fight: Dict[int, Set[str]] = {}
    for fight in chosen:
        roster = _fight_roster_from_metadata(fight, actor_names, actor_classes)
        if roster is None:
            details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
            fight_roles, _ = _infer_player_roles(details)
            participants = {name for name in _players_from_details(details) if name in known_players}
        else:
            participants, fight_roles, _ = roster
            participants = {name for name in participants if name in known_players}
        for player, role in fight_roles.items():
            if player_roles.get(player) in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
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
    damage_by_fight = fetch_events_grouped(
        session,
        bearer,
        code=report_code,
        data_type="DamageTaken",
        fights=chosen,
        ability_id=CAUSTIC_WAVES_ID,
        actor_names=actor_names,
    )

    player_classes = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name and name in known_players
    }
    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    events_by_player: DefaultDict[str, List[UlaTekFuckupEvent]] = defaultdict(list)
    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else float(fight.end)
        for event in collect_caustic_waves_hits(
            report_code=report_code,
            fight=fight,
            pull_index=pull_index_by_fight[fight.id],
            pull_duration_ms=compute_fight_duration_ms(fight),
            event_end=event_end,
            known_players=known_players,
            participants=participants_by_fight.get(fight.id, set()),
            raw_events=damage_by_fight.get(fight.id, ()),
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
    total = sum(entry.total_fuckups for entry in entries)
    return UlaTekFuckupSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=list(fight_ids) if fight_ids else None,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        total_fuckups=total,
        caustic_waves_hits=total,
        entries=entries,
        player_classes={player: player_classes.get(player) for player in players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players},
        player_specs={player: player_specs.get(player) for player in players},
        player_events={entry.player: entry.events for entry in entries},
        source_reports=[report_code],
    )


def collect_caustic_waves_hits(
    *,
    report_code: str,
    fight: Fight,
    pull_index: int,
    pull_duration_ms: Optional[float],
    event_end: float,
    known_players: Set[str],
    participants: Set[str],
    raw_events: Iterable[dict],
) -> List[UlaTekFuckupEvent]:
    """Return one scored failure for each distinct Caustic Waves contact."""
    counted: List[UlaTekFuckupEvent] = []
    events_by_player: DefaultDict[str, List[dict]] = defaultdict(list)
    for event in sorted(raw_events, key=lambda item: _event_timestamp(item) or 0.0):
        if _ability_id(event) != CAUSTIC_WAVES_ID:
            continue
        player = _target_player_name(event)
        if not _is_player_in_scope(player, known_players, participants):
            continue
        timestamp = _event_timestamp(event)
        if timestamp is None or timestamp > event_end:
            continue
        events_by_player[player].append(event)

    for player, player_events in events_by_player.items():
        for sequence in _group_event_sequences(player_events, WAVE_CONTACT_RESET_MS):
            timestamp = _event_timestamp(sequence[0])
            if timestamp is None:
                continue
            amount = sum(_numeric_event_value(event, "amount") for event in sequence)
            absorbed = sum(_numeric_event_value(event, "absorbed") for event in sequence)
            counted.append(
                UlaTekFuckupEvent(
                    source_report_code=report_code,
                    player=player,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index,
                    timestamp=timestamp,
                    offset_ms=timestamp - float(fight.start),
                    ability_id=CAUSTIC_WAVES_ID,
                    ability_label=CAUSTIC_WAVES_LABEL,
                    tick_count=len(sequence),
                    amount=amount,
                    absorbed=absorbed,
                    pull_duration_ms=pull_duration_ms,
                )
            )
    return sorted(counted, key=lambda event: event.timestamp)


def _group_event_sequences(events: Iterable[dict], maximum_gap_ms: float) -> List[List[dict]]:
    groups: List[List[dict]] = []
    for event in sorted(events, key=lambda item: _event_timestamp(item) or 0.0):
        timestamp = _event_timestamp(event)
        if timestamp is None:
            continue
        previous = _event_timestamp(groups[-1][-1]) if groups else None
        if previous is None or timestamp - previous > maximum_gap_ms:
            groups.append([event])
        else:
            groups[-1].append(event)
    return groups


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[UlaTekFuckupEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[UlaTekFuckupEntry]:
    entries: List[UlaTekFuckupEntry] = []
    for player in sorted(
        players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -len(events_by_player.get(name, [])),
            name.lower(),
        ),
    ):
        events = sorted(
            events_by_player.get(player, []),
            key=lambda event: (event.source_report_code or "", event.timestamp),
        )
        pulls = pulls_by_player.get(player, 0) or 1
        total = len(events)
        entries.append(
            UlaTekFuckupEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_fuckups=total,
                caustic_waves_hits=total,
                fuckups_per_pull=total / pulls if pulls else 0.0,
                events=events,
            )
        )
    return entries


def _merge_summaries(summaries: List[UlaTekFuckupSummary]) -> UlaTekFuckupSummary:
    primary = summaries[0]
    combined_classes: Dict[str, Optional[str]] = {}
    combined_roles: Dict[str, str] = {}
    combined_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[UlaTekFuckupEvent]] = defaultdict(list)
    source_reports: List[str] = []

    for summary in summaries:
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for player, class_name in summary.player_classes.items():
            if combined_classes.get(player) is None:
                combined_classes[player] = class_name
        for player, role in summary.player_roles.items():
            if combined_roles.get(player) in (None, ROLE_UNKNOWN):
                combined_roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if combined_specs.get(player) is None:
                combined_specs[player] = spec
        for entry in summary.entries:
            combined_pulls[entry.player] += entry.pulls
            combined_events[entry.player].extend(entry.events)

    players = set(combined_pulls) | set(combined_events)
    entries = _build_entries(
        players=players,
        events_by_player=combined_events,
        pulls_by_player=combined_pulls,
        player_roles=combined_roles,
        player_classes=combined_classes,
    )
    total = sum(entry.total_fuckups for entry in entries)
    return UlaTekFuckupSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=sum(summary.pull_count for summary in summaries),
        ignore_after_deaths=primary.ignore_after_deaths,
        total_fuckups=total,
        caustic_waves_hits=total,
        entries=entries,
        player_classes=combined_classes,
        player_roles=combined_roles,
        player_specs=combined_specs,
        player_events={entry.player: entry.events for entry in entries},
        source_reports=source_reports,
    )


def _target_player_name(event: dict) -> Optional[str]:
    target_name = event.get("targetName")
    if target_name:
        return str(target_name)
    target = event.get("target")
    if isinstance(target, dict) and target.get("name"):
        return str(target["name"])
    return None


def _is_player_in_scope(player: Optional[str], known_players: Set[str], participants: Set[str]) -> bool:
    return bool(player and player in known_players and (not participants or player in participants))


def _event_timestamp(event: dict) -> Optional[float]:
    raw = event.get("timestamp")
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _ability_id(event: dict) -> Optional[int]:
    raw = event.get("abilityGameID")
    if raw in (None, "") and isinstance(event.get("ability"), dict):
        raw = event["ability"].get("gameID") or event["ability"].get("id")
    try:
        return int(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _numeric_event_value(event: dict, key: str) -> float:
    try:
        return float(event.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "CAUSTIC_WAVES_ID",
    "CAUSTIC_WAVES_LABEL",
    "REPORT_DEFAULT_FIGHT",
    "UlaTekFuckupEntry",
    "UlaTekFuckupEvent",
    "UlaTekFuckupSummary",
    "WAVE_CONTACT_RESET_MS",
    "collect_caustic_waves_hits",
    "fetch_ula_tek_fuckup_summary",
]
