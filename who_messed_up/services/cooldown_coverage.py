"""Build pull-relative coverage timelines from paginated WCL event streams.

Damage is health damage (excluding overkill). Heal absorbs are measured when
consumed, not an inferred pool at application time. Readiness is an estimate:
WCL cast events do not report the exact moment a cooldown becomes available.
"""
import math

import requests

from ..api import fetch_fights
from ..env import load_env
from .common import _resolve_token, _sanitize_report_code, _select_fights
from .cooldown_catalog import ability_display, coverage_catalog, resolve_timing, talent_ranks
from .cooldown_usage import _event_ability_id, _fetch_ability_labels
from .event_streams import fetch_event_streams
from .cooldown_effectiveness import add_cast_effectiveness


def build_coverage_pull(*, code, fight, boss, streams, actor_names, player_ids, ability_labels=None, actor_owners=None):
    spells, _ = coverage_catalog()
    duration = max(0.001, (fight.end - fight.start) / 1000)
    combatants = {e["sourceID"]: e for e in streams.get("combatants", []) if e.get("sourceID")}
    participants = set(fight.friendly_player_ids) or set(player_ids)
    participants.update(combatants)
    casts = sorted((e for e in [*streams.get("casts", []), *streams.get("bossCasts", [])] if e.get("type") == "cast"),
                   key=lambda e: e["timestamp"])
    lanes = {}
    boss_spells = {s["spell_id"]: s for s in boss["abilities"]}
    seen = set()
    for event in casts:
        actual_spell_id = _event_ability_id(event)
        spell_id = 370537 if actual_spell_id == 370564 else actual_spell_id
        source = event.get("sourceID")
        time = (event["timestamp"] - fight.start) / 1000
        if not 0 <= time <= duration:
            continue
        key = (source, actual_spell_id, event["timestamp"])
        if key in seen:
            continue
        seen.add(key)
        is_player = source in participants
        spell = spells.get(spell_id) if is_player else boss_spells.get(spell_id)
        if not spell:
            continue
        info = combatants.get(source, {})
        # Shared spells such as Avenging Wrath must not create DPS healer lanes.
        if is_player and info.get("specID", info.get("specId")) not in (None, spell["specId"]):
            continue
        lane_id = f"{source}:{spell_id}" if is_player else f"boss:{spell_id}"
        if lane_id not in lanes:
            lanes[lane_id] = make_lane(lane_id, spell, source, actor_names, info, is_player)
        lane = lanes[lane_id]
        window = lane.get("duration")
        duration_basis = "nominal" if window is not None else "unknown"
        # A paired self aura is stronger evidence than a nominal buff duration.
        if is_player and spell["duration"]["kind"] == "buff":
            auras = [e for e in streams.get("auras", []) if _event_ability_id(e) == spell_id
                     and e.get("targetID") == source and e["timestamp"] >= event["timestamp"]]
            application = next((e for e in auras if e["type"] in ("applybuff", "refreshbuff")
                                and e["timestamp"] - event["timestamp"] <= 1500), None)
            removal = next((e for e in auras if e["type"] == "removebuff"
                            and application and e["timestamp"] > application["timestamp"]), None)
            next_cast = next((e for e in casts if e.get("sourceID") == source
                              and _event_ability_id(e) == spell_id and e["timestamp"] > event["timestamp"]), None)
            if removal and (not next_cast or removal["timestamp"] <= next_cast["timestamp"]):
                window = (removal["timestamp"] - event["timestamp"]) / 1000
                duration_basis = "observed aura"
        ready = time + lane["cooldown"] if lane.get("cooldown") is not None else None
        event_label = None
        if spell_id == 370537:
            # Preparation is not healing coverage. Release is a separate cast,
            # including releases whose preparation happened before the pull.
            event_label = "Release" if actual_spell_id == 370564 else "Store"
            ready = ready if event_label == "Release" else None
        lane["events"].append({"time": round(time, 3), "label": event_label,
                               "end": round(min(duration, time + window), 3) if window is not None else None,
                               "durationBasis": duration_basis,
                               "ready": round(ready, 3) if ready is not None else None})
    # Talented but unused cooldowns deserve a visible lane, too. Cast evidence
    # alone is insufficient to claim every possible talent was available.
    for source, info in combatants.items():
        ranks = talent_ranks(info)
        for spell_id, spell in spells.items():
            if info.get("specID", info.get("specId")) != spell["specId"] or spell_id not in ranks:
                continue
            lane_id = f"{source}:{spell_id}"
            lanes.setdefault(lane_id, make_lane(lane_id, spell, source, actor_names, info, True))
    for lane in lanes.values():
        # A later cast proves availability by that instant, not the exact earlier
        # ready time. Do not draw a predicted recovery across an observed reuse.
        for current, following in zip(lane["events"], lane["events"][1:]):
            if current["ready"] is not None and following["time"] < current["ready"]:
                current["ready"] = following["time"]
                current["readyBasis"] = "Available by observed next cast"
    ordered = sorted(lanes.values(), key=lambda row: (row["kind"] != "boss", row.get("player", ""), row["name"]))
    add_cast_effectiveness(ordered, fight=fight, streams=streams, participants=participants,
                           actor_owners=actor_owners, ability_labels=ability_labels)
    return {"id": f"{code}:{fight.id}", "fightId": fight.id, "reportCode": code,
            "duration": duration, "kill": fight.kill, "lanes": ordered,
            "url": f"https://www.warcraftlogs.com/reports/{code}?fight={fight.id}",
            "pressure": pressure_series(streams.get("pressure", []), fight, participants, boss_spells, ability_labels=ability_labels),
            "deaths": death_markers(streams.get("deaths", []), fight, participants, actor_names),
            "warnings": ([] if combatants else ["No combatant talent data was recorded. Timings use base values; unused cooldowns cannot be inferred."])
                         + ([] if any(l["kind"] == "boss" for l in ordered) else ["No catalogue boss casts found. Damage timings may still be available."])}


