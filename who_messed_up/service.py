"""
High-level orchestration for fetching Warcraft Logs events and summarizing hits.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

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
    hits_by_player_fight: Dict[Tuple[str, int], int]
    player_roles_by_fight: Dict[int, Dict[str, str]]

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
    ghost_counts_by_player_fight: Dict[Tuple[int, str], int]
    player_roles_by_fight: Dict[int, Dict[str, str]]

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


@dataclass
class PhasePlayerEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    besiege_hits: int
    besiege_per_pull: float
    ghost_misses: int
    ghost_per_pull: float
    fuckup_rate: float


@dataclass
class PhaseSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    besiege_ability_id: int
    ghost_ability_id: int
    entries: List[PhasePlayerEntry]
    total_besieges: int
    total_ghosts: int
    avg_besieges_per_pull: float
    avg_ghosts_per_pull: float
    combined_per_pull: float
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    hit_ignore_after_deaths: Optional[int]
    hit_exclude_final_ms: Optional[float]


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
    dedupe_ms: Optional[float] = None,
    exclude_final_ms: Optional[float] = None,
    ignore_after_deaths: Optional[int] = None,
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
    player_roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        fight_details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(fight_details)
        if fight_roles:
            player_roles_by_fight[fight.id] = fight_roles
    death_cutoffs_by_fight: Dict[int, float] = {}
    if ignore_after_deaths and ignore_after_deaths > 0:
        for fight in chosen:
            total_deaths = 0
            cutoff_ts: Optional[float] = None
            for death_event in fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="Deaths",
                start=fight.start,
                end=fight.end,
                limit=1000,
                actor_names=actor_names,
            ):
                event_type = (death_event.get("type") or "").lower()
                if event_type not in {"death", "instakill"}:
                    continue
                ts_raw = death_event.get("timestamp")
                try:
                    ts_val = float(ts_raw)
                except (TypeError, ValueError):
                    ts_val = None
                if ts_val is None:
                    continue
                total_deaths += 1
                if total_deaths >= ignore_after_deaths:
                    if cutoff_ts is None or ts_val < cutoff_ts:
                        cutoff_ts = ts_val
            if cutoff_ts is not None:
                death_cutoffs_by_fight[fight.id] = cutoff_ts

    def _event_stream() -> Iterable[Dict[str, Any]]:
        for fight in chosen:
            cutoff = None
            if exclude_final_ms is not None:
                cutoff = float(fight.end) - float(exclude_final_ms)
            fight_death_cutoff = death_cutoffs_by_fight.get(fight.id)
            seen_targets: Set[str] = set()
            for event in fetch_events(
                session,
                bearer,
                code=report_code,
                data_type=data_type,
                start=fight.start,
                end=fight.end,
                limit=limit,
                ability_id=ability_id,
                ability_name=ability,
                actor_names=actor_names,
            ):
                if cutoff is not None:
                    ts = event.get("timestamp")
                    if isinstance(ts, (int, float)):
                        if ts >= cutoff:
                            continue
                    else:
                        try:
                            ts_val = float(ts)
                        except (TypeError, ValueError):
                            ts_val = None
                        if ts_val is not None and ts_val >= cutoff:
                            continue
                if fight_death_cutoff is not None:
                    ts = event.get("timestamp")
                    try:
                        ts_val = float(ts)
                    except (TypeError, ValueError):
                        ts_val = None
                    if ts_val is not None and ts_val >= fight_death_cutoff:
                        continue
                target_name = event.get("targetName")
                if not target_name and isinstance(event.get("target"), dict):
                    target_name = event["target"].get("name")
                if target_name:
                    if target_name in seen_targets:
                        continue
                    seen_targets.add(target_name)
                yield event

    events_iter = _event_stream()

    agg: HitAggregate = count_hits(
        events_iter,
        ability_regex=ability_re,
        only_ability=ability,
        only_ability_id=str(ability_id) if ability_id is not None else None,
        only_source=source,
        dedupe_ms=dedupe_ms,
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
        hits_by_player_fight=dict(agg.hits_by_player_fight),
        player_roles_by_fight=player_roles_by_fight,
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
    player_roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            player_roles_by_fight[fight.id] = fight_roles
        for name in set(_players_from_details(details)):
            pulls_per_player[name] += 1

    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    ghost_counts: Dict[str, int] = defaultdict(int)
    ghost_counts_by_fight: Dict[Tuple[int, str], int] = defaultdict(int)

    for fight in chosen:
        seen_targets: Set[str] = set()
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
            if target_name in seen_targets:
                continue
            seen_targets.add(target_name)
            ghost_counts[target_name] += 1
            ghost_counts_by_fight[(fight.id, target_name)] += 1

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
        ghost_counts_by_player_fight=dict(ghost_counts_by_fight),
        player_roles_by_fight=player_roles_by_fight,
    )


def fetch_phase_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    besiege_ability_id: int = 1227472,
    ghost_ability_id: int = 1224737,
    hit_data_type: str = "DamageTaken",
    hit_dedupe_ms: Optional[float] = 1500.0,
    hit_exclude_final_ms: Optional[float] = None,
    hit_ignore_after_deaths: Optional[int] = None,
) -> PhaseSummary:
    """
    Aggregate Besiege hits and Oathbound ghost misses into a combined per-player report.
    """
    hit_summary = fetch_hit_summary(
        report_code=report_code,
        data_type=hit_data_type,
        ability_id=besiege_ability_id,
        fight_name=fight_name,
        fight_ids=fight_ids,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        dedupe_ms=hit_dedupe_ms,
        exclude_final_ms=hit_exclude_final_ms,
        ignore_after_deaths=hit_ignore_after_deaths,
    )
    ghost_summary = fetch_ghost_summary(
        report_code=report_code,
        ability_id=ghost_ability_id,
        fight_name=fight_name,
        fight_ids=fight_ids,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )

    pull_count = ghost_summary.pull_count or hit_summary.pull_count

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    roles_by_fight.update(hit_summary.player_roles_by_fight)
    for fight_id, mapping in ghost_summary.player_roles_by_fight.items():
        roles_by_fight.setdefault(fight_id, {}).update(mapping)

    fight_ids_by_player_role: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    besiege_by_player_role: Dict[Tuple[str, str], int] = defaultdict(int)
    ghost_by_player_role: Dict[Tuple[str, str], int] = defaultdict(int)

    for (player, fight_id), hits in hit_summary.hits_by_player_fight.items():
        role = roles_by_fight.get(fight_id, {}).get(player)
        if not role:
            role = hit_summary.player_roles_by_fight.get(fight_id, {}).get(player) if hit_summary.player_roles_by_fight else None
        if not role:
            role = hit_summary.player_roles.get(player) or ghost_summary.player_roles.get(player) or ROLE_UNKNOWN
        key = (player, role)
        besiege_by_player_role[key] += hits
        fight_ids_by_player_role[key].add(fight_id)

    for (fight_id, player), misses in ghost_summary.ghost_counts_by_player_fight.items():
        role = roles_by_fight.get(fight_id, {}).get(player)
        if not role:
            role = ghost_summary.player_roles_by_fight.get(fight_id, {}).get(player) if ghost_summary.player_roles_by_fight else None
        if not role:
            role = ghost_summary.player_roles.get(player) or hit_summary.player_roles.get(player) or ROLE_UNKNOWN
        key = (player, role)
        ghost_by_player_role[key] += misses
        fight_ids_by_player_role[key].add(fight_id)

    for fight_id, role_map in roles_by_fight.items():
        for player, role in role_map.items():
            key = (player, role or ROLE_UNKNOWN)
            fight_ids_by_player_role[key].add(fight_id)

    player_classes: Dict[str, Optional[str]] = {}
    player_classes.update(hit_summary.player_classes)
    player_classes.update(ghost_summary.player_classes)
    player_roles: Dict[str, str] = {}
    player_roles.update(hit_summary.player_roles)
    player_roles.update(ghost_summary.player_roles)
    player_specs: Dict[str, Optional[str]] = {}
    player_specs.update(hit_summary.player_specs)
    player_specs.update(ghost_summary.player_specs)

    all_player_roles = set(besiege_by_player_role.keys()) | set(ghost_by_player_role.keys()) | set(fight_ids_by_player_role.keys())

    entries: List[PhasePlayerEntry] = []
    for player, role in sorted(
        all_player_roles,
        key=lambda item: (
            ROLE_PRIORITY.get(item[1] or ROLE_UNKNOWN, ROLE_PRIORITY["Unknown"]),
            item[0].lower(),
        ),
    ):
        key = (player, role or ROLE_UNKNOWN)
        pulls = len(fight_ids_by_player_role.get(key, set()))
        besiege_hits = besiege_by_player_role.get(key, 0)
        ghost_misses = ghost_by_player_role.get(key, 0)
        ghost_per_pull = ghost_misses / pulls if pulls else 0.0
        besiege_per_pull = besiege_hits / pulls if pulls else 0.0
        fuckup_rate = besiege_per_pull + ghost_per_pull

        if pulls == 0 and besiege_hits == 0 and ghost_misses == 0:
            continue

        if player not in player_classes:
            player_classes[player] = hit_summary.player_classes.get(player) or ghost_summary.player_classes.get(player)
        if player not in player_roles:
            player_roles[player] = role or ROLE_UNKNOWN

        entries.append(
            PhasePlayerEntry(
                player=player,
                role=role or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                besiege_hits=besiege_hits,
                besiege_per_pull=besiege_per_pull,
                ghost_misses=ghost_misses,
                ghost_per_pull=ghost_per_pull,
                fuckup_rate=fuckup_rate,
            )
        )

    total_besieges = sum(hit_summary.total_hits.values())
    total_ghosts = sum(ghost_by_player_role.values())
    avg_besieges = total_besieges / pull_count if pull_count else 0.0
    avg_ghosts = total_ghosts / pull_count if pull_count else 0.0

    return PhaseSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=list(int(fid) for fid in fight_ids) if fight_ids else None,
        pull_count=pull_count,
        besiege_ability_id=besiege_ability_id,
        ghost_ability_id=ghost_ability_id,
        entries=entries,
        total_besieges=total_besieges,
        total_ghosts=total_ghosts,
        avg_besieges_per_pull=avg_besieges,
        avg_ghosts_per_pull=avg_ghosts,
        combined_per_pull=avg_besieges + avg_ghosts,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        hit_ignore_after_deaths=hit_ignore_after_deaths,
        hit_exclude_final_ms=hit_exclude_final_ms,
    )
