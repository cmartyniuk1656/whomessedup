"""Calculate instance-specific add contributions and direct pickup/contact evidence."""
from collections import Counter, defaultdict

from .common import _resolve_event_source_player
from .mechanics_events import ability, damage, instance, timestamp
from .mechanics_lifetimes import enemy_lives
from .mechanics_models import MechanicDetail
from .the_twin_fangs_mechanics_models import ADD_NAMES, GLOBULE, WAVE


def _scoped(ctx, stream):
    return [e for e in ctx.events(stream)
            if ctx.fight.start <= timestamp(e) <= ctx.fight.end]


def contact_events(ctx, *, waves=False):
    """Return the direct contacts shared by contact and matched-stack reports."""
    for event in sorted(_scoped(ctx, "debuffs" if waves else "pickups"), key=timestamp):
        if event.get("targetID") not in ctx.players or ability(event) != (WAVE if waves else GLOBULE):
            continue
        if event.get("sourceID") in ctx.players or event.get("sourceID") in ctx.owners:
            continue
        if waves:
            if event.get("type") != "applydebuff":
                continue
        elif event.get("type") != "damage" or event.get("tick"):
            continue
        yield event


def build_contacts(ctx, *, waves=False):
    rows = []
    for event in contact_events(ctx, waves=waves):
        player = ctx.name(event["targetID"])
        label = "Stir the Depths" if waves else "Caustic Globule"
        row = ctx.row(timestamp(event), len(rows) + 1, label)
        row.players["players"] = [player]
        row.soak_counts = {player: 1}
        row.values["contacts"] = 1
        row.details.append(MechanicDetail(
            "Contact evidence", player, timestamp(event),
            "Stir the Depths debuff applied; no damage tick is required." if waves
            else "Direct Caustic Globule soak impact; this is a pickup, not an unsoaked rupture.",
        ))
        rows.append(row)
    return rows


def build_add_damage(ctx):
    evidence = defaultdict(list)
    for stream in ("add_damage", "summons", "enemy_deaths"):
        for event in _scoped(ctx, stream):
            if ctx.names.get(event.get("targetID")) not in ADD_NAMES:
                continue
            if stream == "add_damage" and (event.get("type") != "damage" or event.get("hitType") == 10):
                continue
            evidence[instance(event, "target")].append(event)
    rows = []
    for index, life in enumerate(enemy_lives(evidence, ctx.fight.end), 1):
        row = ctx.row(life.start, index, f"{ctx.name(life.key[0])} {life.key[1] or '?'}")
        totals = Counter()
        for event in life.events:
            if event.get("type") != "damage":
                continue
            name, player = _resolve_event_source_player(event, ctx.names, ctx.owners)
            if player in ctx.players and damage(event) > 0:
                totals[name] += damage(event)
        row.contributions = dict(totals)
        row.players["contributors"] = sorted(totals, key=lambda name: (-totals[name], name))
        row.values.update(damage=sum(totals.values()),
                          duration=(life.end - life.start) / 1000 if life.death is not None else None)
        row.details.append(MechanicDetail(
            "Add lifetime", "Confirmed death" if life.death is not None else "Unresolved at pull end",
            life.start,
            f"{'Summoned' if life.summoned else 'First observed'} {ctx.offset(life.start)}; "
            f"observed through {ctx.offset(life.end)}. Effective damage excludes absorbs and overkill.",
        ))
        rows.append(row)
    return rows
