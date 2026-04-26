"""
Shared helpers for player consumable usage.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import requests

from ..api import Fight, fetch_events


@dataclass(frozen=True)
class HealingConsumable:
    id: str
    ability_name: str
    label: str


@dataclass
class HealingConsumableStatus:
    consumable_id: str
    label: str
    used: bool
    timestamps: List[float] = field(default_factory=list)
    offsets_ms: List[float] = field(default_factory=list)


DEATH_REPORT_HEALING_CONSUMABLES = (
    HealingConsumable(
        id="silvermoon_health_potion",
        ability_name="Silvermoon Health Potion",
        label="Silvermoon Health Potion",
    ),
    HealingConsumable(
        id="healthstone",
        ability_name="Healthstone",
        label="Healthstone",
    ),
)


def collect_healing_consumable_uses(
    session: requests.Session,
    bearer: str,
    *,
    fights: Iterable[Fight],
    report_code: str,
    ability_names: Iterable[str],
    actor_names: Dict[int, str],
) -> Dict[int, Dict[str, Dict[str, List[float]]]]:
    usage_by_fight: Dict[int, Dict[str, Dict[str, List[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
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
                usage_by_fight[fight.id][str(target_name)][ability_name].append(ts_val)
    return usage_by_fight


def build_healing_consumable_statuses(
    consumable_usage: Optional[Dict[str, List[float]]],
    *,
    consumables: Iterable[HealingConsumable] = DEATH_REPORT_HEALING_CONSUMABLES,
    fight_start: float,
    reference_timestamp: float,
) -> List[HealingConsumableStatus]:
    usage = consumable_usage or {}
    statuses: List[HealingConsumableStatus] = []
    for consumable in consumables:
        raw_timestamps = usage.get(consumable.ability_name) or []
        timestamps: List[float] = []
        for timestamp in raw_timestamps:
            try:
                ts_val = float(timestamp)
            except (TypeError, ValueError):
                continue
            if float(fight_start) <= ts_val <= float(reference_timestamp):
                timestamps.append(ts_val)
        timestamps.sort()
        statuses.append(
            HealingConsumableStatus(
                consumable_id=consumable.id,
                label=consumable.label,
                used=bool(timestamps),
                timestamps=timestamps,
                offsets_ms=[timestamp - float(fight_start) for timestamp in timestamps],
            )
        )
    return statuses


__all__ = [
    "DEATH_REPORT_HEALING_CONSUMABLES",
    "HealingConsumable",
    "HealingConsumableStatus",
    "build_healing_consumable_statuses",
    "collect_healing_consumable_uses",
]
