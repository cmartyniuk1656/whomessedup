"""
Dimensius Phase One analysis helpers (Reverse Gravity + Excess Mass overlaps).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple

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
)

REVERSE_GRAVITY_ID = 1243577
EXCESS_MASS_ID = 1228206

APPLY_EVENTS = {"applydebuff", "applydebuffstack", "refreshdebuff"}
REMOVE_EVENTS = {"removedebuff", "removedebuffstack"}


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
class DimensiusPhaseOneEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    metrics: Dict[str, MetricValue]
    fuckup_rate: float


@dataclass
class DimensiusPhaseOneSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    metrics: List[MetricDefinition]
    entries: List[DimensiusPhaseOneEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    metric_totals: Dict[str, MetricValue]
    combined_per_pull: float
    ability_ids: Dict[str, int]


def fetch_dimensius_phase_one_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    include_rg_em_overlap: bool = True,
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

    overlap_counts_by_player: DefaultDict[str, int] = defaultdict(int)
    if include_rg_em_overlap:
        rg_intervals = _collect_debuff_intervals(
            session,
            bearer,
            fights=chosen,
            report_code=report_code,
            ability_id=REVERSE_GRAVITY_ID,
            actor_names=actor_names,
        )
        em_intervals = _collect_debuff_intervals(
            session,
            bearer,
            fights=chosen,
            report_code=report_code,
            ability_id=EXCESS_MASS_ID,
            actor_names=actor_names,
        )
        for fight in chosen:
            fight_rg = rg_intervals.get(fight.id, {})
            fight_em = em_intervals.get(fight.id, {})
            players = set(fight_rg.keys()) | set(fight_em.keys())
            for player in players:
                overlaps = _count_interval_overlaps(fight_rg.get(player, []), fight_em.get(player, []))
                if overlaps > 0:
                    overlap_counts_by_player[player] += overlaps

    pull_count = len(chosen)
    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    all_players = set(player_roles.keys()) | set(pulls_by_player.keys()) | set(overlap_counts_by_player.keys())
    if not all_players and participants_by_fight:
        for participants in participants_by_fight.values():
            all_players.update(participants)

    entries: List[DimensiusPhaseOneEntry] = []
    metric_totals: Dict[str, MetricValue] = {}

    if include_rg_em_overlap:
        total_overlaps = float(sum(overlap_counts_by_player.values()))
        avg_per_pull = total_overlaps / pull_count if pull_count else 0.0
        metric_totals["rg_em_overlap"] = MetricValue(total=total_overlaps, per_pull=avg_per_pull)

    combined_per_pull = sum(value.per_pull for value in metric_totals.values())

    for player in sorted(
        all_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -((overlap_counts_by_player.get(name, 0)) if include_rg_em_overlap else 0),
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

        fuckup_rate = sum(value.per_pull for value in metrics_map.values())

        entries.append(
            DimensiusPhaseOneEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=name_to_class.get(player),
                pulls=pulls,
                metrics=metrics_map,
                fuckup_rate=fuckup_rate,
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
    )


def _collect_debuff_intervals(
    session: requests.Session,
    bearer: str,
    *,
    fights: Iterable[Fight],
    report_code: str,
    ability_id: int,
    actor_names: Dict[int, str],
) -> Dict[int, Dict[str, List[Tuple[float, float]]]]:
    intervals_by_fight: Dict[int, Dict[str, List[Tuple[float, float]]]] = {}
    for fight in fights:
        intervals: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        active_start: Dict[str, float] = {}
        stack_counts: Dict[str, int] = {}
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
            target_name = event.get("targetName")
            if not target_name and isinstance(event.get("target"), dict):
                target_name = event["target"].get("name")
            if not target_name:
                continue

            if event_type in APPLY_EVENTS:
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
                        intervals[target_name].append((start_ts, ts_val))
                else:
                    stack_counts[target_name] = current - 1

        for player, start_ts in active_start.items():
            intervals[player].append((start_ts, float(fight.end)))
        for player in intervals:
            intervals[player].sort(key=lambda pair: pair[0])
        intervals_by_fight[fight.id] = intervals
    return intervals_by_fight


def _count_interval_overlaps(
    first: List[Tuple[float, float]],
    second: List[Tuple[float, float]],
) -> int:
    if not first or not second:
        return 0
    count = 0
    i = 0
    j = 0
    while i < len(first) and j < len(second):
        start = max(first[i][0], second[j][0])
        end = min(first[i][1], second[j][1])
        if start < end:
            count += 1
        if first[i][1] <= second[j][1]:
            i += 1
        else:
            j += 1
    return count


__all__ = [
    "DimensiusPhaseOneEntry",
    "DimensiusPhaseOneSummary",
    "MetricDefinition",
    "MetricValue",
    "fetch_dimensius_phase_one_summary",
    "REVERSE_GRAVITY_ID",
    "EXCESS_MASS_ID",
]
