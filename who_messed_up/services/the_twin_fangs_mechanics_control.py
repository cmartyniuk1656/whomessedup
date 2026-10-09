"""Attribute explicit kicks and conservatively correlate CC with shield removal.

Shield removal has no player source in WCL. Match applied control auras on the
same actor instance and retain competing/unsupported evidence without credit.
"""
from collections import defaultdict

from .common import _resolve_event_source_player
from .mechanics_events import ability, instance, timestamp
from .mechanics_models import MechanicDetail
from .the_twin_fangs_mechanics_models import (
    ADD_NAMES, BULWARK_NAME, BULWARK_SHIELD, INTERRUPT_ABILITIES,
    INTERRUPTED_SPELLS, SHIELD_CC_ABILITIES, SHIELD_CC_WINDOW_MS,
)


def _events(ctx, stream):
    return sorted((e for e in ctx.events(stream)
                   if ctx.fight.start <= timestamp(e) <= ctx.fight.end), key=timestamp)


def _target_label(ctx, event):
    target, number = instance(event, "target")
    return f"{ctx.name(target)} #{number}" if number else f"{ctx.name(target)} (instance unavailable)"


def build_interrupts(ctx):
    rows, seen = [], set()
    for event in _events(ctx, "interrupts"):
        if event.get("type") != "interrupt" or ctx.names.get(event.get("targetID")) not in ADD_NAMES:
            continue
        name, player = _resolve_event_source_player(event, ctx.names, ctx.owners)
        if player not in ctx.players:
            continue
        key = (timestamp(event), instance(event, "target"), event.get("sourceID"),
               ability(event), event.get("extraAbilityGameID"))
        if key in seen:
            continue
        seen.add(key)
        row = ctx.row(timestamp(event), len(rows) + 1, _target_label(ctx, event))
        row.players["players"] = [name]
        row.soak_counts = {name: 1}
        row.values.update(interrupts=1, spell=INTERRUPTED_SPELLS.get(
            event.get("extraAbilityGameID"), f"Spell {event.get('extraAbilityGameID', 'unknown')}"))
        row.details.append(MechanicDetail(
            "Successful interrupt", name, timestamp(event),
            f"{INTERRUPT_ABILITIES.get(ability(event), 'Interrupt ability ' + str(ability(event)))} "
            f"interrupted {row.values['spell']} on {row.label}.",
        ))
        rows.append(row)
    return rows


def build_shield_ccs(ctx):
    events = [e for e in _events(ctx, "shield_control")
              if ctx.names.get(e.get("targetID")) == BULWARK_NAME]
    controls = defaultdict(list)
    for event in events:
        if event.get("type") == "applydebuff" and ability(event) in SHIELD_CC_ABILITIES:
            controls[instance(event, "target")].append(event)
    active, seen, rows = {}, set(), []
    for event in events:
        if ability(event) != BULWARK_SHIELD:
            continue
        key, at = instance(event, "target"), timestamp(event)
        if event.get("type") == "applybuff":
            # WCL can emit a second application when the absorb amount changes.
            active.setdefault(key, at)
            continue
        if event.get("type") != "removebuff" or (key, at) in seen:
            continue
        seen.add((key, at))
        start = active.pop(key, None)
        candidates = [e for e in controls[key] if start is not None
                      and max(start, at - SHIELD_CC_WINDOW_MS) <= timestamp(e) <= at]
        row = ctx.row(at, len(rows) + 1, _target_label(ctx, event))
        players, signatures = {}, set()
        for cc in candidates:
            name, player = _resolve_event_source_player(cc, ctx.names, ctx.owners)
            signature = (player, cc.get("sourceID"), ability(cc), timestamp(cc))
            if signature in signatures:
                continue
            signatures.add(signature)
            if player in ctx.players:
                players[player] = name
            row.details.append(MechanicDetail(
                "Applied CC", name, timestamp(cc),
                f"{SHIELD_CC_ABILITIES[ability(cc)]} applied {at - timestamp(cc):.0f}ms before shield removal.",
            ))
        supported = bool(key[1] and start is not None and (event.get("absorb") or 0) > 0)
        credited = supported and len(players) == 1 and all(
            _resolve_event_source_player(cc, ctx.names, ctx.owners)[1] in ctx.players for cc in candidates)
        status = "Attributed CC break" if credited else "Ambiguous CCs" if supported and len(players) > 1 else "Unattributed removal"
        row.values.update(breaks=int(credited), ambiguous=int(status == "Ambiguous CCs"),
                          unattributed=int(status == "Unattributed removal"), status=status)
        row.players["players"] = sorted(players.values())
        if credited:
            row.soak_counts = {next(iter(players.values())): 1}
        row.details.insert(0, MechanicDetail(
            "Shield removal", status, at,
            "Credit requires an observed shield, a known instance, remaining absorb, and a single player with matching CC. "
            "Competing players are shown for review without awarding duplicate credit.",
        ))
        rows.append(row)
    return rows
