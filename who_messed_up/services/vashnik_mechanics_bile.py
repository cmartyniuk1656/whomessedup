"""Catalytic Bile cast windows and observed participation, without circle claims."""
from collections import Counter

from .mechanics_events import cast_times, clusters, damage
from .vashnik_mechanics_events import hit_details, inside, player_hits
from .vashnik_mechanics_models import BILE, CATALYST, MISSED_BILE


def build_bile(ctx):
    starts = cast_times(ctx.events("enemy_casts"), {CATALYST})
    hits = player_hits(ctx, {BILE, MISSED_BILE})
    if hits and (not starts or min(e["timestamp"] for e in hits) < starts[0]):
        starts.insert(0, min(e["timestamp"] for e in hits))
    rows = []
    for index, start in enumerate(starts, 1):
        end = starts[index] if index < len(starts) else ctx.fight.end + 1
        soaks = inside(player_hits(ctx, {BILE}), start, end)
        misses = inside(player_hits(ctx, {MISSED_BILE}), start, end)
        row = ctx.row(start, index, f"Bile {index}")
        row.soak_counts = dict(Counter(ctx.name(e["targetID"]) for e in soaks))
        row.players["soakers"] = sorted(row.soak_counts)
        row.values.update(soaks=len(soaks), bursts=len(clusters(misses)), miss_hits=len(misses),
                          damage=sum(map(damage, misses)))
        hit_details(ctx, row, soaks, "Soak participation")
        hit_details(ctx, row, misses, "Missed-soak bursts")
        rows.append(row)
    return rows
