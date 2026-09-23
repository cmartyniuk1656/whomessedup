"""Attribute Frost Orb contacts and compare them with observed Rain channels.

Use initial damage impacts rather than debuff applications: immune soakers can
still trigger Frost Burst without gaining a debuff. Never count raid victims as
soakers. Calculations accept recorded streams for deterministic regression tests.
"""
from collections import Counter

from .mechanics_events import ability, timestamp
from .mechanics_models import MechanicDetail
from .nymrissa_mechanics_models import BUFFER_MS, FROST_ORB, RAIN_CHANNEL, RAIN_DAMAGE, RAIN_PULSE_GAP_MS


def _damage_events(ctx):
    return sorted((e for e in ctx.events("damage", {RAIN_DAMAGE, FROST_ORB}, friendly=True)
                   if e.get("type") == "damage"
                   and ctx.fight.start <= timestamp(e) <= ctx.fight.end
                   and e.get("sourceID") not in ctx.players
                   and e.get("sourceID") not in ctx.owners), key=timestamp)


def _rain_windows(ctx, events):
    active, channels = {}, []
    for event in sorted(ctx.events("channels", {RAIN_CHANNEL}), key=timestamp):
        at = timestamp(event)
        target = event.get("targetID")
        if not ctx.fight.start <= at <= ctx.fight.end or target in ctx.players or target in ctx.owners:
            continue
        key = (target, event.get("targetInstance", 0))
        if event.get("type") == "applybuff":
            active[key] = at
        elif event.get("type") == "removebuff":
            start = active.pop(key, None)
            if start is not None and at >= start:
                channels.append((start, at, "channel"))

    # A missing boundary is not permission to extend the window through the DoT.
    # Direct pulse evidence provides an explicitly labeled, conservative fallback.
    windows = []
    for event in events:
        if ability(event) != RAIN_DAMAGE or event.get("tick"):
            continue
        at = timestamp(event)
        if not windows or at - windows[-1][1] > RAIN_PULSE_GAP_MS:
            windows.append([at, at])
        else:
            windows[-1][1] = at
    for start, end in windows:
        # Final direct impacts can arrive just after the buff removal.
        if not any(start <= b + 250 and end >= a - 250 for a, b, _ in channels):
            channels.append((start, end, "pulses"))
    return sorted(channels)


def _window_detail(ctx, start, end, basis):
    return MechanicDetail(
        "Rain timing", "Observed channel" if basis == "channel" else "Direct damage fallback", start,
        f"{ctx.offset(start)} to {ctx.offset(end)}. Lingering damage is excluded. "
        f"Flagging window: {ctx.offset(max(ctx.fight.start, start - BUFFER_MS))} to "
        f"{ctx.offset(min(ctx.fight.end, end + BUFFER_MS))} (one-second buffer)."
        + (" Full channel boundaries are unavailable; only observed direct pulses define this window."
           if basis == "pulses" else ""),
    )


def build_orb_sets(ctx):
    events = _damage_events(ctx)
    windows = _rain_windows(ctx, events)
    rain_rows = []
    for index, (start, end, basis) in enumerate(windows, 1):
        row = ctx.row(start, index, f"Rain {index}")
        row.values = dict(pops=0, during=0, before=0, after=0,
                          duration=(end - start) / 1000, end=ctx.offset(end))
        row.details.append(_window_detail(ctx, start, end, basis))
        rain_rows.append(row)

    orbs, overlaps = [], []
    for event in events:
        if ability(event) != FROST_ORB or event.get("tick"):
            continue
        at = timestamp(event)
        name = ctx.name(event["targetID"])
        # Choose the nearest actual window if two buffered windows touch, so a
        # pop is never counted twice. Prefer being inside real damage over a buffer.
        candidates = [(max(start - at, 0, at - end), i)
                      for i, (start, end, _) in enumerate(windows)
                      if start - BUFFER_MS <= at <= end + BUFFER_MS]
        match = min(candidates)[1] if candidates else None
        row = ctx.row(at, len(orbs) + 1, f"Orb pop {len(orbs) + 1}")
        row.players["soakers"] = [name]
        row.soak_counts = {name: 1}
        row.values = dict(pops=1, flagged=int(match is not None), during=0, before=0, after=0,
                          timing="Outside recorded channel", rain="None observed")
        if match is not None:
            start, end, basis = windows[match]
            phase = "before" if at < start else "after" if at > end else "during"
            label = "Rain channel" if basis == "channel" else "direct Rain pulses"
            timing = {"before": f"{(start - at) / 1000:.2f}s before {label}",
                      "after": f"{(at - end) / 1000:.2f}s after {label}",
                      "during": f"During {label}"}[phase]
            row.values.update(timing=timing, rain=f"Rain {match + 1}", **{phase: 1})
            row.details.append(_window_detail(ctx, start, end, basis))
            rain = rain_rows[match]
            rain.values["pops"] += 1
            rain.values[phase] += 1
            rain.soak_counts[name] = rain.soak_counts.get(name, 0) + 1
            rain.details.append(MechanicDetail("Orb pops", name, at, timing, tone="danger"))
            overlaps.append(row)
        row.details.append(MechanicDetail(
            "Orb impact", name, at,
            "Initial Frost Orb impact; immune and fully absorbed contacts are included.",
            badges=[row.values["timing"]], tone="danger" if match is not None else None,
        ))
        orbs.append(row)
    for rain in rain_rows:
        rain.players["soakers"] = list(dict(Counter(rain.soak_counts).most_common()))
    return dict(overlaps=overlaps, rain=rain_rows, orbs=orbs)
