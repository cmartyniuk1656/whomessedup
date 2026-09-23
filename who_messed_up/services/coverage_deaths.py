"""Attach bounded five-second death recaps using the coverage streams already fetched.

Index only deceased players, then reuse EventWindow for each death. Totals cover
the complete window even when the displayed event tail is capped. Repeat deaths
never inherit the preceding life's killing hit.
"""
from collections import defaultdict

from .cooldown_effectiveness import EventWindow
from .death_reports import resolve_damage_ability, resolve_damage_amount

LOOKBACK_MS = 5000
MAX_EVENTS = 100


def _amount(event, key="amount"):
    return max(0, float(event.get(key) or 0))


def add_death_recaps(deaths, *, streams, fight, actor_names, ability_labels=None):
    labels = dict(ability_labels or {})
    players = {death["playerId"] for death in deaths}
    grouped = defaultdict(list)
    for stream, kinds in (("pressure", {"damage", "healabsorbed"}), ("healing", {"heal", "absorbed"})):
        for event in streams.get(stream, []):
            at = event.get("timestamp")
            if (event.get("targetID") in players and event.get("type") in kinds
                    and isinstance(at, (int, float)) and fight.start <= at <= fight.end
                    and (_amount(event) or _amount(event, "overkill") or _amount(event, "absorbed"))):
                grouped[event["targetID"]].append(event)
    windows = {player: EventWindow(events) for player, events in grouped.items()}
    previous_death = {}
    for death in deaths:
        player = death["playerId"]
        at = fight.start + death["time"] * 1000
        start = max(fight.start, at - LOOKBACK_MS, previous_death.get(player, fight.start - 1) + 0.001)
        window = windows.get(player)
        # EventWindow is end-exclusive; retain all events at the death timestamp.
        events = window.between(start, at + 0.001) if window else []
        rows = []
        totals = dict(damageTaken=0, healingReceived=0, healingAbsorbed=0, damageAbsorbed=0)
        for event in events:
            kind = event["type"]
            spell_id, name = resolve_damage_ability(event, labels)
            amount = _amount(event)
            source = event.get("sourceID")
            overkill = _amount(event, "overkill") if kind == "damage" else 0
            rows.append({
                "offset": round((event["timestamp"] - at) / 1000, 3),
                "kind": kind, "spellId": spell_id,
                "name": name or ("Melee" if spell_id == 1 else f"Spell {spell_id}" if spell_id else "Unknown ability"),
                "source": actor_names.get(source) or event.get("sourceName") or ("Environment" if source in (None, -1, 0) else "Unknown source"),
                "amount": round((resolve_damage_amount(event) or amount) if kind == "damage" else amount),
                "overkill": round(overkill), "absorbed": round(_amount(event, "absorbed")) if kind == "damage" else 0,
                # A final hit alone does not prove the cause of death. Positive
                # overkill near death does; exact-lethal hits may remain unknown.
                "killingBlow": kind == "damage" and overkill > 0 and at - event["timestamp"] <= 1000,
            })
            if kind == "damage":
                totals["damageTaken"] += amount  # WCL amount already excludes overkill.
                totals["damageAbsorbed"] += _amount(event, "absorbed")
            elif kind == "heal":
                totals["healingReceived"] += amount  # Effective healing; overheal is a separate field.
            elif kind == "healabsorbed":
                totals["healingAbsorbed"] += amount
            # Absorbed healing-stream rows identify shields. Do not add them to
            # health restored or count them again in damageAbsorbed totals.
        lethal = next((row for row in reversed(rows) if row["killingBlow"]), None)
        for row in rows:
            row["killingBlow"] = row is lethal
        selected = rows[-MAX_EVENTS:]
        if lethal is not None and not any(row is lethal for row in selected):
            selected = [lethal, *selected[-(MAX_EVENTS - 1):]]
        death["recap"] = {
            "windowSeconds": round(max(0, (at - start) / 1000), 3),
            "events": selected, "totalEvents": len(rows),
            **{key: round(value) for key, value in totals.items()},
        }
        previous_death[player] = at
