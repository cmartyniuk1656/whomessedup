"""Recorded defensive usage and personal exposure, composed from shared WCL streams.

Static readiness is estimated separately from usable opportunities. Personal, external
and raid casts retain recipients; absent casts never prove an available button.
"""
from collections import defaultdict

import requests

from ..api import fetch_fights
from ..env import load_env
from .common import _resolve_token, _sanitize_report_code, _select_fights
from .cooldown_catalog import coverage_catalog
from .cooldown_coverage import death_markers, make_lane
from .cooldown_effectiveness import EventWindow
from .cooldown_usage import _event_ability_id, _fetch_ability_labels
from .coverage_deaths import add_death_recaps
from .defensive_catalog import defensive_catalog, defensive_display, ability_access
from .defensive_damage import damage_evidence, personal_damage_series
from .defensive_attribution import add_cooldown_attribution
from .defensive_readiness import add_defensive_readiness
from .event_streams import fetch_event_streams


def _window_end(event, ability, aura_events, fight, deaths):
    """Only a same-source, same-recipient paired aura establishes actual duration."""
    at, source = event["timestamp"], event.get("sourceID")
    target = event.get("targetID")
    own = [e for e in aura_events if _event_ability_id(e) == ability["spellId"]
           and e.get("targetID") == target and e.get("sourceID") == source and e["timestamp"] >= at]
    apply = next((e for e in own if e["type"] in ("applybuff", "refreshbuff") and e["timestamp"] <= at + 1500), None)
    remove = next((e for e in own if apply and e["timestamp"] > apply["timestamp"]
                   and e["type"] in ("removebuff", "refreshbuff", "applybuff")), None)
    if apply and remove and remove["type"] == "removebuff":
        end, basis = remove["timestamp"], "observed aura"
    else:
        duration = ability.get("duration")
        end, basis = (at + duration * 1000, "nominal") if duration is not None else (at, "unknown")
    # A self defensive cannot continue through that player's death.
    death = next((d for d in deaths if d["playerId"] == target and d["time"] * 1000 + fight.start >= at), None)
    if death:
        end = min(end, death["time"] * 1000 + fight.start)
    return round((min(end, fight.end) - fight.start) / 1000, 3), basis


