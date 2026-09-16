"""Event normalization and aura lifetimes used by the Sentinels analyses.

Missing aura applications are never manufactured. Removals near death or the
end of a pull are censored so cleanup cannot masquerade as a mechanic clear.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def timestamp(event):
    return float(event.get("timestamp") or 0)


def ability(event):
    return int(event.get("abilityGameID") or 0)


def damage(event):
    # WCL stores overkill separately; amount already excludes it.
    return max(0, float(event.get("amount") or 0))


def instance(event, side):
    return (event.get(side + "ID"), event.get(side + "Instance") or 0)


def clusters(events, gap=100):
    """Group against the first event, avoiding transitive chains of distant hits."""
    result = []
    for event in sorted(events, key=timestamp):
        if not result or timestamp(event) - timestamp(result[-1][0]) > gap:
            result.append([])
        result[-1].append(event)
    return result


def cast_times(events, ids):
    return [timestamp(group[0]) for group in clusters(
        [e for e in events if e.get("type") == "cast" and ability(e) in ids]
    )]


def windows(starts, end):
    return list(zip(starts, starts[1:] + [end + 1]))


def assignment_starts(casts, lives, cast_ids, application_span):
    """Anchor staggered assignments to casts, retaining orphan application sets."""
    starts = cast_times(casts, cast_ids)
    for life in sorted(lives, key=lambda item: item.start):
        if not any(0 <= life.start - start <= application_span for start in starts):
            starts.append(life.start)
    return sorted(starts)


def match_aura_dispel(life, events, fight_end):
    """Match explicit dispel evidence to one aura life, never a later reapplication."""
    end = min(fight_end, life.superseded if life.superseded is not None else fight_end,
              life.removed + 250 if life.removed is not None else fight_end)
    return next((event for event in sorted(events, key=timestamp)
                 if event.get("type") == "dispel"
                 and event.get("targetID") == life.player_id
                 and int(event.get("extraAbilityGameID") or 0) == life.ability_id
                 and life.start <= timestamp(event) <= end
                 and (life.superseded is None or timestamp(event) < life.superseded)), None)


@dataclass
class AuraLife:
    player_id: int
    ability_id: int
    start: float
    initial_stack: Optional[int] = None
    removed: Optional[float] = None
    superseded: Optional[float] = None
    changes: list = field(default_factory=list)

    def status(self, deaths, fight_end, *, expiry=None):
        stop = min(self.removed if self.removed is not None else fight_end,
                   self.superseded if self.superseded is not None else fight_end, fight_end)
        death = next((timestamp(e) for e in deaths
                      if e.get("targetID") == self.player_id
                      and self.start <= timestamp(e) <= stop + 1000), None)
        if death is not None:
            return "Died before resolution", min(death, fight_end)
        if self.removed is None:
            if self.superseded is not None:
                return "Removal not logged before reapplication", self.superseded
            return "Unresolved at pull end", fight_end
        if self.removed >= fight_end - 1000:
            return "Pull-end cleanup", self.removed
        if expiry is not None and self.removed - self.start >= expiry - 250:
            return "Expiry / unresolved", self.removed
        return "Removed alive", self.removed


def aura_lives(events, ids, players):
    lives = []
    active = {}
    for event in sorted(events, key=timestamp):
        aid, target = ability(event), event.get("targetID")
        if aid not in ids or target not in players:
            continue
        key = (target, aid)
        kind = event.get("type")
        if kind == "applydebuff":
            # A new application is separate evidence, even if an earlier removal
            # was omitted by the log. Never silently mark that earlier life clear.
            if key in active:
                active[key].superseded = timestamp(event)
            life = AuraLife(target, aid, timestamp(event), event.get("stack"))
            lives.append(life)
            active[key] = life
        elif kind == "removedebuff":
            life = active.pop(key, None)
            if life:
                life.removed = timestamp(event)
        elif kind in ("applydebuffstack", "removedebuffstack") and key in active:
            active[key].changes.append((timestamp(event), event.get("stack")))
    return lives
