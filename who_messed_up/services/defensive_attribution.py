"""Attribute shield output and estimate supported cooldown DR, never baseline armor.

Rates below are explicit adapters for the supplied Midnight 12.1 research. Only
all-school, multiplicative DR is supported. Require a paired recipient aura;
nominal durations, school/area restrictions, deferrals and health-dependent DR
are not silently approximated. Marginal per-cast estimates are not additive.
"""
from collections import defaultdict
from math import prod

from .cooldown_usage import _event_ability_id
from .defensive_catalog import defensive_catalog, selected_rank
from .defensive_events import STANCES

# Base fractions and talent IDs adding percentage points, from defensives.json.
RATES = {
    118038: (.30, {}), 184364: (.30, {}), 871: (.40, {}),
    498: (.20, {}), 403876: (.20, {1261562: .10}), 31850: (.30, {}),
    86659: (.50, {}), 389539: (.30, {}), 48792: (.30, {}),
    22812: (.20, {393618: .10, 449191: .10}), 61336: (.50, {449191: .10}),
    102342: (.20, {}), 198589: (.25, {205411: .10}), 47585: (.75, {}),
    33206: (.40, {440738: .10}), 108271: (.40, {377933: .20}),
    363916: (.30, {441180: .10}), 264735: (.30, {472707: .10}),
    414658: (.70, {}), 104773: (.25, {317138: .15}),
    586: (0, {373446: .10}), 386208: (.15, {1235047: .06}),
}


def reduction_rate(spell, combatant):
    if spell not in RATES:
        return None, "This effect has no supported damage-reduction estimate."
    base, additions = RATES[spell]
    # Bloody Fortitude depends on missing health at the hit, which we don't model.
    uncertain = {434136} if spell == 48792 else set()
    if spell == 386208:
        uncertain.add(452494)
    spec = combatant.get("specID", combatant.get("specId"))
    modifiers = defensive_catalog()[2]["talent_modifiers"]
    for modifier in modifiers:
        sid = modifier["spell_id"]
        if sid not in additions and sid not in uncertain:
            continue
        profiles = [p for p in modifier["applicability"] if p["specialization_id"] == spec or spec is None]
        if profiles and not combatant.get("talentTree"):
            return None, "Talent data is needed to resolve this cooldown's reduction."
        if any(selected_rank(combatant, p["talent"]) for p in profiles):
            if sid in uncertain:
                return None, ("The selected talent makes reduction depend on damage school." if sid == 452494
                              else "The selected talent makes reduction depend on missing health.")
            base += additions[sid]
    if spell == 586 and not base:
        return None, "Translucent Image is not selected; Fade has no damage-reduction estimate."
    return base, None


def _aura_window(auras, source, target, spell, at, until, until_cancelled=False):
    # Match the small cast/application ordering tolerance used by usage windows.
    own = [e for e in auras if e.get("sourceID") == source and e.get("targetID") == target
           and _event_ability_id(e) == spell and e["timestamp"] >= at - 100]
    apply = next((e for e in own if e["type"] in ("applybuff", "refreshbuff") and e["timestamp"] <= at + 1500), None)
    if not apply:
        return None
    end = next((e for e in own if e["timestamp"] > apply["timestamp"]
                and e["type"] in ("removebuff", "refreshbuff", "applybuff")), None)
    if not end and not until_cancelled:
        return None
    return dict(start=apply["timestamp"], end=min(until, end["timestamp"]) if end else until, initialStack=apply.get("stack", 15),
                stacks=[(e["timestamp"], e.get("stack")) for e in own
                        if e["type"] in ("applybuffstack", "removebuffstack")])


def _rate_at(model, timestamp):
    window = model["window"]
    if not window["start"] <= timestamp < window["end"]:
        return None
    if model["spell"] == 389539:
        # Sentinel starts at 15; use logged changes, not a guessed decay timer.
        stack = window["initialStack"]
        for at, value in window["stacks"]:
            if at > timestamp:
                break
            stack = value
        return stack * .02 if isinstance(stack, (int, float)) and 0 < stack <= 15 else None
    return model["rate"]


def _prevented(hit, remaining_fraction):
    # Post-DR, pre-absorb impact. Baseline armor/passives remain in both worlds.
    impact = sum(max(0, hit.get(key) or 0) for key in ("amount", "absorbed", "overkill"))
    estimate = impact * (1 / remaining_fraction - 1)
    # Never claim more DR than WCL recorded, or invent DR when it is unavailable.
    return min(estimate, max(0, hit.get("mitigated") or 0))


