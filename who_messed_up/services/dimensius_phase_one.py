"""
Dimensius Phase One analysis helpers (Reverse Gravity + Excess Mass overlaps).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple, Set

import requests

from ..env import load_env
from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _select_fights,
    compute_death_cutoffs,
    compute_fight_duration_ms,
)

REVERSE_GRAVITY_ID = 1243577
EXCESS_MASS_ID = 1228206
DARK_ENERGY_ID = 1231002

APPLY_EVENTS = {"applydebuff", "applydebuffstack", "refreshdebuff"}
REMOVE_EVENTS = {"removedebuff", "removedebuffstack"}
EARLY_MASS_WINDOW_SECONDS = 1
EARLY_MASS_WINDOW_MS = EARLY_MASS_WINDOW_SECONDS * 1000.0
EARLY_MASS_WINDOW_MIN_SECONDS = 1
EARLY_MASS_WINDOW_MAX_SECONDS = 15
REVERSE_GRAVITY_SET_GAP_MS = 1500.0


@dataclass
class MetricDefinition:
    id: str
    label: str
    per_pull_label: str


@dataclass
class MetricValue:
    total: float
    per_pull: float


@dataclass
class TrackedEvent:
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    metric_id: str
    pull_duration_ms: Optional[float] = None


@dataclass
class DimensiusPhaseOneEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    metrics: Dict[str, MetricValue]
    fuckup_rate: float
    events: List[TrackedEvent]


@dataclass
class DimensiusPhaseOneSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    early_mass_window_seconds: Optional[int]
    metrics: List[MetricDefinition]
    entries: List[DimensiusPhaseOneEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    metric_totals: Dict[str, MetricValue]
    combined_per_pull: float
    ability_ids: Dict[str, int]
    player_events: Dict[str, List[TrackedEvent]]


def fetch_dimensius_phase_one_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    include_rg_em_overlap: bool = True,
    include_early_mass: bool = False,
    early_mass_window_seconds: Optional[int] = None,
    include_dark_energy_hits: bool = False,
    ignore_after_deaths: Optional[int] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DimensiusPhaseOneSummary:
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

    metrics: List[MetricDefinition] = []
    if include_rg_em_overlap:
        metrics.append(
            MetricDefinition(
                id="rg_em_overlap",
                label="Reverse Gravity + Excess Mass",
                per_pull_label="Overlap / Pull",
            )
        )
    if include_early_mass:
        metrics.append(
            MetricDefinition(
                id="early_mass",
                label="Excess Mass before Reverse Gravity",
                per_pull_label="Early Mass / Pull",
            )
        )
    if include_dark_energy_hits:
        metrics.append(
            MetricDefinition(
                id="dark_energy",
                label="Dark Energy hits",
                per_pull_label="Dark Energy hits / Pull",
            )
        )

    death_limit = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    death_cutoffs = compute_death_cutoffs(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        actor_names=actor_names,
        max_deaths=death_limit,
    )

    overlap_counts_by_player: DefaultDict[str, int] = defaultdict(int)
    player_events: DefaultDict[str, List[TrackedEvent]] = defaultdict(list)
    pull_index_by_fight: Dict[int, int] = {fight.id: idx + 1 for idx, fight in enumerate(chosen)}
    early_mass_counts_by_player: DefaultDict[str, int] = defaultdict(int)
    dark_energy_counts_by_player: DefaultDict[str, int] = defaultdict(int)
    early_mass_window_value: Optional[int] = None
    early_mass_window_ms = EARLY_MASS_WINDOW_MS
    if include_early_mass:
        early_mass_window_value, early_mass_window_ms = _normalize_early_mass_window(early_mass_window_seconds)

    if include_rg_em_overlap:
        rg_intervals, rg_apply_events = _collect_debuff_intervals(
            session,
            bearer,
            fights=chosen,
            report_code=report_code,
            ability_id=REVERSE_GRAVITY_ID,
            actor_names=actor_names,
            capture_applies=True,
            death_cutoffs=death_cutoffs,
        )
        em_intervals, _ = _collect_debuff_intervals(
            session,
            bearer,
            fights=chosen,
            report_code=report_code,
            ability_id=EXCESS_MASS_ID,
            actor_names=actor_names,
            death_cutoffs=death_cutoffs,
        )
        for fight in chosen:
            pull_duration = compute_fight_duration_ms(fight)
            fight_rg = rg_intervals.get(fight.id, {})
            fight_em = em_intervals.get(fight.id, {})
            players = set(fight_rg.keys()) | set(fight_em.keys())
            for player in players:
                overlaps = _detect_interval_overlaps(fight_rg.get(player, []), fight_em.get(player, []))
                if overlaps:
                    overlap_counts_by_player[player] += len(overlaps)
                    for overlap_ts in overlaps:
                        offset = overlap_ts - float(fight.start)
                        player_events[player].append(
                            TrackedEvent(
                                player=player,
                                fight_id=fight.id,
                                fight_name=fight.name or "",
                                pull_index=pull_index_by_fight.get(fight.id, 0),
                                timestamp=overlap_ts,
                                offset_ms=offset,
                                metric_id="rg_em_overlap",
                                pull_duration_ms=pull_duration,
                            )
                        )
    else:
        rg_intervals, rg_apply_events = _collect_debuff_intervals(
            session,
            bearer,
            fights=chosen,
            report_code=report_code,
            ability_id=REVERSE_GRAVITY_ID,
            actor_names=actor_names,
            capture_applies=True,
            death_cutoffs=death_cutoffs,
        )
        em_intervals, _ = _collect_debuff_intervals(
            session,
            bearer,
            fights=chosen,
            report_code=report_code,
            ability_id=EXCESS_MASS_ID,
            actor_names=actor_names,
            death_cutoffs=death_cutoffs,
        )

    if include_early_mass:
        set_starts_by_fight = _identify_reverse_gravity_sets(rg_apply_events or {})
        for fight in chosen:
            pull_duration = compute_fight_duration_ms(fight)
            set_starts = set_starts_by_fight.get(fight.id, [])
            if not set_starts:
                continue
            em_map = em_intervals.get(fight.id, {})
            seen_pairs: Set[Tuple[str, float]] = set()
            for player, intervals in em_map.items():
                for start_ts, _ in intervals:
                    for set_start in set_starts:
                        if set_start - early_mass_window_ms <= start_ts < set_start:
                            key = (player, set_start)
                            if key in seen_pairs:
                                continue
                            seen_pairs.add(key)
                            early_mass_counts_by_player[player] += 1
                            offset = start_ts - float(fight.start)
                            player_events[player].append(
                                TrackedEvent(
                                    player=player,
                                    fight_id=fight.id,
                                    fight_name=fight.name or "",
                                    pull_index=pull_index_by_fight.get(fight.id, 0),
                                    timestamp=start_ts,
                                    offset_ms=offset,
                                    metric_id="early_mass",
                                    pull_duration_ms=pull_duration,
                                )
                            )
                            break

    if include_dark_energy_hits:
        for fight in chosen:
            pull_duration = compute_fight_duration_ms(fight)
            for event in fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="DamageTaken",
                start=fight.start,
                end=fight.end,
                ability_id=DARK_ENERGY_ID,
                actor_names=actor_names,
            ):
                timestamp = event.get("timestamp")
                if timestamp is None:
                    continue
                try:
                    ts_val = float(timestamp)
                except (TypeError, ValueError):
                    continue
                cutoff = death_cutoffs.get(fight.id) if death_cutoffs else None
                if cutoff is not None and ts_val >= cutoff:
                    continue
                target_name = event.get("targetName")
                if not target_name and isinstance(event.get("target"), dict):
                    target_name = event["target"].get("name")
                if not target_name:
                    continue
                amount = event.get("amount")
                absorbed = event.get("absorbed")
                mitigated = event.get("mitigated")
                total_amount = 0.0
                for value in (amount, absorbed, mitigated):
                    if isinstance(value, (int, float)):
                        total_amount += float(value)
                if total_amount <= 0:
                    continue
                dark_energy_counts_by_player[target_name] += 1
                offset = ts_val - float(fight.start)
                player_events[target_name].append(
                    TrackedEvent(
                        player=target_name,
                        fight_id=fight.id,
                        fight_name=fight.name or "",
                        pull_index=pull_index_by_fight.get(fight.id, 0),
                        timestamp=ts_val,
                        offset_ms=offset,
                        metric_id="dark_energy",
                        pull_duration_ms=pull_duration,
                    )
                )

    pull_count = len(chosen)
    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    all_players = (
        set(player_roles.keys())
        | set(pulls_by_player.keys())
        | set(overlap_counts_by_player.keys())
        | set(early_mass_counts_by_player.keys())
        | set(dark_energy_counts_by_player.keys())
        | set(player_events.keys())
    )
    if not all_players and participants_by_fight:
        for participants in participants_by_fight.values():
            all_players.update(participants)

    entries: List[DimensiusPhaseOneEntry] = []
    metric_totals: Dict[str, MetricValue] = {}

    if include_rg_em_overlap:
        total_overlaps = float(sum(overlap_counts_by_player.values()))
        avg_per_pull = total_overlaps / pull_count if pull_count else 0.0
        metric_totals["rg_em_overlap"] = MetricValue(total=total_overlaps, per_pull=avg_per_pull)
    if include_early_mass:
        total_early = float(sum(early_mass_counts_by_player.values()))
        avg_early = total_early / pull_count if pull_count else 0.0
        metric_totals["early_mass"] = MetricValue(total=total_early, per_pull=avg_early)
    if include_dark_energy_hits:
        total_dark = float(sum(dark_energy_counts_by_player.values()))
        avg_dark = total_dark / pull_count if pull_count else 0.0
        metric_totals["dark_energy"] = MetricValue(total=total_dark, per_pull=avg_dark)

    combined_per_pull = sum(value.per_pull for value in metric_totals.values())

    def _player_metric_total(name: str) -> int:
        total = 0
        if include_rg_em_overlap:
            total += overlap_counts_by_player.get(name, 0)
        if include_early_mass:
            total += early_mass_counts_by_player.get(name, 0)
        if include_dark_energy_hits:
            total += dark_energy_counts_by_player.get(name, 0)
        return total

    for player in sorted(
        all_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -_player_metric_total(name),
            name.lower(),
        ),
    ):
        pulls = pulls_by_player.get(player, pull_count)
        if pulls <= 0:
            pulls = pull_count or 1
        metrics_map: Dict[str, MetricValue] = {}
        if include_rg_em_overlap:
            total = float(overlap_counts_by_player.get(player, 0))
            per_pull = total / pulls if pulls else 0.0
            metrics_map["rg_em_overlap"] = MetricValue(total=total, per_pull=per_pull)
        if include_early_mass:
            total = float(early_mass_counts_by_player.get(player, 0))
            per_pull = total / pulls if pulls else 0.0
            metrics_map["early_mass"] = MetricValue(total=total, per_pull=per_pull)
        if include_dark_energy_hits:
            total = float(dark_energy_counts_by_player.get(player, 0))
            per_pull = total / pulls if pulls else 0.0
            metrics_map["dark_energy"] = MetricValue(total=total, per_pull=per_pull)

        fuckup_rate = sum(value.per_pull for value in metrics_map.values())

        entries.append(
            DimensiusPhaseOneEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=name_to_class.get(player),
                pulls=pulls,
                metrics=metrics_map,
                fuckup_rate=fuckup_rate,
                events=list(player_events.get(player, [])),
            )
        )

    entries.sort(
        key=lambda entry: (
            ROLE_PRIORITY.get(entry.role or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            -entry.fuckup_rate,
            -entry.pulls,
            entry.player.lower(),
        )
    )

    ability_ids = {
        "reverse_gravity": REVERSE_GRAVITY_ID,
        "excess_mass": EXCESS_MASS_ID,
        "dark_energy": DARK_ENERGY_ID,
    }

    return DimensiusPhaseOneSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=pull_count,
        metrics=metrics,
        entries=entries,
        player_classes={player: name_to_class.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        metric_totals=metric_totals,
        combined_per_pull=combined_per_pull,
        ability_ids=ability_ids,
        ignore_after_deaths=death_limit,
        early_mass_window_seconds=early_mass_window_value,
        player_events={player: list(events) for player, events in player_events.items()},
    )


def _normalize_early_mass_window(candidate: Optional[int]) -> Tuple[int, float]:
    seconds = EARLY_MASS_WINDOW_SECONDS
    if isinstance(candidate, (int, float)):
        seconds = int(candidate)
    elif isinstance(candidate, str):
        try:
            seconds = int(candidate)
        except ValueError:
            seconds = EARLY_MASS_WINDOW_SECONDS
    if seconds < EARLY_MASS_WINDOW_MIN_SECONDS:
        seconds = EARLY_MASS_WINDOW_MIN_SECONDS
    elif seconds > EARLY_MASS_WINDOW_MAX_SECONDS:
        seconds = EARLY_MASS_WINDOW_MAX_SECONDS
    return seconds, float(seconds) * 1000.0


def _collect_debuff_intervals(
    session: requests.Session,
    bearer: str,
    *,
    fights: Iterable[Fight],
    report_code: str,
    ability_id: int,
    actor_names: Dict[int, str],
    capture_applies: bool = False,
    death_cutoffs: Optional[Dict[int, float]] = None,
) -> Tuple[Dict[int, Dict[str, List[Tuple[float, float]]]], Optional[Dict[int, List[Tuple[float, str]]]]]:
    intervals_by_fight: Dict[int, Dict[str, List[Tuple[float, float]]]] = {}
    apply_events_by_fight: Dict[int, List[Tuple[float, str]]] = defaultdict(list)
    for fight in fights:
        intervals: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        active_start: Dict[str, float] = {}
        stack_counts: Dict[str, int] = {}
        cutoff = death_cutoffs.get(fight.id) if death_cutoffs else None
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=fight.end,
            ability_id=ability_id,
            actor_names=actor_names,
        ):
            event_type = (event.get("type") or "").lower()
            if event_type not in APPLY_EVENTS and event_type not in REMOVE_EVENTS:
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

            if event_type in APPLY_EVENTS:
                if capture_applies:
                    apply_events_by_fight[fight.id].append((ts_val, target_name))
                current = stack_counts.get(target_name, 0)
                stack_counts[target_name] = current + 1
                if current == 0:
                    active_start[target_name] = ts_val
            elif event_type in REMOVE_EVENTS:
                current = stack_counts.get(target_name, 0)
                if current <= 1:
                    start_ts = active_start.pop(target_name, None)
                    stack_counts.pop(target_name, None)
                    if start_ts is not None and ts_val >= start_ts:
                        end_ts = ts_val
                        if cutoff is not None and end_ts > cutoff:
                            end_ts = cutoff
                        if cutoff is not None and start_ts >= cutoff:
                            continue
                        intervals[target_name].append((start_ts, end_ts))
                else:
                    stack_counts[target_name] = current - 1

        for player, start_ts in active_start.items():
            if cutoff is not None and start_ts >= cutoff:
                continue
            end_ts = float(fight.end)
            if cutoff is not None and cutoff < end_ts:
                end_ts = cutoff
            intervals[player].append((start_ts, end_ts))
        for player in intervals:
            intervals[player].sort(key=lambda pair: pair[0])
        intervals_by_fight[fight.id] = intervals
    if capture_applies:
        for events in apply_events_by_fight.values():
            events.sort(key=lambda item: item[0])
        return intervals_by_fight, dict(apply_events_by_fight)
    return intervals_by_fight, None


def _detect_interval_overlaps(
    first: List[Tuple[float, float]],
    second: List[Tuple[float, float]],
) -> List[float]:
    if not first or not second:
        return []
    overlaps: List[float] = []
    i = 0
    j = 0
    while i < len(first) and j < len(second):
        start = max(first[i][0], second[j][0])
        end = min(first[i][1], second[j][1])
        if start < end:
            overlaps.append(start)
        if first[i][1] <= second[j][1]:
            i += 1
        else:
            j += 1
    return overlaps


def _identify_reverse_gravity_sets(
    apply_events_by_fight: Dict[int, List[Tuple[float, str]]],
) -> Dict[int, List[float]]:
    set_starts: Dict[int, List[float]] = {}
    for fight_id, events in apply_events_by_fight.items():
        if not events:
            continue
        starts: List[float] = []
        prev_ts: Optional[float] = None
        for ts, _ in events:
            if prev_ts is None or ts - prev_ts > REVERSE_GRAVITY_SET_GAP_MS:
                starts.append(ts)
            prev_ts = ts
        set_starts[fight_id] = starts
    return set_starts


__all__ = [
    "DimensiusPhaseOneEntry",
    "DimensiusPhaseOneSummary",
    "MetricDefinition",
    "MetricValue",
    "TrackedEvent",
    "fetch_dimensius_phase_one_summary",
    "REVERSE_GRAVITY_ID",
    "EXCESS_MASS_ID",
    "DARK_ENERGY_ID",
]
