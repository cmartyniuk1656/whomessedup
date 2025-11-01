"""
Utilities for normalizing Warcraft Logs events and counting ability hits.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Pattern, Tuple

ABILITY_KEYS = [
    "ability.name",
    "abilityName",
    "spellName",
    "spell",
    "Ability",
    "Ability Name",
    "ability",
]

ABILITY_ID_KEYS = [
    "ability.guid",
    "abilityGuid",
    "abilityId",
    "Ability ID",
    "AbilityID",
    "abilityGameID",
    "spellId",
    "spellID",
]

TIMESTAMP_KEYS = [
    "timestamp",
    "time",
]

TARGET_KEYS = [
    "target.name",
    "targetName",
    "victim",
    "destName",
    "Target",
    "target",
]

SOURCE_KEYS = [
    "source.name",
    "sourceName",
    "source",
    "srcName",
    "Source",
]

TYPE_KEYS = [
    "type",
    "eventType",
    "resultType",
    "result",
]

AMOUNT_KEYS = [
    "amount",
    "value",
    "damage",
]

MISS_HINTS = {"miss", "evade", "parry", "dodge", "immune", "resist", "absorb"}


def get_deep(d: Dict[str, Any], dotted: str) -> Any:
    if "." not in dotted:
        return d.get(dotted)
    cur: Any = d
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def first_present(d: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        val = get_deep(d, key)
        if val is not None and val != "":
            return val
    return None


def normalize_event(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a raw row (JSON/CSV event) into a normalized dict that captures the fields we care about.
    """
    ability_name = first_present(row, ABILITY_KEYS)
    ability_id = first_present(row, ABILITY_ID_KEYS)
    target_name = first_present(row, TARGET_KEYS)
    source_name = first_present(row, SOURCE_KEYS)
    event_type = first_present(row, TYPE_KEYS)
    amount = first_present(row, AMOUNT_KEYS)
    fight_id = row.get("fight")
    timestamp = first_present(row, TIMESTAMP_KEYS)

    normalized_id: Optional[str] = None
    if ability_id is not None and ability_id != "":
        try:
            normalized_id = str(int(ability_id))
        except Exception:
            normalized_id = str(ability_id)

    if isinstance(amount, str):
        try:
            amount = float(amount)
        except Exception:
            amount = None

    is_miss = False
    if event_type:
        et = str(event_type).lower()
        if any(hint in et for hint in MISS_HINTS):
            is_miss = True
    for key in ("hitType", "result", "Result", "HitType"):
        value = row.get(key)
        if value and str(value).strip().lower() in MISS_HINTS:
            is_miss = True
            break

    if isinstance(timestamp, str):
        try:
            timestamp = float(timestamp)
        except Exception:
            timestamp = None

    source_id = row.get("sourceID")
    if source_id is None and isinstance(row.get("source"), dict):
        source_id = row["source"].get("id")
    target_id = row.get("targetID")
    if target_id is None and isinstance(row.get("target"), dict):
        target_id = row["target"].get("id")

    def _normalize_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return {
        "ability_name": ability_name,
        "ability_id": normalized_id,
        "target_name": target_name,
        "source_name": source_name,
        "event_type": event_type,
        "amount": amount,
        "is_miss": is_miss,
        "fight_id": fight_id,
        "timestamp": timestamp,
        "source_id": _normalize_int(source_id),
        "target_id": _normalize_int(target_id),
    }


def is_hit(ev: Dict[str, Any]) -> bool:
    if ev["is_miss"]:
        return False
    et = (ev["event_type"] or "").lower()
    if et in {"damage", "spell_damage", "range", "melee", "swing"}:
        return True
    return bool(ev["ability_name"] and ev["target_name"])


