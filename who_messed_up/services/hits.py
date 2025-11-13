"""
Hit summary helpers shared across backend modules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

import requests

from ..analysis import HitAggregate, count_hits
from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_UNKNOWN,
    _infer_player_roles,
    _resolve_token,
    _select_fights,
)


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


__all__ = [
    "HitSummary",
    "fetch_hit_summary",
]
