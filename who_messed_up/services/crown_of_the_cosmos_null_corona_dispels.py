"""
Null Corona dispel quality report for Crown of the Cosmos.

Null Corona is a healing absorb that jumps when dispelled. A dispel is treated
as "great" when the target was inside the configured HP window, or when there
was another strong reason to clear the absorb immediately without going below
the configured floor.
"""
from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple

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
    compute_fight_duration_ms,
)

REPORT_DEFAULT_FIGHT = "Crown of the Cosmos"

NULL_CORONA_INITIAL_ID = 1233865
NULL_CORONA_JUMP_ID = 1233887
NULL_CORONA_DEBUFF_IDS = {NULL_CORONA_INITIAL_ID, NULL_CORONA_JUMP_ID}
CORRUPTING_ESSENCE_ID = 1261531
GRASP_OF_EMPTINESS_ID = 1260027
BURSTING_EMPTINESS_ID = 1255378

DEFAULT_HP_FLOOR_PERCENT = 30.0
DEFAULT_HP_CEILING_PERCENT = 60.0
HEALTH_SNAPSHOT_MAX_AGE_MS = 5000.0
DANGEROUS_DAMAGE_LOOKBACK_MS = 1000.0
DANGEROUS_DAMAGE_LOOKAHEAD_MS = 5000.0
DANGEROUS_DAMAGE_ABILITY_IDS = {GRASP_OF_EMPTINESS_ID, BURSTING_EMPTINESS_ID}

DISPEL_CAST_ABILITY_LABELS: Dict[int, str] = {
    527: "Purify",
    4987: "Cleanse",
    77130: "Purify Spirit",
    88423: "Nature's Cure",
    115310: "Revival",
    115450: "Detox",
    360823: "Naturalize",
}

DEBUFF_LABELS: Dict[int, str] = {
    NULL_CORONA_INITIAL_ID: "Null Corona",
    NULL_CORONA_JUMP_ID: "Null Corona",
    CORRUPTING_ESSENCE_ID: "Corrupting Essence",
    GRASP_OF_EMPTINESS_ID: "Grasp of Emptiness",
    BURSTING_EMPTINESS_ID: "Bursting Emptiness",
}


@dataclass
class CrownNullCoronaDispelEvent:
    source_report_code: Optional[str]
    player: str
    target: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    debuff_id: int
    debuff_label: str
    dispel_ability_id: Optional[int]
    dispel_ability_label: Optional[str]
    hp_floor_percent: float
    hp_ceiling_percent: float
    target_hit_points: Optional[float]
    target_max_hit_points: Optional[float]
    target_hp_percent: Optional[float]
    health_snapshot_age_ms: Optional[float]
    is_great: bool
    jumped_while_low: bool = False
    jump_application_hp_percent: Optional[float] = None
    reason_labels: Tuple[str, ...] = ()
    companion_debuff_ids: Tuple[int, ...] = ()
    companion_debuff_labels: Tuple[str, ...] = ()
    dangerous_damage_ability_ids: Tuple[int, ...] = ()
    dangerous_damage_labels: Tuple[str, ...] = ()
    pull_duration_ms: Optional[float] = None


@dataclass
class CrownNullCoronaDispelEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_dispels: int
    great_dispels: int
    needs_review_dispels: int
    great_rate: float
    hp_window_dispels: int
    low_jump_dispels: int
    companion_dispels: int
    danger_window_dispels: int
    events: List[CrownNullCoronaDispelEvent] = field(default_factory=list)


@dataclass
class CrownNullCoronaDispelSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    hp_floor_percent: float
    hp_ceiling_percent: float
    total_dispels: int
    great_dispels: int
    needs_review_dispels: int
    hp_window_dispels: int
    low_jump_dispels: int
    companion_dispels: int
    danger_window_dispels: int
    entries: List[CrownNullCoronaDispelEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[CrownNullCoronaDispelEvent]]
    source_reports: List[str] = field(default_factory=list)

    @property
    def great_rate(self) -> float:
        if not self.total_dispels:
            return 0.0
        return self.great_dispels / self.total_dispels