def build_defensive_pull(*, code, fight, boss, streams, actor_names, player_ids, ability_labels=None):
    abilities, specs, _ = defensive_catalog()
    labels = ability_labels or {}
    combatants = {e["sourceID"]: e for e in streams.get("combatants", []) if e.get("sourceID")}
    participants = (set(fight.friendly_player_ids) or set(player_ids)) | set(combatants)
    duration = max(.001, (fight.end - fight.start) / 1000)
    boss_spells = {s["spell_id"]: s for s in boss["abilities"]}
    deaths = death_markers(streams.get("deaths", []), fight, participants, actor_names)
    add_death_recaps(deaths, streams=streams, fight=fight, actor_names=actor_names, ability_labels=labels)
    damage, healing = defaultdict(list), defaultdict(list)
    for e in streams.get("pressure", []): damage[e.get("targetID")].append(e)
    for e in streams.get("immunities", []): damage[e.get("targetID")].append({**e, "type": "immune"})
    for e in streams.get("healing", []): healing[e.get("targetID")].append(e)
    damage_windows = {p: EventWindow(events) for p, events in damage.items()}
    heal_windows = {p: EventWindow(events) for p, events in healing.items()}
    players = []
    casts = sorted((e for e in streams.get("casts", []) if e.get("type") == "cast"), key=lambda e: e["timestamp"])
    for actor in sorted(participants, key=lambda p: actor_names.get(p, "")):
        info = combatants.get(actor, {})
        spec_id = info.get("specID", info.get("specId"))
        lanes = {}
        for sid, ability in abilities.items():
            if ability_access(ability, info) == "available" or ability["category"] == "consumable":
                lanes[sid] = dict(id=f"{actor}:{sid}", **defensive_display(ability, info), events=[])
        seen = set()
        for event in casts:
            sid, at = _event_ability_id(event), event["timestamp"]
            if event.get("sourceID") != actor or sid not in abilities or not fight.start <= at <= fight.end:
                continue
            key = (sid, at)
            if key in seen: continue
            seen.add(key)
            if sid not in lanes:
                lanes[sid] = dict(id=f"{actor}:{sid}", **defensive_display(abilities[sid], info), events=[])
            lane = lanes[sid]
            lane["access"] = "observed"
            time = round((at - fight.start) / 1000, 3)
            recipient = event.get("targetID")
            # WCL item/self casts commonly carry targetID=-1 even though their
            # healing and protection target the caster. Never assign externals
            # to self merely because their recipient is missing.
            if lane["category"] in ("personal", "consumable"):
                recipient = actor
            elif not recipient or recipient < 0:
                recipient = None
            end, basis = _window_end({**event, "targetID": recipient}, lane, streams.get("auras", []), fight, deaths)
            observation_end = min(fight.end, fight.start + end * 1000 if end > time else at + 3000)
            # Recipient exposure for targeted externals; caster context for group casts.
            exposure_actor = recipient if recipient in participants else actor
            hits = damage_windows[exposure_actor].between(at, observation_end + .001) if exposure_actor in damage_windows else []
            protection = damage_evidence(hits)
            # Do not credit a refreshed/recast shield to both casts when the
            # older duration could only be inferred from research metadata.
            next_cast = next((e["timestamp"] for e in casts if e["timestamp"] > at
                and e.get("sourceID") == actor and _event_ability_id(e) == sid
                and (lane["category"] in ("personal", "consumable") or e.get("targetID") == recipient)), fight.end + 1)
            shield_end = min(observation_end + .001, next_cast)
            shield_events = heal_windows[recipient].between(at, shield_end) if recipient in heal_windows and end > time else []
            protection["spellAbsorbed"] = round(sum(max(0, e.get("amount") or 0) for e in shield_events
                if e.get("type") == "absorbed" and e.get("sourceID") == actor and _event_ability_id(e) == sid))
            protection["subject"] = actor_names.get(exposure_actor, "Unknown player")
            heals = heal_windows[recipient].between(at, min(fight.end, at + 7000)) if recipient in heal_windows else []
            # Only this spell's direct output, not other healing during the window.
            own_heals = [e for e in heals if _event_ability_id(e) == sid and e.get("sourceID") == actor and e.get("type") == "heal"]
            nearest = sorted((e for e in streams.get("bossCasts", []) if e.get("type") == "cast"
                              and _event_ability_id(e) in boss_spells), key=lambda e: abs(e["timestamp"] - at))
            boss_event = nearest[0] if nearest else None
            lane["events"].append(dict(time=time, end=end, durationBasis=basis,
                target=actor_names.get(recipient, "Unknown target"), targetId=recipient,
                selfUse=recipient == actor, origin="Recorded cast",
                damageTaken=protection["damageTaken"], protection=protection,
                observationSeconds=round((observation_end - at) / 1000, 3),
                effectiveHealing=round(sum(max(0, e.get("amount") or 0) for e in own_heals)),
                overhealing=round(sum(max(0, e.get("overheal") or 0) for e in own_heals)),
                nearbyBoss=(dict(name=boss_spells[_event_ability_id(boss_event)]["name"],
                                delta=round((at-boss_event["timestamp"])/1000, 3)) if boss_event else None)))
        players.append(dict(id=f"{code}:{actor}", actorId=actor, name=actor_names.get(actor, f"Player {actor}"),
            specId=spec_id, spec=specs.get(spec_id, {}).get("name", "Unknown specialization"),
            role=specs.get(spec_id, {}).get("role", "unknown"),
            lanes=sorted(lanes.values(), key=lambda l: (l["category"] == "consumable", l["name"])),
            pressure=personal_damage_series(damage.get(actor, []), fight, boss_spells, ability_labels=labels),
            deaths=[d for d in deaths if d["playerId"] == actor],
            buildKnown=bool(info.get("talentTree"))))
    add_defensive_readiness(players, combatants)
    add_cooldown_attribution(players, fight, streams, combatants)
    raid_pressure = personal_damage_series([event for actor in participants for event in damage.get(actor, [])],
                                           fight, boss_spells, ability_labels=labels)
    for index, point in enumerate(raid_pressure):
        for field in ("cooldownMitigated", "cooldownAbsorbed"):
            point[field] = round(sum(player["pressure"][index][field] for player in players), 2)
        point["cooldownSources"] = list(dict.fromkeys(label for player in players
            for label in player["pressure"][index]["cooldownSources"]))
    boss_lanes = {}
    for event in sorted(streams.get("bossCasts", []), key=lambda e: e["timestamp"]):
        sid = _event_ability_id(event)
        if event.get("type") != "cast" or sid not in boss_spells or not fight.start <= event["timestamp"] <= fight.end: continue
        lane = boss_lanes.setdefault(sid, make_lane(f"boss:{sid}", boss_spells[sid], None, actor_names, {}, False))
        time = round((event["timestamp"] - fight.start) / 1000, 3)
        if not any(e["time"] == time for e in lane["events"]):
            lane["events"].append(dict(time=time, end=time, durationBasis="Recorded cast"))
    return dict(id=f"{code}:{fight.id}", fightId=fight.id, reportCode=code, duration=duration, kill=fight.kill,
                url=f"https://www.warcraftlogs.com/reports/{code}?fight={fight.id}", players=players,
                bossLanes=list(boss_lanes.values()), deaths=deaths,
                pressure=raid_pressure)


