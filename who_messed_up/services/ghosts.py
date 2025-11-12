"""
Ghost miss summary helpers.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

import requests

from ..env import load_env
from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    DEFAULT_GHOST_MISS_MODE,
    GhostMissMode,
    GHOST_SET_WINDOW_MS,
    normalize_ghost_miss_mode,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _select_fights,
)


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

    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    ghost_counts: Dict[str, int] = defaultdict(int)
    ghost_counts_by_fight: Dict[Tuple[int, str], int] = defaultdict(int)
    ghost_events: List[GhostEvent] = []

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

    entries.sort(
        key=lambda e: (
            ROLE_PRIORITY.get(player_roles_full.get(e.player, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -e.misses,
            e.player.lower(),
        )
    )

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


__all__ = [
    "GhostEntry",
    "GhostSummary",
    "fetch_ghost_summary",
]
