"""Infection evidence: explicit dispels and healer-attributed absorb healing."""
from collections import Counter

from .mechanics_events import clusters, damage, match_aura_dispel, timestamp
from .mechanics_models import DispelRecord, MechanicDetail
from .vashnik_mechanics_events import assignment_groups, hit_details, inside, life_end, player_hits
from .vashnik_mechanics_models import EXPLODING, EXPLOSION, STYGIAN, STYGIAN_BURST


def build_dispels(ctx):
    groups = assignment_groups(ctx, EXPLODING)
    events = [e for e in ctx.events("dispels") if e.get("type") == "dispel"
              and e.get("extraAbilityGameID") == EXPLODING and e.get("targetID") in ctx.players]
    used = set()
    rows = []
    for index, group in enumerate(groups, 1):
        row = ctx.row(group[0].start, index, f"Infection {index}")
        row.players["assigned"] = sorted(ctx.name(l.player_id) for l in group)
        row.values.update(assigned=len(group), dispelled=0, unmatched=0, not_dispelled=0)
        for life in group:
            event = match_aura_dispel(life, [e for e in events if id(e) not in used], ctx.fight.end)
            status, stop = life.status(ctx.events("deaths", friendly=True), ctx.fight.end)
            peak = max([life.initial_stack or 1] + [stack or 1 for _, stack in life.changes])
            description = status
            if event:
                used.add(id(event))
                stop = timestamp(event)
                healer = ctx.name(event.get("sourceID"))
                delay = (stop - life.start) / 1000
                row.dispels.append(DispelRecord(ctx.name(life.player_id), healer, stop, delay))
                row.dispel_counts[healer] = row.dispel_counts.get(healer, 0) + 1
                row.values["dispelled"] += 1
                description = f"Dispelled by {healer} at {ctx.offset(stop)} ({delay:.2f}s after application)."
            else:
                row.values["not_dispelled"] += 1
            row.details.append(MechanicDetail("Infections", ctx.name(life.player_id), life.start,
                                             description, [f"Peak stack {peak}"]))
        rows.append(row)
    # Keep dispels whose applications were not recorded, without manufacturing delays.
    for event in events:
        if id(event) in used:
            continue
        row = ctx.row(timestamp(event), len(rows) + 1, "Unmatched dispel")
        healer = ctx.name(event.get("sourceID"))
        row.players["assigned"] = [ctx.name(event.get("targetID"))]
        row.values.update(assigned=0, dispelled=1, unmatched=1, not_dispelled=0)
        row.dispel_counts[healer] = 1
        row.details.append(MechanicDetail("Infections", healer, timestamp(event),
                                         f"Dispelled {row.players['assigned'][0]}; application and delay unknown."))
        rows.append(row)
    # Impact windows follow application sets, not removal times. Each hit appears once.
    rows.sort(key=lambda r: r.start)
    impacts = clusters(player_hits(ctx, {EXPLOSION}))
    for index, row in enumerate(rows):
        end = rows[index + 1].start if index + 1 < len(rows) else ctx.fight.end + 1
        hits = inside(player_hits(ctx, {EXPLOSION}), row.start, end)
        row.values["explosion_hits"] = len(hits)
        hit_details(ctx, row, hits, "Caustic Explosion impacts")
        for impact_index, impact in enumerate(impacts):
            at = timestamp(impact[0])
            if row.start <= at < end and impact_index:
                gap = (at - timestamp(impacts[impact_index - 1][0])) / 1000
                row.details.append(MechanicDetail("Explosion spacing", f"{gap:.2f}s since preceding impact burst", at,
                                                 "Simultaneous impacts may merge; spacing is context, not a dispel score."))
    return rows


def build_stygian(ctx):
    rows = []
    groups = assignment_groups(ctx, STYGIAN)
    absorbs = [e for e in ctx.events("stygian_absorbs", {STYGIAN}, friendly=True)
               if e.get("type") == "healabsorbed"]
    for index, group in enumerate(groups, 1):
        row = ctx.row(group[0].start, index, f"Stygian {index}")
        row.players["assigned"] = sorted(ctx.name(l.player_id) for l in group)
        totals = Counter()
        row.values.update(assigned=len(group), cleared=0, unresolved=0, healing=0, clear_seconds=[])
        for life in group:
            stop = life_end(life, ctx.fight.end)
            heals = [e for e in absorbs if e.get("targetID") == life.player_id
                     and life.start <= timestamp(e) <= stop]
            for event in heals:
                healer_id = event.get("healerID")
                # WCL's source is the boss; only healerID identifies the contribution.
                totals[ctx.name(healer_id) if healer_id in ctx.players else "Unknown healer"] += damage(event)
            amount = sum(map(damage, heals))
            status, _ = life.status(ctx.events("deaths", friendly=True), ctx.fight.end)
            clear = status == "Removed alive" and any(stop - timestamp(e) <= 250 for e in heals)
            row.values["cleared" if clear else "unresolved"] += 1
            row.values["healing"] += amount
            if clear:
                row.values["clear_seconds"].append((stop - life.start) / 1000)
            row.details.append(MechanicDetail("Absorb outcomes", ctx.name(life.player_id), life.start,
                                             f"{'Healing-supported clear' if clear else status + '; clear unconfirmed'} at {ctx.offset(stop)}; {amount:,.0f} absorb healing.",
                                             [f"Observed {(stop - life.start) / 1000:.2f}s"], None if clear else "warning"))
        row.contributions = dict(totals)
        durations = row.values["clear_seconds"]
        row.values["average"] = sum(durations) / len(durations) if durations else None
        end = groups[index][0].start if index < len(groups) else ctx.fight.end + 1
        hits = inside(player_hits(ctx, {STYGIAN_BURST}), row.start, end)
        row.values["burst_hits"] = len(hits)
        hit_details(ctx, row, hits, "Stygian Burst victims (origin unknown)")
        rows.append(row)
    return rows