def fetch_defensive_usage(*, report_codes, encounter_id, difficulty, include_reference=False,
                          token=None, client_id=None, client_secret=None):
    load_env()
    abilities, _, research = defensive_catalog()
    _, bosses = coverage_catalog()
    boss = bosses[int(encounter_id)]
    bearer = _resolve_token(token, client_id, client_secret)
    pulls = []
    tracked = set(abilities) | {s["spell_id"] for s in boss["abilities"]}
    spell_filter = "ability.id IN (" + ",".join(map(str, sorted(tracked))) + ")"
    for reference in dict.fromkeys(report_codes):
        code = _sanitize_report_code(reference)
        with requests.Session() as session:
            fights, names, classes, _ = fetch_fights(session, bearer, code)
            chosen = sorted(_select_fights([f for f in fights if f.encounter_id == int(encounter_id)],
                name_filter=None, fight_ids=None, difficulty=difficulty), key=lambda f: f.start)
            labels = _fetch_ability_labels(session, bearer, code)
            streams = fetch_event_streams(code=code, fights=chosen, token=bearer, actor_names=names,
                streams={"casts": {"data_type": "Casts", "extra_filter": spell_filter},
                         "bossCasts": {"data_type": "Casts", "extra_filter": spell_filter, "hostility_type": "Enemies"},
                         
                         "immunities": {"data_type": "All", "extra_filter": 'type = "miss" AND missType = "immune"'},
                         "combatants": {"data_type": "CombatantInfo"}, "deaths": {"data_type": "Deaths"},
                         "auras": {"data_type": "Buffs", "extra_filter": spell_filter},
                         "healing": {"data_type": "Healing", "extra_filter": 'type = "heal" OR type = "absorbed"'},
                         "pressure": {"data_type": "All", "extra_filter": 'type = "damage" OR type = "healabsorbed"'}},
                partitioned_streams=("pressure", "healing"))
            for fight in chosen:
                pull = build_defensive_pull(code=code, fight=fight, boss=boss,
                    streams={k: v.get(fight.id, []) for k, v in streams.items()}, actor_names=names,
                    player_ids={p for p, cls in classes.items() if cls}, ability_labels=labels)
                pull["label"] = f"Pull {len(pulls)+1} · {'Kill' if fight.kill else 'Wipe'} · {int(pull['duration'])//60}:{int(pull['duration'])%60:02d} · {code} / {fight.id}"
                pulls.append(pull)
    # Retain the legacy keyword and empty response field for existing callers;
    # defensive reports no longer fetch third-party comparison data.
    return dict(boss=boss["name"], patch=research["patch"], catalogueDate=research["research_as_of"],
                binSeconds=2, pulls=pulls, references={})
