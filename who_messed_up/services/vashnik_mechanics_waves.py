"""Totem lives and Froth exposure, with explicitly limited wave-owner inference.

Totem kill credit is absent from WCL. A timing candidate never becomes logged
kill credit, and a missing removal never becomes a successful clear.
"""
from collections import Counter, defaultdict

from .mechanics_events import ability, cast_times, instance, timestamp
from .mechanics_lifetimes import enemy_lives
from .mechanics_models import MechanicDetail
from .vashnik_mechanics_events import active_at, assignment_groups, hit_details, infusion_context, inside, player_hits
from .vashnik_mechanics_models import FROTH, FROTH_DAMAGE, IMBIBE, MALIGNANCE, PLAGUE_WAVE, TOTEM_SUMMON

TRAVEL_WINDOW_MS = 10000
BOUNDARY_TOLERANCE_MS = 250


def wave_candidates(ctx, at):
    return [life for life in ctx.lives({FROTH})
            if life.removed is not None and life.removed < ctx.fight.end - 1000
            and -BOUNDARY_TOLERANCE_MS <= at - life.removed <= TRAVEL_WINDOW_MS]


def _totem_lives(ctx):
    evidence = defaultdict(list)
    for event in ctx.events("totems"):
        kind = event.get("type")
        side = "target" if kind in {"summon", "death"} else "source"
        if kind in {"summon", "death", "begincast", "cast"} and ctx.names.get(event.get(side + "ID")) == "Malignant Totem":
            evidence[instance(event, side)].append(event)
    return enemy_lives(evidence, ctx.fight.end)


def build_totem_waves(ctx):
    """Every assignment group is visible, even without a release or a totem clear."""
    groups = assignment_groups(ctx, FROTH, 500)
    rows = []
    for index, group in enumerate(groups, 1):
        row = ctx.row(group[0].start, index, f"Wave {index}")
        row.players["carriers"] = sorted(ctx.name(life.player_id) for life in group)
        releases = [life.removed for life in group if life.removed is not None and life.removed < ctx.fight.end - 1000]
        row.values.update(cleared=0, late_clears=0, assigned=len(group), released=len(releases),
                          release=ctx.offset(min(releases)) if releases else "Not observed")
        for life in group:
            released = life.removed is not None and life.removed < ctx.fight.end - 1000
            status, stop = life.status(ctx.events("deaths", friendly=True), ctx.fight.end)
            description = f"Assigned {ctx.offset(life.start)}; "
            description += f"released {ctx.offset(life.removed)} after {(life.removed - life.start) / 1000:.2f}s." if released else "no release observed before pull-end cleanup."
            if status != "Removed alive":
                description += f" {status} at {ctx.offset(stop)}."
            row.details.append(MechanicDetail("Wave carriers", ctx.name(life.player_id), life.start, description))
        rows.append(row)
    for life in _totem_lives(ctx):
        if life.death is None or life.death >= ctx.fight.end - 1000:
            continue
        candidates = wave_candidates(ctx, life.death)
        matched = [i for i, group in enumerate(groups) if any(candidate in group for candidate in candidates)]
        if len(matched) != 1:
            continue
        row = rows[matched[0]]
        failed = any(e.get("type") == "cast" and ability(e) == MALIGNANCE for e in life.events)
        row.values["late_clears" if failed else "cleared"] += 1
    for row in rows:
        row.values["result"] = "Group-associated clears" if row.values["cleared"] else "No associated clears observed"
    return rows