@dataclass(frozen=True)
class _HealthSnapshot:
    timestamp: float
    hit_points: float
    max_hit_points: float


@dataclass
class _HealthContext:
    snapshots_by_target: Dict[str, List[_HealthSnapshot]]
    snapshot_times_by_target: Dict[str, List[float]]
    dangerous_damage_by_target: Dict[str, List[Tuple[float, int]]]


def fetch_crown_of_the_cosmos_null_corona_dispel_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    hp_floor_percent: Optional[float] = None,
    hp_ceiling_percent: Optional[float] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> CrownNullCoronaDispelSummary:
    primary_code = _sanitize_report_code(report_code)
    floor, ceiling = _normalize_hp_window(hp_floor_percent, hp_ceiling_percent)
    primary_summary = _fetch_single_crown_null_corona_dispel_summary(
        report_code=primary_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        hp_floor_percent=floor,
        hp_ceiling_percent=ceiling,
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
            _fetch_single_crown_null_corona_dispel_summary(
                report_code=code,
                fight_name=fight_name or REPORT_DEFAULT_FIGHT,
                fight_ids=fight_ids,
                difficulty=difficulty,
                hp_floor_percent=floor,
                hp_ceiling_percent=ceiling,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    return _merge_crown_null_corona_dispel_summaries(summaries)


def _fetch_single_crown_null_corona_dispel_summary(
    *,
    report_code: str,
    fight_name: Optional[str],
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    hp_floor_percent: float,
    hp_ceiling_percent: float,
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> CrownNullCoronaDispelSummary:
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
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = {name for name in _players_from_details(details) if name in known_players}
        for name in participants:
            pulls_by_player[name] += 1
    for fight_roles in roles_by_fight.values():
        for player, role in fight_roles.items():
            if player not in player_roles or player_roles[player] in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN

    player_classes = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name and name in known_players
    }

    events_by_player: DefaultDict[str, List[CrownNullCoronaDispelEvent]] = defaultdict(list)
    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    pull_duration_by_fight = {fight.id: compute_fight_duration_ms(fight) for fight in chosen}

    for fight in chosen:
        all_dispels = _collect_dispel_events(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            known_players=known_players,
        )
        null_dispels = [event for event in all_dispels if _extra_ability_id(event) in NULL_CORONA_DEBUFF_IDS]
        if not null_dispels:
            continue

        target_names = {
            _target_name(event, actor_names)
            for event in null_dispels
            if _target_name(event, actor_names)
        }
        health_context = _collect_health_context(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            target_names=target_names,
        )
        jump_applications_by_target = _collect_null_corona_jump_applications(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            target_names=target_names,
        )
        dispels_by_group = _group_dispels(all_dispels)

        for event in null_dispels:
            player = _source_name(event, actor_names)
            target = _target_name(event, actor_names)
            timestamp = _event_timestamp(event)
            if not player or not target or timestamp is None:
                continue
            debuff_id = _extra_ability_id(event)
            if debuff_id is None:
                continue
            health = _health_at(health_context, target, timestamp)
            companion_ids = _companion_debuff_ids(event, dispels_by_group)
            dangerous_ids = _dangerous_damage_ids(health_context, target, timestamp)
            jump_application = _latest_timestamp_before(jump_applications_by_target.get(target, []), timestamp)
            jump_application_health = (
                _health_at(health_context, target, jump_application)
                if debuff_id == NULL_CORONA_JUMP_ID and jump_application is not None
                else None
            )
            jumped_while_low = (
                debuff_id == NULL_CORONA_JUMP_ID
                and _health_percent(jump_application_health) is not None
                and _health_percent(jump_application_health) < hp_floor_percent
            )
            reason_labels = _great_reason_labels(
                health=health,
                floor=hp_floor_percent,
                ceiling=hp_ceiling_percent,
                jumped_while_low=jumped_while_low,
                companion_ids=companion_ids,
                dangerous_ids=dangerous_ids,
            )
            event_model = CrownNullCoronaDispelEvent(
                source_report_code=report_code,
                player=player,
                target=target,
                fight_id=fight.id,
                fight_name=fight.name or "",
                pull_index=pull_index_by_fight.get(fight.id, 0),
                timestamp=timestamp,
                offset_ms=timestamp - float(fight.start),
                debuff_id=debuff_id,
                debuff_label=_debuff_label(debuff_id),
                dispel_ability_id=_ability_id(event),
                dispel_ability_label=_dispel_ability_label(_ability_id(event)),
                hp_floor_percent=hp_floor_percent,
                hp_ceiling_percent=hp_ceiling_percent,
                target_hit_points=health.hit_points if health else None,
                target_max_hit_points=health.max_hit_points if health else None,
                target_hp_percent=_health_percent(health),
                health_snapshot_age_ms=(timestamp - health.timestamp) if health else None,
                is_great=bool(reason_labels),
                jumped_while_low=jumped_while_low,
                jump_application_hp_percent=_health_percent(jump_application_health),
                reason_labels=tuple(reason_labels),
                companion_debuff_ids=tuple(companion_ids),
                companion_debuff_labels=tuple(_debuff_label(ability_id) for ability_id in companion_ids),
                dangerous_damage_ability_ids=tuple(dangerous_ids),
                dangerous_damage_labels=tuple(_debuff_label(ability_id) for ability_id in dangerous_ids),
                pull_duration_ms=pull_duration_by_fight.get(fight.id),
            )
            events_by_player[player].append(event_model)

    players = set(events_by_player.keys())
    entries = _build_entries(
        players=players,
        events_by_player=events_by_player,
        pulls_by_player=pulls_by_player,
        player_roles=player_roles,
        player_classes=player_classes,
    )
    totals = _summarize_totals(entries)

    return CrownNullCoronaDispelSummary(
        report_code=report_code,
        fight_filter=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=len(chosen),
        hp_floor_percent=hp_floor_percent,
        hp_ceiling_percent=hp_ceiling_percent,
        total_dispels=totals["total"],
        great_dispels=totals["great"],
        needs_review_dispels=totals["review"],
        hp_window_dispels=totals["window"],
        low_jump_dispels=totals["low_jump"],
        companion_dispels=totals["companion"],
        danger_window_dispels=totals["danger"],
        entries=entries,
        player_classes={player: player_classes.get(player) for player in players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players},
        player_specs={player: player_specs.get(player) for player in players},
        player_events={player: sorted(events, key=lambda item: item.timestamp) for player, events in events_by_player.items()},
        source_reports=[report_code],
    )


def _collect_dispel_events(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    actor_names: Dict[int, str],
    known_players: Set[str],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
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
        source = _source_name(event, actor_names)
        target = _target_name(event, actor_names)
        if not source or not target:
            continue
        if source not in known_players or target not in known_players:
            continue
        rows.append(event)
    return sorted(rows, key=lambda event: _event_timestamp(event) or 0.0)


def _collect_health_context(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    actor_names: Dict[int, str],
    target_names: Set[str],
) -> _HealthContext:
    if not target_names:
        return _HealthContext({}, {}, {})

    target_filter = _target_filter(target_names)
    snapshots_by_target: DefaultDict[str, List[_HealthSnapshot]] = defaultdict(list)
    dangerous_damage_by_target: DefaultDict[str, List[Tuple[float, int]]] = defaultdict(list)

    for data_type in ("Resources", "DamageTaken"):
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type=data_type,
            start=fight.start,
            end=fight.end,
            limit=5000,
            extra_filter=target_filter,
            include_resources=True,
            actor_names=actor_names,
        ):
            target = _target_name(event, actor_names)
            timestamp = _event_timestamp(event)
            if not target or timestamp is None or target not in target_names:
                continue
            snapshot = _health_snapshot(event, timestamp)
            if snapshot:
                snapshots_by_target[target].append(snapshot)
            ability_id = _ability_id(event)
            if data_type == "DamageTaken" and ability_id in DANGEROUS_DAMAGE_ABILITY_IDS:
                dangerous_damage_by_target[target].append((timestamp, ability_id))

    snapshot_times_by_target: Dict[str, List[float]] = {}
    for target, snapshots in snapshots_by_target.items():
        snapshots.sort(key=lambda item: item.timestamp)
        snapshot_times_by_target[target] = [snapshot.timestamp for snapshot in snapshots]
    for damage_events in dangerous_damage_by_target.values():
        damage_events.sort(key=lambda item: item[0])

    return _HealthContext(
        snapshots_by_target=dict(snapshots_by_target),
        snapshot_times_by_target=snapshot_times_by_target,
        dangerous_damage_by_target=dict(dangerous_damage_by_target),
    )


def _collect_null_corona_jump_applications(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    actor_names: Dict[int, str],
    target_names: Set[str],
) -> Dict[str, List[float]]:
    if not target_names:
        return {}

    applications_by_target: DefaultDict[str, List[float]] = defaultdict(list)
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        start=fight.start,
        end=fight.end,
        limit=5000,
        ability_id=NULL_CORONA_JUMP_ID,
        extra_filter=_target_filter(target_names),
        actor_names=actor_names,
    ):
        if (event.get("type") or "").lower() != "applydebuff":
            continue
        target = _target_name(event, actor_names)
        timestamp = _event_timestamp(event)
        if not target or timestamp is None or target not in target_names:
            continue
        applications_by_target[target].append(timestamp)

    for timestamps in applications_by_target.values():
        timestamps.sort()
    return dict(applications_by_target)


def _target_filter(target_names: Set[str]) -> str:
    parts = []
    for name in sorted(target_names):
        safe_name = name.replace('"', '\\"')
        parts.append(f'target.name = "{safe_name}"')
    return " or ".join(parts)


def _health_at(context: _HealthContext, target: str, timestamp: float) -> Optional[_HealthSnapshot]:
    snapshots = context.snapshots_by_target.get(target) or []
    times = context.snapshot_times_by_target.get(target) or []
    index = bisect.bisect_right(times, timestamp) - 1
    if index < 0:
        return None
    snapshot = snapshots[index]
    if timestamp - snapshot.timestamp > HEALTH_SNAPSHOT_MAX_AGE_MS:
        return None
    return snapshot


def _latest_timestamp_before(timestamps: Sequence[float], timestamp: float) -> Optional[float]:
    index = bisect.bisect_right(timestamps, timestamp) - 1
    if index < 0:
        return None
    return timestamps[index]


def _dangerous_damage_ids(context: _HealthContext, target: str, timestamp: float) -> List[int]:
    events = context.dangerous_damage_by_target.get(target) or []
    if not events:
        return []
    times = [item[0] for item in events]
    start_index = bisect.bisect_left(times, timestamp - DANGEROUS_DAMAGE_LOOKBACK_MS)
    end_index = bisect.bisect_right(times, timestamp + DANGEROUS_DAMAGE_LOOKAHEAD_MS)
    ids: List[int] = []
    for _, ability_id in events[start_index:end_index]:
        if ability_id not in ids:
            ids.append(ability_id)
    return ids


def _group_dispels(events: Sequence[Dict[str, object]]) -> Dict[Tuple[object, object, int], List[Dict[str, object]]]:
    grouped: DefaultDict[Tuple[object, object, int], List[Dict[str, object]]] = defaultdict(list)
    for event in events:
        timestamp = _event_timestamp(event)
        if timestamp is None:
            continue
        grouped[(event.get("sourceID"), event.get("targetID"), int(round(timestamp)))].append(event)
    return dict(grouped)


def _companion_debuff_ids(
    event: Dict[str, object],
    dispels_by_group: Dict[Tuple[object, object, int], List[Dict[str, object]]],
) -> List[int]:
    timestamp = _event_timestamp(event)
    if timestamp is None:
        return []
    key = (event.get("sourceID"), event.get("targetID"), int(round(timestamp)))
    companion_ids: List[int] = []
    for candidate in dispels_by_group.get(key, []):
        if candidate is event:
            continue
        ability_id = _extra_ability_id(candidate)
        if ability_id is None or ability_id in NULL_CORONA_DEBUFF_IDS:
            continue
        if ability_id not in companion_ids:
            companion_ids.append(ability_id)
    return companion_ids


def _great_reason_labels(
    *,
    health: Optional[_HealthSnapshot],
    floor: float,
    ceiling: float,
    jumped_while_low: bool,
    companion_ids: Sequence[int],
    dangerous_ids: Sequence[int],
) -> List[str]:
    reasons: List[str] = []
    hp_percent = _health_percent(health)
    if jumped_while_low:
        reasons.append(f"Jumped onto target below {floor:g}% HP")
    if hp_percent is None or hp_percent < floor:
        return reasons
    if hp_percent <= ceiling:
        reasons.append(f"Target {floor:g}-{ceiling:g}% HP")
    if companion_ids:
        labels = ", ".join(_debuff_label(ability_id) for ability_id in companion_ids)
        reasons.append(f"Also removed {labels}")
    if dangerous_ids:
        labels = ", ".join(_debuff_label(ability_id) for ability_id in dangerous_ids)
        reasons.append(f"Near {labels} damage")
    return reasons


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[CrownNullCoronaDispelEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[CrownNullCoronaDispelEntry]:
    entries: List[CrownNullCoronaDispelEntry] = []
    for player in sorted(
        players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -sum(1 for event in events_by_player.get(name, []) if event.is_great),
            -len(events_by_player.get(name, [])),
            name.lower(),
        ),
    ):
        events = sorted(events_by_player.get(player, []), key=lambda item: item.timestamp)
        total = len(events)
        if total <= 0:
            continue
        great = sum(1 for event in events if event.is_great)
        hp_window = sum(1 for event in events if _has_reason_prefix(event, "Target "))
        low_jump = sum(1 for event in events if event.jumped_while_low)
        companion = sum(1 for event in events if event.companion_debuff_ids)
        danger = sum(1 for event in events if event.dangerous_damage_ability_ids)
        pulls = pulls_by_player.get(player, 0) or 1
        entries.append(
            CrownNullCoronaDispelEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_dispels=total,
                great_dispels=great,
                needs_review_dispels=total - great,
                great_rate=great / total if total else 0.0,
                hp_window_dispels=hp_window,
                low_jump_dispels=low_jump,
                companion_dispels=companion,
                danger_window_dispels=danger,
                events=events,
            )
        )
    return entries


