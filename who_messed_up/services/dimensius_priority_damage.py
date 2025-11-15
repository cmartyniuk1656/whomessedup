"""
Dimensius phase-two (Artoshion) priority damage summaries.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _resolve_event_source_player,
    _resolve_token,
    _select_fights,
)

ARTOSHION_NAME = "Artoshion"
SHOOTING_STAR_NAME = "Shooting Star"
SHOOTING_STAR_ID = 1246948
PHASE_FILTER = f'encounterPhase = 3 and target.name = "{ARTOSHION_NAME}"'


@dataclass
class PriorityDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float


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
    target_name: str
    ignored_source: str


def fetch_dimensius_priority_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
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
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles

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

    for fight in chosen:
        damage_map, phase_start = _collect_phase_damage(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            actor_owners=actor_owners,
        )
        if phase_start is None:
            continue
        fights_with_phase += 1
        if not damage_map:
            continue
        for player, total in damage_map.items():
            if total <= 0:
                continue
            pulls_by_player[player] += 1
            damage_totals[player] += total

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
        entries.append(
            PriorityDamageEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=average_damage,
            )
        )

    total_damage_amount = sum(entry.total_damage for entry in entries)
    avg_damage_per_pull = total_damage_amount / fights_with_phase if fights_with_phase else 0.0

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
        target_name=ARTOSHION_NAME,
        ignored_source=SHOOTING_STAR_NAME,
    )


def _collect_phase_damage(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Fight,
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
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
        extra_filter=PHASE_FILTER,
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
        if ts_val is not None and (phase_start is None or ts_val < phase_start):
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


__all__ = [
    "DimensiusPriorityDamageSummary",
    "PriorityDamageEntry",
    "fetch_dimensius_priority_damage_summary",
]
