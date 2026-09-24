"""Validated log aliases and stance entries, preserving recorded-cast evidence.

Guardian's 212641 cast/buff mapping was verified in Sentinels and Nymrissa logs.
Aura-only Guardian procs are deliberately not synthesized into manual uses.
Stances may activate through another action, so their observed entries also count.
"""
from collections import defaultdict

from .cooldown_usage import _event_ability_id


CAST_ALIASES = {212641: 86659}
STANCES = {5487, 386208}


def normalize_defensive_streams(streams):
    # Damage/healing streams can contain millions of events; aliases only affect
    # the small cast and buff streams and must not copy the large evidence arrays.
    normalized = dict(streams)
    for name in ("casts", "auras"):
        normalized[name] = [dict(event, abilityGameID=CAST_ALIASES[_event_ability_id(event)])
                            if _event_ability_id(event) in CAST_ALIASES else event
                            for event in streams.get(name, [])]
    casts = list(normalized.get("casts", []))
    stance_casts = defaultdict(list)
    for event in casts:
        spell = _event_ability_id(event)
        if spell in STANCES and event.get("type") == "cast":
            stance_casts[(event.get("sourceID"), spell)].append(event)
    for aura in normalized.get("auras", []):
        spell = _event_ability_id(aura)
        if spell not in STANCES or aura.get("type") != "applybuff" or aura.get("sourceID") != aura.get("targetID"):
            continue
        if not any(abs(event["timestamp"] - aura["timestamp"]) <= 1500
                   for event in stance_casts[(aura.get("sourceID"), spell)]):
            casts.append(dict(aura, type="cast", defensiveOrigin="Observed stance entry"))
    normalized["casts"] = casts
    return normalized
