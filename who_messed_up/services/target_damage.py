"""
Reusable encounter target-damage summaries for v2 reports.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import DefaultDict, Dict, Iterable, List, Optional, Set

import requests

from ..api import fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_event_source_player,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
)


class EncounterTargetBucket(str, Enum):
    BOSS = "boss"
    PRIORITY_ADD = "priority_add"
    PAD_ADD = "pad_add"


@dataclass(frozen=True)
class EncounterTargetConfig:
    slug: str
    label: str
    enemy_name: str
    bucket: Optional[EncounterTargetBucket] = None


@dataclass
class EncounterTargetDamageBreakdown:
    target: str
    label: str
    total_damage: float
    average_damage: float


@dataclass
class EncounterTargetDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float
    target_totals: Dict[str, EncounterTargetDamageBreakdown]


@dataclass
class EncounterTargetSummary:
    target: str
    label: str
    bucket: Optional[EncounterTargetBucket]
    total_damage: float
    avg_damage_per_pull: float


@dataclass
class EncounterTargetDamageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    entries: List[EncounterTargetDamageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    pull_count: int
    total_damage: float
    avg_damage_per_pull: float
    targets: List[EncounterTargetSummary]
    kill_only: bool = False
    omit_dead_players: bool = False


def fetch_encounter_target_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    target_configs: Dict[str, EncounterTargetConfig],
    targets: Optional[Iterable[str]] = None,
    default_target_slugs: Optional[Iterable[str]] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    kill_only: bool = False,
    omit_dead_players: bool = False,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> EncounterTargetDamageSummary:
    primary_code = _sanitize_report_code(report_code)
    primary_summary = _fetch_single_encounter_target_damage_summary(
        report_code=primary_code,
        fight_name=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
        target_configs=target_configs,
        targets=targets,
        default_target_slugs=default_target_slugs,
        kill_only=kill_only,
        omit_dead_players=omit_dead_players,
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
            _fetch_single_encounter_target_damage_summary(
                report_code=code,
                fight_name=fight_name,
                fight_ids=fight_ids,
                difficulty=difficulty,
                target_configs=target_configs,
                targets=targets,
                default_target_slugs=default_target_slugs,
                kill_only=kill_only,
                omit_dead_players=omit_dead_players,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    return _merge_encounter_target_damage_summaries(summaries)


def _fetch_single_encounter_target_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    target_configs: Dict[str, EncounterTargetConfig],
    targets: Optional[Iterable[str]] = None,
    default_target_slugs: Optional[Iterable[str]] = None,
    kill_only: bool = False,
    omit_dead_players: bool = False,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> EncounterTargetDamageSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)

    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    known_players = {
        name
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    if kill_only:
        chosen = [fight for fight in chosen if fight.kill]
    fight_id_list = [fight.id for fight in chosen]

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    participants_by_fight: Dict[int, Set[str]] = {}
    dead_players_by_fight: Dict[int, Set[str]] = {}
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    eligible_players: Set[str] = set()
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        dead_players = (
            _collect_dead_players_in_fight(
                session,
                bearer,
                report_code=report_code,
                fight=fight,
                actor_names=actor_names,
                known_players=known_players,
            )
            if omit_dead_players
            else set()
        )
        dead_players_by_fight[fight.id] = dead_players
        fight_participants = {
            name
            for name in set(_players_from_details(details))
            if name and name in known_players and name not in dead_players
        }
        participants_by_fight[fight.id] = fight_participants
        if fight_roles:
            roles_by_fight[fight.id] = {
                player: role for player, role in fight_roles.items() if player in fight_participants
            }
        for name in fight_participants:
            eligible_players.add(name)
            pulls_by_player[name] += 1

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

    active_targets = _resolve_targets(
        values=targets,
        target_configs=target_configs,
        default_target_slugs=default_target_slugs,
    )
    selected_slugs = [cfg.slug for cfg in active_targets]

    damage_totals: DefaultDict[str, float] = defaultdict(float)
    per_target_totals: Dict[str, DefaultDict[str, float]] = {
        slug: defaultdict(float) for slug in selected_slugs
    }
    target_summary_totals: DefaultDict[str, float] = defaultdict(float)

    for fight in chosen:
        dead_players = dead_players_by_fight.get(fight.id, set())
        fight_participants = participants_by_fight.get(fight.id, set())
        fight_damage_maps: Dict[str, Dict[str, float]] = {}
        for cfg in active_targets:
            damage_map = _collect_target_damage(
                session,
                bearer,
                report_code=report_code,
                fight_start=fight.start,
                fight_end=fight.end,
                actor_names=actor_names,
                actor_classes=actor_classes,
                actor_owners=actor_owners,
                player_classes=player_classes,
                player_roles=player_roles,
                player_specs=player_specs,
                known_players=known_players,
                role_defaults=roles_by_fight.get(fight.id, {}),
                global_specs=player_specs_global,
                target_name=cfg.enemy_name,
            )
            if dead_players:
                damage_map = {
                    player: total for player, total in damage_map.items() if player not in dead_players
                }
            fight_damage_maps[cfg.slug] = damage_map

        for player in fight_participants:
            combined = 0.0
            for slug in selected_slugs:
                combined += fight_damage_maps.get(slug, {}).get(player, 0.0)
            damage_totals[player] += combined

        for cfg in active_targets:
            damage_map = fight_damage_maps.get(cfg.slug, {})
            if not damage_map:
                continue
            for player, total in damage_map.items():
                if total <= 0:
                    continue
                per_target_totals[cfg.slug][player] += total
                target_summary_totals[cfg.slug] += total

    players = sorted(
        (eligible_players | set(damage_totals.keys())) & known_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            name.lower(),
        ),
    )

    entries: List[EncounterTargetDamageEntry] = []
    for player in players:
        pulls = pulls_by_player.get(player, len(chosen))
        if pulls <= 0:
            pulls = len(chosen)
        role = player_roles.get(player) or ROLE_UNKNOWN
        total_damage = float(damage_totals.get(player, 0.0))
        average_damage = total_damage / pulls if pulls else 0.0
        target_breakdowns: Dict[str, EncounterTargetDamageBreakdown] = {}
        for cfg in active_targets:
            player_target_total = per_target_totals[cfg.slug].get(player, 0.0)
            target_breakdowns[cfg.slug] = EncounterTargetDamageBreakdown(
                target=cfg.slug,
                label=cfg.label,
                total_damage=player_target_total,
                average_damage=player_target_total / pulls if pulls else 0.0,
            )
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, player_specs_global.get(player))
        entries.append(
            EncounterTargetDamageEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=average_damage,
                target_totals=target_breakdowns,
            )
        )

    total_damage_amount = sum(entry.total_damage for entry in entries)
    pull_count = len(chosen)
    target_summaries = [
        EncounterTargetSummary(
            target=cfg.slug,
            label=cfg.label,
            bucket=cfg.bucket,
            total_damage=target_summary_totals.get(cfg.slug, 0.0),
            avg_damage_per_pull=target_summary_totals.get(cfg.slug, 0.0) / pull_count if pull_count else 0.0,
        )
        for cfg in active_targets
    ]

    return EncounterTargetDamageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        pull_count=pull_count,
        total_damage=total_damage_amount,
        avg_damage_per_pull=total_damage_amount / pull_count if pull_count else 0.0,
        targets=target_summaries,
        kill_only=kill_only,
        omit_dead_players=omit_dead_players,
    )


def _merge_encounter_target_damage_summaries(
    summaries: List[EncounterTargetDamageSummary],
) -> EncounterTargetDamageSummary:
    primary = summaries[0]
    target_order = [target.target for target in primary.targets]
    target_labels = {target.target: target.label for target in primary.targets}
    target_buckets = {target.target: target.bucket for target in primary.targets}

    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_damage: DefaultDict[str, float] = defaultdict(float)
    combined_target_totals: Dict[str, DefaultDict[str, float]] = {
        slug: defaultdict(float) for slug in target_order
    }
    combined_target_summaries: DefaultDict[str, float] = defaultdict(float)
    combined_pull_count = 0

    for summary in summaries:
        combined_pull_count += summary.pull_count

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

        for target in summary.targets:
            target_labels.setdefault(target.target, target.label)
            target_buckets.setdefault(target.target, target.bucket)
            combined_target_summaries[target.target] += target.total_damage

        for entry in summary.entries:
            combined_pulls[entry.player] += entry.pulls
            combined_damage[entry.player] += entry.total_damage
            if combined_player_classes.get(entry.player) is None:
                combined_player_classes[entry.player] = entry.class_name
            current_role = combined_player_roles.get(entry.player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[entry.player] = entry.role or ROLE_UNKNOWN
            for target_slug in target_order:
                breakdown = entry.target_totals.get(target_slug)
                if breakdown:
                    combined_target_totals[target_slug][entry.player] += breakdown.total_damage

    players = sorted(
        set(combined_pulls.keys()) | set(combined_damage.keys()) | set(combined_player_roles.keys()),
        key=lambda name: (
            ROLE_PRIORITY.get(combined_player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            name.lower(),
        ),
    )

    entries: List[EncounterTargetDamageEntry] = []
    for player in players:
        pulls = combined_pulls.get(player, combined_pull_count)
        if pulls <= 0:
            pulls = combined_pull_count
        role = combined_player_roles.get(player) or ROLE_UNKNOWN
        total_damage = float(combined_damage.get(player, 0.0))
        target_breakdowns: Dict[str, EncounterTargetDamageBreakdown] = {}
        for target_slug in target_order:
            player_target_total = combined_target_totals[target_slug].get(player, 0.0)
            target_breakdowns[target_slug] = EncounterTargetDamageBreakdown(
                target=target_slug,
                label=target_labels.get(target_slug, target_slug),
                total_damage=player_target_total,
                average_damage=player_target_total / pulls if pulls else 0.0,
            )
        entries.append(
            EncounterTargetDamageEntry(
                player=player,
                role=role,
                class_name=combined_player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=total_damage / pulls if pulls else 0.0,
                target_totals=target_breakdowns,
            )
        )

    total_damage_amount = sum(entry.total_damage for entry in entries)
    targets = [
        EncounterTargetSummary(
            target=target_slug,
            label=target_labels.get(target_slug, target_slug),
            bucket=target_buckets.get(target_slug),
            total_damage=combined_target_summaries.get(target_slug, 0.0),
            avg_damage_per_pull=(
                combined_target_summaries.get(target_slug, 0.0) / combined_pull_count if combined_pull_count else 0.0
            ),
        )
        for target_slug in target_order
    ]

    return EncounterTargetDamageSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        pull_count=combined_pull_count,
        total_damage=total_damage_amount,
        avg_damage_per_pull=total_damage_amount / combined_pull_count if combined_pull_count else 0.0,
        targets=targets,
        kill_only=primary.kill_only,
        omit_dead_players=primary.omit_dead_players,
    )


def _collect_dead_players_in_fight(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    known_players: Set[str],
) -> Set[str]:
    dead_players: Set[str] = set()
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
        event_type = (event.get("type") or "").lower()
        if event_type not in {"death", "instakill"}:
            continue
        target_name = event.get("targetName")
        if not target_name and isinstance(event.get("target"), dict):
            target_name = event["target"].get("name")
        if target_name and target_name in known_players:
            dead_players.add(target_name)
    return dead_players


def _resolve_targets(
    *,
    values: Optional[Iterable[str]],
    target_configs: Dict[str, EncounterTargetConfig],
    default_target_slugs: Optional[Iterable[str]],
) -> List[EncounterTargetConfig]:
    normalized: List[EncounterTargetConfig] = []
    seen: Set[str] = set()
    if values:
        for value in values:
            slug = str(value or "").strip().lower()
            if not slug or slug in seen or slug not in target_configs:
                continue
            normalized.append(target_configs[slug])
            seen.add(slug)
    if normalized:
        return normalized
    defaults = list(default_target_slugs or target_configs.keys())
    for slug in defaults:
        cfg = target_configs.get(str(slug))
        if cfg and cfg.slug not in seen:
            normalized.append(cfg)
            seen.add(cfg.slug)
    return normalized


def _collect_target_damage(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight_start: float,
    fight_end: float,
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
    actor_owners: Dict[int, Optional[int]],
    player_classes: Dict[str, Optional[str]],
    player_roles: Dict[str, str],
    player_specs: Dict[str, Optional[str]],
    known_players: set[str],
    role_defaults: Dict[str, str],
    global_specs: Dict[str, Optional[str]],
    target_name: str,
) -> Dict[str, float]:
    damage_by_player: DefaultDict[str, float] = defaultdict(float)
    safe_target_name = target_name.replace('"', '\\"')

    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="DamageDone",
        start=fight_start,
        end=fight_end,
        limit=10000,
        extra_filter=f'target.name = "{safe_target_name}"',
        actor_names=actor_names,
    ):
        source_name, resolved_actor_id = _resolve_event_source_player(event, actor_names, actor_owners)
        if not source_name or source_name not in known_players:
            continue
        if resolved_actor_id is not None:
            player_classes.setdefault(source_name, actor_classes.get(resolved_actor_id))
        player_roles.setdefault(source_name, role_defaults.get(source_name) or ROLE_UNKNOWN)
        player_specs.setdefault(source_name, global_specs.get(source_name))

        total_amount = _event_damage_amount(event)
        if total_amount <= 0:
            continue
        damage_by_player[source_name] += total_amount

    return damage_by_player


def _event_damage_amount(event: Dict[str, object]) -> float:
    total = 0.0
    for field in ("amount", "absorbed", "overkill", "blocked", "resisted", "mitigated"):
        value = event.get(field)
        if isinstance(value, (int, float)):
            total += float(value)
    return total


__all__ = [
    "EncounterTargetBucket",
    "EncounterTargetConfig",
    "EncounterTargetDamageBreakdown",
    "EncounterTargetDamageEntry",
    "EncounterTargetDamageSummary",
    "EncounterTargetSummary",
    "fetch_encounter_target_damage_summary",
]
