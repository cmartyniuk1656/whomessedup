"""
Inferred Silver Simulacrum hit tracking for Crown of the Cosmos.

Warcraft Logs does not emit a direct Bursting Emptiness damage/death event when a
Silver entity is destroyed. The usable signal is instance-level Silver
Simulacrum activity: each instance casts Ranger Captain's Mark, then repeatedly
emits Simulacrum Backlash until a later Grasp of Emptiness release destroys it.
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

REPORT_DEFAULT_FIGHT = "Crown of the Cosmos"

GRASP_OF_EMPTINESS_ID = 1260027
BURSTING_EMPTINESS_ID = 1255378
RANGER_CAPTAINS_MARK_ID = 1259856
SIMULACRUM_BACKLASH_ID = 1260019
SILVER_SIMULACRUM_NAME = "Silver Simulacrum"

DEFAULT_MATCH_WINDOW_MS = 2500.0
AMBIGUOUS_RELEASE_GAP_MS = 1000.0
MIN_CAST_TO_GRASP_MS = 10000.0
MAX_CAST_TO_GRASP_MS = 30000.0


@dataclass
class CrownSilverHitEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    silver_instance: int
    set_index: Optional[int]
    silver_cast_offset_ms: Optional[float]
    silver_last_backlash_offset_ms: Optional[float]
    backlash_delta_ms: Optional[float]
    player_clip_count: int
    success: bool
    ambiguous: bool = False
    set_release_gap_ms: Optional[float] = None
    paired_player: Optional[str] = None
    paired_player_success: Optional[bool] = None
    pull_duration_ms: Optional[float] = None
    silver_x: Optional[float] = None
    silver_y: Optional[float] = None


@dataclass
class CrownSilverHitEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    assignments: int
    successful_hits: int
    missed_hits: int
    ambiguous_assignments: int
    success_rate: float
    missed_per_pull: float
    player_clips: int
    events: List[CrownSilverHitEvent]


@dataclass
class CrownSilverHitSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    match_window_ms: float
    entries: List[CrownSilverHitEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[CrownSilverHitEvent]]
    total_assignments: int
    total_successful_hits: int
    total_missed_hits: int
    total_ambiguous_assignments: int
    total_player_clips: int
    source_reports: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        known_assignments = self.total_successful_hits + self.total_missed_hits
        if not known_assignments:
            return 0.0
        return self.total_successful_hits / known_assignments


@dataclass
class _GraspRelease:
    player: str
    target_key: str
    timestamp: float
    clip_count: int


@dataclass
class _SilverInstance:
    instance_id: int
    cast_timestamp: float
    last_backlash_timestamp: Optional[float]
    x: Optional[float]
    y: Optional[float]


def fetch_crown_of_the_cosmos_silver_hit_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    match_window_ms: Optional[float] = None,
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> CrownSilverHitSummary:
    primary_code = _sanitize_report_code(report_code)
    resolved_window = _normalize_match_window(match_window_ms)
    primary_summary = _fetch_single_crown_silver_hit_summary(
        report_code=primary_code,
        fight_name=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
        match_window_ms=resolved_window,
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
            _fetch_single_crown_silver_hit_summary(
                report_code=code,
                fight_name=fight_name,
                fight_ids=fight_ids,
                difficulty=difficulty,
                match_window_ms=resolved_window,
                ignore_after_deaths=ignore_after_deaths,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    return _merge_crown_silver_hit_summaries(summaries)


def _fetch_single_crown_silver_hit_summary(
    *,
    report_code: str,
    fight_name: Optional[str],
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    match_window_ms: float,
    ignore_after_deaths: Optional[int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> CrownSilverHitSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    known_players = {
        name
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }
    chosen = _select_fights(
        fights,
        name_filter=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
    )
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

    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    events_by_player: DefaultDict[str, List[CrownSilverHitEvent]] = defaultdict(list)

    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else float(fight.end)
        pull_duration = compute_fight_duration_ms(fight)
        releases = _collect_grasp_releases(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
        )
        if not releases:
            continue

        bursting_clips = list(
            fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="All",
                start=fight.start,
                end=event_end,
                limit=10000,
                ability_id=BURSTING_EMPTINESS_ID,
                include_resources=True,
                use_actor_ids=True,
                actor_names=actor_names,
            )
        )
        for release in releases:
            release.clip_count = sum(
                1
                for event in bursting_clips
                if (event.get("type") or "").lower() == "damage"
                and _coerce_float(event.get("timestamp")) is not None
                and abs(float(event["timestamp"]) - release.timestamp) <= 300.0
            )

        silver_instances = _collect_silver_instances(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
        )
        fight_events: List[CrownSilverHitEvent] = []
        for pair_index, (instance, release) in enumerate(_pair_silver_instances_to_releases(silver_instances, releases)):
            last_backlash = instance.last_backlash_timestamp
            if last_backlash is None:
                continue
            delta_ms = last_backlash - release.timestamp
            success = abs(delta_ms) <= match_window_ms
            fight_events.append(
                CrownSilverHitEvent(
                    source_report_code=report_code,
                    player=release.player,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index_by_fight.get(fight.id, 0),
                    timestamp=release.timestamp,
                    offset_ms=release.timestamp - float(fight.start),
                    silver_instance=instance.instance_id,
                    set_index=(pair_index // 2) + 1,
                    silver_cast_offset_ms=instance.cast_timestamp - float(fight.start),
                    silver_last_backlash_offset_ms=last_backlash - float(fight.start),
                    backlash_delta_ms=delta_ms,
                    player_clip_count=release.clip_count,
                    success=success,
                    pull_duration_ms=pull_duration,
                    silver_x=instance.x,
                    silver_y=instance.y,
                )
            )
        _annotate_setmates(fight_events)
        for event_model in fight_events:
            events_by_player[event_model.player].append(event_model)

    player_classes = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name and name in known_players
    }
    all_players = set(pulls_by_player.keys()) | set(events_by_player.keys())
    entries = _build_entries(
        players=all_players,
        events_by_player=events_by_player,
        pulls_by_player=pulls_by_player,
        player_roles=player_roles,
        player_classes=player_classes,
    )
    totals = _summarize_totals(entries)

    return CrownSilverHitSummary(
        report_code=report_code,
        fight_filter=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        match_window_ms=match_window_ms,
        entries=entries,
        player_classes={player: player_classes.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        player_events={player: sorted(events, key=lambda item: item.timestamp) for player, events in events_by_player.items()},
        total_assignments=totals["assignments"],
        total_successful_hits=totals["successes"],
        total_missed_hits=totals["misses"],
        total_ambiguous_assignments=totals["ambiguous"],
        total_player_clips=totals["clips"],
        source_reports=[report_code],
    )


def _collect_grasp_releases(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
) -> List[_GraspRelease]:
    active: Dict[str, float] = {}
    releases: List[_GraspRelease] = []
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        start=fight.start,
        end=event_end,
        limit=5000,
        ability_id=GRASP_OF_EMPTINESS_ID,
        actor_names=actor_names,
    ):
        target_id = _coerce_int(event.get("targetID"))
        player = _target_player_name(event, actor_names)
        if not player:
            continue
        target_key = str(target_id) if target_id is not None else player
        timestamp = _coerce_float(event.get("timestamp"))
        if timestamp is None:
            continue
        event_type = (event.get("type") or "").lower()
        if event_type in {"applydebuff", "applydebuffstack", "refreshdebuff"}:
            active[target_key] = timestamp
            continue
        if event_type not in {"removedebuff", "removedebuffstack"}:
            continue
        if target_key not in active:
            continue
        active.pop(target_key, None)
        if not player or player not in known_players:
            continue
        releases.append(
            _GraspRelease(
                player=player,
                target_key=target_key,
                timestamp=timestamp,
                clip_count=0,
            )
        )
    return sorted(releases, key=lambda item: item.timestamp)


def _collect_silver_instances(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
) -> List[_SilverInstance]:
    rows = list(
        fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="All",
            start=fight.start,
            end=event_end,
            limit=10000,
            extra_filter=f'source.name = "{SILVER_SIMULACRUM_NAME}" or target.name = "{SILVER_SIMULACRUM_NAME}"',
            include_resources=True,
            use_actor_ids=True,
            actor_names=actor_names,
        )
    )
    source_rows_by_instance: DefaultDict[int, List[dict]] = defaultdict(list)
    for event in rows:
        source_id = _coerce_int(event.get("sourceID"))
        if source_id is None or actor_names.get(source_id) != SILVER_SIMULACRUM_NAME:
            continue
        instance_id = _coerce_int(event.get("sourceInstance"))
        if instance_id is None:
            continue
        source_rows_by_instance[instance_id].append(event)

    instances: List[_SilverInstance] = []
    for instance_id, instance_rows in source_rows_by_instance.items():
        cast_rows = [
            event
            for event in instance_rows
            if (event.get("type") or "").lower() == "cast"
            and _event_ability_id(event) == RANGER_CAPTAINS_MARK_ID
        ]
        if not cast_rows:
            continue
        cast_row = min(cast_rows, key=lambda item: float(item.get("timestamp") or 0.0))
        cast_timestamp = _coerce_float(cast_row.get("timestamp"))
        if cast_timestamp is None:
            continue
        backlash_timestamps = [
            timestamp
            for event in instance_rows
            if (event.get("type") or "").lower() == "damage"
            and _event_ability_id(event) == SIMULACRUM_BACKLASH_ID
            for timestamp in [_coerce_float(event.get("timestamp"))]
            if timestamp is not None
        ]
        instances.append(
            _SilverInstance(
                instance_id=instance_id,
                cast_timestamp=cast_timestamp,
                last_backlash_timestamp=max(backlash_timestamps) if backlash_timestamps else None,
                x=_coerce_float(cast_row.get("x")),
                y=_coerce_float(cast_row.get("y")),
            )
        )
    return sorted(instances, key=lambda item: (item.cast_timestamp, item.instance_id))


def _pair_silver_instances_to_releases(
    instances: List[_SilverInstance],
    releases: List[_GraspRelease],
) -> List[tuple[_SilverInstance, _GraspRelease]]:
    pairs: List[tuple[_SilverInstance, _GraspRelease]] = []
    used_release_indexes: Set[int] = set()
    for instance in instances:
        for index, release in enumerate(releases):
            if index in used_release_indexes:
                continue
            delta = release.timestamp - instance.cast_timestamp
            if delta < MIN_CAST_TO_GRASP_MS:
                continue
            if delta > MAX_CAST_TO_GRASP_MS:
                break
            used_release_indexes.add(index)
            pairs.append((instance, release))
            break
    return pairs


def _annotate_setmates(events: List[CrownSilverHitEvent]) -> None:
    by_set: DefaultDict[int, List[CrownSilverHitEvent]] = defaultdict(list)
    for event in events:
        if event.set_index is None:
            continue
        by_set[event.set_index].append(event)
    for set_events in by_set.values():
        if len(set_events) != 2:
            continue
        first, second = sorted(set_events, key=lambda item: item.timestamp)
        release_gap_ms = abs(second.timestamp - first.timestamp)
        first.paired_player = second.player
        first.paired_player_success = second.success
        first.set_release_gap_ms = release_gap_ms
        second.paired_player = first.player
        second.paired_player_success = first.success
        second.set_release_gap_ms = release_gap_ms
        if release_gap_ms < AMBIGUOUS_RELEASE_GAP_MS:
            first.ambiguous = True
            second.ambiguous = True


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[CrownSilverHitEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[CrownSilverHitEntry]:
    entries: List[CrownSilverHitEntry] = []
    for player in sorted(
        players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -sum(1 for event in events_by_player.get(name, []) if not event.success),
            name.lower(),
        ),
    ):
        events = sorted(events_by_player.get(player, []), key=lambda item: item.timestamp)
        assignments = len(events)
        if assignments <= 0:
            continue
        ambiguous = sum(1 for event in events if event.ambiguous)
        hits = sum(1 for event in events if event.success and not event.ambiguous)
        misses = sum(1 for event in events if not event.success and not event.ambiguous)
        known_assignments = hits + misses
        pulls = pulls_by_player.get(player, 0)
        if pulls <= 0:
            pulls = 1
        entries.append(
            CrownSilverHitEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                assignments=assignments,
                successful_hits=hits,
                missed_hits=misses,
                ambiguous_assignments=ambiguous,
                success_rate=hits / known_assignments if known_assignments else 0.0,
                missed_per_pull=misses / pulls if pulls else 0.0,
                player_clips=sum(event.player_clip_count for event in events),
                events=events,
            )
        )
    return entries


def _merge_crown_silver_hit_summaries(summaries: List[CrownSilverHitSummary]) -> CrownSilverHitSummary:
    primary = summaries[0]
    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[CrownSilverHitEvent]] = defaultdict(list)
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
            current = combined_player_roles.get(player)
            if current in (None, ROLE_UNKNOWN):
                combined_player_roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if player not in combined_player_specs or combined_player_specs[player] is None:
                combined_player_specs[player] = spec
        for entry in summary.entries:
            combined_pulls[entry.player] += entry.pulls
            combined_events[entry.player].extend(entry.events)
            if combined_player_classes.get(entry.player) is None:
                combined_player_classes[entry.player] = entry.class_name
            current = combined_player_roles.get(entry.player)
            if current in (None, ROLE_UNKNOWN):
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
    player_events = {entry.player: entry.events for entry in entries}

    return CrownSilverHitSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=pull_count,
        ignore_after_deaths=primary.ignore_after_deaths,
        match_window_ms=primary.match_window_ms,
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        player_events=player_events,
        total_assignments=totals["assignments"],
        total_successful_hits=totals["successes"],
        total_missed_hits=totals["misses"],
        total_ambiguous_assignments=totals["ambiguous"],
        total_player_clips=totals["clips"],
        source_reports=source_reports,
    )


def _summarize_totals(entries: List[CrownSilverHitEntry]) -> Dict[str, int]:
    return {
        "assignments": sum(entry.assignments for entry in entries),
        "successes": sum(entry.successful_hits for entry in entries),
        "misses": sum(entry.missed_hits for entry in entries),
        "ambiguous": sum(entry.ambiguous_assignments for entry in entries),
        "clips": sum(entry.player_clips for entry in entries),
    }


def _event_ability_id(event: dict) -> Optional[int]:
    raw = event.get("abilityGameID")
    if raw is None and isinstance(event.get("ability"), dict):
        raw = event["ability"].get("guid") or event["ability"].get("id")
    return _coerce_int(raw)


def _actor_name(actor_id: int, actor_names: Dict[int, str], event: dict, *, target: bool) -> Optional[str]:
    key = "targetName" if target else "sourceName"
    name = event.get(key)
    if name:
        return str(name)
    nested_key = "target" if target else "source"
    nested = event.get(nested_key)
    if isinstance(nested, dict) and nested.get("name"):
        return str(nested["name"])
    return actor_names.get(actor_id)


def _target_player_name(event: dict, actor_names: Dict[int, str]) -> Optional[str]:
    target_id = _coerce_int(event.get("targetID"))
    if target_id is not None:
        resolved = _actor_name(target_id, actor_names, event, target=True)
        if resolved:
            return resolved
    target_name = event.get("targetName")
    if target_name:
        return str(target_name)
    target = event.get("target")
    if isinstance(target, dict) and target.get("name"):
        return str(target["name"])
    return None


def _coerce_int(value: object) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_match_window(value: Optional[float]) -> float:
    if value is None:
        return DEFAULT_MATCH_WINDOW_MS
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return DEFAULT_MATCH_WINDOW_MS
    if numeric <= 0:
        return DEFAULT_MATCH_WINDOW_MS
    return numeric


__all__ = [
    "CrownSilverHitEntry",
    "CrownSilverHitEvent",
    "CrownSilverHitSummary",
    "REPORT_DEFAULT_FIGHT",
    "fetch_crown_of_the_cosmos_silver_hit_summary",
]
