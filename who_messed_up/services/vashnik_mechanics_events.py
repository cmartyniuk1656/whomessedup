"""Small Vashnik event selectors shared by the independent subreport calculators."""
from .mechanics_events import ability, clusters, damage, timestamp
from .mechanics_models import MechanicDetail


def inside(events, start, end):
    return [e for e in events if start <= timestamp(e) < end]


def player_hits(ctx, ids):
    return [e for e in ctx.events("damage_taken", ids, friendly=True)
            if e.get("type") == "damage" and e.get("hitType") != 10]


def assignment_groups(ctx, aid, span=3000):
    return [[e["life"] for e in group] for group in clusters(
        [{"timestamp": life.start, "life": life} for life in ctx.lives({aid})], span)]


def hit_details(ctx, row, hits, section):
    for group in clusters(hits):
        names = sorted({ctx.name(e.get("targetID")) for e in group})
        row.details.append(MechanicDetail(section, ", ".join(names), timestamp(group[0]),
                                         f"{len(group)} hit events; {sum(map(damage, group)):,.0f} damage.",
                                         tone="warning"))


def life_end(life, fight_end):
    return min(life.removed if life.removed is not None else fight_end,
               life.superseded if life.superseded is not None else fight_end, fight_end)


def active_at(life, at, fight_end, tolerance=250):
    return life.start - tolerance <= at <= life_end(life, fight_end) + tolerance


def infusion_context(ctx, row, at):
    """Show the latest logged boss infusion state, including nearby application packets."""
    for aid, name in ((1293971, "Flame Infusion"), (1293968, "Shadow Infusion")):
        events = sorted([e for e in ctx.events("enemy_buffs", {aid})
                         if e.get("type") in {"applybuff", "applybuffstack", "removebuff", "removebuffstack"}
                         and timestamp(e) <= at + 1000], key=timestamp)
        if events:
            last = events[-1]
            stack = 0 if last.get("type") == "removebuff" else last.get("stack", 1)
            row.details.append(MechanicDetail("Fountain context", name, timestamp(last), f"Latest logged stack: {stack}."))