def _merge_crown_null_corona_dispel_summaries(
    summaries: List[CrownNullCoronaDispelSummary],
) -> CrownNullCoronaDispelSummary:
    primary = summaries[0]
    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[CrownNullCoronaDispelEvent]] = defaultdict(list)
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

    players = set(combined_events.keys())
    entries = _build_entries(
        players=players,
        events_by_player=combined_events,
        pulls_by_player=combined_pulls,
        player_roles=combined_player_roles,
        player_classes=combined_player_classes,
    )
    totals = _summarize_totals(entries)
    player_events = {entry.player: entry.events for entry in entries}

    return CrownNullCoronaDispelSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=pull_count,
        hp_floor_percent=primary.hp_floor_percent,
        hp_ceiling_percent=primary.hp_ceiling_percent,
        total_dispels=totals["total"],
        great_dispels=totals["great"],
        needs_review_dispels=totals["review"],
        hp_window_dispels=totals["window"],
        low_jump_dispels=totals["low_jump"],
        companion_dispels=totals["companion"],
        danger_window_dispels=totals["danger"],
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        player_events=player_events,
        source_reports=source_reports,
    )


def _summarize_totals(entries: List[CrownNullCoronaDispelEntry]) -> Dict[str, int]:
    return {
        "total": sum(entry.total_dispels for entry in entries),
        "great": sum(entry.great_dispels for entry in entries),
        "review": sum(entry.needs_review_dispels for entry in entries),
        "window": sum(entry.hp_window_dispels for entry in entries),
        "low_jump": sum(entry.low_jump_dispels for entry in entries),
        "companion": sum(entry.companion_dispels for entry in entries),
        "danger": sum(entry.danger_window_dispels for entry in entries),
    }


