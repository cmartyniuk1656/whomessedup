"""Measured per-cast context, without claiming causal cooldown attribution.

All healer/pet healing inside the analysis window is included. Nominal windows
and short observation windows are explicit; mitigation is not scored as healing.
"""
from bisect import bisect_left
from collections import defaultdict

from .cooldown_usage import _event_ability_id


class EventWindow:
    """Index a stream once so every cooldown only scans its own time window."""

    def __init__(self, events):
        self.events = sorted(events, key=lambda event: event["timestamp"])
        self.times = [event["timestamp"] for event in self.events]

    def between(self, start, end):
        return self.events[bisect_left(self.times, start):bisect_left(self.times, end)]


def _owner(source, owners):
    seen = set()
    while owners.get(source) and source not in seen:
        seen.add(source)
        source = owners[source]
    return source


def _amount(event, key="amount"):
    return max(0.0, float(event.get(key) or 0))


def _pressure_totals(events):
    damage = absorbs = 0
    for event in events:
        if event["type"] == "damage":
            damage += max(0, _amount(event) - _amount(event, "overkill"))
        elif event["type"] == "healabsorbed":
            absorbs += _amount(event)
    return damage, absorbs


def _healing_totals(events, source, owners, labels):
    health = shields = overheal = raid = 0
    targets = set()
    abilities = defaultdict(lambda: {"effective": 0, "overheal": 0})
    for event in events:
        amount = _amount(event)
        raid += amount
        if _owner(event.get("sourceID"), owners) != source:
            continue
        if event["type"] == "heal":
            health += amount
            overheal += _amount(event, "overheal")
        else:
            shields += amount
        if amount > 0:
            targets.add(event["targetID"])
        ability_id = _event_ability_id(event)
        name = labels.get(ability_id, f"Spell {ability_id}")
        abilities[name]["effective"] += amount
        if event["type"] == "heal":
            abilities[name]["overheal"] += _amount(event, "overheal")
    return {
        "healthRestored": round(health), "shieldsConsumed": round(shields),
        "effectiveHealing": round(health + shields), "overhealing": round(overheal),
        "overhealPercent": round(100 * overheal / (health + overheal), 1) if health + overheal else None,
        "targetsHelped": len(targets),
        "raidHealingShare": round(100 * (health + shields) / raid, 1) if raid else None,
        "abilities": [{"name": name, "effective": round(values["effective"]),
                       "overheal": round(values["overheal"])} for name, values in
                      sorted(abilities.items(), key=lambda item: -(item[1]["effective"] + item[1]["overheal"]))[:6]],
    }


def add_cast_effectiveness(lanes, *, fight, streams, participants, actor_owners=None, ability_labels=None):
    """Attach measured context to healer casts; keep boss events untouched."""
    owners, labels = actor_owners or {}, ability_labels or {}
    healing = EventWindow(event for event in streams.get("healing", [])
                          if event.get("type") in ("heal", "absorbed") and event.get("targetID") in participants)
    pressure = EventWindow(event for event in streams.get("pressure", [])
                           if event.get("type") in ("damage", "healabsorbed") and event.get("targetID") in participants)
    duration = max(0, (fight.end - fight.start) / 1000)
    healer_lanes = [lane for lane in lanes if lane["kind"] == "healer"]
    for lane in healer_lanes:
        source = int(lane["id"].split(":")[0])
        previous = None
        for event in lane["events"]:
            start = event["time"]
            if event.get("label") == "Store":
                event["effectiveness"] = {"status": "preparation", "note": "Stasis is storing spells. Select its Release to review healing output."}
                continue
            end = event.get("end")
            if end is not None and end > start:
                end = min(duration, end)
                basis = event["durationBasis"] + " duration"
            else:
                # Instant heals and variable replay/travel effects cannot be
                # assigned a fabricated active duration on the coverage strip.
                end = min(duration, start + (3 if end is not None else 5))
                basis = "3-second observation after instant cast" if event.get("end") is not None else "5-second observation; effect duration unknown"
            if end <= start:
                event["effectiveness"] = {"status": "unavailable", "note": "The pull ended at this cast; there is no post-cast window to measure."}
                previous = event
                continue
            start_ms, end_ms = fight.start + start * 1000, fight.start + end * 1000
            output = _healing_totals(healing.between(start_ms, end_ms), source, owners, labels)
            damage, absorbs = _pressure_totals(pressure.between(start_ms, end_ms))
            before_start = max(fight.start, start_ms - 5000)
            before_damage, before_absorbs = _pressure_totals(pressure.between(before_start, start_ms))
            overlaps = []
            for other in healer_lanes:
                for other_event in other["events"]:
                    if other_event is event or other_event.get("label") == "Store":
                        continue
                    other_end = other_event.get("end")
                    active = other_end is not None and other_end > other_event["time"]
                    intersects = (other_event["time"] < end and other_end > start) if active else start <= other_event["time"] < end
                    if intersects:
                        overlaps.append({"laneId": other["id"], "player": other["player"], "name": other["name"],
                                         "time": other_event["time"], "kind": "window" if active else "cast"})
            held = None
            if previous and previous.get("ready") is not None:
                held = round(max(0, start - previous["ready"]), 3)
            event["effectiveness"] = {
                "status": "measured" if "healing" in streams else "unavailable",
                "windowStart": start, "windowEnd": end, "windowBasis": basis,
                **output, "effectiveHps": round(output["effectiveHealing"] / (end - start)),
                "raidDamage": round(damage), "healAbsorbsConsumed": round(absorbs),
                "pressurePerSecond": round((damage + absorbs) / (end - start)),
                "precedingPressure": round(before_damage + before_absorbs),
                "precedingSeconds": round((start_ms - before_start) / 1000, 3),
                "heldSeconds": held, "overlaps": overlaps,
                "note": "Healer and owned-pet output during this window, including other spells and existing HoTs/shields. This is not healing attributed solely to the cooldown. Damage prevention and health redistribution are not measured.",
            }
            if "healing" not in streams:
                event["effectiveness"]["note"] = "Healing data is not present in this saved report. Run a fresh report to measure this cast."
            previous = event
