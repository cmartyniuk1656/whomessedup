"""
Shared helpers for player consumable usage.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import requests

from ..api import Fight, fetch_events


@dataclass(frozen=True)
class HealingConsumable:
    id: str
    ability_name: str
    label: str
    aliases: Tuple[str, ...] = ()
    ability_ids: Tuple[int, ...] = ()

    @property
    def ability_names(self) -> Tuple[str, ...]:
        return (self.ability_name, *self.aliases)


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
        label="Health Potion",
        aliases=("Concentrated Silvermoon Health Potion",),
        ability_ids=(1234768, 1295247),
    ),
    HealingConsumable(
        id="healthstone",
        ability_name="Healthstone",
        label="Healthstone",
        ability_ids=(6262,),
    ),
)


def healing_consumable_ability_names(
    consumables: Iterable[HealingConsumable] = DEATH_REPORT_HEALING_CONSUMABLES,
) -> Tuple[str, ...]:
    """Return every Warcraft Logs spell name recognized for consumable slots."""
    return tuple(
        dict.fromkeys(
            ability_name
            for consumable in consumables
            for ability_name in consumable.ability_names
            if ability_name
        )
    )


def _known_consumable_names_by_ability_id() -> Dict[int, str]:
    names_by_id: Dict[int, str] = {}
    for consumable in DEATH_REPORT_HEALING_CONSUMABLES:
        for ability_id, ability_name in zip(
            consumable.ability_ids, consumable.ability_names
        ):
            names_by_id[int(ability_id)] = ability_name
    return names_by_id


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
    selected_fights = list(fights)
    selected_names = list(dict.fromkeys(str(name) for name in ability_names if name))
    if not selected_fights or not selected_names:
        return usage_by_fight
    normalized_names = {name.casefold(): name for name in selected_names}
    known_names_by_id = _known_consumable_names_by_ability_id()
    filter_expr = " or ".join(
        f'ability.name = "{name.replace(chr(34), chr(92) + chr(34))}"'
        for name in selected_names
    )
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Healing",
        start=min(float(fight.start) for fight in selected_fights),
        end=max(float(fight.end) for fight in selected_fights),
        extra_filter=filter_expr,
        fight_ids=[fight.id for fight in selected_fights],
        use_actor_ids=False,
        actor_names=actor_names,
    ):
        timestamp = event.get("timestamp")
        if timestamp is None:
            continue
        try:
            ts_val = float(timestamp)
        except (TypeError, ValueError):
            continue
        fight_id = _event_fight_id(event, selected_fights, ts_val)
        if fight_id is None:
            continue
        target_name = event.get("targetName")
        if not target_name and isinstance(event.get("target"), dict):
            target_name = event["target"].get("name")
        ability = event.get("ability")
        event_ability_name = ability.get("name") if isinstance(ability, dict) else event.get("abilityName")
        if not event_ability_name:
            try:
                event_ability_name = known_names_by_id.get(int(event.get("abilityGameID")))
            except (TypeError, ValueError):
                event_ability_name = None
        canonical_name = normalized_names.get(str(event_ability_name or "").casefold())
        if not target_name or not canonical_name:
            continue
        usage_by_fight[fight_id][str(target_name)][canonical_name].append(ts_val)
    return usage_by_fight


def _event_fight_id(
    event: Dict[str, object], fights: Iterable[Fight], timestamp: float
) -> Optional[int]:
    try:
        return int(event.get("fight"))
    except (TypeError, ValueError):
        pass
    for fight in fights:
        if float(fight.start) <= timestamp <= float(fight.end):
            return int(fight.id)
    return None


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
        raw_timestamps = [
            timestamp
            for ability_name in consumable.ability_names
            for timestamp in (usage.get(ability_name) or [])
        ]
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
    "healing_consumable_ability_names",
]
