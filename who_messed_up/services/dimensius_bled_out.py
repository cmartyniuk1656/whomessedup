"""
Dimensius Stage One report for players who died without using consumable heals.
"""
from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, Optional

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _select_fights,
    compute_death_cutoffs,
    compute_fight_duration_ms,
)
from .dimensius_deaths import (
    DimensiusDeathEntry,
    DimensiusDeathEvent,
    DimensiusDeathSummary,
    _fetch_ability_labels,
    _resolve_killing_ability,
)

# Ability names that should count as lethal causes for this report.
BLEED_CAUSE_NAMES = {"devour", "cosmic radiation", "dark energy", "fission"}
# Helpful IDs for the abilities we already track elsewhere.
BLEED_CAUSE_IDS = {1243373, 1231002}  # Devour, Dark Energy

# Consumable heals that disqualify a player if used at any point in the pull.
CONSUMABLE_HEAL_NAMES = ["Healthstone", "Invigorating Healing Potion"]


def fetch_dimensius_bled_out_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    ignore_after_deaths: Optional[int] = None,
    bled_out_mode: str = "no_forgiveness",
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> DimensiusDeathSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)

    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids)
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
    death_cutoffs = compute_death_cutoffs(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        actor_names=actor_names,
        max_deaths=death_limit,
    )

    consumable_heals = _collect_consumable_heals(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        ability_names=CONSUMABLE_HEAL_NAMES,
        actor_names=actor_names,
    )

    ability_labels = _fetch_ability_labels(session, bearer, report_code)
    events_by_player: DefaultDict[str, List[DimensiusDeathEvent]] = defaultdict(list)
    death_counts: DefaultDict[str, int] = defaultdict(int)
    pull_index_by_fight: Dict[int, int] = {fight.id: idx + 1 for idx, fight in enumerate(chosen)}

    for fight in chosen:
        pull_duration = compute_fight_duration_ms(fight)
        fight_consumables = consumable_heals.get(fight.id, {})
        cutoff = death_cutoffs.get(fight.id) if death_cutoffs else None
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
            if cutoff is not None and ts_val > cutoff:
                continue
            target_name = event.get("targetName")
            if not target_name and isinstance(event.get("target"), dict):
                target_name = event["target"].get("name")
            if not target_name:
                continue
            ability_id, ability_label = _resolve_killing_ability(event, ability_labels)
            if not _matches_bleed_cause(ability_id, ability_label):
                continue
            player_consumables = fight_consumables.get(target_name)
            if _should_exclude_for_consumables(player_consumables, bled_out_mode):
                continue
            death_counts[target_name] += 1
            offset_ms = ts_val - float(fight.start)
            events_by_player[target_name].append(
                DimensiusDeathEvent(
                    player=target_name,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index_by_fight.get(fight.id, 0),
                    timestamp=ts_val,
                    offset_ms=offset_ms,
                    ability_id=int(ability_id) if ability_id is not None else None,
                    ability_label=ability_label,
                    label="Death",
                    pull_duration_ms=pull_duration,
                )
            )
            _append_consumable_summary_events(
                events_by_player,
                player=target_name,
                fight=fight,
                pull_index=pull_index_by_fight.get(fight.id, 0),
                reference_timestamp=ts_val,
                consumable_usage=player_consumables,
                pull_duration_ms=pull_duration,
            )

    pull_count = len(chosen)
    name_to_class: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            name_to_class[name] = actor_classes.get(actor_id)

    all_players = set(pulls_by_player.keys()) | set(events_by_player.keys())
    if not all_players and participants_by_fight:
        for participants in participants_by_fight.values():
            all_players.update(participants)

    entries: List[DimensiusDeathEntry] = []
    total_deaths = 0

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
        death_rate = deaths / pulls if pulls else 0.0
        entries.append(
            DimensiusDeathEntry(
                player=player,
                role=player_roles.get(player, ROLE_UNKNOWN),
                class_name=name_to_class.get(player),
                pulls=pulls,
                deaths=deaths,
                death_rate=death_rate,
                events=sorted(events_by_player.get(player, []), key=lambda evt: evt.timestamp),
            )
        )

    return DimensiusDeathSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=pull_count,
        ignore_after_deaths=death_limit,
        oblivion_filter="exclude_without_recent",
        bled_out_filter="no_consumable_heals",
        bled_out_mode=bled_out_mode,
        total_deaths=total_deaths,
        entries=entries,
        player_classes={player: name_to_class.get(player) for player in all_players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in all_players},
        player_specs={player: player_specs.get(player) for player in all_players},
        player_events={player: list(events) for player, events in events_by_player.items()},
        ability_labels=ability_labels,
    )


