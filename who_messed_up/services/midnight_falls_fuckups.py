"""
Midnight Falls fuck-up event report.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Set

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
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

REPORT_DEFAULT_FIGHT = "Midnight Falls"

HEAVENS_GLAIVES_ID = 1254076
HEAVENS_GLAIVES_LABEL = "Heaven's Glaives"
TEARS_OF_LURA_ID = 1254257
DARK_PULSAR_DAMAGE_ID = 1282469
DARK_PULSAR_CAST_ID = 1282470
DARK_PULSAR_LABEL = "Dark Pulsar"
DEFAULT_DEDUPE_WINDOW_MS = 2000.0
DARK_PULSAR_SET_RESET_MS = 50000.0
DARK_PULSAR_OPENING_WINDOW_MS = 2000.0
DARK_PULSAR_TEARS_EXCLUSION_WINDOW_MS = 3000.0


@dataclass
class MidnightFallsFuckupEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    mechanic_type: str
    mechanic_label: str
    ability_id: int
    ability_label: str
    deduped_tick_count: int
    set_index: Optional[int] = None
    set_start_offset_ms: Optional[float] = None
    excluded_by_tears: bool = False
    pull_duration_ms: Optional[float] = None


@dataclass
class MidnightFallsFuckupEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_fuckups: int
    heavens_glaives_hits: int
    dark_pulsar_hits: int
    fuckups_per_pull: float
    events: List[MidnightFallsFuckupEvent] = field(default_factory=list)


@dataclass
class MidnightFallsFuckupSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    dedupe_window_ms: float
    total_fuckups: int
    heavens_glaives_hits: int
    dark_pulsar_hits: int
    entries: List[MidnightFallsFuckupEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[MidnightFallsFuckupEvent]]
    source_reports: List[str] = field(default_factory=list)

    @property
    def fuckups_per_pull(self) -> float:
        if not self.pull_count:
            return 0.0
        return self.total_fuckups / self.pull_count


def fetch_midnight_falls_fuckup_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    dedupe_window_ms: Optional[float] = None,
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> MidnightFallsFuckupSummary:
    primary_code = _sanitize_report_code(report_code)
    resolved_window = _normalize_dedupe_window(dedupe_window_ms)
    primary_summary = _fetch_single_midnight_falls_fuckup_summary(
        report_code=primary_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        dedupe_window_ms=resolved_window,
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
            _fetch_single_midnight_falls_fuckup_summary(
                report_code=code,
                fight_name=fight_name or REPORT_DEFAULT_FIGHT,
                fight_ids=fight_ids,
                difficulty=difficulty,
                dedupe_window_ms=resolved_window,
                ignore_after_deaths=ignore_after_deaths,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    return _merge_midnight_falls_fuckup_summaries(summaries)


def _fetch_single_midnight_falls_fuckup_summary(
    *,
    report_code: str,
    fight_name: Optional[str],
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    dedupe_window_ms: float,
    ignore_after_deaths: Optional[int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> MidnightFallsFuckupSummary:
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
    player_roles, player_specs = _infer_player_roles(aggregated_details)

    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    participants_by_fight: Dict[int, Set[str]] = {}
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = {name for name in _players_from_details(details) if name in known_players}
        participants_by_fight[fight.id] = participants
        for name in participants:
            pulls_by_player[name] += 1
    for fight_roles in roles_by_fight.values():
        for player, role in fight_roles.items():
            if player not in player_roles or player_roles[player] in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN

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
        if name and name in known_players
    }
    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    events_by_player: DefaultDict[str, List[MidnightFallsFuckupEvent]] = defaultdict(list)

    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else float(fight.end)
        participants = participants_by_fight.get(fight.id, set())
        pull_duration_ms = compute_fight_duration_ms(fight)
        positive_hits_by_player: DefaultDict[str, List[dict]] = defaultdict(list)
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="DamageTaken",
            start=fight.start,
            end=event_end,
            limit=5000,
            ability_id=HEAVENS_GLAIVES_ID,
            actor_names=actor_names,
        ):
            player = _target_player_name(event)
            if not _is_player_in_scope(player, known_players, participants):
                continue
            timestamp = _event_timestamp(event)
            if timestamp is None:
                continue
            if _actual_damage_amount(event) <= 0:
                continue
            positive_hits_by_player[player].append(event)

        for player, player_hits in positive_hits_by_player.items():
            clustered_events = _cluster_heavens_glaives_hits(
                report_code=report_code,
                player=player,
                fight=fight,
                pull_index=pull_index_by_fight.get(fight.id, 0),
                pull_duration_ms=pull_duration_ms,
                events=player_hits,
                dedupe_window_ms=dedupe_window_ms,
            )
            events_by_player[player].extend(clustered_events)

        for event_model in _collect_dark_pulsar_hits(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
            participants=participants,
            pull_index=pull_index_by_fight.get(fight.id, 0),
            pull_duration_ms=pull_duration_ms,
        ):
            events_by_player[event_model.player].append(event_model)

    players = set(pulls_by_player.keys()) | set(events_by_player.keys())
    entries = _build_entries(
        players=players,
        events_by_player=events_by_player,
        pulls_by_player=pulls_by_player,
        player_roles=player_roles,
        player_classes=player_classes,
    )
    totals = _summarize_totals(entries)

    return MidnightFallsFuckupSummary(
        report_code=report_code,
        fight_filter=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        dedupe_window_ms=dedupe_window_ms,
        total_fuckups=totals["total"],
        heavens_glaives_hits=totals["heavens_glaives"],
        dark_pulsar_hits=totals["dark_pulsar"],
        entries=entries,
        player_classes={player: player_classes.get(player) for player in players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players},
        player_specs={player: player_specs.get(player) for player in players},
        player_events={entry.player: entry.events for entry in entries},
        source_reports=[report_code],
    )


def _cluster_heavens_glaives_hits(
    *,
    report_code: str,
    player: str,
    fight: Fight,
    pull_index: int,
    pull_duration_ms: Optional[float],
    events: List[dict],
    dedupe_window_ms: float,
) -> List[MidnightFallsFuckupEvent]:
    sorted_events = sorted(events, key=lambda event: _event_timestamp(event) or 0.0)
    clustered: List[MidnightFallsFuckupEvent] = []
    current_window_start: Optional[float] = None
    current_window_end: Optional[float] = None
    current_tick_count = 0

    for event in sorted_events:
        timestamp = _event_timestamp(event)
        if timestamp is None:
            continue
        if current_window_start is None or current_window_end is None or timestamp >= current_window_end:
            if current_window_start is not None:
                clustered.append(
                    _build_heavens_glaives_event(
                        source_report_code=report_code,
                        player=player,
                        fight=fight,
                        pull_index=pull_index,
                        timestamp=current_window_start,
                        tick_count=current_tick_count,
                        pull_duration_ms=pull_duration_ms,
                    )
                )
            current_window_start = timestamp
            current_window_end = timestamp + dedupe_window_ms
            current_tick_count = 1
        else:
            current_tick_count += 1

    if current_window_start is not None:
        clustered.append(
            _build_heavens_glaives_event(
                source_report_code=report_code,
                player=player,
                fight=fight,
                pull_index=pull_index,
                timestamp=current_window_start,
                tick_count=current_tick_count,
                pull_duration_ms=pull_duration_ms,
            )
        )
    return clustered


def _collect_dark_pulsar_hits(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
    pull_index: int,
    pull_duration_ms: Optional[float],
) -> List[MidnightFallsFuckupEvent]:
    casts = [
        event
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="All",
            start=fight.start,
            end=event_end,
            limit=5000,
            ability_id=DARK_PULSAR_CAST_ID,
            actor_names=actor_names,
        )
        if str(event.get("type") or "").lower() == "cast" and _event_timestamp(event) is not None
    ]
    damage_events = [
        event
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="DamageTaken",
            start=fight.start,
            end=event_end,
            limit=5000,
            ability_id=DARK_PULSAR_DAMAGE_ID,
            actor_names=actor_names,
        )
        if _event_timestamp(event) is not None and _actual_damage_amount(event) > 0
    ]
    if not casts and not damage_events:
        return []

    tears_by_player = _collect_tears_timestamps_by_player(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        event_end=event_end,
        actor_names=actor_names,
        known_players=known_players,
        participants=participants,
    )
    set_starts = _dark_pulsar_set_starts(casts or damage_events)
    if not set_starts:
        return []

    counted: List[MidnightFallsFuckupEvent] = []
    for set_index, set_start in enumerate(set_starts, start=1):
        set_end = set_start + DARK_PULSAR_SET_RESET_MS
        next_set_start = set_starts[set_index] if set_index < len(set_starts) else None
        if next_set_start is not None:
            set_end = min(set_end, next_set_start)
        opening_end = set_start + DARK_PULSAR_OPENING_WINDOW_MS
        first_hit_by_player: Dict[str, dict] = {}
        for event in sorted(damage_events, key=lambda item: _event_timestamp(item) or 0.0):
            timestamp = _event_timestamp(event)
            if timestamp is None or timestamp < set_start or timestamp >= set_end:
                continue
            player = _target_player_name(event)
            if not _is_player_in_scope(player, known_players, participants):
                continue
            if timestamp > opening_end:
                continue
            if _has_nearby_tears(
                tears_by_player.get(player, []),
                timestamp,
                DARK_PULSAR_TEARS_EXCLUSION_WINDOW_MS,
            ):
                continue
            first_hit_by_player.setdefault(player, event)

        for player, event in sorted(first_hit_by_player.items(), key=lambda item: _event_timestamp(item[1]) or 0.0):
            timestamp = _event_timestamp(event)
            if timestamp is None:
                continue
            counted.append(
                _build_dark_pulsar_event(
                    source_report_code=report_code,
                    player=player,
                    fight=fight,
                    pull_index=pull_index,
                    timestamp=timestamp,
                    set_index=set_index,
                    set_start=set_start,
                    pull_duration_ms=pull_duration_ms,
                )
            )
    return counted


def _collect_tears_timestamps_by_player(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
) -> Dict[str, List[float]]:
    timestamps_by_player: DefaultDict[str, List[float]] = defaultdict(list)
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="DamageTaken",
        start=fight.start,
        end=event_end,
        limit=5000,
        ability_id=TEARS_OF_LURA_ID,
        actor_names=actor_names,
    ):
        player = _target_player_name(event)
        if not _is_player_in_scope(player, known_players, participants):
            continue
        timestamp = _event_timestamp(event)
        if timestamp is not None:
            timestamps_by_player[player].append(timestamp)
    return timestamps_by_player


def _dark_pulsar_set_starts(events: List[dict]) -> List[float]:
    starts: List[float] = []
    for event in sorted(events, key=lambda item: _event_timestamp(item) or 0.0):
        timestamp = _event_timestamp(event)
        if timestamp is None:
            continue
        if not starts or timestamp - starts[-1] >= DARK_PULSAR_SET_RESET_MS:
            starts.append(timestamp)
    return starts


def _has_nearby_tears(tears_timestamps: List[float], timestamp: float, window_ms: float) -> bool:
    return any(abs(timestamp - tears_timestamp) <= window_ms for tears_timestamp in tears_timestamps)


def _build_heavens_glaives_event(
    *,
    source_report_code: str,
    player: str,
    fight: Fight,
    pull_index: int,
    timestamp: float,
    tick_count: int,
    pull_duration_ms: Optional[float],
) -> MidnightFallsFuckupEvent:
    return MidnightFallsFuckupEvent(
        source_report_code=source_report_code,
        player=player,
        fight_id=fight.id,
        fight_name=fight.name or "",
        pull_index=pull_index,
        timestamp=timestamp,
        offset_ms=timestamp - float(fight.start),
        mechanic_type="heavens_glaives",
        mechanic_label=HEAVENS_GLAIVES_LABEL,
        ability_id=HEAVENS_GLAIVES_ID,
        ability_label=HEAVENS_GLAIVES_LABEL,
        deduped_tick_count=tick_count,
        pull_duration_ms=pull_duration_ms,
    )


def _build_dark_pulsar_event(
    *,
    source_report_code: str,
    player: str,
    fight: Fight,
    pull_index: int,
    timestamp: float,
    set_index: int,
    set_start: float,
    pull_duration_ms: Optional[float],
) -> MidnightFallsFuckupEvent:
    return MidnightFallsFuckupEvent(
        source_report_code=source_report_code,
        player=player,
        fight_id=fight.id,
        fight_name=fight.name or "",
        pull_index=pull_index,
        timestamp=timestamp,
        offset_ms=timestamp - float(fight.start),
        mechanic_type="dark_pulsar",
        mechanic_label=DARK_PULSAR_LABEL,
        ability_id=DARK_PULSAR_DAMAGE_ID,
        ability_label="Dark Quasar",
        deduped_tick_count=1,
        set_index=set_index,
        set_start_offset_ms=set_start - float(fight.start),
        pull_duration_ms=pull_duration_ms,
    )


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[MidnightFallsFuckupEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[MidnightFallsFuckupEntry]:
    entries: List[MidnightFallsFuckupEntry] = []
    for player in sorted(
        players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -len(events_by_player.get(name, [])),
            name.lower(),
        ),
    ):
        events = sorted(events_by_player.get(player, []), key=lambda item: (item.source_report_code or "", item.timestamp))
        total = len(events)
        pulls = pulls_by_player.get(player, 0) or 1
        heavens_glaives = sum(1 for event in events if event.mechanic_type == "heavens_glaives")
        dark_pulsar = sum(1 for event in events if event.mechanic_type == "dark_pulsar")
        entries.append(
            MidnightFallsFuckupEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_fuckups=total,
                heavens_glaives_hits=heavens_glaives,
                dark_pulsar_hits=dark_pulsar,
                fuckups_per_pull=total / pulls if pulls else 0.0,
                events=events,
            )
        )
    return entries


def _merge_midnight_falls_fuckup_summaries(
    summaries: List[MidnightFallsFuckupSummary],
) -> MidnightFallsFuckupSummary:
    primary = summaries[0]
    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[MidnightFallsFuckupEvent]] = defaultdict(list)
    source_reports: List[str] = []
    pull_count = 0

    for summary in summaries:
        pull_count += summary.pull_count
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
            combined_events[entry.player].extend(entry.events)
            if combined_player_classes.get(entry.player) is None:
                combined_player_classes[entry.player] = entry.class_name
            current_role = combined_player_roles.get(entry.player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[entry.player] = entry.role or ROLE_UNKNOWN

    players = set(combined_pulls.keys()) | set(combined_events.keys())
    entries = _build_entries(
        players=players,
        events_by_player=combined_events,
        pulls_by_player=combined_pulls,
        player_roles=combined_player_roles,
        player_classes=combined_player_classes,
    )
    totals = _summarize_totals(entries)

    return MidnightFallsFuckupSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=pull_count,
        ignore_after_deaths=primary.ignore_after_deaths,
        dedupe_window_ms=primary.dedupe_window_ms,
        total_fuckups=totals["total"],
        heavens_glaives_hits=totals["heavens_glaives"],
        dark_pulsar_hits=totals["dark_pulsar"],
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        player_events={entry.player: entry.events for entry in entries},
        source_reports=source_reports,
    )


def _summarize_totals(entries: List[MidnightFallsFuckupEntry]) -> Dict[str, int]:
    return {
        "total": sum(entry.total_fuckups for entry in entries),
        "heavens_glaives": sum(entry.heavens_glaives_hits for entry in entries),
        "dark_pulsar": sum(entry.dark_pulsar_hits for entry in entries),
    }


def _target_player_name(event: dict) -> Optional[str]:
    target_name = event.get("targetName")
    if target_name:
        return str(target_name)
    target = event.get("target")
    if isinstance(target, dict) and target.get("name"):
        return str(target["name"])
    return None


def _is_player_in_scope(player: Optional[str], known_players: Set[str], participants: Set[str]) -> bool:
    if not player or player not in known_players:
        return False
    return not participants or player in participants


def _event_timestamp(event: dict) -> Optional[float]:
    raw = event.get("timestamp")
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _actual_damage_amount(event: dict) -> float:
    try:
        return float(event.get("amount") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_dedupe_window(value: Optional[float]) -> float:
    if value is None:
        return DEFAULT_DEDUPE_WINDOW_MS
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return DEFAULT_DEDUPE_WINDOW_MS
    if numeric <= 0:
        return DEFAULT_DEDUPE_WINDOW_MS
    return numeric


__all__ = [
    "DEFAULT_DEDUPE_WINDOW_MS",
    "DARK_PULSAR_CAST_ID",
    "DARK_PULSAR_DAMAGE_ID",
    "DARK_PULSAR_LABEL",
    "HEAVENS_GLAIVES_ID",
    "HEAVENS_GLAIVES_LABEL",
    "MidnightFallsFuckupEntry",
    "MidnightFallsFuckupEvent",
    "MidnightFallsFuckupSummary",
    "REPORT_DEFAULT_FIGHT",
    "fetch_midnight_falls_fuckup_summary",
]