def _has_reason_prefix(event: CrownNullCoronaDispelEvent, prefix: str) -> bool:
    return any(reason.startswith(prefix) for reason in event.reason_labels)


def _health_snapshot(event: Dict[str, object], timestamp: float) -> Optional[_HealthSnapshot]:
    hit_points = _coerce_float(event.get("hitPoints"))
    max_hit_points = _coerce_float(event.get("maxHitPoints"))
    if hit_points is None or max_hit_points is None or max_hit_points <= 0:
        return None
    return _HealthSnapshot(timestamp=timestamp, hit_points=hit_points, max_hit_points=max_hit_points)


def _health_percent(snapshot: Optional[_HealthSnapshot]) -> Optional[float]:
    if not snapshot or snapshot.max_hit_points <= 0:
        return None
    return snapshot.hit_points / snapshot.max_hit_points * 100.0


def _source_name(event: Dict[str, object], actor_names: Dict[int, str]) -> Optional[str]:
    name = event.get("sourceName")
    if name:
        return str(name)
    return _actor_name(event.get("sourceID"), actor_names)


def _target_name(event: Dict[str, object], actor_names: Dict[int, str]) -> Optional[str]:
    name = event.get("targetName")
    if name:
        return str(name)
    return _actor_name(event.get("targetID"), actor_names)