def add_cooldown_attribution(players, fight, streams, combatants):
    """Enrich cast evidence and per-player bins; raid bins sum these once.

    A joint graph estimate removes all supported active cooldown multipliers.
    Each cast's separate marginal estimate removes just that cast while keeping
    other protection fixed. Adding marginal figures would misstate overlaps.
    """
    models = defaultdict(list)
    shields = defaultdict(list)
    by_actor = {p["actorId"]: p for p in players}
    auras = sorted(streams.get("auras", []), key=lambda e: e["timestamp"])
    for player in players:
        source = player["actorId"]
        for point in player["pressure"]:
            point.update(cooldownMitigated=0, cooldownAbsorbed=0, cooldownSources=[])
        for lane in player["lanes"]:
            for index, event in enumerate(lane["events"]):
                target, spell = event["targetId"], lane["spellId"]
                at = fight.start + event["time"] * 1000
                until = fight.start + event["end"] * 1000
                next_cast = next((other for other in lane["events"][index + 1:] if other["targetId"] == target), None)
                if next_cast:
                    until = min(until, fight.start + next_cast["time"] * 1000)
                attribution = dict(estimatedReduction=None, matchedAbsorbed=event["protection"]["spellAbsorbed"],
                                   evaluatedHits=0, status="unavailable", note="")
                event["attribution"] = attribution
                if target not in by_actor:
                    attribution["note"] = "A confirmed player recipient is required."
                    continue
                shield_end = fight.start + event["end"] * 1000 + .001
                if next_cast:
                    shield_end = min(shield_end, fight.start + next_cast["time"] * 1000)
                shields[(source, target, spell)].append((at, shield_end))
                rate, reason = reduction_rate(spell, combatants.get(source, {}))
                window = _aura_window(auras, source, target, spell, at, until, spell in STANCES) if rate else None
                if not window or not rate:
                    attribution["note"] = reason or "A paired buff application and end are needed; a nominal window is insufficient."
                    continue
                attribution.update(estimatedReduction=0, status="estimated",
                    note="Estimated by removing this cooldown's reduction while keeping other protection fixed. Only logged hits are valued; immunity, avoidance and death-save benefits are not priced.")
                models[target].append(dict(spell=spell, rate=rate, window=window, attribution=attribution,
                                           label=f"{lane['name']} ({player['name']})"))

    def bucket(actor, timestamp):
        if actor not in by_actor or not fight.start <= timestamp <= fight.end:
            return None
        points = by_actor[actor]["pressure"]
        return points[min(len(points) - 1, int((timestamp - fight.start) / 2000))]

    for hit in streams.get("pressure", []):
        if hit.get("type") != "damage":
            continue
        target, at = hit.get("targetID"), hit["timestamp"]
        point = bucket(target, at)
        if point is None:
            continue
        active = [(model, _rate_at(model, at)) for model in models.get(target, [])]
        active = [(model, rate) for model, rate in active if rate is not None]
        # The same buff from different casters does not multiply with itself.
        active = list({model["spell"]: (model, rate) for model, rate in
                       sorted(active, key=lambda pair: pair[0]["window"]["start"])}.values())
        if not active:
            continue
        point["cooldownMitigated"] += _prevented(hit, prod(1 - rate for _, rate in active))
        for model, rate in active:
            if _prevented(hit, 1 - rate) > 0 and model["label"] not in point["cooldownSources"]:
                point["cooldownSources"].append(model["label"])
            evidence = model["attribution"]
            if "mitigated" in hit or "unmitigatedAmount" in hit:
                evidence["evaluatedHits"] += 1
            evidence["estimatedReduction"] += _prevented(hit, 1 - rate)

    for heal in streams.get("healing", []):
        if heal.get("type") != "absorbed":
            continue
        at, target = heal["timestamp"], heal.get("targetID")
        windows = shields.get((heal.get("sourceID"), target, _event_ability_id(heal)), [])
        point = bucket(target, at)
        if point is not None and any(start <= at < end for start, end in windows):
            point["cooldownAbsorbed"] += max(0, heal.get("amount") or 0)
            source = by_actor.get(heal.get("sourceID"))
            ability = defensive_catalog()[0].get(_event_ability_id(heal))
            if source and ability and (heal.get("amount") or 0) > 0:
                label = f"{ability['name']} ({source['name']})"
                if label not in point["cooldownSources"]:
                    point["cooldownSources"].append(label)
    for player in players:
        for point in player["pressure"]:
            width = min(2, (fight.end - fight.start) / 1000 - point["time"])
            point["cooldownMitigated"] = round(point["cooldownMitigated"] / width, 2)
            point["cooldownAbsorbed"] = min(point["absorbed"], round(point["cooldownAbsorbed"] / width, 2))
        for lane in player["lanes"]:
            for event in lane["events"]:
                evidence = event["attribution"]
                if evidence["estimatedReduction"] is not None:
                    if evidence["evaluatedHits"]:
                        evidence["estimatedReduction"] = round(evidence["estimatedReduction"])
                    else:
                        evidence.update(estimatedReduction=None, status="unavailable",
                            note="No evaluable damage hits during the confirmed buff; this is not a zero-value verdict.")
