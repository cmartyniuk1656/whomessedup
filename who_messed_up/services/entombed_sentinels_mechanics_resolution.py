"""Dispel attribution and intermission timing from observed aura lifetimes.

Toxin resolution and Stasis healing use separate clocks: the final boss heal
can follow the last toxin removal. Failed/partial windows retain their healing
but do not contribute a successful completion time.
"""
from __future__ import annotations

from .common import _resolve_event_source_player
from .entombed_sentinels_mechanics_events import (
    ability, assignment_starts, damage, match_aura_dispel, timestamp, windows,
)
from .entombed_sentinels_mechanics_models import DispelRecord, MechanicDetail


BLIGHTED_BLOOD = 1284471
HELICAL_TOXINS = 1284590
STASIS = {1284588, 1284606}
STASIS_HEAL = 1284635
BOSSES = {"Blood of Ula'tek", "Breath of Ula'tek"}


def build_dispels(ctx):
    lives = ctx.lives({BLIGHTED_BLOOD})
    # Four applications can arrive almost three seconds apart in this report.
    starts = assignment_starts(ctx.events("enemy_casts"), lives, {1284483}, 5000)
    result = []
    for index, (start, end) in enumerate(windows(starts, ctx.fight.end), 1):
        row = ctx.row(start, index, f"Set {index}")
        assigned = [life for life in lives if start <= life.start < end]
        row.players["assigned"] = sorted({ctx.name(life.player_id) for life in assigned})
        for life in assigned:
            player = ctx.name(life.player_id)
            dispel = match_aura_dispel(life, ctx.events("dispels"), ctx.fight.end)
            if dispel is not None:
                dispeller, _ = _resolve_event_source_player(dispel, ctx.names, ctx.owners)
                at = timestamp(dispel)
                delay = (at - life.start) / 1000
                row.dispels.append(DispelRecord(player, dispeller, at, delay))
                row.dispel_counts[dispeller] = row.dispel_counts.get(dispeller, 0) + 1
                row.details.append(MechanicDetail(
                    "Blighted Blood", player, life.start,
                    f"Dispelled by {dispeller} at {ctx.offset(at)} ({delay:.2f}s after application).",
                    ["Dispelled"],
                ))
            else:
                status, stop = life.status(ctx.events("deaths", friendly=True), ctx.fight.end)
                row.details.append(MechanicDetail(
                    "Blighted Blood", player, life.start, "No dispel event observed.",
                    [status, f"Last observed: {ctx.offset(stop)}"], "warning",
                ))
        row.dispels.sort(key=lambda record: record.timestamp)
        row.values.update(assigned=len(assigned), dispelled=len(row.dispels),
                          not_dispelled=len(assigned) - len(row.dispels))
        result.append(row)
    return result


def _stasis_healing(ctx, row, anchor, next_start):
    """Attribute healing to each boss's aura window, including its removal tick."""
    buffs = ctx.events("enemy_buffs", STASIS)
    heals = [event for event in ctx.events("boss_healing", {STASIS_HEAL})
             if event.get("type") == "heal"
             and ctx.names.get(event.get("targetID")) in BOSSES]
    boss_ids = {event.get("targetID") for event in buffs + heals
                if ctx.names.get(event.get("targetID")) in BOSSES}
    for boss in sorted(boss_ids, key=ctx.name):
        applications = [event for event in buffs if event.get("targetID") == boss
                        and event.get("type") == "applybuff"
                        and anchor - 250 <= timestamp(event) < min(anchor + 3000, next_start)]
        start = min(map(timestamp, applications), default=anchor)
        removals = [event for event in buffs if event.get("targetID") == boss
                    and event.get("type") == "removebuff" and start <= timestamp(event) < next_start]
        stop = min(map(timestamp, removals), default=min(start + 30000, next_start, ctx.fight.end))
        observed_end = bool(removals)
        # Exit packets can be logged just after removebuff (1 ms in fight 24).
        # Keep a small tolerance, bounded by this pull and the next Stasis.
        healing_end = min(stop + (250 if observed_end else 0), ctx.fight.end)
        selected = [event for event in heals
                    if event.get("targetID") == boss and start <= timestamp(event) <= healing_end
                    and timestamp(event) < next_start]
        amount = sum(damage(event) for event in selected)
        row.boss_healing[ctx.name(boss)] = amount
        row.details.append(MechanicDetail(
            "Boss healing", ctx.name(boss), start,
            f"{amount:,.0f} healing through {ctx.offset(stop)}.",
            ["Stasis end observed" if observed_end else "Stasis end not logged"],
        ))
    row.values["healing"] = sum(row.boss_healing.values())


def build_intermissions(ctx):
    lives = ctx.lives({HELICAL_TOXINS})
    starts = assignment_starts(ctx.events("enemy_casts"), lives, STASIS, 3000)
    deaths = ctx.events("deaths", friendly=True)
    failures = [event for event in ctx.events("debuffs", {1284947}, friendly=True)
                if event.get("type") == "applydebuff"]
    result = []
    for anchor, end in windows(starts, ctx.fight.end):
        assigned = [life for life in lives if anchor <= life.start < end]
        if not assigned:
            continue  # The timer begins with toxins, not a cast without assignments.
        start = min(life.start for life in assigned)
        row = ctx.row(start, len(result) + 1, f"Intermission {len(result) + 1}")
        cleared = 0
        failed = False
        for life in assigned:
            status, stop = life.status(deaths, min(ctx.fight.end, end), expiry=28000)
            burst = any(event.get("targetID") == life.player_id
                        and life.start <= timestamp(event) <= min(stop + 1000, end)
                        for event in failures)
            if burst:
                status = "Cultivated Burst applied"
            if status == "Removed alive":
                cleared += 1
            else:
                failed |= burst or status in {"Died before resolution", "Expiry / unresolved"}
            row.details.append(MechanicDetail(
                "Toxin resolution", ctx.name(life.player_id), stop, status,
                [f"Held {(stop - life.start) / 1000:.2f}s"],
                None if status == "Removed alive" else "warning",
            ))
        completed = cleared == len(assigned)
        finish = max(life.removed for life in assigned) if completed else None
        row.values.update(
            status="Cleared" if completed else "Failed" if failed else "Incomplete",
            completed=int(completed), assigned=len(assigned), cleared=cleared,
            resolution=f"{cleared} / {len(assigned)}",
            duration=round((finish - start) / 1000, 3) if finish is not None else None,
            end=ctx.offset(finish) if finish is not None else None,
        )
        _stasis_healing(ctx, row, anchor, end)
        result.append(row)
    return result
