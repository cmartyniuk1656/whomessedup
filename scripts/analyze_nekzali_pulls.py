"""Build a compact Mythic Nek'zali pull-analysis snapshot from Warcraft Logs.

This is an investigation tool, not an application endpoint.  It deliberately
stores derived metrics instead of raw combat events so a raid lead can review,
diff, and annotate the result without committing an enormous log export.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Iterator

import requests

from who_messed_up.api import fetch_player_details, fetch_tables, get_token_from_client, gql
from who_messed_up.env import load_env
from who_messed_up.services.common import _infer_player_roles


ENCOUNTER_ID = 3470
MYTHIC_DIFFICULTY = 5

SOULCOIL_IGNITION = 1293664
RITUAL_OF_AWAKENING = 1295124
INVOKE = 1299673
UNCOILED_RAGE = 1284034
SOULCOILERS_CURSE = 1300238
SOULCOILED_IDS = {1290361, 1292751, 1311788}
GRASPING_DEPTHS = 1293214
IMMORTAL_COIL_DAMAGE = 1308227
SOUL_EXHAUSTION = 1300235
SOUL_EXHAUSTION_DURATION_MS = 60_000
SWIRLING_SPIRIT = 1300239
SOULCOIL_RITE = 1288772
CORPSE_BLIGHT = 1307939
VESSEL_OF_AWAKENING = 1297630
SOULCOIL_WELL = 1290390
LATENT_CULTIST = 1288554
ANGUISHED_ECHOES = 1294846
SOUL_TRANSFER = 1295085
POSSESSION_BARRAGE = 1292034
HUNGERING_PYRE = 1289855
CREMATION = 1289875
SLITHERING_FLAME = 1294933
UNCOILING = 1292315

MECHANIC_DAMAGE_IDS = {
    GRASPING_DEPTHS,
    IMMORTAL_COIL_DAMAGE,
    SWIRLING_SPIRIT,
    SOULCOIL_RITE,
    CORPSE_BLIGHT,
    VESSEL_OF_AWAKENING,
    SOULCOIL_WELL,
    LATENT_CULTIST,
    ANGUISHED_ECHOES,
    SOUL_TRANSFER,
    POSSESSION_BARRAGE,
    HUNGERING_PYRE,
    CREMATION,
    SLITHERING_FLAME,
    UNCOILING,
}

HEALING_COOLDOWN_IDS = {
    740,       # Tranquility
    62618,     # Power Word: Barrier
    64843,     # Divine Hymn
    98008,     # Spirit Link Totem
    108280,    # Healing Tide Totem
    108281,    # Ancestral Guidance
    114052,    # Ascendance
    197721,    # Flourish
    33891,     # Incarnation: Tree of Life
    357170,    # Time Dilation
    359816,    # Dream Flight
    363534,    # Rewind
    370537,    # Stasis
    370564,    # Stasis release
    370960,    # Emerald Communion
    374227,    # Zephyr
    421453,    # Ultimate Penitence
    47788,     # Guardian Spirit
}

DEFENSIVE_AND_RAID_UTILITY_IDS = HEALING_COOLDOWN_IDS | {
    871, 12975, 22812, 48707, 48792, 61336, 642, 45438, 186265, 196555,
    104773, 108271, 198589, 363916, 374348, 122278, 122783,
}

OVERVIEW_QUERY = """
query($code: String!) {
  reportData {
    report(code: $code) {
      title
      startTime
      endTime
      fights {
        id encounterID name startTime endTime kill difficulty bossPercentage
        fightPercentage averageItemLevel wipeCalledTime friendlyPlayers friendlySpecs
      }
      masterData {
        actors { id name type subType petOwner }
        abilities { gameID name }
      }
    }
  }
}
"""

EVENTS_QUERY = """
query(
  $code: String!, $dataType: EventDataType!, $hostilityType: HostilityType!,
  $start: Float!, $end: Float!, $limit: Int!, $filter: String,
  $fightIDs: [Int!], $includeResources: Boolean
) {
  reportData {
    report(code: $code) {
      events(
        dataType: $dataType, hostilityType: $hostilityType,
        startTime: $start, endTime: $end, limit: $limit,
        filterExpression: $filter, fightIDs: $fightIDs,
        includeResources: $includeResources, useActorIDs: true
      ) { data nextPageTimestamp }
    }
  }
}
"""


@dataclass(frozen=True)
class Selection:
    report_code: str
    fight_ids: tuple[int, ...] | None
    label: str
    cohort: str


def _parse_selection(raw: str, *, cohort: str) -> Selection:
    parts = raw.split(":", 2)
    code = parts[0].strip()
    fight_ids = None
    label = code
    if len(parts) >= 2 and parts[1].strip():
        fight_ids = tuple(int(value) for value in parts[1].split(","))
    if len(parts) == 3 and parts[2].strip():
        label = parts[2].strip()
    return Selection(code, fight_ids, label, cohort)


def _event_ability(event: dict[str, Any]) -> int | None:
    value = event.get("abilityGameID")
    if value is None and isinstance(event.get("ability"), dict):
        value = event["ability"].get("gameID") or event["ability"].get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _event_amount(event: dict[str, Any]) -> float:
    try:
        return float(event.get("amount") or 0) + float(event.get("absorbed") or 0)
    except (TypeError, ValueError):
        return 0.0


def _actor_name(event: dict[str, Any], side: str, actor_names: dict[int, str]) -> str:
    direct = event.get(f"{side}Name")
    if direct:
        return str(direct)
    actor = event.get(side)
    if isinstance(actor, dict) and actor.get("name"):
        return str(actor["name"])
    try:
        return actor_names.get(int(event.get(f"{side}ID")), "Unknown")
    except (TypeError, ValueError):
        return "Unknown"


def _offset(timestamp: float, fight: dict[str, Any]) -> float:
    return round((float(timestamp) - float(fight["startTime"])) / 1000.0, 3)


def _format_filter_ids(ids: Iterable[int]) -> str:
    return "ability.id in (" + ",".join(str(value) for value in sorted(set(ids))) + ")"


def _fetch_events(
    session: requests.Session,
    token: str,
    *,
    code: str,
    data_type: str,
    hostility_type: str,
    fights: list[dict[str, Any]],
    filter_expression: str | None = None,
    include_resources: bool = False,
) -> Iterator[dict[str, Any]]:
    start = min(float(fight["startTime"]) for fight in fights)
    end = max(float(fight["endTime"]) for fight in fights)
    cursor = start
    while True:
        payload = gql(
            session,
            token,
            EVENTS_QUERY,
            {
                "code": code,
                "dataType": data_type,
                "hostilityType": hostility_type,
                "start": cursor,
                "end": end,
                "limit": 10000,
                "filter": filter_expression,
                "fightIDs": [int(fight["id"]) for fight in fights],
                "includeResources": include_resources,
            },
        )
        paginator = payload["reportData"]["report"]["events"]
        yield from paginator.get("data") or []
        next_timestamp = paginator.get("nextPageTimestamp")
        if next_timestamp is None or float(next_timestamp) >= end:
            break
        if float(next_timestamp) <= cursor:
            raise RuntimeError(f"WCL pagination did not advance for {code}/{data_type}")
        cursor = float(next_timestamp)


def _group_by_fight(
    events: Iterable[dict[str, Any]], fights: list[dict[str, Any]]
) -> dict[int, list[dict[str, Any]]]:
    grouped = {int(fight["id"]): [] for fight in fights}
    for event in events:
        fight_id = event.get("fight")
        try:
            fight_id = int(fight_id)
        except (TypeError, ValueError):
            timestamp = float(event.get("timestamp") or -1)
            fight_id = next(
                (
                    int(fight["id"])
                    for fight in fights
                    if float(fight["startTime"]) <= timestamp <= float(fight["endTime"])
                ),
                None,
            )
        if fight_id in grouped:
            grouped[fight_id].append(event)
    return grouped


def _cluster_timestamps(timestamps: Iterable[float], *, max_gap_ms: float) -> list[list[float]]:
    clusters: list[list[float]] = []
    for timestamp in sorted(set(float(value) for value in timestamps)):
        if not clusters or timestamp - clusters[-1][-1] > max_gap_ms:
            clusters.append([timestamp])
        else:
            clusters[-1].append(timestamp)
    return clusters


def _target_windows(
    events: list[dict[str, Any]],
    *,
    target_name: str,
    actor_names: dict[int, str],
    fight: dict[str, Any],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if _actor_name(event, "target", actor_names) != target_name:
            continue
        try:
            key = (int(event.get("targetID") or 0), int(event.get("targetInstance") or 0))
        except (TypeError, ValueError):
            continue
        grouped[key].append(event)

    windows = []
    split_groups: list[tuple[int, int, list[dict[str, Any]]]] = []
    for (target_id, target_instance), rows in grouped.items():
        rows.sort(key=lambda event: float(event["timestamp"]))
        # WCL can recycle the same actor/instance pair for later spawns.  A
        # fresh add is therefore identified by a quiet gap as well as its IDs.
        chunks: list[list[dict[str, Any]]] = []
        for event in rows:
            if not chunks or float(event["timestamp"]) - float(chunks[-1][-1]["timestamp"]) > 15000:
                chunks.append([event])
            else:
                chunks[-1].append(event)
        split_groups.extend((target_id, target_instance, chunk) for chunk in chunks)

    for target_id, target_instance, rows in split_groups:
        by_player: dict[str, float] = defaultdict(float)
        max_hp = 0.0
        last_hp = None
        for event in rows:
            by_player[_actor_name(event, "source", actor_names)] += _event_amount(event)
            try:
                max_hp = max(max_hp, float(event.get("maxHitPoints") or 0))
            except (TypeError, ValueError):
                pass
            if event.get("hitPoints") is not None:
                try:
                    last_hp = float(event["hitPoints"])
                except (TypeError, ValueError):
                    pass
        first = float(rows[0]["timestamp"])
        last = float(rows[-1]["timestamp"])
        total = sum(by_player.values())
        windows.append(
            {
                "target_id": target_id,
                "target_instance": target_instance,
                "first_hit_s": _offset(first, fight),
                "last_hit_s": _offset(last, fight),
                "active_damage_s": round((last - first) / 1000.0, 3),
                "damage": round(total),
                "max_hp": round(max_hp) if max_hp else None,
                "last_hp": round(last_hp) if last_hp is not None else None,
                "killed": bool(
                    (last_hp is not None and last_hp <= 0)
                    or (max_hp and total >= max_hp * 0.98)
                ),
                "players": [
                    {"name": name, "damage": round(amount), "share": round(amount / total, 4) if total else 0}
                    for name, amount in sorted(by_player.items(), key=lambda item: (-item[1], item[0]))
                    if name != "Unknown"
                ],
                "_first_ms": first,
                "_last_ms": last,
            }
        )
    windows.sort(key=lambda row: row["_first_ms"])
    return windows


def _mechanic_damage_summary(
    events: list[dict[str, Any]], actor_names: dict[int, str], player_ids: set[int]
) -> dict[str, dict[str, Any]]:
    totals: dict[int, float] = defaultdict(float)
    hits: Counter[int] = Counter()
    players: dict[int, set[str]] = defaultdict(set)
    for event in events:
        try:
            if int(event.get("targetID")) not in player_ids:
                continue
        except (TypeError, ValueError):
            continue
        ability_id = _event_ability(event)
        if ability_id not in MECHANIC_DAMAGE_IDS:
            continue
        amount = _event_amount(event)
        totals[ability_id] += amount
        hits[ability_id] += 1
        players[ability_id].add(_actor_name(event, "target", actor_names))
    return {
        str(ability_id): {
            "damage": round(totals[ability_id]),
            "hits": hits[ability_id],
            "players": len(players[ability_id]),
        }
        for ability_id in sorted(totals)
    }


def _mechanic_hit_clusters(
    events: list[dict[str, Any]],
    death_events: list[dict[str, Any]],
    *,
    ability_id: int,
    actor_names: dict[int, str],
    player_ids: set[int],
    fight: dict[str, Any],
    max_gap_ms: float,
) -> list[dict[str, Any]]:
    relevant = []
    for event in events:
        if _event_ability(event) != ability_id:
            continue
        try:
            if int(event.get("targetID")) not in player_ids:
                continue
        except (TypeError, ValueError):
            continue
        relevant.append(event)
    clusters: list[list[dict[str, Any]]] = []
    for event in sorted(relevant, key=lambda row: float(row["timestamp"])):
        if not clusters or float(event["timestamp"]) - float(clusters[-1][-1]["timestamp"]) > max_gap_ms:
            clusters.append([event])
        else:
            clusters[-1].append(event)

    results = []
    for cluster in clusters:
        start = float(cluster[0]["timestamp"])
        end = float(cluster[-1]["timestamp"])
        amounts = [_event_amount(event) for event in cluster]
        targets = sorted({_actor_name(event, "target", actor_names) for event in cluster})
        player_hits: Counter[str] = Counter()
        player_damage: dict[str, float] = defaultdict(float)
        player_max_hit: dict[str, float] = defaultdict(float)
        for event in cluster:
            player = _actor_name(event, "target", actor_names)
            amount = _event_amount(event)
            player_hits[player] += 1
            player_damage[player] += amount
            player_max_hit[player] = max(player_max_hit[player], amount)
        source_instances = sorted(
            {
                (
                    _actor_name(event, "source", actor_names),
                    int(event.get("sourceInstance") or 0),
                )
                for event in cluster
                if event.get("sourceID") is not None
            }
        )
        killed = []
        for event in death_events:
            timestamp = float(event.get("timestamp") or -1)
            if not start - 500 <= timestamp <= end + 1000:
                continue
            if int(event.get("killingAbilityGameID") or 0) != ability_id:
                continue
            killed.append(_actor_name(event, "target", actor_names))
        results.append(
            {
                "start_s": _offset(start, fight),
                "end_s": _offset(end, fight),
                "hits": len(cluster),
                "players": targets,
                "player_breakdown": [
                    {
                        "player": player,
                        "hits": player_hits[player],
                        "damage": round(player_damage[player]),
                        "max_hit": round(player_max_hit[player]),
                    }
                    for player in sorted(
                        targets, key=lambda name: (-player_damage[name], name)
                    )
                ],
                "sources": [
                    {"name": name, "instance": instance}
                    for name, instance in source_instances
                ],
                "total_damage": round(sum(amounts)),
                "max_hit": round(max(amounts, default=0)),
                "killed": sorted(set(killed)),
            }
        )
    return results


def _healing_table_summary(table: dict[str, Any]) -> dict[str, Any]:
    healer_rows = []
    for entry in table.get("entries") or []:
        total = float(entry.get("total") or 0)
        overheal = float(entry.get("overheal") or 0)
        if total <= 0:
            continue
        healer_rows.append(
            {"name": entry.get("name"), "healing": round(total), "overheal": round(overheal)}
        )
    healer_rows.sort(key=lambda row: (-row["healing"], str(row["name"])))
    return {
        "healing": sum(row["healing"] for row in healer_rows),
        "overheal": sum(row["overheal"] for row in healer_rows),
        "players": healer_rows,
    }


def _damage_table_summary(table: dict[str, Any]) -> dict[str, Any]:
    target_totals: dict[str, float] = defaultdict(float)
    player_totals: dict[str, float] = defaultdict(float)
    for entry in table.get("entries") or []:
        name = str(entry.get("name") or "Unknown")
        player_totals[name] += float(entry.get("total") or 0)
        for target in entry.get("targets") or []:
            target_totals[str(target.get("name") or "Unknown")] += float(target.get("total") or 0)
    return {
        "targets": {name: round(value) for name, value in sorted(target_totals.items())},
        "players": [
            {"name": name, "damage": round(value)}
            for name, value in sorted(player_totals.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def _analyze_selection(
    session: requests.Session, token: str, selection: Selection
) -> dict[str, Any]:
    report = gql(session, token, OVERVIEW_QUERY, {"code": selection.report_code})["reportData"]["report"]
    if not report:
        raise ValueError(f"Report {selection.report_code} was not found or is inaccessible")
    fights = [
        fight
        for fight in report.get("fights") or []
        if int(fight.get("encounterID") or 0) == ENCOUNTER_ID
        and int(fight.get("difficulty") or 0) == MYTHIC_DIFFICULTY
        and (selection.fight_ids is None or int(fight["id"]) in selection.fight_ids)
    ]
    if not fights:
        raise ValueError(f"No selected Mythic Nek'zali fights in {selection.report_code}")

    actors = {int(actor["id"]): actor for actor in report["masterData"].get("actors") or []}
    actor_names = {actor_id: str(actor.get("name") or actor_id) for actor_id, actor in actors.items()}
    abilities = {
        int(ability["gameID"]): str(ability.get("name") or ability["gameID"])
        for ability in report["masterData"].get("abilities") or []
    }

    enemy_casts = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="Casts",
            hostility_type="Enemies", fights=fights,
        ),
        fights,
    )
    drowned_damage = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="DamageDone",
            hostility_type="Friendlies", fights=fights,
            filter_expression='target.name = "Drowned Echo"', include_resources=True,
        ),
        fights,
    )
    jawae_damage = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="DamageDone",
            hostility_type="Friendlies", fights=fights,
            filter_expression='target.name = "Echo of Jawae"', include_resources=True,
        ),
        fights,
    )
    damage_taken = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="DamageTaken",
            hostility_type="Friendlies", fights=fights,
            filter_expression=_format_filter_ids(MECHANIC_DAMAGE_IDS), include_resources=True,
        ),
        fights,
    )
    debuffs = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="Debuffs",
            hostility_type="Friendlies", fights=fights,
            filter_expression=_format_filter_ids(
                {SOUL_EXHAUSTION, SWIRLING_SPIRIT} | SOULCOILED_IDS
            ),
        ),
        fights,
    )
    deaths = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="Deaths",
            hostility_type="Friendlies", fights=fights,
        ),
        fights,
    )
    interrupts = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="Interrupts",
            hostility_type="Friendlies", fights=fights,
        ),
        fights,
    )
    friendly_casts = _group_by_fight(
        _fetch_events(
            session, token, code=selection.report_code, data_type="Casts",
            hostility_type="Friendlies", fights=fights,
            filter_expression=_format_filter_ids(DEFENSIVE_AND_RAID_UTILITY_IDS),
        ),
        fights,
    )

    fight_results = []
    table_requests: list[dict[str, Any]] = []
    table_plan: list[tuple[int, str, float]] = []
    derived_by_fight: dict[int, dict[str, Any]] = {}
    for fight in fights:
        fight_id = int(fight["id"])
        player_ids = {int(value) for value in fight.get("friendlyPlayers") or []}
        casts = enemy_casts[fight_id]
        drowned = _target_windows(
            drowned_damage[fight_id], target_name="Drowned Echo", actor_names=actor_names, fight=fight
        )
        jawae = _target_windows(
            jawae_damage[fight_id], target_name="Echo of Jawae", actor_names=actor_names, fight=fight
        )

        grasp_clusters = _cluster_timestamps(
            (
                float(event["timestamp"])
                for event in damage_taken[fight_id]
                if _event_ability(event) == GRASPING_DEPTHS
                and event.get("targetID") in player_ids
            ),
            max_gap_ms=5000,
        )
        grasp_windows = [
            {
                "start_ms": cluster[0],
                "end_ms": cluster[-1] + 1000,
                "start_s": _offset(cluster[0], fight),
                "end_s": _offset(cluster[-1] + 1000, fight),
                "duration_s": round((cluster[-1] + 1000 - cluster[0]) / 1000.0, 3),
            }
            for cluster in grasp_clusters
        ]

        mechanic_casts = []
        for event in casts:
            ability_id = _event_ability(event)
            if ability_id not in {
                SOULCOIL_IGNITION, RITUAL_OF_AWAKENING, INVOKE, UNCOILED_RAGE,
                SOULCOILERS_CURSE, HUNGERING_PYRE,
            }:
                continue
            event_type = str(event.get("type") or "")
            if event_type not in {"begincast", "cast"}:
                continue
            mechanic_casts.append(
                {
                    "time_s": _offset(event["timestamp"], fight),
                    "type": event_type,
                    "ability_id": ability_id,
                    "ability": abilities.get(ability_id, str(ability_id)),
                    "source_instance": event.get("sourceInstance"),
                }
            )

        first_p2 = next(
            (
                float(event["timestamp"])
                for event in casts
                if _event_ability(event) == INVOKE and event.get("type") == "begincast"
            ),
            None,
        )
        intermission_start = next(
            (
                float(event["timestamp"])
                for event in casts
                if _event_ability(event) == RITUAL_OF_AWAKENING and event.get("type") == "begincast"
            ),
            None,
        )

        exhaustion_events = []
        for event in debuffs[fight_id]:
            if _event_ability(event) != SOUL_EXHAUSTION:
                continue
            try:
                target_id = int(event.get("targetID"))
            except (TypeError, ValueError):
                continue
            if target_id not in player_ids:
                continue
            exhaustion_events.append(
                {
                    "time_s": _offset(event["timestamp"], fight),
                    "type": event.get("type"),
                    "player": actor_names.get(target_id, str(target_id)),
                    "_time_ms": float(event["timestamp"]),
                }
            )

        swirling_aura_events = []
        slithering_flame_aura_events = []
        for event in debuffs[fight_id]:
            ability_id = _event_ability(event)
            if ability_id not in {SWIRLING_SPIRIT, SLITHERING_FLAME}:
                continue
            try:
                target_id = int(event.get("targetID"))
            except (TypeError, ValueError):
                continue
            if target_id not in player_ids:
                continue
            row = {
                "time_s": _offset(event["timestamp"], fight),
                "type": event.get("type"),
                "player": actor_names.get(target_id, str(target_id)),
                "stack": event.get("stack"),
            }
            if ability_id == SWIRLING_SPIRIT:
                swirling_aura_events.append(row)
            else:
                slithering_flame_aura_events.append(row)

        soulcoiled_aura_events = []
        for event in debuffs[fight_id]:
            ability_id = _event_ability(event)
            if ability_id not in SOULCOILED_IDS:
                continue
            try:
                target_id = int(event.get("targetID"))
            except (TypeError, ValueError):
                continue
            if target_id not in player_ids:
                continue
            soulcoiled_aura_events.append(
                {
                    "time_s": _offset(event["timestamp"], fight),
                    "type": event.get("type"),
                    "ability_id": ability_id,
                    "player": actor_names.get(target_id, str(target_id)),
                }
            )

        interrupt_rows = []
        for event in interrupts[fight_id]:
            if int(event.get("extraAbilityGameID") or 0) != SOULCOILERS_CURSE:
                continue
            interrupt_rows.append(
                {
                    "time_s": _offset(event["timestamp"], fight),
                    "player": _actor_name(event, "source", actor_names),
                    "target_instance": event.get("targetInstance"),
                }
            )

        # Grasping Depths windows are the authoritative measure of how long the
        # raid remains under pressure.  Do not pair these positionally with NPC
        # actor instances: WCL omits some phased target streams and recycles
        # instance IDs, so positional pairing silently corrupts later windows.
        exhaustion_sorted = sorted(exhaustion_events, key=lambda row: row["_time_ms"])

        def exhaustion_at(player: str, timestamp: float) -> dict[str, Any] | None:
            active = False
            applied_ms = None
            for row in exhaustion_sorted:
                if row["_time_ms"] > timestamp:
                    break
                if row["player"] != player:
                    continue
                if row["type"] in {"applydebuff", "refreshdebuff", "applydebuffstack"}:
                    active = True
                    applied_ms = row["_time_ms"]
                elif row["type"] == "removedebuff":
                    active = False
                    applied_ms = None
            if not active:
                return None
            removal_ms = next(
                (
                    row["_time_ms"]
                    for row in exhaustion_sorted
                    if row["player"] == player
                    and row["_time_ms"] > timestamp
                    and row["type"] == "removedebuff"
                ),
                None,
            )
            estimated_expiry_ms = (
                applied_ms + SOUL_EXHAUSTION_DURATION_MS
                if applied_ms is not None else None
            )
            if removal_ms is not None and estimated_expiry_ms is not None:
                expiry_ms = min(removal_ms, estimated_expiry_ms)
            else:
                expiry_ms = removal_ms or estimated_expiry_ms
            return {
                "player": player,
                "applied_s": _offset(applied_ms, fight) if applied_ms is not None else None,
                "remaining_s": (
                    round(max(expiry_ms - timestamp, 0) / 1000.0, 3)
                    if expiry_ms is not None else None
                ),
            }

        grasp_events = []
        for grasp_index, grasp in enumerate(grasp_windows):
            start_ms = float(grasp["start_ms"])
            end_ms = float(grasp["end_ms"])
            # When Grasp windows occur close together, the old +/- grace
            # periods overlap. Split the gap at its midpoint so an Immortal
            # Coil tick cannot make a player appear in both adjacent cycles.
            analysis_start_ms = start_ms - 3000
            analysis_end_ms = end_ms + 15000
            if grasp_index:
                previous_end_ms = float(grasp_windows[grasp_index - 1]["end_ms"])
                analysis_start_ms = max(
                    analysis_start_ms, (previous_end_ms + start_ms) / 2
                )
            if grasp_index + 1 < len(grasp_windows):
                next_start_ms = float(grasp_windows[grasp_index + 1]["start_ms"])
                analysis_end_ms = min(
                    analysis_end_ms, (end_ms + next_start_ms) / 2
                )
            immortal_ticks: dict[str, list[float]] = defaultdict(list)
            for event in damage_taken[fight_id]:
                if _event_ability(event) != IMMORTAL_COIL_DAMAGE:
                    continue
                timestamp = float(event["timestamp"])
                if not analysis_start_ms <= timestamp < analysis_end_ms:
                    continue
                try:
                    target_id = int(event.get("targetID"))
                except (TypeError, ValueError):
                    continue
                if target_id in player_ids:
                    immortal_ticks[actor_names.get(target_id, str(target_id))].append(timestamp)

            entry_times = {player: min(times) for player, times in immortal_ticks.items()}
            first_five_entrants = [
                player
                for player, _timestamp in sorted(
                    entry_times.items(), key=lambda item: item[1]
                )[:5]
            ]
            exhaustion_at_grasp_start = [
                state
                for player in first_five_entrants
                if (state := exhaustion_at(player, start_ms)) is not None
            ]
            max_exhaustion_remaining_at_grasp_start = max(
                (float(state["remaining_s"] or 0) for state in exhaustion_at_grasp_start),
                default=0.0,
            )
            clean_time_ms = min(
                start_ms + max_exhaustion_remaining_at_grasp_start * 1000,
                end_ms,
            )
            grasp_damage_until_clean = sum(
                _event_amount(event)
                for event in damage_taken[fight_id]
                if _event_ability(event) == GRASPING_DEPTHS
                and start_ms <= float(event["timestamp"]) < clean_time_ms
            )
            first_entry_ms = min(entry_times.values(), default=None)
            wait_end_ms = (
                min(first_entry_ms, end_ms)
                if first_entry_ms is not None else end_ms
            )
            grasp_damage_before_first_entry = sum(
                _event_amount(event)
                for event in damage_taken[fight_id]
                if _event_ability(event) == GRASPING_DEPTHS
                and start_ms <= float(event["timestamp"]) < wait_end_ms
            )
            grasp_damage_total = sum(
                _event_amount(event)
                for event in damage_taken[fight_id]
                if _event_ability(event) == GRASPING_DEPTHS
                and start_ms <= float(event["timestamp"]) < end_ms
            )
            seconds_to_first_entry = (
                max((wait_end_ms - start_ms) / 1000.0, 0.0)
                if first_entry_ms is not None else None
            )
            exit_group = sorted(
                {
                    row["player"]
                    for row in exhaustion_events
                    if start_ms <= row["_time_ms"] < analysis_end_ms
                    and row["type"] in {"applydebuff", "refreshdebuff"}
                }
            )
            entered_group = sorted(set(entry_times) | set(exit_group))
            exhaustion_at_entry = []
            realm_participation = []
            for player, timestamp in entry_times.items():
                state = exhaustion_at(player, timestamp)
                if state:
                    state["entry_s"] = _offset(timestamp, fight)
                    exhaustion_at_entry.append(state)
                realm_participation.append(
                    {
                        "player": player,
                        "entry_s": _offset(timestamp, fight),
                        "last_tick_s": _offset(max(immortal_ticks[player]), fight),
                        "entered_with_exhaustion": bool(state),
                        "exhaustion_remaining_s": (
                            state["remaining_s"] if state else None
                        ),
                    }
                )
            exhaustion_at_entry.sort(key=lambda row: row["player"])
            realm_participation.sort(key=lambda row: (row["entry_s"], row["player"]))
            entered_with_exhaustion = [row["player"] for row in exhaustion_at_entry]

            downstairs_damage: dict[str, float] = defaultdict(float)
            for event in drowned_damage[fight_id]:
                timestamp = float(event["timestamp"])
                if not analysis_start_ms <= timestamp < analysis_end_ms:
                    continue
                try:
                    source_id = int(event.get("sourceID"))
                except (TypeError, ValueError):
                    continue
                owner_id = actors.get(source_id, {}).get("petOwner")
                resolved_id = int(owner_id) if owner_id is not None else source_id
                if resolved_id not in player_ids:
                    continue
                downstairs_damage[actor_names.get(resolved_id, str(resolved_id))] += _event_amount(event)
            total_downstairs_damage = sum(downstairs_damage.values())
            grasp_events.append(
                {
                    "start_s": grasp["start_s"],
                    "end_s": grasp["end_s"],
                    "duration_s": grasp["duration_s"],
                    "max_exhaustion_remaining_at_grasp_start": round(
                        max_exhaustion_remaining_at_grasp_start, 3
                    ),
                    "grasp_damage_until_clean": round(grasp_damage_until_clean),
                    "seconds_to_first_entry": (
                        round(seconds_to_first_entry, 3)
                        if seconds_to_first_entry is not None else None
                    ),
                    "grasp_damage_before_first_entry": round(
                        grasp_damage_before_first_entry
                    ),
                    "grasp_damage_total": round(grasp_damage_total),
                    "grasp_dps_before_first_entry": (
                        round(grasp_damage_before_first_entry / seconds_to_first_entry, 1)
                        if seconds_to_first_entry else None
                    ),
                    "entered_group": entered_group,
                    "exit_group": exit_group,
                    "entered_with_exhaustion": entered_with_exhaustion,
                    "exhaustion_at_entry": exhaustion_at_entry,
                    "realm_participation": realm_participation,
                    "downstairs_damage": round(total_downstairs_damage),
                    "downstairs_players": [
                        {
                            "name": player,
                            "damage": round(amount),
                            "share": round(amount / total_downstairs_damage, 4)
                            if total_downstairs_damage else 0,
                        }
                        for player, amount in sorted(
                            downstairs_damage.items(), key=lambda item: (-item[1], item[0])
                        )
                    ],
                    "interrupts": [
                        row for row in interrupt_rows
                        if max(start_ms - 2000, analysis_start_ms)
                        <= float(fight["startTime"]) + row["time_s"] * 1000
                        < analysis_end_ms
                    ],
                }
            )

        meaningful_deaths = []
        wipe_called = fight.get("wipeCalledTime")
        wipe_abs = (
            float(fight["startTime"]) + float(wipe_called)
            if wipe_called is not None and float(wipe_called) < float(fight["startTime"])
            else (float(wipe_called) if wipe_called is not None else None)
        )
        for event in sorted(deaths[fight_id], key=lambda row: float(row["timestamp"])):
            try:
                target_id = int(event.get("targetID"))
            except (TypeError, ValueError):
                continue
            if target_id not in player_ids:
                continue
            ts = float(event["timestamp"])
            if wipe_abs is not None and ts > wipe_abs + 1500:
                continue
            ability_id = int(event.get("killingAbilityGameID") or 0) or None
            meaningful_deaths.append(
                {
                    "time_s": _offset(ts, fight),
                    "player": actor_names.get(target_id, str(target_id)),
                    "ability_id": ability_id,
                    "ability": abilities.get(ability_id, str(ability_id)) if ability_id else None,
                }
            )

        cooldowns = []
        for event in friendly_casts[fight_id]:
            if event.get("type") != "cast":
                continue
            ability_id = _event_ability(event)
            if ability_id not in DEFENSIVE_AND_RAID_UTILITY_IDS:
                continue
            try:
                source_id = int(event.get("sourceID"))
            except (TypeError, ValueError):
                continue
            if source_id not in player_ids:
                continue
            cooldowns.append(
                {
                    "time_s": _offset(event["timestamp"], fight),
                    "player": actor_names.get(source_id, str(source_id)),
                    "ability_id": ability_id,
                    "ability": abilities.get(ability_id, str(ability_id)),
                }
            )

        clustered_mechanics = {
            str(ability_id): _mechanic_hit_clusters(
                damage_taken[fight_id], deaths[fight_id], ability_id=ability_id,
                actor_names=actor_names, player_ids=player_ids, fight=fight,
                max_gap_ms=max_gap_ms,
            )
            for ability_id, max_gap_ms in {
                HUNGERING_PYRE: 5000,
                SLITHERING_FLAME: 1500,
                VESSEL_OF_AWAKENING: 2500,
                SOUL_TRANSFER: 3000,
                SWIRLING_SPIRIT: 1500,
                LATENT_CULTIST: 1500,
                ANGUISHED_ECHOES: 1500,
                POSSESSION_BARRAGE: 5000,
                SOULCOIL_WELL: 1500,
            }.items()
        }

        healing_windows = []
        for kind, starts, duration_s in (
            (
                "ignition",
                [
                    float(event["timestamp"])
                    for event in casts
                    if _event_ability(event) == SOULCOIL_IGNITION and event.get("type") == "begincast"
                ],
                15,
            ),
            (
                "invoke",
                [
                    float(event["timestamp"])
                    for event in casts
                    if _event_ability(event) == INVOKE and event.get("type") == "begincast"
                ],
                12,
            ),
        ):
            for start_ms in starts:
                healing_windows.append(
                    {
                        "kind": kind,
                        "start_ms": start_ms,
                        "end_ms": min(start_ms + duration_s * 1000, float(fight["endTime"])),
                        "start_s": _offset(start_ms, fight),
                    }
                )
        for grasp in grasp_windows:
            healing_windows.append({"kind": "grasp", **grasp})

        derived_by_fight[fight_id] = {
            "drowned": drowned,
            "jawae": jawae,
            "grasp_windows": grasp_windows,
            "healing_windows": healing_windows,
        }
        table_requests.append(
            {
                "data_type": "DamageDone", "fight_ids": [fight_id],
                "start": float(fight["startTime"]), "end": float(fight["endTime"]),
                "filter_expr": None,
            }
        )
        table_plan.append((fight_id, "damage", 0))
        table_requests.append(
            {
                "data_type": "Healing", "fight_ids": [fight_id],
                "start": float(fight["startTime"]), "end": float(fight["endTime"]),
                "filter_expr": None,
            }
        )
        table_plan.append((fight_id, "healing", 0))
        for window_index, window in enumerate(healing_windows):
            table_requests.append(
                {
                    "data_type": "Healing", "fight_ids": [fight_id],
                    "start": window["start_ms"], "end": window["end_ms"],
                    "filter_expr": None,
                }
            )
            table_plan.append((fight_id, "window", float(window_index)))

        duration_s = (float(fight["endTime"]) - float(fight["startTime"])) / 1000.0
        fight_results.append(
            {
                "fight_id": fight_id,
                "url": f"https://www.warcraftlogs.com/reports/{selection.report_code}#fight={fight_id}",
                "kill": bool(fight.get("kill")),
                "duration_s": round(duration_s, 3),
                "boss_percentage": fight.get("bossPercentage"),
                "average_item_level": fight.get("averageItemLevel"),
                "intermission_start_s": _offset(intermission_start, fight) if intermission_start else None,
                "phase_two_start_s": _offset(first_p2, fight) if first_p2 else None,
                "intermission_duration_s": (
                    round((first_p2 - intermission_start) / 1000.0, 3)
                    if first_p2 and intermission_start else None
                ),
                "mechanic_casts": mechanic_casts,
                "grasp_events": grasp_events,
                "drowned_echoes": drowned,
                "echoes_of_jawae": jawae,
                "mechanic_damage": _mechanic_damage_summary(
                    damage_taken[fight_id], actor_names, player_ids
                ),
                "mechanic_hit_clusters": clustered_mechanics,
                "soul_exhaustion_auras": [
                    {
                        "time_s": row["time_s"],
                        "type": row["type"],
                        "player": row["player"],
                    }
                    for row in exhaustion_events
                ],
                "swirling_spirit_auras": swirling_aura_events,
                "slithering_flame_auras": slithering_flame_aura_events,
                "soulcoiled_auras": soulcoiled_aura_events,
                "deaths_before_wipe": meaningful_deaths,
                "healing_cooldowns_and_defensives": cooldowns,
            }
        )

    tables = fetch_tables(
        session, token, code=selection.report_code, table_requests=table_requests, batch_size=8
    )
    result_by_id = {int(result["fight_id"]): result for result in fight_results}
    for (fight_id, kind, index_value), table in zip(table_plan, tables):
        result = result_by_id[fight_id]
        if kind == "damage":
            result["damage_done"] = _damage_table_summary(table)
        elif kind == "healing":
            summary = _healing_table_summary(table)
            summary["hps"] = round(summary["healing"] / result["duration_s"], 1)
            result["healing"] = summary
        else:
            index = int(index_value)
            window = derived_by_fight[fight_id]["healing_windows"][index]
            summary = _healing_table_summary(table)
            duration_s = max((window["end_ms"] - window["start_ms"]) / 1000.0, 0.001)
            summary.update(
                {
                    "kind": window["kind"],
                    "start_s": window["start_s"],
                    "duration_s": round(duration_s, 3),
                    "hps": round(summary["healing"] / duration_s, 1),
                }
            )
            result.setdefault("healing_windows", []).append(summary)

    # Drop private sort keys from the persisted output.
    for result in fight_results:
        for key in ("drowned_echoes", "echoes_of_jawae"):
            for row in result[key]:
                row.pop("_first_ms", None)
                row.pop("_last_ms", None)

    details = fetch_player_details(
        session, token, code=selection.report_code, fight_ids=[int(fight["id"]) for fight in fights]
    )
    roles, specs = _infer_player_roles(details)
    return {
        "label": selection.label,
        "cohort": selection.cohort,
        "report_code": selection.report_code,
        "report_title": report.get("title"),
        "roles": roles,
        "specs": specs,
        "abilities": {str(key): value for key, value in sorted(abilities.items()) if key in MECHANIC_DAMAGE_IDS | DEFENSIVE_AND_RAID_UTILITY_IDS | {SOULCOIL_IGNITION, RITUAL_OF_AWAKENING, INVOKE, UNCOILED_RAGE, SOULCOILERS_CURSE}},
        "fights": fight_results,
    }


def _cohort_summary(reports: list[dict[str, Any]], cohort: str) -> dict[str, Any]:
    fights = [fight for report in reports if report["cohort"] == cohort for fight in report["fights"]]
    killed = [fight for fight in fights if fight["kill"]]
    drowned_durations = [
        grasp["duration_s"]
        for fight in killed
        for grasp in fight["grasp_events"]
        if grasp["duration_s"] >= 5 and grasp["downstairs_damage"] >= 5_000_000
    ]
    intermissions = [fight["intermission_duration_s"] for fight in killed if fight["intermission_duration_s"]]
    return {
        "fights": len(fights),
        "kills": len(killed),
        "duration_median_s": round(median([fight["duration_s"] for fight in killed]), 3) if killed else None,
        "drowned_duration_median_s": round(median(drowned_durations), 3) if drowned_durations else None,
        "intermission_duration_median_s": round(median(intermissions), 3) if intermissions else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Guild report code")
    parser.add_argument(
        "--fight-ids", help="Comma-separated guild fight IDs; defaults to every Mythic Nek'zali pull"
    )
    parser.add_argument(
        "--benchmark", action="append", default=[],
        help="CODE:FIGHT_ID:LABEL (repeatable)",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    load_env()
    token = get_token_from_client(os.getenv("WCL_CLIENT_ID"), os.getenv("WCL_CLIENT_SECRET"))
    if not token:
        raise SystemExit("Unable to obtain a Warcraft Logs token from repository credentials")

    guild_fights = tuple(int(value) for value in args.fight_ids.split(",")) if args.fight_ids else None
    selections = [Selection(args.report, guild_fights, "Guild progression", "guild")]
    selections.extend(_parse_selection(value, cohort="benchmark") for value in args.benchmark)

    session = requests.Session()
    reports = []
    for selection in selections:
        print(f"Analyzing {selection.label}: {selection.report_code}", flush=True)
        reports.append(_analyze_selection(session, token, selection))

    output = {
        "schema_version": 1,
        "encounter_id": ENCOUNTER_ID,
        "difficulty": "mythic",
        "reports": reports,
        "cohorts": {
            "guild": _cohort_summary(reports, "guild"),
            "benchmark": _cohort_summary(reports, "benchmark"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
