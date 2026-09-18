"""Living Venom instance lifetimes, shield work, and explosion spacing."""
from collections import Counter, defaultdict

from .common import _resolve_event_source_player
from .mechanics_events import ability, damage, instance, timestamp
from .mechanics_lifetimes import enemy_lives
from .mechanics_models import MechanicDetail
from .vashnik_mechanics_events import hit_details, infusion_context
from .vashnik_mechanics_models import ADD_NAMES, COATING, LEAK, SURGE


def build_adds(ctx):
    evidence = defaultdict(list)
    for stream, side in (("add_summons", "target"), ("enemy_deaths", "target"),
                         ("enemy_buffs", "target"), ("add_damage", "target"), ("enemy_casts", "source")):
        for event in ctx.events(stream):
            if ctx.names.get(event.get(side + "ID")) not in ADD_NAMES:
                continue
            if stream == "enemy_casts" and ability(event) not in {SURGE, LEAK}:
                continue
            if stream == "enemy_buffs" and ability(event) != COATING:
                continue
            if stream == "add_damage" and (event.get("type") != "damage" or event.get("hitType") == 10):
                continue
            evidence[instance(event, side)].append(event)
    lives = enemy_lives(evidence, ctx.fight.end)
    surges = sorted([e for life in lives for e in life.events
                     if e.get("type") == "cast" and ability(e) == SURGE], key=timestamp)
    previous_surge = {id(e): timestamp(surges[i - 1]) if i else None for i, e in enumerate(surges)}
    rows = []
    for index, life in enumerate(lives, 1):
        row = ctx.row(life.start, index, f"{ctx.name(life.key[0])} {life.key[1] or '?'}")
        infusion_context(ctx, row, row.start)
        casts = [e for e in life.events if e.get("type") == "cast"]
        leaked = any(ability(e) == LEAK for e in casts)
        dead = life.death is not None and life.death < ctx.fight.end - 1000
        totals = Counter()
        health = shield = 0
        for event in life.events:
            if event.get("type") != "damage" or instance(event, "target") != life.key:
                continue
            name, player = _resolve_event_source_player(event, ctx.names, ctx.owners)
            if player not in ctx.players:
                continue
            amount, absorbed = damage(event), max(0, float(event.get("absorbed") or 0))
            health += amount
            shield += absorbed
            totals[name] += amount + absorbed
        row.contributions = dict(totals)
        row.players["contributors"] = sorted(totals, key=lambda name: -totals[name])
        row.values.update(status="Leaked" if leaked else "Confirmed death" if dead else "Unresolved",
                          kills=int(dead and not leaked), leaks=int(leaked), unresolved=int(not dead and not leaked),
                          duration=(life.end - life.start) / 1000 if dead else None,
                          health=health, shield=shield, damage=health + shield, surge=0, close=0)
        row.details.append(MechanicDetail("Lifetime", row.values["status"], life.start,
                                         f"{'Summoned' if life.summoned else 'First observed'} {ctx.offset(life.start)}; observed through {ctx.offset(life.end)}.",
                                         ["Summon recorded" if life.summoned else "Spawn time unavailable"]))
        for event in casts:
            at = timestamp(event)
            previous = previous_surge.get(id(event))
            close = ability(event) == SURGE and previous is not None and at - previous < 3000
            row.values["surge"] += int(ability(event) == SURGE)
            row.values["close"] += int(close)
            description = f"{(at - previous) / 1000:.2f}s since preceding Burning Surge." if ability(event) == SURGE and previous is not None else "Cast completed."
            row.details.append(MechanicDetail("Add casts", "Burning Surge" if ability(event) == SURGE else "Leaking Fumes", at,
                                             description, ["Close explosions: review"] if close else [], "warning" if close or leaked else None))
        coating = [e for e in life.events if e.get("type") == "applybuff" and ability(e) == COATING]
        for event in coating:
            row.details.append(MechanicDetail("Shrouded Coating", "Shield applied", timestamp(event),
                                             f"Logged shield value: {event.get('absorb', 'unavailable')}."))
        for event in life.events:
            if event.get("type") == "removebuff" and ability(event) == COATING:
                alive = life.death is None or timestamp(event) < life.death - 250
                row.details.append(MechanicDetail("Shrouded Coating", "Shield removed", timestamp(event),
                                                 "Removed while alive; inspect shield contributions." if alive else "Removal near death; may be cleanup."))
        # Damage after death can be a legitimate explosion/DoT. It is contextual
        # raid pressure, never player damage credited against a dead add.
        next_start = min((other.start for other in lives if other.key == life.key and other.start > life.start), default=ctx.fight.end + 1)
        pressure = [e for e in ctx.events("damage_taken", friendly=True)
                    if e.get("type") == "damage" and e.get("hitType") != 10
                    and instance(e, "source") == life.key and life.start <= timestamp(e) < next_start]
        row.values["pressure"] = sum(map(damage, pressure))
        hit_details(ctx, row, pressure, "Add-originated raid damage")
        rows.append(row)
    return rows