def iter_json_events(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        first_char = handle.read(1)
        handle.seek(0)
        if first_char == "[":
            data = json.load(handle)
            events = data.get("events", data)
            for item in events:
                yield item
        else:
            text = handle.read().strip()
            if text.startswith("{") and '"events"' in text[:2000]:
                obj = json.loads(text)
                events = obj.get("events", [])
                for item in events:
                    yield item
            else:
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue


def iter_csv_rows(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def iter_events_from_path(path: Path) -> Iterator[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl"}:
        yield from iter_json_events(path)
        return
    if suffix == ".csv":
        yield from iter_csv_rows(path)
        return
    try:
        iterator = iter_json_events(path)
        first = next(iterator)
    except Exception:
        yield from iter_csv_rows(path)
        return
    yield first
    for row in iterator:
        yield row


@dataclass
class HitAggregate:
    hits_by_player: Counter
    hits_by_player_ability: Dict[Tuple[str, str], int]
    hits_by_player_fight: Dict[Tuple[str, int], int]
    damage_by_player: Counter
    fight_total_hits: Dict[int, int]
    fight_total_damage: Dict[int, float]


@dataclass
class AmountAggregate:
    amount_by_actor: Dict[Any, float]
    amount_by_actor_fight: Dict[Tuple[Any, int], float]


def count_hits(
    events: Iterable[Dict[str, Any]],
    *,
    ability_regex: Optional[Pattern[str]] = None,
    only_ability: Optional[str] = None,
    only_ability_id: Optional[str] = None,
    only_source: Optional[str] = None,
    dedupe_ms: Optional[float] = None,
) -> HitAggregate:
    hits_by_player: Counter = Counter()
    hits_by_player_ability: Dict[Tuple[str, str], int] = defaultdict(int)
    hits_by_player_fight: Dict[Tuple[str, int], int] = defaultdict(int)
    damage_by_player: Counter = Counter()
    fight_total_hits: Dict[int, int] = defaultdict(int)
    fight_total_damage: Dict[int, float] = defaultdict(float)
    last_hit_timestamp: Dict[Tuple[str, str], float] = {}

    for raw in events:
        normalized = normalize_event(raw)

        if only_source and (normalized["source_name"] or "") != only_source:
            continue

        if only_ability_id:
            ability_id = normalized.get("ability_id")
            if ability_id != only_ability_id:
                continue

        if only_ability:
            if (normalized["ability_name"] or "") != only_ability:
                continue
        elif ability_regex is not None:
            ability_name = normalized["ability_name"] or ""
            if not ability_name or not ability_regex.search(ability_name):
                continue

        if not is_hit(normalized):
            continue

        target = normalized["target_name"] or "Unknown Target"
        ability = normalized["ability_name"] or "Unknown Ability"

        timestamp = normalized.get("timestamp")
        ability_key = (target, ability)
        if (
            dedupe_ms is not None
            and isinstance(timestamp, (int, float))
            and ability_key in last_hit_timestamp
            and (timestamp - last_hit_timestamp[ability_key]) < dedupe_ms
        ):
            continue

        hits_by_player[target] += 1
        hits_by_player_ability[(target, ability)] += 1

        fight_raw = normalized.get("fight_id")
        if fight_raw is not None:
            try:
                fight_key = int(fight_raw)
            except (TypeError, ValueError):
                fight_key = None
            if fight_key is not None:
                hits_by_player_fight[(target, fight_key)] += 1

        damage_value = normalized.get("amount")
        if isinstance(damage_value, (int, float)):
            damage_by_player[target] += float(damage_value)
        fight_id = normalized.get("fight_id")
        if isinstance(damage_value, (int, float)) and fight_id is not None:
            try:
                fight_key = int(fight_id)
            except (TypeError, ValueError):
                fight_key = None
            if fight_key is not None:
                fight_total_damage[fight_key] += float(damage_value)
                fight_total_hits[fight_key] += 1
        elif fight_id is not None:
            try:
                fight_key = int(fight_id)
            except (TypeError, ValueError):
                fight_key = None
            if fight_key is not None:
                fight_total_hits[fight_key] += 1
        if isinstance(timestamp, (int, float)):
            last_hit_timestamp[ability_key] = float(timestamp)

    return HitAggregate(
        hits_by_player=hits_by_player,
        hits_by_player_ability=hits_by_player_ability,
        hits_by_player_fight=dict(hits_by_player_fight),
        damage_by_player=damage_by_player,
        fight_total_hits=dict(fight_total_hits),
        fight_total_damage=dict(fight_total_damage),
    )


def build_counter(
    path: Path,
    *,
    ability_regex: Optional[Pattern[str]] = None,
    only_ability: Optional[str] = None,
    only_ability_id: Optional[int] = None,
    only_source: Optional[str] = None,
    dedupe_ms: Optional[float] = None,
) -> HitAggregate:
    """
    Backwards-compatible wrapper that reads events from disk before counting.
    """
    events = iter_events_from_path(path)
    ability_id_str = str(only_ability_id) if only_ability_id is not None else None
    return count_hits(
        events,
        ability_regex=ability_regex,
        only_ability=only_ability,
        only_ability_id=ability_id_str,
        only_source=only_source,
        dedupe_ms=dedupe_ms,
    )


def aggregate_amounts(
    events: Iterable[Dict[str, Any]],
    *,
    actor_field: str = "source_name",
    actor_id_field: str = "source_id",
) -> AmountAggregate:
    """
    Sum event ``amount`` values grouped by actor (preferring IDs) and fight.
    """
    amount_by_actor: Dict[Any, float] = defaultdict(float)
    amount_by_actor_fight: Dict[Tuple[Any, int], float] = defaultdict(float)

    for raw in events:
        normalized = normalize_event(raw)

        actor_key: Any = normalized.get(actor_id_field)
        if actor_key is None:
            actor_key = normalized.get(actor_field)
        if actor_key in (None, ""):
            continue

        amount = normalized.get("amount")
        if not isinstance(amount, (int, float)):
            continue
        amount_value = float(amount)

        amount_by_actor[actor_key] += amount_value

        fight_id = normalized.get("fight_id")
        if fight_id is not None:
            try:
                fight_key = int(fight_id)
            except (TypeError, ValueError):
                fight_key = None
            if fight_key is not None:
                amount_by_actor_fight[(actor_key, fight_key)] += amount_value

    return AmountAggregate(
        amount_by_actor=dict(amount_by_actor),
        amount_by_actor_fight=dict(amount_by_actor_fight),
    )
