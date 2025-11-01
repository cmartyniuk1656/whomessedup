"""
High-level orchestration for fetching Warcraft Logs events and summarizing hits.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from .analysis import HitAggregate, count_hits
from .env import load_env
from .api import (
    Fight,
    events_for_fights,
    fetch_events,
    fetch_fights,
    fetch_player_details,
    filter_fights,
    get_token_from_client,
)

SPEC_ROLE_BY_CLASS: Dict[Tuple[str, str], str] = {
    ("DeathKnight", "Blood"): "Tank",
    ("DeathKnight", "Frost"): "Melee",
    ("DeathKnight", "Unholy"): "Melee",
    ("DemonHunter", "Havoc"): "Melee",
    ("DemonHunter", "Vengeance"): "Tank",
    ("Druid", "Balance"): "Ranged",
    ("Druid", "Feral"): "Melee",
    ("Druid", "Guardian"): "Tank",
    ("Druid", "Restoration"): "Healer",
    ("Evoker", "Devastation"): "Ranged",
    ("Evoker", "Preservation"): "Healer",
    ("Evoker", "Augmentation"): "Ranged",
    ("Hunter", "Beast Mastery"): "Ranged",
    ("Hunter", "Marksmanship"): "Ranged",
    ("Hunter", "Survival"): "Melee",
    ("Mage", "Arcane"): "Ranged",
    ("Mage", "Fire"): "Ranged",
    ("Mage", "Frost"): "Ranged",
    ("Monk", "Brewmaster"): "Tank",
    ("Monk", "Mistweaver"): "Healer",
    ("Monk", "Windwalker"): "Melee",
    ("Paladin", "Holy"): "Healer",
    ("Paladin", "Protection"): "Tank",
    ("Paladin", "Retribution"): "Melee",
    ("Priest", "Discipline"): "Healer",
    ("Priest", "Holy"): "Healer",
    ("Priest", "Shadow"): "Ranged",
    ("Rogue", "Assassination"): "Melee",
    ("Rogue", "Outlaw"): "Melee",
    ("Rogue", "Subtlety"): "Melee",
    ("Shaman", "Elemental"): "Ranged",
    ("Shaman", "Enhancement"): "Melee",
    ("Shaman", "Restoration"): "Healer",
    ("Warlock", "Affliction"): "Ranged",
    ("Warlock", "Demonology"): "Ranged",
    ("Warlock", "Destruction"): "Ranged",
    ("Warrior", "Arms"): "Melee",
    ("Warrior", "Fury"): "Melee",
    ("Warrior", "Protection"): "Tank",
}

CLASS_DEFAULT_ROLE: Dict[str, str] = {
    "Mage": "Ranged",
    "Warlock": "Ranged",
    "Hunter": "Ranged",
    "Priest": "Ranged",
    "Shaman": "Ranged",
    "Evoker": "Ranged",
    "DemonHunter": "Melee",
    "DeathKnight": "Melee",
    "Druid": "Melee",
    "Monk": "Melee",
    "Paladin": "Melee",
    "Rogue": "Melee",
    "Warrior": "Melee",
}

ROLE_UNKNOWN = "Unknown"

ROLE_PRIORITY: Dict[str, int] = {
    "Tank": 0,
    "Healer": 1,
    "Melee": 2,
    "Ranged": 3,
    ROLE_UNKNOWN: 4,
}


def _extract_spec(entry: Dict[str, Any]) -> Optional[str]:
    specs = entry.get("specs") or []
    for spec_obj in specs:
        spec = spec_obj.get("spec")
        if spec:
            return spec
    icon = entry.get("icon")
    if icon and "-" in icon:
        return icon.split("-", 1)[1].replace("_", " ")
    return None


def _infer_player_roles(details: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Optional[str]]]:
    roles: Dict[str, str] = {}
    specs: Dict[str, Optional[str]] = {}

    def register(entry: Dict[str, Any], role: str):
        name = entry.get("name")
        if not name:
            return
        spec = _extract_spec(entry)
        specs[name] = spec
        roles[name] = role

    for category, role in (("tanks", "Tank"), ("healers", "Healer")):
        for entry in details.get(category, []):
            register(entry, role)

    for entry in details.get("dps", []):
        name = entry.get("name")
        if not name:
            continue
        spec = _extract_spec(entry)
        class_name = entry.get("type")
        inferred_role = None
        if spec and class_name:
            inferred_role = SPEC_ROLE_BY_CLASS.get((class_name, spec))
        if inferred_role is None and class_name:
            inferred_role = CLASS_DEFAULT_ROLE.get(class_name)
        if inferred_role is None:
            inferred_role = ROLE_UNKNOWN
        register(entry, inferred_role)

    return roles, specs


def _players_from_details(details: Dict[str, Any]) -> List[str]:
    players: List[str] = []
    for category in ("tanks", "healers", "dps"):
        for entry in details.get(category, []):
            name = entry.get("name")
            if name:
                players.append(name)
    return players


@dataclass
class HitSummary:
    report_code: str
    data_type: str
    ability: Optional[str]
    ability_regex: Optional[str]
    ability_id: Optional[int]
    source: Optional[str]
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    total_hits: Dict[str, int]
    per_player_ability: Dict[Tuple[str, str], int]
    damage_per_player: Dict[str, float]
    fight_total_hits: Dict[int, int]
    fight_total_damage: Dict[int, float]
    fights_considered: List[Fight]
    actor_names: Dict[int, str]
    actor_classes: Dict[int, Optional[str]]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]

    def per_player(self) -> Dict[str, int]:
        return dict(self.total_hits)

    def per_player_rows(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for (player, ability), hits in self.per_player_ability.items():
            rows.append(
                {
                    "player": player,
                    "ability": ability,
                    "hits": hits,
                    "damage": self.damage_per_player.get(player, 0.0),
                    "role": self.player_roles.get(player, ROLE_UNKNOWN),
                }
            )
        rows.sort(key=lambda row: (row["player"].lower(), -row["hits"], row["ability"].lower()))
        return rows

    @property
    def total_damage(self) -> float:
        return float(sum(self.damage_per_player.values()))

    @property
    def pull_count(self) -> int:
        return len(self.fights_considered)

    @property
    def average_hits_per_pull(self) -> float:
        pulls = self.pull_count or 1
        return float(sum(self.total_hits.values()) / pulls)

    def per_player_hits_per_pull(self) -> Dict[str, float]:
        pulls = self.pull_count or 1
        return {player: hits / pulls for player, hits in self.total_hits.items()}

@dataclass
class GhostEntry:
    player: str
    pulls: int
    misses: int
    misses_per_pull: float


@dataclass
class GhostSummary:
    report_code: str
    ability_id: int
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    fights_considered: List[Fight]
    entries: List[GhostEntry]
    actor_names: Dict[int, str]
    actor_classes: Dict[int, Optional[str]]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]

    @property
    def pull_count(self) -> int:
        return len(self.fights_considered)

    @property
    def total_ghosts(self) -> int:
        return sum(entry.misses for entry in self.entries)

    def per_player_misses(self) -> Dict[str, int]:
        return {entry.player: entry.misses for entry in self.entries}

    def misses_per_pull_by_player(self) -> Dict[str, float]:
        return {entry.player: entry.misses_per_pull for entry in self.entries}


class TokenError(RuntimeError):
    pass


class FightSelectionError(RuntimeError):
    pass


def _resolve_token(
    token: Optional[str], client_id: Optional[str], client_secret: Optional[str]
) -> str:
    if token:
        return token
    fetched = get_token_from_client(client_id, client_secret)
    if not fetched:
        raise TokenError("Unable to retrieve bearer token. Provide --token or client credentials.")
    return fetched


def _select_fights(
    fights: List[Fight],
    *,
    name_filter: Optional[str],
    fight_ids: Optional[Iterable[int]],
) -> List[Fight]:
    chosen = filter_fights(fights, name_filter)
    if fight_ids:
        id_set = {int(fid) for fid in fight_ids}
        chosen = [fight for fight in chosen if fight.id in id_set]
    if not chosen:
        raise FightSelectionError("No fights matched the supplied criteria.")
    return chosen


def fetch_hit_summary(
    *,
    report_code: str,
    data_type: str = "DamageTaken",
    ability: Optional[str] = None,
    ability_id: Optional[int] = None,
    ability_regex: Optional[str] = None,
    source: Optional[str] = None,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    limit: int = 5000,
) -> HitSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)

    ability_re = re.compile(ability_regex) if ability_regex else None

    fight_id_list = [fight.id for fight in chosen]
    player_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(player_details)
    events_iter = events_for_fights(
        session,
        bearer,
        code=report_code,
        data_type=data_type,
        fights=chosen,
        limit=limit,
        ability_id=ability_id,
        ability_name=ability,
        actor_names=actor_names,
    )

    agg: HitAggregate = count_hits(
        events_iter,
        ability_regex=ability_re,
        only_ability=ability,
        only_ability_id=str(ability_id) if ability_id is not None else None,
        only_source=source,
    )

    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    player_classes = {player: name_to_class.get(player) for player in agg.hits_by_player.keys()}
    player_roles_full = {player: player_roles.get(player, ROLE_UNKNOWN) for player in agg.hits_by_player.keys()}
    player_specs_full = {player: player_specs.get(player) for player in agg.hits_by_player.keys()}

    return HitSummary(
        report_code=report_code,
        data_type=data_type,
        ability=ability,
        ability_id=ability_id,
        ability_regex=ability_regex,
        source=source,
        fight_filter=fight_name,
        fight_ids=list(int(fid) for fid in fight_ids) if fight_ids else None,
        total_hits=dict(agg.hits_by_player),
        per_player_ability=dict(agg.hits_by_player_ability),
        damage_per_player=dict(agg.damage_by_player),
        fight_total_hits=agg.fight_total_hits,
        fight_total_damage=agg.fight_total_damage,
        fights_considered=chosen,
        actor_names=actor_names,
        actor_classes=actor_classes,
        player_classes=player_classes,
        player_roles=player_roles_full,
        player_specs=player_specs_full,
    )


def fetch_ghost_summary(
    *,
    report_code: str,
    ability_id: int = 1224737,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> GhostSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)
    fight_id_list = [fight.id for fight in chosen]

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(aggregated_details)

    pulls_per_player: Dict[str, int] = defaultdict(int)
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        for name in set(_players_from_details(details)):
            pulls_per_player[name] += 1

    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    ghost_counts: Dict[str, int] = defaultdict(int)

    for fight in chosen:
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=fight.end,
            limit=2000,
            ability_id=None,
            actor_names=actor_names,
        ):
            event_type = (event.get("type") or "").lower()
            if event_type not in {"applydebuff", "applydebuffstack"}:
                continue
            timestamp = event.get("timestamp")
            if timestamp is None:
                continue
            if timestamp < fight.start + 15000:
                continue
            ability_game_id = event.get("abilityGameID")
            ability_id_match = False
            if ability_game_id is not None:
                try:
                    ability_id_match = int(ability_game_id) == int(ability_id)
                except (TypeError, ValueError):
                    ability_id_match = False
            ability_obj = event.get("ability") or {}
            if not ability_id_match and isinstance(ability_obj, dict):
                try:
                    ability_id_match = int(ability_obj.get("id")) == int(ability_id)
                except (TypeError, ValueError):
                    ability_id_match = False
            if ability_id is not None and not ability_id_match:
                continue
            target_name = event.get("targetName")
            if not target_name and isinstance(event.get("target"), dict):
                target_name = event["target"].get("name")
            if not target_name:
                continue
            ghost_counts[target_name] += 1

    all_players = set(pulls_per_player.keys()) | set(ghost_counts.keys())
    if not all_players:
        all_players = set(player_roles.keys())

    entries: List[GhostEntry] = []
    total_pulls = len(chosen) or 1

    for player in sorted(all_players):
        pulls = pulls_per_player.get(player, total_pulls)
        if pulls <= 0:
            pulls = total_pulls
        misses = ghost_counts.get(player, 0)
        misses_per_pull = misses / pulls if pulls else 0.0
        entries.append(
            GhostEntry(
                player=player,
                pulls=pulls,
                misses=misses,
                misses_per_pull=misses_per_pull,
            )
        )

    player_classes = {player: name_to_class.get(player) for player in all_players}
    player_roles_full = {player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players}
    player_specs_full = {player: player_specs.get(player) for player in all_players}

    entries.sort(key=lambda e: (ROLE_PRIORITY.get(player_roles_full.get(e.player, ROLE_UNKNOWN), ROLE_PRIORITY["Unknown"]), -e.misses, e.player.lower()))

    return GhostSummary(
        report_code=report_code,
        ability_id=ability_id,
        fight_filter=fight_name,
        fight_ids=list(int(fid) for fid in fight_ids) if fight_ids else None,
        fights_considered=chosen,
        entries=entries,
        actor_names=actor_names,
        actor_classes=actor_classes,
        player_classes=player_classes,
        player_roles=player_roles_full,
        player_specs=player_specs_full,
    )
