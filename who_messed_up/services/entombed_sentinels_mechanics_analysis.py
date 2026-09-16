"""Pure, cast-anchored calculators for the Mythic Sentinels views.

Each calculator consumes a single pull's streams. Cast rows survive missing
damage, while instance-specific evidence anchors add lifetimes. This keeps
incomplete pulls visible and avoids assigning splash damage as an assignment.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .common import _resolve_event_source_player
from .entombed_sentinels_mechanics_events import (
    ability, aura_lives, cast_times, clusters, damage, instance, timestamp, windows,
)
from .entombed_sentinels_mechanics_models import MechanicDetail, MechanicSet
from .entombed_sentinels_mechanics_resolution import build_dispels, build_intermissions


@dataclass
class PullContext:
    code: str
    fight: object
    pull_index: int
    streams: dict
    names: dict
    owners: dict

    @property
    def players(self):
        return set(self.fight.friendly_player_ids)

    def events(self, stream, ids=None, *, friendly=False):
        return [e for e in self.streams.get(stream, [])
                if (ids is None or ability(e) in ids)
                and (not friendly or e.get("targetID") in self.players)]

    def name(self, actor_id):
        return self.names.get(actor_id, f"Player {actor_id}")

    def row(self, start, index, label):
        return MechanicSet(self.code, self.fight.id, self.pull_index,
                           self.fight.start, start, index, label)

    def offset(self, at):
        seconds = max(0, (at - self.fight.start) / 1000)
        return f"{int(seconds // 60)}:{seconds % 60:05.2f}"

    def lives(self, ids):
        return aura_lives(self.events("debuffs", ids), ids, self.players)


def _names(ctx, events):
    return sorted({ctx.name(e.get("targetID")) for e in events})


def _inside(events, start, end):
    return [e for e in events if start <= timestamp(e) < end]


def _damage_details(ctx, row, events, section):
    for group in clusters(events):
        row.details.append(MechanicDetail(
            section, ", ".join(_names(ctx, group)), timestamp(group[0]),
            f"{len(group)} hit events; {sum(damage(e) for e in group):,.0f} damage taken.",
            tone="warning",
        ))


def _aura_details(ctx, row, lives, *, expiry=None, failures=(), stacks=False):
    deaths = ctx.events("deaths", friendly=True)
    counts = defaultdict(int)
    for life in lives:
        status, stop = life.status(deaths, ctx.fight.end, expiry=expiry)
        failure = any(e.get("targetID") == life.player_id
                      and life.start <= timestamp(e) <= stop + 1000 for e in failures)
        if status == "Died before resolution":
            counts["deaths"] += 1
        if failure:
            counts["failures"] += 1
            if status == "Removed alive":
                status = "Cultivated Burst applied"
        counts[status] += 1
        badges = [status, f"Held {(stop - life.start) / 1000:.2f}s",
                  f"Last observed: {ctx.offset(stop)}"]
        if stacks:
            badges.append(f"Initial stacks: {life.initial_stack if life.initial_stack is not None else 'not logged'}")
            badges.extend(f"{ctx.offset(at)}: {stack} stacks" for at, stack in life.changes)
        if failure and status != "Cultivated Burst applied":
            badges.append("Cultivated Burst applied")
        row.details.append(MechanicDetail(
            "Assignments", ctx.name(life.player_id), life.start,
            "Aura application and observed resolution.",
            badges, "danger" if failure or status == "Died before resolution" else None,
        ))
    row.players["assigned"] = sorted({ctx.name(life.player_id) for life in lives})
    row.values.update(assigned=len(lives), removed=counts["Removed alive"],
                      deaths=counts["deaths"],
                      unresolved=len(lives) - counts["Removed alive"] - counts["deaths"],
                      failures=counts["failures"])


def build_protovenom(ctx):
    starts = cast_times(ctx.events("enemy_casts"), {1296878})
    lives = ctx.lives({1296880})
    # Retain application evidence if a cast packet is missing, without merging
    # the two staggered groups of four into separate waves.
    for group in clusters([{"timestamp": life.start} for life in lives], 2000):
        at = timestamp(group[0])
        if not any(0 <= at - start <= 3000 for start in starts):
            starts.append(at)
    result = []
    for index, (start, end) in enumerate(windows(sorted(starts), ctx.fight.end), 1):
        row = ctx.row(start, index, f"Wave {index}")
        _aura_details(ctx, row, [life for life in lives if start <= life.start < end])
        eruptions = _inside(ctx.events("damage_taken", {1296962}, friendly=True), start, end)
        row.values["eruption_hits"] = len(eruptions)
        _damage_details(ctx, row, eruptions, "Eruption victims (cause unknown)")
        result.append(row)
    return result


def stasis_starts(ctx):
    return cast_times(ctx.events("enemy_casts"), {1284588, 1284606})


def build_helical(ctx):
    starts = stasis_starts(ctx)
    lives = ctx.lives({1284590})
    for group in clusters([{"timestamp": life.start} for life in lives], 2000):
        at = timestamp(group[0])
        if not any(0 <= at - start <= 3000 for start in starts):
            starts.append(at)
    result = []
    for index, (start, end) in enumerate(windows(sorted(starts), ctx.fight.end), 1):
        row = ctx.row(start, index, f"Intermission {index}")
        failures = _inside(ctx.events("debuffs", {1284947}, friendly=True), start, end)
        failures = [e for e in failures if e.get("type") == "applydebuff"]
        _aura_details(ctx, row, [life for life in lives if start <= life.start < end],
                      expiry=28000, failures=failures, stacks=True)
        hits = _inside(ctx.events("damage_taken", {1284941, 1284948}, friendly=True), start, end)
        row.values["burst_damage"] = sum(damage(e) for e in hits)
        _damage_details(ctx, row, hits, "Cultivated Burst damage victims")
        result.append(row)
    return result


def build_miasma(ctx):
    starts = cast_times(ctx.events("enemy_casts"), {1288232})
    lives = ctx.lives({1288260})
    result = []
    for index, (start, next_start) in enumerate(windows(starts, ctx.fight.end), 1):
        row = ctx.row(start, index, f"Miasma {index}")
        assigned = [life for life in lives if start <= life.start < min(next_start, start + 3000)]
        row.players["marked"] = sorted({ctx.name(life.player_id) for life in assigned})
        # The eight-second target aura is the impact clock. Keep the cast even
        # if its target dies, the pull ends, or no impact packet is recorded.
        expected = [life.start + 8000 for life in assigned] or [start + 8500]
        hits = [e for e in ctx.events("damage_taken", {1288282}, friendly=True)
                if start <= timestamp(e) < next_start
                and any(abs(timestamp(e) - at) <= 2000 for at in expected)]
        row.players["soakers"] = _names(ctx, hits)
        impact = min(map(timestamp, hits), default=None)
        hit_players = {e.get("targetID") for e in hits}
        deaths = [e for e in ctx.events("deaths", friendly=True)
                  if impact is not None and impact <= timestamp(e) <= impact + 2000
                  and e.get("targetID") in hit_players]
        row.values.update(soakers=len(hit_players), damage=sum(damage(e) for e in hits),
                          deaths=len(deaths), impact=ctx.offset(impact) if impact is not None else "Not observed")
        for life in assigned:
            row.details.append(MechanicDetail("Marked target", ctx.name(life.player_id), life.start,
                                               "Miasma assignment aura applied."))
        for player in sorted(hit_players, key=ctx.name):
            player_hits = [e for e in hits if e.get("targetID") == player]
            player_deaths = [e for e in deaths if e.get("targetID") == player]
            row.details.append(MechanicDetail(
                "Soakers", ctx.name(player), min(map(timestamp, player_hits)),
                f"{sum(damage(e) for e in player_hits):,.0f} damage taken.",
                [f"Died {ctx.offset(timestamp(e))} within 2s of impact" for e in player_deaths],
                "danger" if player_deaths else None,
            ))
        if not hits:
            row.details.append(MechanicDetail("Impact", "No impact observed", start,
                                               "The completed cast is retained; missing hits do not prove an unsoaked Miasma."))
        result.append(row)
    return result


def build_droplets(ctx):
    starts = cast_times(ctx.events("enemy_casts"), {1284434})
    result = []
    for index, (start, end) in enumerate(windows(starts, ctx.fight.end), 1):
        row = ctx.row(start, index, f"Wave {index}")
        pops = _inside(ctx.events("damage_taken", {1284451}, friendly=True), start, end)
        blasts = _inside(ctx.events("damage_taken", {1284452}, friendly=True), start, end)
        row.players["poppers"] = _names(ctx, pops)
        row.values.update(pops=len(pops), bursts=len(clusters(blasts)), blast_hits=len(blasts),
                          damage=sum(damage(e) for e in blasts))
        for player in sorted({e.get("targetID") for e in pops}, key=ctx.name):
            hits = [e for e in pops if e.get("targetID") == player]
            row.soak_counts[ctx.name(player)] = len(hits)
        _damage_details(ctx, row, blasts, "Noxious Blast bursts (not a missed-droplet count)")
        result.append(row)
    return result


def build_coagulations(ctx):
    summons = cast_times(ctx.events("enemy_casts"), {1284251})
    evidence = defaultdict(list)
    for stream, side, ids in (("add_damage", "target", None), ("enemy_deaths", "target", None),
                              ("enemy_buffs", "source", {1284257}),
                              ("enemy_casts", "source", {1284257}),
                              ("damage_taken", "source", {1284258})):
        for event in ctx.events(stream, ids):
            if stream == "add_damage" and damage(event) <= 1:
                continue
            if ctx.names.get(event.get(side + "ID")) == "Venom Coagulation":
                evidence[instance(event, side)].append(event)
    lives = []
    for key, events in evidence.items():
        deaths = sorted({timestamp(e) for e in events if e.get("type") == "death"})
        killing_hits = [e for e in events if e.get("type") == "damage"
                        and instance(e, "target") == key and float(e.get("overkill") or 0) > 0]
        for group in clusters(killing_hits, 1000):
            at = timestamp(group[0])
            if not any(abs(at - death) <= 1000 for death in deaths):
                deaths.append(at)
        deaths.sort()
        # WCL omits instances on some pulls, reusing the same actor for several
        # adds. A death (or channel ending without a death packet) ends a life.
        stops = sorted(set(deaths + [timestamp(e) for e in events
                                    if e.get("type") == "removebuff" and ability(e) == 1284257
                                    and not any(abs(timestamp(e) - at) <= 1000 for at in deaths)]))
        lower = ctx.fight.start - 1
        for upper in stops + [ctx.fight.end]:
            segment = [e for e in events if lower < timestamp(e) <= upper]
            meaningful = [e for e in segment if e.get("type") != "removebuff"]
            if meaningful:
                lives.append((key, meaningful, lower, upper,
                              next((at for at in deaths if lower < at <= upper), None)))
            lower = upper
    lives.sort(key=lambda item: min(map(timestamp, item[1])))
    result = []
    observed_starts = []
    for key, events, lower, observed_end, death in lives:
        start = min(map(timestamp, events))
        observed_starts.append(start)
        attacks = [e for e in ctx.events("add_damage") if instance(e, "target") == key
                   and e.get("type") == "damage" and damage(e) > 1
                   and lower < timestamp(e) <= observed_end]
        end = death if death is not None else observed_end
        row = ctx.row(start, len(result) + 1, f"Coagulation {len(result) + 1}")
        for event in attacks:
            name, player = _resolve_event_source_player(event, ctx.names, ctx.owners)
            if player in ctx.players:
                row.contributions[name] = row.contributions.get(name, 0) + damage(event)
        hits = [e for e in ctx.events("damage_taken", {1284258}, friendly=True)
                if instance(e, "source") == key and start <= timestamp(e) <= end]
        first = min((timestamp(e) for e in attacks
                     if _resolve_event_source_player(e, ctx.names, ctx.owners)[1] in ctx.players), default=None)
        summon = max((at for at in summons if 0 <= start - at <= 15000), default=None)
        buff_only = all(e.get("type") in ("applybuff", "removebuff", "refreshbuff") for e in events)
        row.players["contributors"] = sorted(row.contributions, key=lambda name: -row.contributions[name])
        row.values.update(duration=None if buff_only else round((end - start) / 1000, 2),
                          delay=round((first - summon) / 1000, 2) if first is not None and summon is not None else None,
                          damage=sum(row.contributions.values()),
                          kills=int(death is not None),
                          contaminate=sum(damage(e) for e in hits),
                          status="Killed" if death is not None else "Unmatched buff signal" if buff_only else "No death observed")
        row.details.append(MechanicDetail(
            "Lifetime", f"Actor {key[0]}, instance {key[1] or 'not logged'}", start,
            "Timing begins with the first instance-specific signal. The true spawn may be earlier.",
            [f"{row.values['status']}: {ctx.offset(end)}", f"{len(clusters(hits))} Contaminate tick groups"],
        ))
        if summon is not None:
            row.details.append(MechanicDetail("Lifetime", "Preceding summon cast", summon,
                                               "First-hit delay is measured from this cast, including spawn travel time."))
        if buff_only:
            row.details.append(MechanicDetail("Lifetime", "Unmatched aura evidence", start,
                                               "This actor has only buff evidence. It may be an attribution discrepancy; an additional add is not confirmed."))
        for name, amount in sorted(row.contributions.items(), key=lambda item: -item[1]):
            first_hit = min(timestamp(e) for e in attacks
                            if _resolve_event_source_player(e, ctx.names, ctx.owners)[0] == name)
            row.details.append(MechanicDetail("Player damage", name, first_hit,
                                               f"{amount:,.0f} effective damage including owned pets.",
                                               [f"First attack +{(first_hit - start) / 1000:.2f}s"]))
        result.append(row)
    # The last summon can precede a wipe with no instance signal at all.
    for start in summons:
        if not any(0 <= observed - start <= 15000 for observed in observed_starts):
            row = ctx.row(start, 0, "Summon")
            row.values.update(duration=None, delay=None, damage=0, contaminate=0,
                              status="No add instance observed")
            row.details.append(MechanicDetail("Lifetime", "Summon cast only", start,
                                               "No instance-specific signal can be matched to this summon."))
            result.append(row)
    result.sort(key=lambda row: row.start)
    for index, row in enumerate(result, 1):
        row.index = index
        row.label = "Unmatched signal" if row.values["status"] == "Unmatched buff signal" else f"Coagulation {index}"
    return result


BUILDERS = {
    "protovenom": build_protovenom,
    "helical-toxins": build_helical,
    "miasma": build_miasma,
    "droplets": build_droplets,
    "coagulations": build_coagulations,
    "dispels": build_dispels,
    "intermission": build_intermissions,
}
