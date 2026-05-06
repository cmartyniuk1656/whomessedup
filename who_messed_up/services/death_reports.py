"""
Shared death-report summary helpers.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Set, Tuple, Union

import requests

from ..api import REPORT_OVERVIEW_QUERY, fetch_events, fetch_fights, fetch_player_details, gql
from ..env import load_env
from .boss_manifest_types import BossAbilityMetadata, BossManifest, is_avoidable_for_role
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
from .consumables import (
    DEATH_REPORT_HEALING_CONSUMABLES,
    HealingConsumableStatus,
    build_healing_consumable_statuses,
    collect_healing_consumable_uses,
)

BATTLE_RESURRECTION_SPELL_IDS = {
    20484,  # Rebirth
    61999,  # Raise Ally
    20707,  # Soulstone
    391054,  # Intercession
}


@dataclass
class DeathReportDamageHit:
    source_report_code: Optional[str]
    timestamp: float
    offset_ms: float
    ability_id: Optional[int]
    ability_label: Optional[str]
    damage_amount: Optional[float]
    max_hit_points: Optional[float]
    hit_points_percent: Optional[float]
    ability_description: Optional[str] = None
    ability_url: Optional[str] = None
    ability_tags: Tuple[str, ...] = ()
    is_killing_blow: bool = False
    is_avoidable: bool = False


@dataclass
class DeathReportEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    ability_id: Optional[int]
    ability_label: Optional[str]
    damage_amount: Optional[float] = None
    recent_hits: List[DeathReportDamageHit] = field(default_factory=list)
    consumables: List[HealingConsumableStatus] = field(default_factory=list)
    label: Optional[str] = None
    description: Optional[str] = None
    pull_duration_ms: Optional[float] = None


@dataclass
class DeathReportEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    deaths: int
    avoidable_deaths: int
    death_rate: float
    events: List[DeathReportEvent]


@dataclass
class DeathReportSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    ignore_unavoidable_after_healer_deaths: Optional[int]
    total_deaths: int
    total_avoidable_deaths: int
    entries: List[DeathReportEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[DeathReportEvent]]
    ability_labels: Dict[int, str]
    source_reports: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class HealerLifeEvent:
    timestamp: float
    player_key: str
    event_type: str


def fetch_death_report_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ignore_after_deaths: Optional[int] = None,
    ignore_unavoidable_after_healer_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    boss_manifest: Optional[BossManifest] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DeathReportSummary:
    primary_code = _sanitize_report_code(report_code)
    primary_summary = _fetch_single_death_report_summary(
        report_code=primary_code,
        fight_name=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
        ignore_after_deaths=ignore_after_deaths,
        ignore_unavoidable_after_healer_deaths=ignore_unavoidable_after_healer_deaths,
        boss_manifest=boss_manifest,
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
            _fetch_single_death_report_summary(
                report_code=code,
                fight_name=fight_name,
                fight_ids=fight_ids,
                difficulty=difficulty,
                ignore_after_deaths=ignore_after_deaths,
                ignore_unavoidable_after_healer_deaths=ignore_unavoidable_after_healer_deaths,
                boss_manifest=boss_manifest,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    return _merge_death_report_summaries(summaries)


def _fetch_single_death_report_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ignore_after_deaths: Optional[int] = None,
    ignore_unavoidable_after_healer_deaths: Optional[int] = None,
    boss_manifest: Optional[BossManifest] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DeathReportSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)

    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
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
    healer_death_limit = (
        ignore_unavoidable_after_healer_deaths
        if ignore_unavoidable_after_healer_deaths and ignore_unavoidable_after_healer_deaths > 0
        else None
    )
    pull_index_by_fight: Dict[int, int] = {fight.id: idx + 1 for idx, fight in enumerate(chosen)}
    ability_labels = _fetch_ability_labels(session, bearer, report_code)
    events_by_player: DefaultDict[str, List[DeathReportEvent]] = defaultdict(list)
    death_counts: DefaultDict[str, int] = defaultdict(int)
    consumable_usage_by_fight = collect_healing_consumable_uses(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        ability_names=[consumable.ability_name for consumable in DEATH_REPORT_HEALING_CONSUMABLES],
        actor_names=actor_names,
    )

    for fight in chosen:
        pull_duration = compute_fight_duration_ms(fight)
        fight_consumables = consumable_usage_by_fight.get(fight.id, {})
        fight_roles = roles_by_fight.get(fight.id, player_roles)
        recent_damage_hits = collect_recent_damage_hits(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            ability_labels=ability_labels,
            boss_manifest=boss_manifest,
            player_roles=fight_roles,
        )
        counted_deaths = 0
        death_events = sorted(
            fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="Deaths",
                start=fight.start,
                end=fight.end,
                actor_names=actor_names,
            ),
            key=_event_timestamp,
        )
        healer_life_events = collect_healer_life_events(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            death_events=death_events,
            actor_names=actor_names,
            fight_roles=fight_roles,
            player_roles=player_roles,
        )
        dead_healers: Set[str] = set()
        healer_life_index = 0
        for event in death_events:
            event_type = str(event.get("type") or "").lower()
            if event_type not in {"death", "instakill"}:
                continue
            timestamp = event.get("timestamp")
            if timestamp is None:
                continue
            try:
                ts_val = float(timestamp)
            except (TypeError, ValueError):
                continue

            target_name = _target_name_from_event(event)
            if not target_name:
                continue
            if death_limit is not None:
                counted_deaths += 1
                if counted_deaths > death_limit:
                    continue
            healer_life_index = apply_healer_life_events_before(
                healer_life_events,
                healer_life_index,
                dead_healers,
                ts_val,
            )
            target_role = fight_roles.get(target_name) or player_roles.get(target_name)

            ability_id, ability_label = resolve_killing_ability(event, ability_labels)
            killing_damage = resolve_killing_damage(event)
            offset_ms = ts_val - float(fight.start)
            recent_hits = recent_hits_for_death(
                recent_damage_hits.get(target_name, []),
                death_timestamp=ts_val,
                death_offset_ms=offset_ms,
                ability_id=ability_id,
                ability_label=ability_label,
                damage_amount=killing_damage,
                source_report_code=report_code,
                boss_manifest=boss_manifest,
                player_role=target_role,
            )
            death_event = DeathReportEvent(
                source_report_code=report_code,
                player=target_name,
                fight_id=fight.id,
                fight_name=fight.name or "",
                pull_index=pull_index_by_fight.get(fight.id, 0),
                timestamp=ts_val,
                offset_ms=offset_ms,
                ability_id=int(ability_id) if ability_id is not None else None,
                ability_label=ability_label,
                damage_amount=killing_damage,
                recent_hits=recent_hits,
                consumables=build_healing_consumable_statuses(
                    fight_consumables.get(target_name),
                    fight_start=fight.start,
                    reference_timestamp=ts_val,
                ),
                label="Death",
                pull_duration_ms=pull_duration,
            )
            filter_unavoidable_after_healer_deaths = (
                healer_death_limit is not None
                and len(dead_healers) >= healer_death_limit
                and not is_avoidable_death_event(death_event)
            )
            if not filter_unavoidable_after_healer_deaths:
                death_counts[target_name] += 1
                events_by_player[target_name].append(death_event)

    pull_count = len(chosen)
    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    all_players = set(pulls_by_player.keys()) | set(events_by_player.keys())
    if not all_players and participants_by_fight:
        for participants in participants_by_fight.values():
            all_players.update(participants)

    entries: List[DeathReportEntry] = []
    total_deaths = 0
    total_avoidable_deaths = 0
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
        player_events = sorted(events_by_player.get(player, []), key=lambda evt: evt.timestamp)
        avoidable_deaths = count_avoidable_death_events(player_events)
        total_avoidable_deaths += avoidable_deaths
        entries.append(
            DeathReportEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=name_to_class.get(player),
                pulls=pulls,
                deaths=deaths,
                avoidable_deaths=avoidable_deaths,
                death_rate=deaths / pulls if pulls else 0.0,
                events=player_events,
            )
        )

    return DeathReportSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=pull_count,
        ignore_after_deaths=death_limit,
        ignore_unavoidable_after_healer_deaths=healer_death_limit,
        total_deaths=total_deaths,
        total_avoidable_deaths=total_avoidable_deaths,
        entries=entries,
        player_classes={player: name_to_class.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        player_events={player: list(events) for player, events in events_by_player.items()},
        ability_labels=ability_labels,
        source_reports=[report_code],
    )


def _merge_death_report_summaries(summaries: List[DeathReportSummary]) -> DeathReportSummary:
    primary = summaries[0]
    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_deaths: DefaultDict[str, int] = defaultdict(int)
    combined_avoidable_deaths: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[DeathReportEvent]] = defaultdict(list)
    combined_ability_labels: Dict[int, str] = {}
    combined_pull_count = 0
    source_reports: List[str] = []

    for summary in summaries:
        combined_pull_count += summary.pull_count
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)

        for ability_id, label in summary.ability_labels.items():
            combined_ability_labels.setdefault(ability_id, label)

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
            combined_deaths[entry.player] += entry.deaths
            combined_avoidable_deaths[entry.player] += getattr(
                entry,
                "avoidable_deaths",
                count_avoidable_death_events(entry.events),
            )
            combined_events[entry.player].extend(entry.events)
            if combined_player_classes.get(entry.player) is None:
                combined_player_classes[entry.player] = entry.class_name
            current_role = combined_player_roles.get(entry.player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[entry.player] = entry.role or ROLE_UNKNOWN

    players = sorted(
        set(combined_pulls.keys()) | set(combined_deaths.keys()) | set(combined_events.keys()),
        key=lambda name: (
            ROLE_PRIORITY.get(combined_player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -combined_deaths.get(name, 0),
            name.lower(),
        ),
    )

    entries: List[DeathReportEntry] = []
    total_deaths = 0
    total_avoidable_deaths = 0
    player_events: Dict[str, List[DeathReportEvent]] = {}
    for player in players:
        pulls = combined_pulls.get(player, combined_pull_count)
        if pulls <= 0:
            pulls = combined_pull_count or 1
        deaths = combined_deaths.get(player, 0)
        total_deaths += deaths
        avoidable_deaths = combined_avoidable_deaths.get(player, 0)
        total_avoidable_deaths += avoidable_deaths
        events = sorted(combined_events.get(player, []), key=lambda evt: (evt.source_report_code or "", evt.timestamp))
        player_events[player] = events
        role = combined_player_roles.get(player) or ROLE_UNKNOWN
        entries.append(
            DeathReportEntry(
                player=player,
                role=role,
                class_name=combined_player_classes.get(player),
                pulls=pulls,
                deaths=deaths,
                avoidable_deaths=avoidable_deaths,
                death_rate=deaths / pulls if pulls else 0.0,
                events=events,
            )
        )

    return DeathReportSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=combined_pull_count,
        ignore_after_deaths=primary.ignore_after_deaths,
        ignore_unavoidable_after_healer_deaths=primary.ignore_unavoidable_after_healer_deaths,
        total_deaths=total_deaths,
        total_avoidable_deaths=total_avoidable_deaths,
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        player_events=player_events,
        ability_labels=combined_ability_labels,
        source_reports=source_reports,
    )


def is_avoidable_death_event(event: object) -> bool:
    for hit in getattr(event, "recent_hits", []) or []:
        if getattr(hit, "is_killing_blow", False):
            return bool(getattr(hit, "is_avoidable", False))
    return False


def count_avoidable_death_events(events: Iterable[object]) -> int:
    return sum(1 for event in events or [] if is_avoidable_death_event(event))


def collect_healer_life_events(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    death_events: Iterable[Dict[str, Any]],
    actor_names: Dict[int, str],
    fight_roles: Dict[str, str],
    player_roles: Dict[str, str],
) -> List[HealerLifeEvent]:
    life_events: List[HealerLifeEvent] = []
    for event in death_events:
        event_type = str(event.get("type") or "").lower()
        if event_type not in {"death", "instakill", "resurrect"}:
            continue
        target_name = _target_name_from_event(event)
        if not target_name or _role_for_player(target_name, fight_roles, player_roles) != "Healer":
            continue
        normalized_type = "resurrect" if event_type == "resurrect" else "death"
        life_events.append(
            HealerLifeEvent(
                timestamp=_event_timestamp(event),
                player_key=_normalize_player_name(target_name),
                event_type=normalized_type,
            )
        )

    life_events.extend(
        collect_healer_resurrection_cast_events(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            fight_roles=fight_roles,
            player_roles=player_roles,
        )
    )
    return sorted(life_events, key=lambda item: (item.timestamp, 0 if item.event_type == "death" else 1))


def collect_healer_resurrection_cast_events(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    fight_roles: Dict[str, str],
    player_roles: Dict[str, str],
) -> List[HealerLifeEvent]:
    life_events: List[HealerLifeEvent] = []
    filter_expr = _build_spell_filter(BATTLE_RESURRECTION_SPELL_IDS)
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Casts",
        start=fight.start,
        end=fight.end,
        limit=1000,
        extra_filter=filter_expr,
        actor_names=actor_names,
    ):
        target_name = _target_name_from_event(event)
        if not target_name or _role_for_player(target_name, fight_roles, player_roles) != "Healer":
            continue
        life_events.append(
            HealerLifeEvent(
                timestamp=_event_timestamp(event),
                player_key=_normalize_player_name(target_name),
                event_type="resurrect",
            )
        )
    return life_events


def apply_healer_life_events_before(
    life_events: List[HealerLifeEvent],
    start_index: int,
    dead_healers: Set[str],
    timestamp: float,
) -> int:
    index = start_index
    while index < len(life_events) and life_events[index].timestamp < timestamp:
        event = life_events[index]
        if event.event_type == "death":
            dead_healers.add(event.player_key)
        elif event.event_type == "resurrect":
            dead_healers.discard(event.player_key)
        index += 1
    return index


def resolve_killing_ability(event: Dict[str, object], ability_labels: Dict[int, str]) -> Tuple[Optional[int], Optional[str]]:
    ability_obj = event.get("killingAbility")
    ability_id = None
    ability_name = None
    if isinstance(ability_obj, dict):
        ability_id = _normalize_ability_id(ability_obj.get("id"))
        ability_name = ability_obj.get("name")
    if ability_id is None:
        ability_id = _normalize_ability_id(event.get("killingAbilityGameID"))
    if ability_id is None:
        ability_id = _normalize_ability_id(event.get("abilityGameID"))
    if ability_name is None and ability_id is not None:
        ability_name = ability_labels.get(ability_id)
    if ability_name is None:
        generic_ability = event.get("ability")
        if isinstance(generic_ability, dict):
            ability_name = generic_ability.get("name")
    if ability_name and ability_id is not None and ability_id not in ability_labels:
        ability_labels[ability_id] = ability_name
    return ability_id, ability_name


def resolve_killing_damage(event: Dict[str, object]) -> Optional[float]:
    for field in ("killingDamage", "killingDamageAmount", "killingHitAmount"):
        value = event.get(field)
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
        if isinstance(value, str):
            try:
                numeric = float(value)
            except ValueError:
                continue
            if numeric > 0:
                return numeric
    return resolve_damage_amount(event)


def resolve_damage_amount(event: Dict[str, object]) -> Optional[float]:
    amount = _coerce_float(event.get("amount"))
    if amount is None or amount <= 0:
        return None
    overkill = _coerce_float(event.get("overkill"))
    if overkill and overkill > 0:
        amount += overkill
    return amount


def collect_recent_damage_hits(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    ability_labels: Dict[int, str],
    boss_manifest: Optional[BossManifest] = None,
    player_roles: Optional[Dict[str, str]] = None,
) -> Dict[str, List[DeathReportDamageHit]]:
    hits_by_player: DefaultDict[str, List[DeathReportDamageHit]] = defaultdict(list)
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="DamageTaken",
        start=fight.start,
        end=fight.end,
        actor_names=actor_names,
        include_resources=True,
    ):
        timestamp = event.get("timestamp")
        if timestamp is None:
            continue
        try:
            ts_val = float(timestamp)
        except (TypeError, ValueError):
            continue

        target_name = _target_name_from_event(event)
        if not target_name:
            continue

        damage_amount = resolve_damage_amount(event)
        if damage_amount is None or damage_amount <= 0:
            continue

        ability_id, ability_label = resolve_damage_ability(event, ability_labels)
        ability_metadata = _ability_metadata(
            ability_id=ability_id,
            ability_label=ability_label,
            boss_manifest=boss_manifest,
        )
        player_role = player_roles.get(target_name) if player_roles else None
        max_hit_points = resolve_max_hit_points(event)
        hits_by_player[target_name].append(
            DeathReportDamageHit(
                source_report_code=report_code,
                timestamp=ts_val,
                offset_ms=ts_val - float(fight.start),
                ability_id=ability_id,
                ability_label=ability_label,
                damage_amount=damage_amount,
                max_hit_points=max_hit_points,
                hit_points_percent=(damage_amount / max_hit_points * 100.0) if max_hit_points else None,
                ability_description=ability_metadata.description if ability_metadata else None,
                ability_url=ability_metadata.url if ability_metadata else None,
                ability_tags=tuple(ability_metadata.tags) if ability_metadata else (),
                is_avoidable=is_avoidable_for_role(ability_metadata, player_role),
            )
        )

    for hits in hits_by_player.values():
        hits.sort(key=lambda hit: hit.timestamp)
    return hits_by_player


def recent_hits_for_death(
    player_hits: List[DeathReportDamageHit],
    *,
    death_timestamp: float,
    death_offset_ms: float,
    ability_id: Optional[int],
    ability_label: Optional[str],
    damage_amount: Optional[float],
    source_report_code: Optional[str],
    boss_manifest: Optional[BossManifest] = None,
    player_role: Optional[str] = None,
    hit_count: int = 3,
) -> List[DeathReportDamageHit]:
    candidates = [hit for hit in player_hits if hit.timestamp <= death_timestamp]
    recent_hits = candidates[-hit_count:]
    if not recent_hits and (ability_label or damage_amount):
        ability_metadata = _ability_metadata(
            ability_id=ability_id,
            ability_label=ability_label,
            boss_manifest=boss_manifest,
        )
        recent_hits = [
            DeathReportDamageHit(
                source_report_code=source_report_code,
                timestamp=death_timestamp,
                offset_ms=death_offset_ms,
                ability_id=ability_id,
                ability_label=ability_label,
                damage_amount=damage_amount,
                max_hit_points=None,
                hit_points_percent=None,
                ability_description=ability_metadata.description if ability_metadata else None,
                ability_url=ability_metadata.url if ability_metadata else None,
                ability_tags=tuple(ability_metadata.tags) if ability_metadata else (),
                is_avoidable=is_avoidable_for_role(ability_metadata, player_role),
            )
        ]

    if not recent_hits:
        return []

    kill_index = _find_killing_hit_index(
        recent_hits,
        ability_id=ability_id,
        damage_amount=damage_amount,
    )
    return [
        DeathReportDamageHit(
            source_report_code=hit.source_report_code,
            timestamp=hit.timestamp,
            offset_ms=hit.offset_ms,
            ability_id=hit.ability_id,
            ability_label=hit.ability_label,
            damage_amount=hit.damage_amount,
            max_hit_points=hit.max_hit_points,
            hit_points_percent=hit.hit_points_percent,
            ability_description=hit.ability_description,
            ability_url=hit.ability_url,
            ability_tags=tuple(hit.ability_tags),
            is_killing_blow=index == kill_index,
            is_avoidable=hit.is_avoidable,
        )
        for index, hit in enumerate(recent_hits)
    ]


def resolve_damage_ability(event: Dict[str, object], ability_labels: Dict[int, str]) -> Tuple[Optional[int], Optional[str]]:
    ability_id = _normalize_ability_id(event.get("abilityGameID"))
    ability_name = None
    ability_obj = event.get("ability")
    if isinstance(ability_obj, dict):
        if ability_id is None:
            ability_id = _normalize_ability_id(ability_obj.get("gameID") or ability_obj.get("id"))
        ability_name = ability_obj.get("name")
    if ability_name is None and ability_id is not None:
        ability_name = ability_labels.get(ability_id)
    if ability_name and ability_id is not None and ability_id not in ability_labels:
        ability_labels[ability_id] = ability_name
    return ability_id, ability_name


def _ability_metadata(
    *,
    ability_id: Optional[int],
    ability_label: Optional[str],
    boss_manifest: Optional[BossManifest],
) -> Optional[BossAbilityMetadata]:
    if not boss_manifest:
        return None
    return boss_manifest.ability_for(
        ability_id=ability_id,
        ability_name=ability_label,
    )


def _is_avoidable_metadata(ability_metadata: Optional[BossAbilityMetadata]) -> bool:
    return is_avoidable_for_role(ability_metadata, None)


def resolve_max_hit_points(event: Dict[str, object]) -> Optional[float]:
    for resources in (
        event.get("targetResources"),
        event.get("resources"),
        (event.get("target") or {}).get("resources") if isinstance(event.get("target"), dict) else None,
    ):
        if not isinstance(resources, dict):
            continue
        for field in ("maxHitPoints", "maxHitpoints", "maxHP", "maxHp"):
            value = _coerce_float(resources.get(field))
            if value and value > 0:
                return value
    return None


def _find_killing_hit_index(
    hits: List[DeathReportDamageHit],
    *,
    ability_id: Optional[int],
    damage_amount: Optional[float],
) -> int:
    fallback_index = len(hits) - 1
    for index in range(len(hits) - 1, -1, -1):
        hit = hits[index]
        if ability_id is not None and hit.ability_id != ability_id:
            continue
        if damage_amount is not None and hit.damage_amount is not None:
            tolerance = max(abs(damage_amount) * 0.01, 1.0)
            if abs(hit.damage_amount - damage_amount) > tolerance:
                continue
        return index
    return fallback_index


def _coerce_float(value: object) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _target_name_from_event(event: Dict[str, object]) -> Optional[str]:
    target_name = event.get("targetName")
    if not target_name and isinstance(event.get("target"), dict):
        target_name = event["target"].get("name")
    return str(target_name) if target_name else None


def _event_timestamp(event: Dict[str, object]) -> float:
    try:
        return float(event.get("timestamp") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_player_name(value: object) -> str:
    return str(value or "").strip().casefold()


def _role_for_player(player: str, fight_roles: Dict[str, str], player_roles: Dict[str, str]) -> str:
    player_key = _normalize_player_name(player)
    for name, role in fight_roles.items():
        if _normalize_player_name(name) == player_key:
            return role or ROLE_UNKNOWN
    for name, role in player_roles.items():
        if _normalize_player_name(name) == player_key:
            return role or ROLE_UNKNOWN
    return ROLE_UNKNOWN


def _build_spell_filter(spell_ids: Set[int]) -> str:
    parts = []
    for spell_id in sorted(spell_ids):
        parts.append(f"(ability.id = {int(spell_id)} or abilityGameID = {int(spell_id)})")
    return " or ".join(parts)


def _normalize_ability_id(raw: Optional[Union[int, str]]) -> Optional[int]:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def _fetch_ability_labels(session, bearer: str, report_code: str) -> Dict[int, str]:
    labels: Dict[int, str] = {}
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
    "DeathReportEntry",
    "DeathReportEvent",
    "DeathReportDamageHit",
    "DeathReportSummary",
    "HealerLifeEvent",
    "apply_healer_life_events_before",
    "collect_healer_life_events",
    "collect_healer_resurrection_cast_events",
    "collect_recent_damage_hits",
    "count_avoidable_death_events",
    "fetch_death_report_summary",
    "is_avoidable_death_event",
    "recent_hits_for_death",
    "resolve_damage_amount",
    "resolve_damage_ability",
    "resolve_killing_ability",
    "resolve_killing_damage",
    "resolve_max_hit_points",
]
