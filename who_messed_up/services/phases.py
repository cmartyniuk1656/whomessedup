"""
Phase summary helpers that combine hit and ghost analyses.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

from .common import (
    DEFAULT_GHOST_MISS_MODE,
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    GhostMissMode,
    normalize_ghost_miss_mode,
)
from .ghosts import GhostEvent, fetch_ghost_summary
from .hits import fetch_hit_summary


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


__all__ = [
    "PhasePlayerEntry",
    "PhaseSummary",
    "fetch_phase_summary",
]