def death_markers(events, fight, participants, actor_names):
    """Retain every player death, including later deaths after a resurrection."""
    markers, seen = [], set()
    for event in sorted(events, key=lambda entry: entry.get("timestamp") or 0):
        target, timestamp = event.get("targetID"), event.get("timestamp")
        if (event.get("type") not in ("death", "instakill") or target not in participants
                or timestamp is None or not fight.start <= timestamp <= fight.end):
            continue
        key = (target, timestamp)
        if key in seen:
            continue
        seen.add(key)
        markers.append({"time": round((timestamp - fight.start) / 1000, 3),
                        "playerId": target, "player": actor_names.get(target, f"Player {target}")})
    return markers


def make_lane(lane_id, spell, source, names, info, is_player):
    lane = {"id": lane_id, **ability_display(spell), "kind": "healer" if is_player else "boss", "events": []}
    if is_player:
        cooldown, duration, basis, dynamic = resolve_timing(spell, info)
        lane.update(player=names.get(source, f"Player {source}"), spec=spell["specName"],
                    cooldown=cooldown, duration=duration, timingBasis=basis, dynamic=dynamic,
                    notes=spell["notes"], modifiers=[m["name"] + ": " + m["effect"] for m in spell["modifiers"]])
    else:
        lane.update(duration=0, timingBasis="Recorded cast", shownByDefault=spell["lorrgs_metadata"]["shown_by_default"])
    return lane