def build_totems(ctx):
    lives = _totem_lives(ctx)
    anchors = cast_times(ctx.events("enemy_casts"), {IMBIBE})
    # Preserve evidence even if the Imbibe cast packet is absent.
    for life in lives:
        if not any(0 <= life.start - at <= 15000 for at in anchors):
            anchors.append(life.start)
    anchors.sort()
    rows = [ctx.row(at, i, f"Totem set {i}") for i, at in enumerate(anchors, 1)]
    for row in rows:
        row.values.update(spawned=0, observed=0, cleared=0, detonated=0, late_clears=0,
                          unresolved=0, inferred=0, group_only=0, unknown=0)
    assigned = defaultdict(list)
    for life in lives:
        index = max(i for i, at in enumerate(anchors) if at <= life.start)
        assigned[index].append(life)
    froth_groups = assignment_groups(ctx, FROTH, 500)
    for index, row in enumerate(rows):
        infusion_context(ctx, row, row.start)
        fountains = set()
        associations = Counter()
        for life in assigned[index]:
            row.values["observed"] += 1
            row.values["spawned"] += int(life.summoned)
            summons = [e for e in life.events if e.get("type") == "summon" and ability(e) == TOTEM_SUMMON]
            fountains.update(ctx.name(e.get("sourceID")).replace(" Tumor Stalker", "") for e in summons)
            casts = [e for e in life.events if e.get("type") == "cast" and ability(e) == MALIGNANCE]
            dead = life.death is not None and life.death < ctx.fight.end - 1000
            status = "Detonated" if casts else "Removed before detonation" if dead else "Unresolved at pull end"
            row.values["detonated" if casts else "cleared" if dead else "unresolved"] += 1
            if casts and dead:
                row.values["late_clears"] += 1
            badges = [status]
            begins = [timestamp(e) for e in life.events if e.get("type") == "begincast"]
            if begins:
                badges.append(f"First cast deadline ~{ctx.offset(min(begins) + 85000)}")
            if casts:
                badges.extend(f"Malignance completed {ctx.offset(timestamp(e))}" for e in casts)
            description = "No death observed before encounter cleanup." if not dead else "Totem death logged; player kill credit is unavailable."
            if dead:
                candidates = wave_candidates(ctx, life.death)
                candidate_ids = {candidate.player_id for candidate in candidates}
                if len(candidates) == 1:
                    carrier = candidates[0]
                    row.values["inferred"] += 1
                    badges.append("Inferred single carrier")
                    description += f" Likely wave: {ctx.name(carrier.player_id)}; released {ctx.offset(carrier.removed)}."
                    if carrier.removed - carrier.start < 5500:
                        description += " Early release; may have occurred on death or removal."
                elif candidates:
                    row.values["group_only"] += 1
                    badges.append("Wave group only")
                    description += " Candidates: " + ", ".join(sorted(ctx.name(player) for player in candidate_ids)) + "."
                else:
                    row.values["unknown"] += 1
                    badges.append("Unknown wave")
                groups = [i for i, group in enumerate(froth_groups)
                          if any(candidate in group for candidate in candidates)]
                if len(groups) == 1:
                    associations[groups[0]] += 1
            row.details.append(MechanicDetail(
                "Totem outcomes", f"Totem {life.key[0]}:{life.key[1] or '?'}", life.death if dead else life.start,
                description, badges, "danger" if casts else "warning" if not dead else None,
            ))
        row.values["fountains"] = ", ".join(sorted(fountains)) or "Not observed"
        # Include zero-clear groups in the set's time window, plus earlier/later
        # waves actually associated with its totems. Full wave view includes all.
        next_set = rows[index + 1].start if index + 1 < len(rows) else ctx.fight.end + 1
        visible = set(associations)
        visible.update(i for i, group in enumerate(froth_groups)
                       if row.start - (TRAVEL_WINDOW_MS if index == 0 else 0) <= group[0].start < next_set)
        wave_details = []
        for wave_index in sorted(visible):
            count = associations[wave_index]
            group = froth_groups[wave_index]
            releases = [life.removed for life in group if life.removed is not None]
            wave_details.append(MechanicDetail(
                "Plague waves", f"Wave {wave_index + 1}: " + ", ".join(sorted(ctx.name(l.player_id) for l in group)),
                min(releases) if releases else group[0].start,
                f"{count} associated totem removals in this set; may include removals after detonation.",
                [],
            ))
        row.details = wave_details + row.details
        row.details.sort(key=lambda detail: detail.timestamp if detail.timestamp is not None else row.start)
    return rows


def build_froth(ctx):
    groups = assignment_groups(ctx, FROTH, 500)
    all_lives = ctx.lives({FROTH})
    rows = []
    for index, group in enumerate(groups):
        start = min(life.start for life in group)
        end = min(life.start for life in groups[index + 1]) if index + 1 < len(groups) else ctx.fight.end + 1
        row = ctx.row(start, index + 1, f"Froth {index + 1}")
        row.players["assigned"] = sorted({ctx.name(life.player_id) for life in group})
        splash = [e for e in inside(player_hits(ctx, {FROTH_DAMAGE}), start, end)
                  if not any(life.player_id == e.get("targetID") and active_at(life, timestamp(e), ctx.fight.end)
                             for life in all_lives)]
        waves = inside(player_hits(ctx, {PLAGUE_WAVE}), start, end)
        row.players["splash_victims"] = sorted({ctx.name(e["targetID"]) for e in splash})
        row.contributions = dict(Counter(ctx.name(e["targetID"]) for e in splash))
        row.values.update(assigned=len(group), splash_hits=len(splash), wave_hits=len(waves), early=0)
        for life in group:
            status, stop = life.status(ctx.events("deaths", friendly=True), ctx.fight.end)
            held = (stop - life.start) / 1000
            early = life.removed is not None and life.removed - life.start < 5500 and life.removed < ctx.fight.end - 1000
            row.values["early"] += int(early)
            row.details.append(MechanicDetail("Assignments", ctx.name(life.player_id), life.start,
                                             f"{status}; observed through {ctx.offset(stop)}.",
                                             [f"Held {held:.2f}s", "Early release" if early else "Assignment"],
                                             "warning" if early else None))
        hit_details(ctx, row, splash, "Unmarked splash victims (cause unknown)")
        hit_details(ctx, row, waves, "Plague Wave hits")
        rows.append(row)
    return rows