def _actor_name(actor_id: object, actor_names: Dict[int, str]) -> Optional[str]:
    try:
        return actor_names.get(int(actor_id))
    except (TypeError, ValueError):
        return None


def _event_timestamp(event: Dict[str, object]) -> Optional[float]:
    return _coerce_float(event.get("timestamp"))


def _ability_id(event: Dict[str, object]) -> Optional[int]:
    return _coerce_int(event.get("abilityGameID"))


def _extra_ability_id(event: Dict[str, object]) -> Optional[int]:
    return _coerce_int(event.get("extraAbilityGameID"))


def _dispel_ability_label(ability_id: Optional[int]) -> Optional[str]:
    if ability_id is None:
        return None
    return DISPEL_CAST_ABILITY_LABELS.get(ability_id, f"Spell {ability_id}")


def _debuff_label(ability_id: int) -> str:
    return DEBUFF_LABELS.get(ability_id, f"Spell {ability_id}")


def _normalize_hp_window(floor_value: Optional[float], ceiling_value: Optional[float]) -> Tuple[float, float]:
    floor = _normalize_hp_percent(floor_value, default=DEFAULT_HP_FLOOR_PERCENT, field_name="hp_floor_percent")
    ceiling = _normalize_hp_percent(ceiling_value, default=DEFAULT_HP_CEILING_PERCENT, field_name="hp_ceiling_percent")
    if floor > ceiling:
        raise ValueError("hp_floor_percent must be less than or equal to hp_ceiling_percent.")
    return floor, ceiling


def _normalize_hp_percent(value: Optional[float], *, default: float, field_name: str) -> float:
    if value is None:
        return default
    try:
        percent = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number.") from exc
    if percent < 0 or percent > 100:
        raise ValueError(f"{field_name} must be between 0 and 100.")
    return percent


def _coerce_float(value: object) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _coerce_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


__all__ = [
    "BURSTING_EMPTINESS_ID",
    "CORRUPTING_ESSENCE_ID",
    "CrownNullCoronaDispelEntry",
    "CrownNullCoronaDispelEvent",
    "CrownNullCoronaDispelSummary",
    "DEFAULT_HP_CEILING_PERCENT",
    "DEFAULT_HP_FLOOR_PERCENT",
    "GRASP_OF_EMPTINESS_ID",
    "NULL_CORONA_DEBUFF_IDS",
    "NULL_CORONA_INITIAL_ID",
    "NULL_CORONA_JUMP_ID",
    "REPORT_DEFAULT_FIGHT",
    "fetch_crown_of_the_cosmos_null_corona_dispel_summary",
]