def pressure_series(events, fight, participants, boss_spells, bin_seconds=2, ability_labels=None):
    duration = max(0.001, (fight.end - fight.start) / 1000)
    bins = [{"time": i * bin_seconds, "damage": 0, "healAbsorbs": 0, "sources": {}}
            for i in range(math.ceil(duration / bin_seconds))]
    for event in events:
        time = (event["timestamp"] - fight.start) / 1000
        if event.get("targetID") not in participants or not 0 <= time <= duration:
            continue
        kind = event.get("type")
        if kind not in ("damage", "healabsorbed"):
            continue
        value = max(0, float(event.get("amount") or 0) - (max(0, event.get("overkill") or 0) if kind == "damage" else 0))
        bucket = bins[min(len(bins) - 1, int(time // bin_seconds))]
        bucket["damage" if kind == "damage" else "healAbsorbs"] += value
        spell_id = _event_ability_id(event)
        ability = event.get("ability") or {}
        label = boss_spells.get(spell_id, {}).get("name") or (ability_labels or {}).get(spell_id) or (ability.get("name") if isinstance(ability, dict) else None) or f"Spell {spell_id}"
        if kind == "healabsorbed":
            label += " (heal absorb)"
        bucket["sources"][label] = bucket["sources"].get(label, 0) + value
    for bucket in bins:
        width = min(bin_seconds, duration - bucket["time"])
        bucket["damage"] = round(bucket["damage"] / width, 2)
        bucket["healAbsorbs"] = round(bucket["healAbsorbs"] / width, 2)
        bucket["sources"] = [{"name": k, "amount": round(v / width, 2)}
                             for k, v in sorted(bucket["sources"].items(), key=lambda item: -item[1])[:5]]
    return bins


def fetch_cooldown_coverage(*, report_codes, encounter_id, difficulty, token=None, client_id=None, client_secret=None):
    load_env()
    spells, bosses = coverage_catalog()
    boss = bosses[int(encounter_id)]
    bearer = _resolve_token(token, client_id, client_secret)
    pulls = []
    tracked = sorted(set(spells) | {370564} | {s["spell_id"] for s in boss["abilities"]})
    spell_filter = "ability.id IN (" + ",".join(map(str, tracked)) + ")"
    for reference in dict.fromkeys(report_codes):
        code = _sanitize_report_code(reference)
        with requests.Session() as session:
            fights, names, classes, owners = fetch_fights(session, bearer, code)
            candidates = [f for f in fights if f.encounter_id == int(encounter_id)]
            chosen = sorted(_select_fights(candidates, name_filter=None, fight_ids=None, difficulty=difficulty), key=lambda f: f.start)
            ability_labels = _fetch_ability_labels(session, bearer, code)
            streams = fetch_event_streams(code=code, fights=chosen, token=bearer, actor_names=names,
                streams={"casts": {"data_type": "Casts", "extra_filter": spell_filter},
                         "bossCasts": {"data_type": "Casts", "extra_filter": spell_filter, "hostility_type": "Enemies"},
                         "combatants": {"data_type": "CombatantInfo"},
                         "deaths": {"data_type": "Deaths"},
                         "auras": {"data_type": "Buffs", "extra_filter": spell_filter},
                         "healing": {"data_type": "Healing", "extra_filter": 'type = "heal" OR type = "absorbed"'},
                         "pressure": {"data_type": "All", "extra_filter": 'type = "damage" OR type = "healabsorbed"'}},
                partitioned_streams=("pressure", "healing"))
            for fight in chosen:
                pull = build_coverage_pull(code=code, fight=fight, boss=boss,
                    streams={k: v.get(fight.id, []) for k, v in streams.items()}, actor_names=names,
                    ability_labels=ability_labels,
                    actor_owners=owners,
                    player_ids={actor for actor, class_name in classes.items() if class_name})
                pull["label"] = f"Pull {len(pulls) + 1} · {'Kill' if fight.kill else 'Wipe'} · {int(pull['duration']) // 60}:{int(pull['duration']) % 60:02d} · {code} / {fight.id}"
                pulls.append(pull)
    return {"boss": boss["name"], "pulls": pulls, "patch": "12.1", "binSeconds": 2}
