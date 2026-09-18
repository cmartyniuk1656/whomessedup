"""Instance-specific enemy lifetimes for mechanics reports.

Inputs are already keyed by the enemy side of each event. A fresh summon
opens a new life; after a death, short delayed packets cannot reopen it.
"""
from dataclasses import dataclass, field

from .mechanics_events import timestamp


@dataclass
class EnemyLife:
    key: tuple
    start: float
    end: float
    events: list = field(default_factory=list)
    death: float | None = None
    summoned: bool = False


def enemy_lives(evidence, fight_end):
    result = []
    for key, events in evidence.items():
        current = None
        last_death = None
        previous = None
        seen = set()
        for event in sorted(events, key=timestamp):
            at = timestamp(event)
            # Preserve distinct attacks; only deduplicate lifecycle packets.
            kind = event.get("type")
            signature = (kind, at, event.get("abilityGameID"))
            if kind in {"summon", "death", "applybuff", "removebuff", "begincast", "cast"}:
                if signature in seen:
                    continue
                seen.add(signature)
            if kind == "summon" and current is not None and at > current.start:
                current.end = min(at, current.end)
                current = None
            if current is None:
                if kind in {"removebuff", "removedebuff"}:
                    continue
                if last_death is not None and kind != "summon":
                    if at <= last_death + 1000:
                        # Death-triggered casts and aura cleanup belong to the old
                        # life, but delayed attacks cannot add damage after death.
                        if kind in {"cast", "removebuff"} and previous is not None:
                            previous.events.append(event)
                        continue
                    if kind not in {"applybuff", "begincast", "cast"}:
                        continue
                current = EnemyLife(key, at, fight_end, summoned=kind == "summon")
                result.append(current)
            current.events.append(event)
            if kind == "death":
                current.death = current.end = at
                last_death = at
                previous = current
                current = None
    return sorted(result, key=lambda life: (life.start, life.key))
