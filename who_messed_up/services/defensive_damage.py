"""Personal damage evidence, shared by cast summaries and timeline bins.

WCL mitigated already includes armor, blocks and damage reductions, but not
absorbs. Never add blocked again or attribute this total to a single cooldown.
Immunities come from a separately filtered WCL miss stream, not missing hits.
"""
import math
from collections import defaultdict

from .cooldown_usage import _event_ability_id


def damage_evidence(events):
    totals = dict(damageTaken=0, absorbed=0, mitigated=0, overkill=0,
                  immuneEvents=0, damageEvents=0, mitigationEvents=0)
    for event in events:
        if event.get("type") == "immune":
            totals["immuneEvents"] += 1
        elif event.get("type") == "damage":
            totals["damageEvents"] += 1
            totals["mitigationEvents"] += int("mitigated" in event or "unmitigatedAmount" in event)
            for output, field in (("damageTaken", "amount"), ("absorbed", "absorbed"),
                                  ("mitigated", "mitigated"), ("overkill", "overkill")):
                totals[output] += max(0, event.get(field) or 0)
    return {key: round(value, 2) for key, value in totals.items()}


def personal_damage_series(events, fight, boss_spells, ability_labels=None, bin_seconds=2):
    """Rates for actual health damage, consumed shields and logged mitigation.

    Heal absorbs are retained separately for context, never counted as incoming
    damage or shield protection. Immune events have a count but no invented value.
    """
    duration = max(.001, (fight.end - fight.start) / 1000)
    buckets = [[] for _ in range(math.ceil(duration / bin_seconds))]
    for event in events:
        time = (event["timestamp"] - fight.start) / 1000
        if 0 <= time <= duration:
            buckets[min(len(buckets) - 1, int(time // bin_seconds))].append(event)
    result = []
    for index, events_in_bin in enumerate(buckets):
        time = index * bin_seconds
        width = min(bin_seconds, duration - time)
        totals = damage_evidence(events_in_bin)
        sources = defaultdict(lambda: dict(amount=0, immuneEvents=0))
        for event in events_in_bin:
            if event.get("type") not in ("damage", "immune"):
                continue
            sid = _event_ability_id(event)
            name = boss_spells.get(sid, {}).get("name") or (ability_labels or {}).get(sid) or f"Spell {sid}"
            value = damage_evidence([event])
            sources[name]["amount"] += value["damageTaken"] + value["absorbed"] + value["mitigated"]
            sources[name]["immuneEvents"] += value["immuneEvents"]
        result.append(dict(time=time,
            damage=round(totals["damageTaken"] / width, 2),
            absorbed=round(totals["absorbed"] / width, 2),
            mitigated=round(totals["mitigated"] / width, 2),
            immuneEvents=totals["immuneEvents"],
            healAbsorbs=round(sum(max(0, e.get("amount") or 0) for e in events_in_bin
                                 if e.get("type") == "healabsorbed") / width, 2),
            sources=[dict(name=name, amount=round(value["amount"] / width, 2), immuneEvents=value["immuneEvents"])
                     for name, value in sorted(sources.items(), key=lambda item: (-item[1]["amount"], -item[1]["immuneEvents"]))[:5]]))
    return result
