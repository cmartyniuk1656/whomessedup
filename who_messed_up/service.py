"""
High-level orchestration for fetching Warcraft Logs events and summarizing hits.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set, Literal

import requests

from .analysis import HitAggregate, count_hits
from .env import load_env
from .api import (
    Fight,
    events_for_fights,
    fetch_events,
    fetch_fights,
    fetch_player_details,
    fetch_table,
    filter_fights,
    get_token_from_client,
)
from .services.dimensius import (
    AddDamageEntry,
    AddDamageSummary,
    fetch_dimensius_add_damage_summary,
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

NEXUS_PHASE_LABELS: Dict[str, str] = {
    "full": "Full Fight",
    "1": "Stage One: Oath Breakers",
    "2": "Stage Two: Rider's of the Dark",
    "3": "Intermission One: Nexus Descent",
    "4": "Intermission Two: King's Hunger",
    "5": "Stage Three: World in Twilight",
}

DIMENSIUS_PHASE_LABELS: Dict[str, str] = {
    "full": "Full Fight",
    "1": "Stage One: Critical Mass",
    "2": "Intermission: Event Horizon",
    "3": "Stage Two: The Dark Heart",
    "4": "Stage Three: Singularity",
}

PHASE_LABEL_PRESETS: Dict[str, Dict[str, str]] = {
    "nexus": NEXUS_PHASE_LABELS,
    "dimensius": DIMENSIUS_PHASE_LABELS,
}
DEFAULT_PHASE_PROFILE = "nexus"

LIVING_MASS_NAME = "Living Mass"
DIMENSIUS_LIVING_MASS_FILTER = f'encounterPhase = 1 and target.name = "{LIVING_MASS_NAME}"'
DIMENSIUS_INITIAL_ADD_IGNORE_COUNT = 6

GhostMissMode = Literal["first_per_set", "first_per_pull", "all"]
DEFAULT_GHOST_MISS_MODE: GhostMissMode = "first_per_set"
_GHOST_MODE_ALIASES: Dict[str, GhostMissMode] = {
    "first_per_set": "first_per_set",
    "firstperset": "first_per_set",
    "per_set": "first_per_set",
    "perset": "first_per_set",
    "set_first": "first_per_set",
    "setfirst": "first_per_set",
    "first_set": "first_per_set",
    "firstset": "first_per_set",
    "first_per_pull": "first_per_pull",
    "firstperpull": "first_per_pull",
    "per_pull": "first_per_pull",
    "perpull": "first_per_pull",
    "pull_first": "first_per_pull",
    "pullfirst": "first_per_pull",
    "first_pull": "first_per_pull",
    "firstpull": "first_per_pull",
    "all": "all",
    "all_hits": "all",
    "allhits": "all",
    "all_misses": "all",
    "allmisses": "all",
    "every": "all",
}
GHOST_SET_WINDOW_MS = 5000


def normalize_ghost_miss_mode(value: Any) -> GhostMissMode:
    """
    Normalize user-provided ghost miss mode values into the canonical set.
    """
    if isinstance(value, bool):
        return "first_per_pull" if value else "all"
    if isinstance(value, (int, float)) and value in (0, 1):
        return "first_per_pull" if int(value) == 1 else "all"
    if value is None:
        return DEFAULT_GHOST_MISS_MODE
    if isinstance(value, str):
        cleaned = value.strip().lower()
        cleaned = cleaned.replace("-", "_").replace(" ", "_")
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        normalized = _GHOST_MODE_ALIASES.get(cleaned)
        if normalized:
            return normalized
    raise ValueError(f"Invalid ghost miss mode: {value}")


def _sanitize_report_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Report code cannot be empty.")
    lowered = text.lower()
    if "/reports/" in lowered:
        parts = text.split("/reports/", 1)
        if len(parts) == 2:
            remainder = parts[1]
            remainder = remainder.split("/", 1)[0]
            remainder = remainder.split("?", 1)[0]
            cleaned = remainder.strip()
            if cleaned:
                return cleaned
    return text


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
    roles_by_fight: Dict[int, Dict[str, str]]

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
class GhostEvent:
    player: str
    fight_id: int
    fight_name: str
    pull_index: int
    timestamp: float
    offset_ms: float


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
    ghost_miss_mode: GhostMissMode
    ghost_counts_by_player_fight: Dict[Tuple[int, str], int]
    roles_by_fight: Dict[int, Dict[str, str]]
    ghost_events: List[GhostEvent]
    ignore_after_deaths: Optional[int]
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
    ghost_events: List[GhostEvent]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    hit_ignore_after_deaths: Optional[int]
    hit_exclude_final_ms: Optional[float]
    first_hit_only_hits: bool
    ghost_miss_mode: GhostMissMode


@dataclass
class PhaseMetric:
    phase_id: str
    phase_label: str
    total_amount: float
    average_per_pull: float


@dataclass
class PhaseDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    metrics: List[PhaseMetric]


@dataclass
class PhaseDamageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    phases: List[str]
    phase_labels: Dict[str, str]
    entries: List[PhaseDamageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    pull_count: int
    source_reports: List[str]
    fight_signature: List[Tuple[str, bool, int]]


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
    first_hit_only: bool = True,
) -> HitSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)

    ability_re = re.compile(ability_regex) if ability_regex else None

    fight_id_list = [fight.id for fight in chosen]
    player_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(player_details)
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        fight_details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(fight_details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
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
            seen_targets: Set[str] = set() if first_hit_only else set()
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
                if target_name and first_hit_only:
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
        roles_by_fight=roles_by_fight,
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
    ghost_miss_mode: Any = DEFAULT_GHOST_MISS_MODE,
    first_miss_only: Optional[bool] = None,
    ignore_after_deaths: Optional[int] = None,
) -> GhostSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)
    fight_id_list = [fight.id for fight in chosen]

    mode_input = ghost_miss_mode
    if first_miss_only is not None and ghost_miss_mode == DEFAULT_GHOST_MISS_MODE:
        mode_input = first_miss_only
    mode = normalize_ghost_miss_mode(mode_input)

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(aggregated_details)

    pulls_per_player: Dict[str, int] = defaultdict(int)
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        for name in set(_players_from_details(details)):
            pulls_per_player[name] += 1

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

    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    ghost_counts: Dict[str, int] = defaultdict(int)
    ghost_counts_by_fight: Dict[Tuple[int, str], int] = defaultdict(int)
    ghost_events: List[GhostEvent] = []

    for pull_index, fight in enumerate(chosen, start=1):
        seen_targets: Set[str] = set()
        last_counted_ts: Dict[str, int] = {}
        fight_death_cutoff = death_cutoffs_by_fight.get(fight.id)
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
            if fight_death_cutoff is not None:
                try:
                    ts_val = float(timestamp)
                except (TypeError, ValueError):
                    ts_val = None
                if ts_val is not None and ts_val >= fight_death_cutoff:
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

            should_count = True
            if mode == "first_per_pull":
                if target_name in seen_targets:
                    should_count = False
                else:
                    seen_targets.add(target_name)
            elif mode == "first_per_set":
                last_timestamp = last_counted_ts.get(target_name)
                if last_timestamp is not None and timestamp - last_timestamp < GHOST_SET_WINDOW_MS:
                    should_count = False
                else:
                    last_counted_ts[target_name] = timestamp

            if not should_count:
                continue

            ghost_counts[target_name] += 1
            ghost_counts_by_fight[(fight.id, target_name)] += 1
            offset_ms = float(timestamp) - float(fight.start)
            ghost_events.append(
                GhostEvent(
                    player=target_name,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index,
                    timestamp=float(timestamp),
                    offset_ms=offset_ms,
                )
            )

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
        ghost_miss_mode=mode,
        ghost_counts_by_player_fight=dict(ghost_counts_by_fight),
        roles_by_fight=roles_by_fight,
        ghost_events=ghost_events,
        ignore_after_deaths=ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None,
    )


def _normalize_phase_ids(
    phases: Optional[Iterable[str]], *, phase_labels: Dict[str, str]
) -> List[str]:
    normalized: List[str] = []
    seen: Set[str] = set()
    if phases:
        for raw in phases:
            if raw is None:
                continue
            text_value = str(raw).strip()
            if not text_value:
                continue
            lowered = text_value.lower()
            if lowered in {"full", "all"} and "full" in phase_labels:
                key = "full"
            else:
                try:
                    phase_int = int(lowered)
                except ValueError:
                    continue
                key = str(phase_int)
            if key not in phase_labels or key in seen:
                continue
            normalized.append(key)
            seen.add(key)
    if not normalized:
        if "full" in phase_labels:
            normalized.append("full")
        else:
            first_key = next(iter(phase_labels.keys()), None)
            if first_key:
                normalized.append(first_key)
    return normalized


def _resolve_phase_labels(profile: Optional[str]) -> Dict[str, str]:
    if profile:
        key = str(profile).strip().lower()
    else:
        key = DEFAULT_PHASE_PROFILE
    if key not in PHASE_LABEL_PRESETS:
        key = DEFAULT_PHASE_PROFILE
    return PHASE_LABEL_PRESETS[key]


def _extract_target_key(event: Dict[str, Any]) -> Optional[Tuple[Any, ...]]:
    target = event.get("target")
    guid = None
    instance = None
    if isinstance(target, dict):
        guid = target.get("guid") or target.get("id")
        instance = target.get("instance")
    target_id = event.get("targetID")
    instance_id = event.get("targetInstance") or event.get("targetInstanceID")
    if any(component is not None for component in (guid, target_id, instance, instance_id)):
        return (guid, target_id, instance, instance_id)
    return None


def _resolve_event_source_player(
    event: Dict[str, Any],
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
) -> Tuple[Optional[str], Optional[int]]:
    source = event.get("source")
    raw_name: Optional[str] = None
    raw_id: Optional[int] = None
    if isinstance(source, dict):
        raw_name = source.get("name") or raw_name
        candidate_id = source.get("guid") or source.get("id")
        try:
            raw_id = int(candidate_id)
        except (TypeError, ValueError):
            raw_id = None
    if raw_id is None:
        candidate_id = event.get("sourceID")
        try:
            raw_id = int(candidate_id)
        except (TypeError, ValueError):
            raw_id = None
    if not raw_name:
        raw_name = event.get("sourceName")

    resolved_id = raw_id
    if raw_id is not None:
        current = raw_id
        seen: Set[int] = set()
        while True:
            owner = actor_owners.get(current)
            if owner in (None, 0) or owner in seen:
                break
            seen.add(current)
            current = owner
        resolved_id = current

    resolved_name = raw_name
    if resolved_id is not None:
        resolved_name = actor_names.get(resolved_id, resolved_name)

    return resolved_name, resolved_id


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
    first_hit_only_hits: bool = True,
    ghost_miss_mode: Any = DEFAULT_GHOST_MISS_MODE,
) -> PhaseSummary:
    fight_id_filter = [int(fid) for fid in fight_ids] if fight_ids else None

    hit_summary = fetch_hit_summary(
        report_code=report_code,
        data_type=hit_data_type,
        ability_id=besiege_ability_id,
        fight_name=fight_name,
        fight_ids=fight_id_filter,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        dedupe_ms=hit_dedupe_ms,
        exclude_final_ms=hit_exclude_final_ms,
        ignore_after_deaths=hit_ignore_after_deaths,
        first_hit_only=first_hit_only_hits,
    )
    normalized_ghost_mode = normalize_ghost_miss_mode(ghost_miss_mode)

    ghost_summary = fetch_ghost_summary(
        report_code=report_code,
        ability_id=ghost_ability_id,
        fight_name=fight_name,
        fight_ids=fight_id_filter,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        ghost_miss_mode=normalized_ghost_mode,
        ignore_after_deaths=hit_ignore_after_deaths,
    )

    fights = list(hit_summary.fights_considered)
    if not fights:
        fights = list(ghost_summary.fights_considered)
    pull_count = len(fights)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    roles_by_fight.update(hit_summary.roles_by_fight or {})
    for fight_id, mapping in ghost_summary.roles_by_fight.items():
        roles_by_fight.setdefault(fight_id, {}).update(mapping)

    hits_by_player_fight = dict(hit_summary.hits_by_player_fight)
    hits_by_fight: Dict[int, Dict[str, int]] = defaultdict(dict)
    for (player, fight_id), count in hits_by_player_fight.items():
        hits_by_fight[int(fight_id)][player] = count

    ghost_counts_by_player_fight: Dict[Tuple[str, int], int] = {}
    for (fight_id, player), count in ghost_summary.ghost_counts_by_player_fight.items():
        ghost_counts_by_player_fight[(player, int(fight_id))] = count
    ghosts_by_fight: Dict[int, Dict[str, int]] = defaultdict(dict)
    for (player, fight_id), count in ghost_counts_by_player_fight.items():
        ghosts_by_fight[fight_id][player] = count

    players: Set[str] = set(hit_summary.total_hits.keys())
    players.update(ghost_summary.per_player_misses().keys())
    for mapping in roles_by_fight.values():
        players.update(mapping.keys())

    player_classes = dict(hit_summary.player_classes)
    for player, class_name in ghost_summary.player_classes.items():
        if player not in player_classes or player_classes[player] is None:
            player_classes[player] = class_name

    player_roles = dict(hit_summary.player_roles)
    for player, role in ghost_summary.player_roles.items():
        player_roles.setdefault(player, role)

    player_specs = dict(hit_summary.player_specs)
    for player, spec in ghost_summary.player_specs.items():
        if player not in player_specs or player_specs[player] is None:
            player_specs[player] = spec

    pulls_by_key: Dict[Tuple[str, str], int] = defaultdict(int)
    besieges_by_key: Dict[Tuple[str, str], int] = defaultdict(int)
    ghosts_by_key: Dict[Tuple[str, str], int] = defaultdict(int)

    for fight in fights:
        fight_roles = roles_by_fight.get(fight.id, {})
        hits_map = hits_by_fight.get(fight.id, {})
        ghosts_map = ghosts_by_fight.get(fight.id, {})
        participants = set(fight_roles.keys()) | set(hits_map.keys()) | set(ghosts_map.keys())
        if not participants:
            continue
        for player in participants:
            role = fight_roles.get(player) or player_roles.get(player) or ROLE_UNKNOWN
            key = (player, role)
            pulls_by_key[key] += 1
            besieges_by_key[key] += hits_map.get(player, 0)
            ghosts_by_key[key] += ghosts_map.get(player, 0)
            players.add(player)
            if player not in player_roles:
                player_roles[player] = role

    for player in players:
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, ROLE_UNKNOWN)
        player_specs.setdefault(player, None)

    entries: List[PhasePlayerEntry] = []
    total_besieges = 0
    total_ghosts = 0

    for (player, role), pulls in pulls_by_key.items():
        if pulls <= 0:
            continue
        bes_hits = besieges_by_key.get((player, role), 0)
        ghost_misses = ghosts_by_key.get((player, role), 0)
        bes_per_pull = bes_hits / pulls if pulls else 0.0
        ghost_per_pull = ghost_misses / pulls if pulls else 0.0
        fuckup_rate = bes_per_pull + ghost_per_pull

        total_besieges += bes_hits
        total_ghosts += ghost_misses

        entries.append(
            PhasePlayerEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                besiege_hits=bes_hits,
                besiege_per_pull=bes_per_pull,
                ghost_misses=ghost_misses,
                ghost_per_pull=ghost_per_pull,
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

    avg_besieges_per_pull = total_besieges / pull_count if pull_count else 0.0
    avg_ghosts_per_pull = total_ghosts / pull_count if pull_count else 0.0
    combined_per_pull = (total_besieges + total_ghosts) / pull_count if pull_count else 0.0

    return PhaseSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=fight_id_filter,
        pull_count=pull_count,
        besiege_ability_id=besiege_ability_id,
        ghost_ability_id=ghost_ability_id,
        entries=entries,
        total_besieges=total_besieges,
        total_ghosts=total_ghosts,
        avg_besieges_per_pull=avg_besieges_per_pull,
        avg_ghosts_per_pull=avg_ghosts_per_pull,
        combined_per_pull=combined_per_pull,
        ghost_events=ghost_summary.ghost_events,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        hit_ignore_after_deaths=hit_ignore_after_deaths,
        hit_exclude_final_ms=hit_exclude_final_ms,
        first_hit_only_hits=first_hit_only_hits,
        ghost_miss_mode=normalized_ghost_mode,
    )


def _fetch_phase_damage_summary_single(
    *,
    report_code: str,
    phases: Optional[Iterable[str]] = None,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    phase_labels: Optional[Dict[str, str]] = None,
) -> PhaseDamageSummary:
    load_env()

    if phase_labels is None:
        phase_labels = NEXUS_PHASE_LABELS

    fight_id_filter = [int(fid) for fid in fight_ids] if fight_ids else None

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_id_filter)

    selected_phases = _normalize_phase_ids(phases, phase_labels=phase_labels)

    fight_id_list = [fight.id for fight in chosen]
    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles

    valid_players: Set[str] = set(player_roles_global.keys())
    for fight_roles in roles_by_fight.values():
        valid_players.update(name for name in fight_roles if name)

    player_classes: Dict[str, Optional[str]] = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name
    }
    player_roles: Dict[str, str] = dict(player_roles_global)
    player_specs: Dict[str, Optional[str]] = dict(player_specs_global)

    fight_ids_by_player_role: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    for fight in chosen:
        fight_roles = roles_by_fight.get(fight.id, {})
        for player, role in fight_roles.items():
            fight_ids_by_player_role[(player, role)].add(fight.id)

    damage_roles = {"Tank", "Melee", "Ranged", ROLE_UNKNOWN}
    healing_roles = {"Healer"}

    def resolve_actor(actor_key: Any) -> Tuple[Optional[int], Optional[str]]:
        if isinstance(actor_key, int):
            current = actor_key
            seen: Set[int] = set()
            while True:
                owner = actor_owners.get(current)
                if owner in (None, 0) or owner in seen:
                    break
                seen.add(current)
                current = owner
            name = actor_names.get(current) or actor_names.get(actor_key)
            return current, name
        if isinstance(actor_key, str):
            return None, actor_key
        return None, None

    def sum_entry_total(entry: Dict[str, Any]) -> float:
        value = entry.get("total")
        if value is None:
            value = entry.get("totalReduced")
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    phase_totals: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for phase_id in selected_phases:
        filter_expr = None
        if phase_id != "full":
            try:
                numeric_phase = int(phase_id)
                filter_expr = f"encounterPhase = {numeric_phase}"
            except ValueError:
                filter_expr = None

        for fight in chosen:
            def consume_entries(entries: Iterable[Dict[str, Any]], *, allowed_roles: Set[str]) -> None:
                for entry in entries:
                    actor_key = entry.get("id")
                    if actor_key is None:
                        continue
                    total_amount = sum_entry_total(entry)
                    if total_amount <= 0:
                        continue
                    owner_id, owner_name = resolve_actor(actor_key)
                    if not owner_name:
                        owner_name = entry.get("name")
                    if not owner_name:
                        continue
                    role = (
                        roles_by_fight.get(fight.id, {}).get(owner_name)
                        or player_roles_global.get(owner_name)
                        or ROLE_UNKNOWN
                    )
                    if role not in allowed_roles:
                        continue
                    key = (owner_name, role)
                    phase_totals[key][phase_id] += float(total_amount)
                    if owner_name not in player_classes and owner_id is not None:
                        player_classes[owner_name] = actor_classes.get(owner_id)
                    player_roles.setdefault(owner_name, role)
                    valid_players.add(owner_name)

            damage_table = fetch_table(
                session,
                bearer,
                code=report_code,
                data_type="DamageDone",
                fight_id=fight.id,
                start=fight.start,
                end=fight.end,
                filter_expr=filter_expr,
            )
            consume_entries(damage_table.get("entries") or [], allowed_roles=damage_roles)

            healing_table = fetch_table(
                session,
                bearer,
                code=report_code,
                data_type="Healing",
                fight_id=fight.id,
                start=fight.start,
                end=fight.end,
                filter_expr=filter_expr,
            )
            consume_entries(healing_table.get("entries") or [], allowed_roles=healing_roles)

    for player, role in list(fight_ids_by_player_role.keys()):
        if player not in valid_players:
            continue
        key = (player, role)
        phase_totals.setdefault(key, defaultdict(float))
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, None)

    entries: List[PhaseDamageEntry] = []
    for player, role in sorted(
        phase_totals.keys(),
        key=lambda item: (
            ROLE_PRIORITY.get(item[1] or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            item[0].lower(),
        ),
    ):
        if player not in valid_players:
            continue
        pulls = len(fight_ids_by_player_role.get((player, role), set()))
        if pulls <= 0:
            continue
        totals_for_player = phase_totals[(player, role)]
        metrics: List[PhaseMetric] = []
        for phase_id in selected_phases:
            total_amount = totals_for_player.get(phase_id, 0.0)
            average_per_pull = total_amount / pulls if pulls else 0.0
            metrics.append(
                PhaseMetric(
                    phase_id=phase_id,
                    phase_label=phase_labels.get(phase_id, phase_id),
                    total_amount=total_amount,
                    average_per_pull=average_per_pull,
                )
            )
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, None)
        entries.append(
            PhaseDamageEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                metrics=metrics,
            )
        )

    return PhaseDamageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=fight_id_filter,
        phases=selected_phases,
        phase_labels={phase: phase_labels.get(phase, phase) for phase in selected_phases},
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        pull_count=len(chosen),
        source_reports=[report_code],
        fight_signature=[
            (fight.name, bool(fight.kill), int(fight.end - fight.start)) for fight in chosen
        ],
    )


def fetch_phase_damage_summary(
    *,
    report_code: str,
    phases: Optional[Iterable[str]] = None,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    phase_profile: Optional[str] = None,
) -> PhaseDamageSummary:
    phase_labels = _resolve_phase_labels(phase_profile)
    primary_code = _sanitize_report_code(report_code)
    primary_summary = _fetch_phase_damage_summary_single(
        report_code=primary_code,
        phases=phases,
        fight_name=fight_name,
        fight_ids=fight_ids,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        phase_labels=phase_labels,
    )

    extra_codes: List[str] = []
    if extra_report_codes:
        for code in extra_report_codes:
            if not code:
                continue
            try:
                code_str = _sanitize_report_code(code)
            except ValueError:
                continue
            if code_str == primary_code or code_str in extra_codes:
                continue
            extra_codes.append(code_str)

    if not extra_codes:
        return primary_summary

    summaries: List[PhaseDamageSummary] = [primary_summary]
    for extra_code in extra_codes:
        extra_summary = _fetch_phase_damage_summary_single(
            report_code=extra_code,
            phases=phases,
            fight_name=fight_name,
            fight_ids=fight_ids,
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            phase_labels=phase_labels,
        )
        summaries.append(extra_summary)

    base_signature = primary_summary.fight_signature
    base_phases = list(primary_summary.phases)
    for other in summaries[1:]:
        if base_phases != list(other.phases):
            raise FightSelectionError(
                "Additional report uses a different phase configuration than the primary report."
            )
        if len(base_signature) != len(other.fight_signature):
            raise FightSelectionError(
                "Additional report does not contain the same number of pulls as the primary report."
            )
        for idx, (base_fight, other_fight) in enumerate(zip(base_signature, other.fight_signature), start=1):
            base_name, base_kill, base_duration = base_fight
            other_name, other_kill, other_duration = other_fight
            if base_name != other_name or base_kill != other_kill:
                raise FightSelectionError(
                    f"Additional report pull #{idx} does not match the primary report (encounter mismatch)."
                )
            duration_delta = abs(base_duration - other_duration)
            if duration_delta > 15000:
                raise FightSelectionError(
                    f"Additional report pull #{idx} duration differs significantly from the primary report."
                )

    phase_ids = list(primary_summary.phases)
    phase_labels = dict(primary_summary.phase_labels)
    combined_totals: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    combined_pulls: Dict[Tuple[str, str], int] = {}
    combined_classes: Dict[str, Optional[str]] = dict(primary_summary.player_classes)
    combined_roles: Dict[str, str] = dict(primary_summary.player_roles)
    combined_specs: Dict[str, Optional[str]] = dict(primary_summary.player_specs)

    def merge_entry(summary: PhaseDamageSummary, entry: PhaseDamageEntry) -> None:
        key = (entry.player, entry.role)
        combined_pulls[key] = max(combined_pulls.get(key, 0), entry.pulls)
        if entry.player not in combined_classes or combined_classes[entry.player] is None:
            combined_classes[entry.player] = summary.player_classes.get(entry.player)
        if entry.player not in combined_roles or combined_roles.get(entry.player) in (None, ROLE_UNKNOWN):
            combined_roles[entry.player] = entry.role
        combined_specs.setdefault(entry.player, summary.player_specs.get(entry.player))
        totals = combined_totals[key]
        for metric in entry.metrics:
            if metric.phase_id not in phase_ids:
                continue
            totals[metric.phase_id] = max(totals.get(metric.phase_id, 0.0), metric.total_amount)

    for summary in summaries:
        for player, class_name in summary.player_classes.items():
            if player not in combined_classes or combined_classes[player] is None:
                combined_classes[player] = class_name
        for player, role in summary.player_roles.items():
            if player not in combined_roles or combined_roles[player] in (None, ROLE_UNKNOWN):
                combined_roles[player] = role
        for player, spec in summary.player_specs.items():
            if player not in combined_specs or combined_specs[player] is None:
                combined_specs[player] = spec
        for entry in summary.entries:
            merge_entry(summary, entry)

    merged_entries: List[PhaseDamageEntry] = []
    for (player, role), totals in combined_totals.items():
        pulls = combined_pulls.get((player, role), primary_summary.pull_count)
        metrics: List[PhaseMetric] = []
        for phase_id in phase_ids:
            total_amount = totals.get(phase_id, 0.0)
            average = total_amount / pulls if pulls else 0.0
            metrics.append(
                PhaseMetric(
                    phase_id=phase_id,
                    phase_label=phase_labels.get(phase_id, NEXUS_PHASE_LABELS.get(phase_id, phase_id)),
                    total_amount=total_amount,
                    average_per_pull=average,
                )
            )
        merged_entries.append(
            PhaseDamageEntry(
                player=player,
                role=role,
                class_name=combined_classes.get(player),
                pulls=pulls,
                metrics=metrics,
            )
        )

    merged_entries.sort(
        key=lambda entry: (
            ROLE_PRIORITY.get(entry.role or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            entry.player.lower(),
        )
    )

    all_reports = [primary_code] + extra_codes

    return PhaseDamageSummary(
        report_code=primary_code,
        fight_filter=primary_summary.fight_filter,
        fight_ids=primary_summary.fight_ids,
        phases=phase_ids,
        phase_labels=phase_labels,
        entries=merged_entries,
        player_classes=combined_classes,
        player_roles=combined_roles,
        player_specs=combined_specs,
        pull_count=primary_summary.pull_count,
        source_reports=all_reports,
        fight_signature=base_signature,
    )