def _matches_bleed_cause(ability_id: Optional[int], ability_label: Optional[str]) -> bool:
    if ability_id is not None and ability_id in BLEED_CAUSE_IDS:
        return True
    if ability_label:
        if ability_label.lower() in BLEED_CAUSE_NAMES:
            return True
    return False


def _collect_consumable_heals(
    session: requests.Session,
    bearer: str,
    *,
    fights: Iterable[Fight],
    report_code: str,
    ability_names: Iterable[str],
    actor_names: Dict[int, str],
) -> Dict[int, Dict[str, Dict[str, List[float]]]]:
    healed_by_fight: Dict[int, Dict[str, Dict[str, List[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for ability_name in ability_names:
        for fight in fights:
            for event in fetch_events(
                session,
                bearer,
                code=report_code,
                data_type="Healing",
                start=fight.start,
                end=fight.end,
                ability_name=ability_name,
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
                healed_by_fight[fight.id][target_name][ability_name].append(ts_val)
    return healed_by_fight


def _append_consumable_summary_events(
    events_by_player: DefaultDict[str, List[DimensiusDeathEvent]],
    *,
    player: str,
    fight: Fight,
    pull_index: int,
    reference_timestamp: float,
    consumable_usage: Optional[Dict[str, List[float]]],
    pull_duration_ms: Optional[float],
) -> None:
    usage = consumable_usage or {}
    fight_start = float(fight.start)
    base_offset = reference_timestamp - fight_start
    for ability_name in CONSUMABLE_HEAL_NAMES:
        timestamps = usage.get(ability_name) or []
        if timestamps:
            for ts_val in timestamps:
                try:
                    ts_float = float(ts_val)
                except (TypeError, ValueError):
                    continue
                offset = ts_float - fight_start
                offset_seconds = offset / 1000.0
                description = f"Used at {offset_seconds:.2f}s"
                events_by_player[player].append(
                    DimensiusDeathEvent(
                        player=player,
                        fight_id=fight.id,
                        fight_name=fight.name or "",
                        pull_index=pull_index,
                        timestamp=ts_float,
                        offset_ms=offset,
                        ability_id=None,
                        ability_label=None,
                        label=ability_name,
                        description=description,
                        pull_duration_ms=pull_duration_ms,
                    )
                )
        else:
            events_by_player[player].append(
                DimensiusDeathEvent(
                    player=player,
                    fight_id=fight.id,
                    fight_name=fight.name or "",
                    pull_index=pull_index,
                    timestamp=reference_timestamp,
                    offset_ms=base_offset,
                    ability_id=None,
                    ability_label=None,
                    label=ability_name,
                    description="Not used during this pull.",
                    pull_duration_ms=pull_duration_ms,
                )
            )

def _should_exclude_for_consumables(
    player_consumables: Optional[Dict[str, List[float]]],
    mode: str,
) -> bool:
    if not player_consumables:
        return False
    has_healthstone = bool(player_consumables.get("Healthstone"))
    has_potion = bool(player_consumables.get("Invigorating Healing Potion"))
    if mode == "lenient":
        return has_healthstone or has_potion
    return has_healthstone and has_potion


__all__ = ["fetch_dimensius_bled_out_summary"]
