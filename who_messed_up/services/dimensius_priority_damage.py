"""
Dimensius phase-two (Artoshion) priority damage summaries.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple, Set

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_event_source_player,
    _resolve_token,
    _select_fights,
)

ARTOSHION_NAME = "Artoshion"
SHOOTING_STAR_NAME = "Shooting Star"
SHOOTING_STAR_ID = 1246948
PHASE_FILTER = f'encounterPhase = 3 and target.name = "{ARTOSHION_NAME}"'
AVERAGING_MODE_PARTICIPATION = "participation"
AVERAGING_MODE_DAMAGE_PULLS = "damage_pulls"


@dataclass(frozen=True)
class PriorityTargetConfig:
    slug: str
    label: str
    enemy_name: str
    averaging_mode: str = AVERAGING_MODE_PARTICIPATION


PRIORITY_TARGETS: Dict[str, PriorityTargetConfig] = {
    "artoshion": PriorityTargetConfig(slug="artoshion", label="Artoshion", enemy_name=ARTOSHION_NAME),
    "pargoth": PriorityTargetConfig(
        slug="pargoth", label="Pargoth", enemy_name="Pargoth", averaging_mode=AVERAGING_MODE_DAMAGE_PULLS
    ),
    "nullbinder": PriorityTargetConfig(slug="nullbinder", label="Nullbinder", enemy_name="Nullbinder"),
    "voidwardem": PriorityTargetConfig(slug="voidwardem", label="Voidwardem", enemy_name="Voidwardem"),
}
DEFAULT_TARGET_SLUGS = ("artoshion",)


@dataclass
class PriorityDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float
    target_totals: Dict[str, "TargetDamageBreakdown"]


@dataclass
class DimensiusPriorityDamageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    entries: List[PriorityDamageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    pull_count: int
    total_damage: float
    avg_damage_per_pull: float
    ignored_source: str
    targets: List["PriorityTargetSummary"]


@dataclass
class TargetDamageBreakdown:
    target: str
    label: str
    total_damage: float
    average_damage: float
    pulls_with_damage: int


@dataclass
class PriorityTargetSummary:
    target: str
    label: str
    averaging_mode: str
    total_damage: float
    avg_damage_per_pull: float


def fetch_dimensius_priority_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    targets: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DimensiusPriorityDamageSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)

    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)

    fight_id_list = [fight.id for fight in chosen]
    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    participants_by_fight: Dict[int, Set[str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = set(_players_from_details(details))
        if participants:
            participants_by_fight[fight.id] = participants

    player_classes: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            player_classes[name] = actor_classes.get(actor_id)

    player_roles: Dict[str, str] = dict(player_roles_global)
    player_specs: Dict[str, Optional[str]] = dict(player_specs_global)
    for fight_role_map in roles_by_fight.values():
        for player, role in fight_role_map.items():
            if player not in player_roles or player_roles[player] in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
            player_specs.setdefault(player, player_specs_global.get(player))

    damage_totals: DefaultDict[str, float] = defaultdict(float)
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    fights_with_phase = 0
    per_target_totals: Dict[str, DefaultDict[str, float]] = {
        slug: defaultdict(float) for slug in PRIORITY_TARGETS.keys()
    }
    per_target_damage_pulls: Dict[str, DefaultDict[str, int]] = {
        slug: defaultdict(int) for slug in PRIORITY_TARGETS.keys()
    }
    target_summary_totals: DefaultDict[str, float] = defaultdict(float)

    active_targets = _resolve_priority_targets(targets)
    selected_slugs = [cfg.slug for cfg in active_targets]

    for fight in chosen:
        art_damage_map, phase_start = _collect_target_damage(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            actor_owners=actor_owners,
            target_name=ARTOSHION_NAME,
            track_phase_start=True,
        )
        if phase_start is None:
            continue
        fights_with_phase += 1
        participants = participants_by_fight.get(fight.id, set())
        if not participants:
            participants = set(roles_by_fight.get(fight.id, {}).keys())
        death_times = _collect_first_death_times(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
        )
        alive_players = _players_alive_at_phase_start(participants, death_times, phase_start)
        if not alive_players:
            continue
        for player in alive_players:
            pulls_by_player[player] += 1

        fight_damage_maps: Dict[str, Dict[str, float]] = {}
        if "artoshion" in selected_slugs:
            fight_damage_maps["artoshion"] = art_damage_map
        for cfg in active_targets:
            if cfg.slug == "artoshion":
                continue
            damage_map, _ = _collect_target_damage(
                session,
                bearer,
                report_code=report_code,
                fight=fight,
                actor_names=actor_names,
                actor_owners=actor_owners,
                target_name=cfg.enemy_name,
            )
            fight_damage_maps[cfg.slug] = damage_map

        for slug, damage_map in fight_damage_maps.items():
            if not damage_map:
                continue
            for player, total in damage_map.items():
                if total <= 0 or player not in alive_players:
                    continue
                per_target_totals[slug][player] += total
                per_target_damage_pulls[slug][player] += 1
                target_summary_totals[slug] += total

        for player in alive_players:
            combined = 0.0
            for slug in selected_slugs:
                combined += fight_damage_maps.get(slug, {}).get(player, 0.0)
            damage_totals[player] += combined

    for player in pulls_by_player.keys():
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, ROLE_UNKNOWN)
        player_specs.setdefault(player, None)

    entries: List[PriorityDamageEntry] = []
    players = sorted(
        pulls_by_player.keys(),
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            name.lower(),
        ),
    )
    for player in players:
        pulls = pulls_by_player.get(player, 0)
        if pulls <= 0:
            continue
        total_damage = damage_totals.get(player, 0.0)
        average_damage = total_damage / pulls if pulls else 0.0
        target_breakdowns: Dict[str, TargetDamageBreakdown] = {}
        for cfg in active_targets:
            player_target_total = per_target_totals[cfg.slug].get(player, 0.0)
            if cfg.averaging_mode == AVERAGING_MODE_DAMAGE_PULLS:
                denom = per_target_damage_pulls[cfg.slug].get(player, 0)
            else:
                denom = pulls
            average = player_target_total / denom if denom else 0.0
            target_breakdowns[cfg.slug] = TargetDamageBreakdown(
                target=cfg.slug,
                label=cfg.label,
                total_damage=player_target_total,
                average_damage=average,
                pulls_with_damage=per_target_damage_pulls[cfg.slug].get(player, 0),
            )
        entries.append(
            PriorityDamageEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=average_damage,
                target_totals=target_breakdowns,
            )
        )

    total_damage_amount = sum(entry.total_damage for entry in entries)
    avg_damage_per_pull = total_damage_amount / fights_with_phase if fights_with_phase else 0.0
    target_summaries: List[PriorityTargetSummary] = []
    for cfg in active_targets:
        total = target_summary_totals.get(cfg.slug, 0.0)
        avg = total / fights_with_phase if fights_with_phase else 0.0
        target_summaries.append(
            PriorityTargetSummary(
                target=cfg.slug,
                label=cfg.label,
                averaging_mode=cfg.averaging_mode,
                total_damage=total,
                avg_damage_per_pull=avg,
            )
        )

    return DimensiusPriorityDamageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        pull_count=fights_with_phase,
        total_damage=total_damage_amount,
        avg_damage_per_pull=avg_damage_per_pull,
        ignored_source=SHOOTING_STAR_NAME,
        targets=target_summaries,
    )


def _collect_target_damage(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
    target_name: str,
    track_phase_start: bool = False,
) -> Tuple[Dict[str, float], Optional[float]]:
    damage_by_player: DefaultDict[str, float] = defaultdict(float)
    phase_start: Optional[float] = None
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="DamageDone",
        start=fight.start,
        end=fight.end,
        extra_filter=f'encounterPhase = 3 and target.name = "{target_name}"',
        actor_names=actor_names,
    ):
        source_name, _ = _resolve_event_source_player(event, actor_names, actor_owners)
        if not source_name:
            continue
        ability_id = _extract_ability_id(event)
        ability_name = _extract_ability_name(event)
        if _is_shooting_star_event(source_name, ability_name, ability_id):
            continue
        amount = _event_damage_amount(event)
        if amount <= 0:
            continue
        timestamp = event.get("timestamp")
        try:
            ts_val = float(timestamp)
        except (TypeError, ValueError):
            ts_val = None
        if track_phase_start and ts_val is not None and (phase_start is None or ts_val < phase_start):
            phase_start = ts_val
        damage_by_player[source_name] += amount
    return damage_by_player, phase_start


def _event_damage_amount(event: Dict[str, object]) -> float:
    total = 0.0
    for field in ("amount", "absorbed", "overkill", "blocked", "resisted", "mitigated"):
        value = event.get(field)
        if isinstance(value, (int, float)):
            total += float(value)
    return total


def _extract_ability_id(event: Dict[str, object]) -> Optional[int]:
    candidates = [
        event.get("abilityGameID"),
        event.get("abilityID"),
        (event.get("ability") or {}).get("gameID"),
        (event.get("ability") or {}).get("id"),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, (int, float)):
            return int(candidate)
        if isinstance(candidate, str):
            try:
                return int(candidate)
            except ValueError:
                continue
    return None


def _extract_ability_name(event: Dict[str, object]) -> Optional[str]:
    name = event.get("abilityName")
    if name:
        return str(name)
    ability = event.get("ability")
    if isinstance(ability, dict):
        ability_name = ability.get("name")
        if ability_name:
            return str(ability_name)
    return None


def _is_shooting_star_event(source_name: str, ability_name: Optional[str], ability_id: Optional[int]) -> bool:
    if source_name == SHOOTING_STAR_NAME:
        return True
    if ability_id is not None and ability_id == SHOOTING_STAR_ID:
        return True
    if ability_name and ability_name.lower() == SHOOTING_STAR_NAME.lower():
        return True
    return False


def _collect_first_death_times(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    actor_names: Dict[int, str],
) -> Dict[str, float]:
    first_death: Dict[str, float] = {}
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
        target_name = event.get("targetName")
        if not target_name and isinstance(event.get("target"), dict):
            target_name = event["target"].get("name")
        if not target_name:
            continue
        existing = first_death.get(target_name)
        if existing is None or ts_val < existing:
            first_death[target_name] = ts_val
    return first_death


def _players_alive_at_phase_start(participants: Set[str], death_times: Dict[str, float], phase_start: float) -> Set[str]:
    alive = set()
    for player in participants:
        death_time = death_times.get(player)
        if death_time is None or death_time >= phase_start:
            alive.add(player)
    return alive


def _resolve_priority_targets(values: Optional[Iterable[str]]) -> List[PriorityTargetConfig]:
    normalized: List[PriorityTargetConfig] = []
    seen: Set[str] = set()
    if values:
        for value in values:
            if value is None:
                continue
            slug = str(value).strip().lower()
            if slug in PRIORITY_TARGETS and slug not in seen:
                normalized.append(PRIORITY_TARGETS[slug])
                seen.add(slug)
    if not normalized:
        for slug in DEFAULT_TARGET_SLUGS:
            cfg = PRIORITY_TARGETS.get(slug)
            if cfg:
                normalized.append(cfg)
    return normalized


__all__ = [
    "DimensiusPriorityDamageSummary",
    "PriorityDamageEntry",
    "PriorityTargetSummary",
    "TargetDamageBreakdown",
    "fetch_dimensius_priority_damage_summary",
]
