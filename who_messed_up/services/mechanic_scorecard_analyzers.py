"""Encounter-specific inference rules for mechanic scorecards.

Each analyzer emits only observations that can be supported by combat-log
events. Position- and assignment-dependent mechanics are contribution-only
unless the log exposes a direct failure signal.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, DefaultDict, Dict, Iterable, List, Optional, Sequence, Set

from ..api import Fight
from .common import compute_fight_duration_ms
from .mechanic_scorecard_types import (
    MechanicDefinition,
    MechanicObservation,
    OUTCOME_CONTRIBUTION,
    OUTCOME_MISTAKE,
    OUTCOME_SUCCESS,
)
from .sszorak_tempest import _collapse_tempest_contacts


TEAM_PLAYER = "Raid team"


@dataclass
class FightMechanicContext:
    report_code: str
    fight: Fight
    pull_index: int
    participants: Set[str]
    known_players: Set[str]
    events_by_type: Dict[str, List[dict]]

    def events(self, data_type: str) -> List[dict]:
        return self.events_by_type.get(data_type, [])


MECHANICS_BY_BOSS: Dict[str, Sequence[MechanicDefinition]] = {
    "nek-zali-the-soulcoiler": (
        MechanicDefinition("essence-rend", "Essence Rend Handling", "Target dispel completion and healer dispel contributions.", "Direct event"),
        MechanicDefinition("corpse-disposal", "Corpse Disposal Participation", "Hungering Pyre soaks and Slithering Flame/Cremation assignments used for corpse control.", "Contribution only", optional=True),
        MechanicDefinition("amani-leaks", "Restless Amani Leak Control", "Vessel of Awakening pulses identify adds that reached the Soulcoil Well.", "Direct team failure"),
    ),
    "entombed-sentinels": (
        MechanicDefinition("helical-toxins", "Helical Toxins Pairing", "Clean toxin removals versus personal Cultivated Burst failures.", "Direct event"),
        MechanicDefinition("toxic-droplets", "Toxic Droplet Cleanup", "Optional orb pickups and raid-wide Noxious Blast failures.", "Direct event", optional=True),
        MechanicDefinition("side-swap", "Sentinel Side-Swap Compliance", "Whether each new Mark segment changes between Acid and Blood after intermissions.", "Correlated event"),
        MechanicDefinition("unstable-miasma", "Unstable Miasma Coverage", "Group-soak participation and under-covered impacts.", "Correlated event"),
    ),
    "the-lost-explorers": (
        MechanicDefinition("elemental-cleanse", "Elemental Cleanse", "Burning Flames and Piercing Frost removed before the next volley.", "Direct aura timing"),
        MechanicDefinition("icebound-interrupts", "Icebound Flames Interrupts", "Successful interrupts and completed-cast failures.", "Direct event", optional=True),
        MechanicDefinition("mighty-thud", "Mighty Thud Coverage", "Players participating in each split-damage landing and under-covered marks.", "Direct damage grouping", optional=True),
        MechanicDefinition("crate-cleanup", "Crate Cleanup", "Splinters participation and Relic Rupture failures.", "Contribution/team failure", optional=True),
        MechanicDefinition("blast-wave", "Blast Wave Avoidance", "Direct Blast Wave contacts; players not hit are not inferred when dead or absent.", "Direct failure event"),
    ),
    "vashnik-the-malignant": (
        MechanicDefinition("exploding-infection", "Exploding Infection Dispels", "Successful dispels with safe spacing versus overlapping Caustic Explosions.", "Direct event"),
        MechanicDefinition("catalytic-bile", "Catalytic Bile Coverage", "Optional bile soaks and uncovered impact failures.", "Direct event", optional=True),
        MechanicDefinition("plague-froth", "Plague Froth and Wave Handling", "Direct Plague Wave contacts; proximity ownership remains unassigned without positions.", "Direct failure event"),
        MechanicDefinition("add-control", "Living Venom Add Control", "Add leaks and Burning Venom death spacing.", "Direct team event"),
        MechanicDefinition("siphon-support", "Siphon Blood Support", "Players standing in the required Siphon Blood circle.", "Contribution only", optional=True),
    ),
    "sszorak": (
        MechanicDefinition("mutilate-rotation", "Mutilate Soak Rotation", "Clean first-group soaks, repeat soaks with Mutilated Gash, and soak size.", "Direct event"),
        MechanicDefinition("crosswinds-pairing", "Raging Crosswinds Pairing", "Marked players who produce the expected proximity burst before the aura ends.", "Correlated event"),
        MechanicDefinition("cyst-stewardship", "Viscous Cyst Stewardship", "Venomous Surge assignments and observed cyst activations without judging placement.", "Contribution only", optional=True),
        MechanicDefinition("tempest-dodging", "Tempest Dodging", "Distinct tornado contacts that apply or increase Tempest.", "Direct failure event"),
    ),
    "the-twin-fangs": (
        MechanicDefinition("globule-soaks", "Caustic Globule Management", "Safe intentional soaks versus Globules taken at the lethal venom threshold.", "Direct event", optional=True),
        MechanicDefinition("feast-rotation", "Ravenous Feast Rotation", "Successful venom removals versus repeat soaks while Feasted.", "Direct event"),
        MechanicDefinition("stone-breaker", "Stone Breaker Soaks", "Tank contributions, non-tank contacts, and missed-soak raid failures.", "Direct event", optional=True),
        MechanicDefinition("ichor-placement", "Coiling Ichor Assignments", "Targeted drop assignments without claiming positional quality.", "Contribution only", optional=True),
    ),
    "the-coiled-altar": (
        MechanicDefinition("orb-relocation", "Coalesced Venom Orb Relocation", "Volatile Venom pickups and carry duration; placement correctness is not inferred.", "Direct contribution", optional=True),
        MechanicDefinition("gravebound", "Gravebound Soul Recovery", "Fragment collection, completion time, and lethal expiration failures.", "Direct event"),
        MechanicDefinition("guillotine-soaks", "Guillotine Coverage", "Soak participation and impacts with fewer than five players.", "Direct damage grouping", optional=True),
        MechanicDefinition("wail-interrupts", "Wail of Terror Interrupts", "Successful interrupters and completed casts.", "Direct event", optional=True),
        MechanicDefinition("gloombomb-spread", "Gloombomb Spread", "Clean marked sets versus unmarked players caught by the explosions.", "Correlated event"),
        MechanicDefinition("dreadmarch-rescue", "Dreadmarch Rescue", "Successful mind-control removals and their resolution time; rescuers are not inferred from friendly damage.", "Direct aura timing"),
        MechanicDefinition("fragment-intercepts", "Fragment Containment", "Observed Spirit Erasure containment without assigning an interceptor the log does not identify.", "Contribution only", optional=True),
    ),
    "ula-tek": (
        MechanicDefinition("egg-control", "Egg and Viper Control", "Avoided egg impacts and uncontrolled Blightscale Viper hatches.", "Direct event"),
        MechanicDefinition("hazard-dodging", "Venom Hazard Dodging", "Distinct Caustic Waves, Falling Debris, and Virulent Spit contacts.", "Direct failure event"),
        MechanicDefinition("tank-uptime", "Boss and Tail Tank Uptime", "Raid-wide Mother's Wrath, Rattler Slam, and Unchecked Rage failures.", "Direct team failure", optional=True),
        MechanicDefinition("fang-pacing", "Grasping Fangs Pacing", "Fangs broken in groups of at most two as required on Heroic.", "Direct aura timing"),
        MechanicDefinition("interrupt-control", "Priority Interrupts", "Malice, Anguished Cry, and Vicious Echoes interrupts and completed-cast damage.", "Direct event"),
        MechanicDefinition("bite-rescue", "Serpent's Bite Rescue", "Bitten players freed before becoming a Calcified Corpse.", "Direct aura timing"),
        MechanicDefinition("purge-spread", "Volatile Purge Spread", "Clean purge windows versus directly logged overlapping purge stacks.", "Direct aura stack"),
    ),
}


REQUIRED_DATA_TYPES: Dict[str, Set[str]] = {
    "nek-zali-the-soulcoiler": {"Debuffs", "Dispels", "DamageTaken"},
    "entombed-sentinels": {"Debuffs", "DamageTaken"},
    "the-lost-explorers": {"Debuffs", "Interrupts", "DamageTaken", "Casts"},
    "vashnik-the-malignant": {"Debuffs", "Dispels", "DamageTaken"},
    "sszorak": {"Debuffs", "DamageTaken"},
    "the-twin-fangs": {"Debuffs", "DamageTaken"},
    "the-coiled-altar": {"Debuffs", "Interrupts", "DamageTaken", "Casts"},
    "ula-tek": {"Debuffs", "Interrupts", "DamageTaken"},
}


def analyze_fight(boss_id: str, context: FightMechanicContext) -> List[MechanicObservation]:
    analyzer = ANALYZERS.get(boss_id)
    return analyzer(context) if analyzer else []


def _observation(
    context: FightMechanicContext,
    *,
    mechanic_id: str,
    player: str,
    outcome: str,
    label: str,
    description: str,
    event: Optional[dict] = None,
    timestamp: Optional[float] = None,
    ability_id: Optional[int] = None,
    ability_label: Optional[str] = None,
    target: Optional[str] = None,
    value: Optional[float] = None,
    value_label: Optional[str] = None,
) -> MechanicObservation:
    event_timestamp = timestamp if timestamp is not None else _timestamp(event)
    if event_timestamp is None:
        event_timestamp = float(context.fight.start)
    return MechanicObservation(
        mechanic_id=mechanic_id,
        player=player,
        outcome=outcome,
        label=label,
        description=description,
        fight_id=context.fight.id,
        fight_name=context.fight.name,
        pull_index=context.pull_index,
        timestamp=event_timestamp,
        offset_ms=event_timestamp - float(context.fight.start),
        ability_id=ability_id if ability_id is not None else _ability_id(event),
        ability_label=ability_label,
        target=target,
        value=value,
        value_label=value_label,
        source_report_code=context.report_code,
        pull_duration_ms=compute_fight_duration_ms(context.fight),
    )


def _analyze_nek_zali(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    dispels = context.events("Dispels")
    damage = context.events("DamageTaken")

    applications = _filter(debuffs, ability_ids={1287434}, event_types={"applydebuff"})
    removals = _events_by_target(_filter(debuffs, ability_ids={1287434}, event_types={"removedebuff"}))
    essence_dispels = _events_by_target([event for event in dispels if _extra_ability_id(event) == 1287434])
    for application in applications:
        player = _target(application)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(application) or 0.0
        end_event = _first_after(removals.get(player, []), start, 30_000.0)
        end = _timestamp(end_event) if end_event else start + 30_000.0
        dispel = _first_between(essence_dispels.get(player, []), start, end + 250.0)
        if dispel:
            duration = ((_timestamp(dispel) or start) - start) / 1000.0
            observations.append(_observation(context, mechanic_id="essence-rend", player=player, outcome=OUTCOME_SUCCESS, label="Essence Rend dispelled", description=f"Removed after {duration:.1f}s.", event=dispel, ability_id=1287434, ability_label="Essence Rend", value=duration, value_label="Dispel time"))
            dispeller = _source(dispel)
            if _player_in_scope(context, dispeller):
                observations.append(_observation(context, mechanic_id="essence-rend", player=dispeller, outcome=OUTCOME_CONTRIBUTION, label="Essence Rend dispel", description=f"Dispelled Essence Rend from {player}.", event=dispel, ability_label=_ability_name(dispel) or "Dispel", target=player))
        else:
            observations.append(_observation(context, mechanic_id="essence-rend", player=player, outcome=OUTCOME_MISTAKE, label="Essence Rend not dispelled", description="The aura ended without a matching successful dispel event.", event=end_event or application, ability_id=1287434, ability_label="Essence Rend"))

    for event in _filter(debuffs, ability_ids={1294933, 1289875}, event_types={"applydebuff"}):
        player = _target(event)
        if _player_in_scope(context, player):
            label = "Slithering Flame assignment" if _ability_id(event) == 1294933 else "Cremation assignment"
            observations.append(_observation(context, mechanic_id="corpse-disposal", player=player, outcome=OUTCOME_CONTRIBUTION, label=label, description="Received a corpse-burning assignment; the log cannot prove placement quality.", event=event, ability_label=label.replace(" assignment", "")))
    for event in _filter(damage, ability_ids={1289855}, event_types={"damage"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="corpse-disposal", player=player, outcome=OUTCOME_CONTRIBUTION, label="Hungering Pyre soak", description="Participated in the group soak used to burn nearby corpses.", event=event, ability_label="Hungering Pyre"))

    # Vessel damage pulses every second after an add reaches the well. Collapse
    # the pulse train so one leaked add window is not reported as five failures.
    for group in _group_sequences(_filter(damage, ability_ids={1297630}, event_types={"damage"}), 2_000.0):
        observations.append(_observation(context, mechanic_id="amani-leaks", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Vessel of Awakening active", description="A Restless Amani reached the well and became an empowered Vessel.", event=group[0], ability_label="Vessel of Awakening"))
    return observations


def _analyze_entombed(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    damage = context.events("DamageTaken")
    failures = _events_by_target(_filter(debuffs, ability_ids={1284948}, event_types={"applydebuff"}))
    removals = _events_by_target(_filter(debuffs, ability_ids={1284590}, event_types={"removedebuff"}))
    for event in _filter(debuffs, ability_ids={1284590}, event_types={"applydebuff"}):
        player = _target(event)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(event) or 0.0
        removal = _first_after(removals.get(player, []), start, 45_000.0)
        end = _timestamp(removal) if removal else start + 45_000.0
        failed = _first_between(failures.get(player, []), start, end + 1_000.0)
        outcome = OUTCOME_MISTAKE if failed else OUTCOME_SUCCESS
        observations.append(_observation(context, mechanic_id="helical-toxins", player=player, outcome=outcome, label="Cultivated Burst" if failed else "Clean toxin pairing", description="Triggered Cultivated Burst while resolving Helical Toxins." if failed else "Helical Toxins cleared without a personal Cultivated Burst.", event=failed or removal or event, ability_id=1284590, ability_label="Helical Toxins"))

    for event in _filter(damage, ability_ids={1284451}, event_types={"damage"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="toxic-droplets", player=player, outcome=OUTCOME_CONTRIBUTION, label="Toxic Droplet collected", description="Destroyed a Toxic Droplet before it could erupt.", event=event, ability_label="Toxic Droplets"))
    for group in _group_timestamps(_filter(damage, ability_ids={1284452}, event_types={"damage"}), 250.0):
        observations.append(_observation(context, mechanic_id="toxic-droplets", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Droplet missed", description="At least one Toxic Droplet erupted into Noxious Blast.", event=group[0], ability_label="Noxious Blast"))

    mark_starts: DefaultDict[str, List[dict]] = defaultdict(list)
    for event in _filter(debuffs, ability_ids={1284500, 1284506}, event_types={"applydebuff"}):
        player = _target(event)
        if _player_in_scope(context, player):
            mark_starts[player].append(event)
    for player, events in mark_starts.items():
        ordered = sorted(events, key=_event_sort_key)
        for previous, current in zip(ordered, ordered[1:]):
            swapped = _ability_id(previous) != _ability_id(current)
            observations.append(_observation(context, mechanic_id="side-swap", player=player, outcome=OUTCOME_SUCCESS if swapped else OUTCOME_MISTAKE, label="Side changed" if swapped else "Same side retained", description="The new Mark changed element after the intermission." if swapped else "The player began another Mark segment with the same element.", event=current, ability_label=_ability_name(current) or "Sentinel Mark"))

    miasma_apps = _filter(debuffs, ability_ids={1288260}, event_types={"applydebuff"})
    miasma_damage = _filter(damage, ability_ids={1288282}, event_types={"damage"})
    for app in miasma_apps:
        start = _timestamp(app) or 0.0
        nearest = [event for event in miasma_damage if 5_000.0 <= (_timestamp(event) or 0.0) - start <= 10_000.0]
        if not nearest:
            continue
        impact_time = min((_timestamp(event) or 0.0) for event in nearest)
        group = [event for event in nearest if abs((_timestamp(event) or 0.0) - impact_time) <= 250.0]
        players = {_target(event) for event in group if _player_in_scope(context, _target(event))}
        target = _target(app)
        outcome = OUTCOME_SUCCESS if len(players) >= 5 else OUTCOME_MISTAKE
        if _player_in_scope(context, target):
            observations.append(_observation(context, mechanic_id="unstable-miasma", player=target, outcome=outcome, label="Miasma covered" if outcome == OUTCOME_SUCCESS else "Miasma under-covered", description=f"The impact was shared by {len(players)} player(s).", timestamp=impact_time, ability_id=1288282, ability_label="Unstable Miasma", value=float(len(players)), value_label="Soakers"))
        for player in players:
            observations.append(_observation(context, mechanic_id="unstable-miasma", player=player, outcome=OUTCOME_CONTRIBUTION, label="Miasma soak", description=f"Helped cover {target or 'the marked player'}.", timestamp=impact_time, ability_id=1288282, ability_label="Unstable Miasma", target=target))
    return observations


def _analyze_lost_explorers(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    damage = context.events("DamageTaken")
    interrupts = context.events("Interrupts")
    casts = context.events("Casts")

    elemental_apps = _filter(debuffs, ability_ids={1295928, 1295954}, event_types={"applydebuff"})
    removals = _events_by_target(_filter(debuffs, ability_ids={1295928, 1295954}, event_types={"removedebuff"}), include_ability=True)
    wave_times = [min(_timestamp(event) or 0.0 for event in group) for group in _group_timestamps(elemental_apps, 1_000.0)]
    for app in elemental_apps:
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        ability_id = _ability_id(app)
        removal = _first_after(removals.get((player, ability_id), []), start, 60_000.0)
        next_wave = next((time for time in wave_times if time > start + 1_000.0), None)
        deadline = next_wave if next_wave is not None else min(float(context.fight.end), start + 25_000.0)
        removed_at = _timestamp(removal) if removal else None
        success = removed_at is not None and removed_at < deadline
        duration = ((removed_at or deadline) - start) / 1000.0
        name = "Burning Flames" if ability_id == 1295928 else "Piercing Frost"
        observations.append(_observation(context, mechanic_id="elemental-cleanse", player=player, outcome=OUTCOME_SUCCESS if success else OUTCOME_MISTAKE, label=f"{name} cleared" if success else f"{name} carried too long", description=f"Aura duration {duration:.1f}s; it must be removed before the next volley.", event=removal or app, ability_id=ability_id, ability_label=name, value=duration, value_label="Clear time"))

    for event in interrupts:
        if _extra_ability_id(event) != 1286922:
            continue
        player = _source(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="icebound-interrupts", player=player, outcome=OUTCOME_CONTRIBUTION, label="Icebound Flames interrupted", description="Successfully interrupted Icebound Flames.", event=event, ability_label=_ability_name(event) or "Interrupt", target=_target(event)))
        observations.append(_observation(context, mechanic_id="icebound-interrupts", player=TEAM_PLAYER, outcome=OUTCOME_SUCCESS, label="Cast stopped", description=f"Interrupted by {player or 'an unknown player'}.", event=event, ability_id=1286922, ability_label="Icebound Flames"))
    for event in _filter(debuffs, ability_ids={1286922}, event_types={"applydebuff"}):
        observations.append(_observation(context, mechanic_id="icebound-interrupts", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Icebound Flames completed", description="The interruptible cast completed and applied its debuff.", event=event, ability_label="Icebound Flames"))

    for group in _group_timestamps(_filter(damage, ability_ids={1300237}, event_types={"damage"}), 250.0):
        players = {_target(event) for event in group if _player_in_scope(context, _target(event))}
        outcome = OUTCOME_SUCCESS if len(players) >= 2 else OUTCOME_MISTAKE
        observations.append(_observation(context, mechanic_id="mighty-thud", player=TEAM_PLAYER, outcome=outcome, label="Thud covered" if outcome == OUTCOME_SUCCESS else "Thud under-covered", description=f"The landing hit {len(players)} player(s).", event=group[0], ability_label="Mighty Thud", value=float(len(players)), value_label="Soakers"))
        for player in players:
            observations.append(_observation(context, mechanic_id="mighty-thud", player=player, outcome=OUTCOME_CONTRIBUTION, label="Mighty Thud soak", description="Participated in a marked-player soak.", event=group[0], ability_label="Mighty Thud"))

    for event in _filter(debuffs, ability_ids={1308853}, event_types={"applydebuff", "applydebuffstack"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="crate-cleanup", player=player, outcome=OUTCOME_CONTRIBUTION, label="Crate cleanup", description="Received Splinters while participating in crate cleanup.", event=event, ability_label="Splinters"))
    for group in _group_timestamps(_filter(damage, ability_ids={1310027, 1310028}, event_types={"damage"}), 250.0):
        observations.append(_observation(context, mechanic_id="crate-cleanup", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Relic Rupture", description="A crate was left intact long enough to erupt.", event=group[0], ability_label="Relic Rupture"))

    blast_hits = [event for event in _filter(damage, ability_ids={1305844}, event_types={"damage"}) if not event.get("tick")]
    for event in blast_hits:
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="blast-wave", player=player, outcome=OUTCOME_MISTAKE, label="Blast Wave contact", description="Was struck by the expanding Blast Wave.", event=event, ability_label="Blast Wave"))
    del casts
    return observations


def _analyze_vashnik(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    dispels = sorted([event for event in context.events("Dispels") if _extra_ability_id(event) == 1295173], key=_event_sort_key)
    damage = context.events("DamageTaken")
    removals = _events_by_target(_filter(debuffs, ability_ids={1295173}, event_types={"removedebuff"}))
    dispels_by_target = _events_by_target(dispels)
    for app in _filter(debuffs, ability_ids={1295173}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        removal = _first_after(removals.get(player, []), start, 30_000.0)
        end = _timestamp(removal) if removal else start + 30_000.0
        dispel = _first_between(dispels_by_target.get(player, []), start, end + 250.0)
        if not dispel:
            observations.append(_observation(context, mechanic_id="exploding-infection", player=player, outcome=OUTCOME_MISTAKE, label="Infection not dispelled", description="Exploding Infection ended without a matching successful dispel.", event=removal or app, ability_label="Exploding Infection"))
            continue
        index = dispels.index(dispel)
        timestamp = _timestamp(dispel) or start
        adjacent = []
        if index:
            adjacent.append(timestamp - (_timestamp(dispels[index - 1]) or timestamp))
        if index + 1 < len(dispels):
            adjacent.append((_timestamp(dispels[index + 1]) or timestamp) - timestamp)
        minimum_gap = min(adjacent) if adjacent else 999_999.0
        safe = minimum_gap >= 5_000.0
        outcome = OUTCOME_SUCCESS if safe else OUTCOME_MISTAKE
        gap_seconds = minimum_gap / 1000.0 if minimum_gap < 999_999.0 else None
        description = "Safely spaced from adjacent Caustic Explosions." if safe else f"Only {gap_seconds:.1f}s from an adjacent dispel."
        observations.append(_observation(context, mechanic_id="exploding-infection", player=player, outcome=outcome, label="Safe infection dispel" if safe else "Overlapping infection dispel", description=description, event=dispel, ability_label="Exploding Infection", value=gap_seconds, value_label="Nearest gap"))
        dispeller = _source(dispel)
        if _player_in_scope(context, dispeller):
            observations.append(_observation(context, mechanic_id="exploding-infection", player=dispeller, outcome=outcome, label="Safely timed dispel" if safe else "Unsafe dispel timing", description=f"Dispelled {player}. {description}", event=dispel, ability_label=_ability_name(dispel) or "Dispel", target=player, value=gap_seconds, value_label="Nearest gap"))

    for event in _filter(damage, ability_ids={1282602}, event_types={"damage"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="catalytic-bile", player=player, outcome=OUTCOME_CONTRIBUTION, label="Catalytic Bile covered", description="Covered a bile impact before it could hit the raid.", event=event, ability_label="Catalytic Bile"))
    for group in _group_timestamps(_filter(damage, ability_ids={1282616}, event_types={"damage"}), 250.0):
        observations.append(_observation(context, mechanic_id="catalytic-bile", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Bile uncovered", description="A Catalytic Bile landed without a nearby player.", event=group[0], ability_label="Catalytic Bile"))

    for event in _filter(damage, ability_ids={1295798}, event_types={"damage"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="plague-froth", player=player, outcome=OUTCOME_MISTAKE, label="Plague Wave contact", description="Was struck by a cardinal Plague Wave.", event=event, ability_label="Plague Wave"))

    leaks = _group_timestamps(_filter(damage, ability_ids={1280189}, event_types={"damage"}), 250.0)
    for group in leaks:
        observations.append(_observation(context, mechanic_id="add-control", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Living Venom leaked", description="A Living Venom reached the central cavity.", event=group[0], ability_label="Malignant Burst"))
    # Caustic Surge is itself a short one-second pulse train. Compare distinct
    # trains rather than treating the ticks inside one train as overlapping adds.
    surge_groups = _group_sequences(_filter(damage, ability_ids={1285979}, event_types={"damage"}), 2_000.0)
    for index, group in enumerate(surge_groups):
        if index == 0:
            continue
        previous_end = _timestamp(surge_groups[index - 1][-1]) or 0.0
        gap = ((_timestamp(group[0]) or 0.0) - previous_end) / 1000.0
        safe = gap >= 5.0
        observations.append(_observation(context, mechanic_id="add-control", player=TEAM_PLAYER, outcome=OUTCOME_SUCCESS if safe else OUTCOME_MISTAKE, label="Burning Venom staggered" if safe else "Burning Venoms overlapped", description=f"Caustic Surge events were {gap:.1f}s apart.", event=group[0], ability_label="Caustic Surge", value=gap, value_label="Death spacing"))

    for event in _filter(damage, ability_ids={1295229}, event_types={"damage"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="siphon-support", player=player, outcome=OUTCOME_CONTRIBUTION, label="Siphon Blood support", description="Stood within Siphon Blood to help the infected player overcome the healing block.", event=event, ability_label="Siphon Blood"))
    return observations


def _analyze_sszorak(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    damage = context.events("DamageTaken")
    gash_windows = _aura_windows(debuffs, 1277051)
    for group in _group_timestamps(_filter(damage, ability_ids={1285999}, event_types={"damage"}), 100.0):
        players = {_target(event) for event in group if _player_in_scope(context, _target(event))}
        timestamp = _timestamp(group[0]) or 0.0
        for player in players:
            repeated = _window_active(gash_windows.get(player, []), timestamp, minimum_age_ms=100.0)
            observations.append(_observation(context, mechanic_id="mutilate-rotation", player=player, outcome=OUTCOME_MISTAKE if repeated else OUTCOME_SUCCESS, label="Repeat Mutilate soak" if repeated else "Clean Mutilate soak", description="Soaked while Mutilated Gash was already active." if repeated else "Participated without a pre-existing Mutilated Gash.", event=group[0], ability_label="Mutilate"))
        enough = len(players) >= 5
        observations.append(_observation(context, mechanic_id="mutilate-rotation", player=TEAM_PLAYER, outcome=OUTCOME_SUCCESS if enough else OUTCOME_MISTAKE, label="Soak covered" if enough else "Mutilate under-soaked", description=f"The frontal hit {len(players)} player(s).", event=group[0], ability_label="Mutilate", value=float(len(players)), value_label="Soakers"))

    crosswind_damage = _events_by_target(_filter(damage, ability_ids={1285616}, event_types={"damage"}))
    crosswind_removals = _events_by_target(_filter(debuffs, ability_ids={1285453}, event_types={"removedebuff"}))
    for app in _filter(debuffs, ability_ids={1285453}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        removal = _first_after(crosswind_removals.get(player, []), start, 15_000.0)
        end = _timestamp(removal) if removal else start + 15_000.0
        collision = _first_between(crosswind_damage.get(player, []), start, end + 500.0)
        success = collision is not None
        observations.append(_observation(context, mechanic_id="crosswinds-pairing", player=player, outcome=OUTCOME_SUCCESS if success else OUTCOME_MISTAKE, label="Crosswinds paired" if success else "No collision detected", description="Produced the expected Raging Crosswinds proximity burst." if success else "The marked window ended without a matching collision burst on the player.", event=collision or removal or app, ability_label="Raging Crosswinds"))

    for app in _filter(debuffs, ability_ids={1305963}, event_types={"applydebuff"}):
        player = _target(app)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="cyst-stewardship", player=player, outcome=OUTCOME_CONTRIBUTION, label="Venomous Surge assignment", description="Received and completed a cyst-placement assignment; exact placement is not inferred.", event=app, ability_label="Venomous Surge"))
    cyst_groups = _group_timestamps(_filter(debuffs, ability_ids={1287205}, event_types={"applydebuff"}), 250.0)
    for group in cyst_groups:
        observations.append(_observation(context, mechanic_id="cyst-stewardship", player=TEAM_PLAYER, outcome=OUTCOME_CONTRIBUTION, label="Viscous Cyst activated", description="A cyst activation was observed; ownership and placement quality are not assigned.", event=group[0], ability_label="Viscous Cyst"))

    for event in _collapse_tempest_contacts(debuffs):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="tempest-dodging", player=player, outcome=OUTCOME_MISTAKE, label="Tempest contact", description="Contacted a tornado and received or increased Tempest.", event=event, ability_label="Tempest"))
    return observations


def _analyze_twin_fangs(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    damage = context.events("DamageTaken")
    venom_apps = _events_by_target(_filter(debuffs, ability_ids={1290336}, event_types={"applydebuff", "applydebuffstack"}))
    for event in _filter(damage, ability_ids={1289201}, event_types={"damage"}):
        player = _target(event)
        if not _player_in_scope(context, player):
            continue
        timestamp = _timestamp(event) or 0.0
        application = _nearest_event(venom_apps.get(player, []), timestamp, 250.0)
        stack = _stack(application) if application else None
        lethal = stack is not None and stack >= 10
        observations.append(_observation(context, mechanic_id="globule-soaks", player=player, outcome=OUTCOME_MISTAKE if lethal else OUTCOME_SUCCESS, label="Lethal Globule soak" if lethal else "Safe Globule soak", description=f"The intentional soak raised Eternal Venom to {stack} stack(s)." if stack else "Completed an intentional Caustic Globule soak.", event=event, ability_label="Caustic Globule", value=float(stack) if stack else None, value_label="Resulting stack"))
    for group in _group_timestamps(_filter(damage, ability_ids={1290338}, event_types={"damage"}), 250.0):
        observations.append(_observation(context, mechanic_id="globule-soaks", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Globule unsoaked", description="A Caustic Globule ruptured and applied venom to the raid.", event=group[0], ability_label="Caustic Globule"))

    feasted_windows = _aura_windows(debuffs, 1310096)
    for event in _filter(damage, ability_ids={1290662}, event_types={"damage"}):
        player = _target(event)
        if not _player_in_scope(context, player):
            continue
        timestamp = _timestamp(event) or 0.0
        repeated = _window_active(feasted_windows.get(player, []), timestamp, minimum_age_ms=100.0)
        observations.append(_observation(context, mechanic_id="feast-rotation", player=player, outcome=OUTCOME_MISTAKE if repeated else OUTCOME_SUCCESS, label="Repeated Feast soak" if repeated else "Clean Feast soak", description="Soaked Ravenous Feast while Feasted was already active." if repeated else "Participated in the Feast and removed an Eternal Venom stack.", event=event, ability_label="Ravenous Feast"))

    for event in _filter(damage, ability_ids={1310371}, event_types={"damage"}):
        player = _target(event)
        if not _player_in_scope(context, player):
            continue
        # Role-aware scoring happens in the entry builder; here every direct hit is visible.
        observations.append(_observation(context, mechanic_id="stone-breaker", player=player, outcome=OUTCOME_CONTRIBUTION, label="Stone Breaker soak", description="Was struck by the assigned Stone Breaker impact.", event=event, ability_label="Stone Breaker"))
    for group in _group_timestamps(_filter(damage, ability_ids={1289153}, event_types={"damage"}), 250.0):
        observations.append(_observation(context, mechanic_id="stone-breaker", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Stone Breaker missed", description="No tank covered the Stone Breaker impact.", event=group[0], ability_label="Stone Breaker"))

    for event in _filter(debuffs, ability_ids={1290814}, event_types={"applydebuff"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="ichor-placement", player=player, outcome=OUTCOME_CONTRIBUTION, label="Coiling Ichor assignment", description="Received an Ichor drop assignment; edge placement is not inferred without position data.", event=event, ability_label="Coiling Ichor"))
    return observations


def _analyze_coiled_altar(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    damage = context.events("DamageTaken")
    interrupts = context.events("Interrupts")
    casts = context.events("Casts")

    volatile_removals = _events_by_target(_filter(debuffs, ability_ids={1282419}, event_types={"removedebuff"}))
    for app in _filter(debuffs, ability_ids={1282419}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        removal = _first_after(volatile_removals.get(player, []), start, 30_000.0)
        duration = (((_timestamp(removal) or start) - start) / 1000.0) if removal else None
        description = f"Carried Volatile Venom for {duration:.1f}s; pickup is credited but final placement is not inferred." if duration is not None else "Picked up Coalesced Venom; final placement is not inferred."
        observations.append(_observation(context, mechanic_id="orb-relocation", player=player, outcome=OUTCOME_CONTRIBUTION, label="Venom orb carried", description=description, event=app, ability_label="Volatile Venom", value=duration, value_label="Carry time"))

    grave_removals = _events_by_target(_filter(debuffs, ability_ids={1286837}, event_types={"removedebuff"}))
    grave_stacks = _events_by_target(_filter(debuffs, ability_ids={1286837}, event_types={"removedebuffstack"}))
    grave_failures = _events_by_target(_filter(damage, ability_ids={1297906}, event_types={"damage"}))
    for app in _filter(debuffs, ability_ids={1286837}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        removal = _first_after(grave_removals.get(player, []), start, 20_000.0)
        end = _timestamp(removal) if removal else start + 20_000.0
        failed = _first_between(grave_failures.get(player, []), start, end + 500.0)
        fragments = [event for event in grave_stacks.get(player, []) if start <= (_timestamp(event) or 0.0) <= end]
        duration = (end - start) / 1000.0
        observations.append(_observation(context, mechanic_id="gravebound", player=player, outcome=OUTCOME_MISTAKE if failed else OUTCOME_SUCCESS, label="Gravebound expired" if failed else "Soul recovered", description=f"Recovered {len(fragments)} logged fragment stack(s) in {duration:.1f}s." if not failed else "Failed to recover every Soul Fragment before Gravebound expired.", event=failed or removal or app, ability_label="Gravebound", value=duration, value_label="Recovery time"))
        for fragment in fragments:
            observations.append(_observation(context, mechanic_id="gravebound", player=player, outcome=OUTCOME_CONTRIBUTION, label="Soul Fragment recovered", description="Recovered one Gravebound fragment stack.", event=fragment, ability_label="Gravebound"))

    for ability_id, label in ((1283594, "Guillotine"), (1299296, "Grim Guillotine")):
        for group in _group_timestamps(_filter(damage, ability_ids={ability_id}, event_types={"damage"}), 250.0):
            players = {_target(event) for event in group if _player_in_scope(context, _target(event))}
            enough = len(players) >= 5
            observations.append(_observation(context, mechanic_id="guillotine-soaks", player=TEAM_PLAYER, outcome=OUTCOME_SUCCESS if enough else OUTCOME_MISTAKE, label="Guillotine covered" if enough else "Guillotine under-soaked", description=f"{label} hit {len(players)} player(s).", event=group[0], ability_label=label, value=float(len(players)), value_label="Soakers"))
            for player in players:
                observations.append(_observation(context, mechanic_id="guillotine-soaks", player=player, outcome=OUTCOME_CONTRIBUTION, label=f"{label} soak", description="Participated in the required group soak.", event=group[0], ability_label=label))

    wail_interrupts = [event for event in interrupts if _extra_ability_id(event) == 1286399]
    for event in wail_interrupts:
        player = _source(event)
        if _player_in_scope(context, player):
            observations.append(_observation(context, mechanic_id="wail-interrupts", player=player, outcome=OUTCOME_CONTRIBUTION, label="Wail of Terror interrupted", description="Successfully stopped Wail of Terror.", event=event, ability_label=_ability_name(event) or "Interrupt", target=_target(event)))
        observations.append(_observation(context, mechanic_id="wail-interrupts", player=TEAM_PLAYER, outcome=OUTCOME_SUCCESS, label="Wail stopped", description=f"Interrupted by {player or 'an unknown player'}.", event=event, ability_id=1286399, ability_label="Wail of Terror"))
    for event in _filter(casts, ability_ids={1286399}, event_types={"cast"}):
        if not _nearest_event(wail_interrupts, _timestamp(event) or 0.0, 1_000.0):
            observations.append(_observation(context, mechanic_id="wail-interrupts", player=TEAM_PLAYER, outcome=OUTCOME_MISTAKE, label="Wail completed", description="Wail of Terror completed without a matching interrupt.", event=event, ability_label="Wail of Terror"))

    gloombomb_removes = _filter(debuffs, ability_ids={1310881}, event_types={"removedebuff"})
    gloombomb_damage = _filter(damage, ability_ids={1310883}, event_types={"damage"})
    # Multiple marked players detonate together, so their own damage cannot be
    # mapped to one bomb. Only victims outside the entire marked set are proven
    # collateral; when that occurs it is a team outcome, not individual blame.
    for marked_group in _group_timestamps(gloombomb_removes, 5_000.0):
        marked = {
            _target(event)
            for event in marked_group
            if _player_in_scope(context, _target(event))
        }
        if not marked:
            continue
        timestamps = [(_timestamp(event) or 0.0) for event in marked_group]
        start, end = min(timestamps), max(timestamps)
        victims = {
            _target(event)
            for event in gloombomb_damage
            if start - 250.0 <= (_timestamp(event) or 0.0) <= end + 250.0
            and _player_in_scope(context, _target(event))
        }
        collateral = victims - marked
        for event in marked_group:
            player = _target(event)
            if player not in marked:
                continue
            observations.append(
                _observation(
                    context,
                    mechanic_id="gloombomb-spread",
                    player=player,
                    outcome=OUTCOME_SUCCESS if not collateral else OUTCOME_CONTRIBUTION,
                    label="Clean Gloombomb set" if not collateral else "Gloombomb assignment",
                    description="No unmarked players were caught." if not collateral else "An unmarked player was caught, but simultaneous bombs prevent individual blame.",
                    event=event,
                    ability_id=1310883,
                    ability_label="Gloombomb",
                )
            )
        if collateral:
            observations.append(
                _observation(
                    context,
                    mechanic_id="gloombomb-spread",
                    player=TEAM_PLAYER,
                    outcome=OUTCOME_MISTAKE,
                    label="Unmarked Gloombomb collateral",
                    description=f"Caught {len(collateral)} unmarked player(s): {', '.join(sorted(collateral))}.",
                    event=marked_group[0],
                    ability_id=1310883,
                    ability_label="Gloombomb",
                    value=float(len(collateral)),
                    value_label="Unmarked players",
                )
            )

    dread_removals = _events_by_target(_filter(debuffs, ability_ids={1297445}, event_types={"removedebuff"}))
    for app in _filter(debuffs, ability_ids={1297445}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        removal = _first_after(dread_removals.get(player, []), start, 15_000.0)
        duration = (((_timestamp(removal) or start + 15_000.0) - start) / 1000.0)
        # Auras still active when a successful pull ends are encounter cleanup,
        # not failed rescues.
        if removal is None and context.fight.kill:
            continue
        success = removal is not None
        observations.append(_observation(context, mechanic_id="dreadmarch-rescue", player=player, outcome=OUTCOME_SUCCESS if success else OUTCOME_MISTAKE, label="Dreadmarch broken" if success else "Dreadmarch not broken", description=f"Mind control lasted {duration:.1f}s; friendly-damage contributors are not inferred.", event=removal or app, ability_label="Dreadmarch", value=duration, value_label="Break time"))

    intercept_groups = _group_timestamps(_filter(damage, ability_ids={1287722}, event_types={"damage"}), 250.0)
    for group in intercept_groups:
        observations.append(_observation(context, mechanic_id="fragment-intercepts", player=TEAM_PLAYER, outcome=OUTCOME_CONTRIBUTION, label="Spirit Erasure contained", description="Observed containment damage from a Fragment of Malacrass; the interceptor is not identified by the raid-wide event.", event=group[0], ability_label="Spirit Erasure"))
    return observations


def _analyze_ula_tek(context: FightMechanicContext) -> List[MechanicObservation]:
    observations: List[MechanicObservation] = []
    debuffs = context.events("Debuffs")
    damage = context.events("DamageTaken")
    interrupts = context.events("Interrupts")

    # An uncontrolled Viper hatch applies Putrid Membrane to the entire raid at
    # once. Collapse the raid-wide applications into one directly observed team
    # failure rather than blaming every victim.
    membrane_apps = _filter(debuffs, ability_ids={1301268}, event_types={"applydebuff"})
    for group in _group_timestamps(membrane_apps, 250.0):
        observations.append(_observation(
            context,
            mechanic_id="egg-control",
            player=TEAM_PLAYER,
            outcome=OUTCOME_MISTAKE,
            label="Blightscale Viper hatched",
            description="An egg contacted venom or completed gestation and applied Putrid Membrane to the raid.",
            event=group[0],
            ability_id=1308275,
            ability_label="Putrid Membrane",
        ))
    for event in _filter(damage, ability_ids={1290409}, event_types={"damage"}):
        player = _target(event)
        if _player_in_scope(context, player):
            observations.append(_observation(
                context,
                mechanic_id="egg-control",
                player=player,
                outcome=OUTCOME_MISTAKE,
                label="Egg impact",
                description="Was within four yards when a Blightscale Clutch landed.",
                event=event,
                ability_label="Blightscale Clutch",
            ))

    hazard_labels = {
        1292403: "Caustic Waves",
        1286885: "Falling Debris",
        1302982: "Virulent Spit",
    }
    for ability_id, ability_label in hazard_labels.items():
        by_player = _events_by_target(_filter(damage, ability_ids={ability_id}, event_types={"damage"}))
        for player, events in by_player.items():
            if not _player_in_scope(context, player):
                continue
            # Periodic effects become one contact until their tick stream has
            # been quiet for long enough to prove a separate mistake.
            for sequence in _group_sequences(events, 2_500.0):
                observations.append(_observation(
                    context,
                    mechanic_id="hazard-dodging",
                    player=player,
                    outcome=OUTCOME_MISTAKE,
                    label=f"{ability_label} contact",
                    description=f"Took {len(sequence)} logged {ability_label} hit(s) in one contact window.",
                    event=sequence[0],
                    ability_label=ability_label,
                    value=float(len(sequence)),
                    value_label="Hits",
                ))

    uptime_labels = {
        1301122: "Mother's Wrath",
        1299206: "Rattler Slam",
        1301007: "Unchecked Rage",
    }
    for ability_id, ability_label in uptime_labels.items():
        for group in _group_timestamps(
            _filter(damage, ability_ids={ability_id}, event_types={"damage"}),
            250.0,
        ):
            observations.append(_observation(
                context,
                mechanic_id="tank-uptime",
                player=TEAM_PLAYER,
                outcome=OUTCOME_MISTAKE,
                label=f"{ability_label} triggered",
                description="The boss or tail had no valid melee target and punished the raid.",
                event=group[0],
                ability_label=ability_label,
            ))

    fang_removals = _filter(debuffs, ability_ids={1311611}, event_types={"removedebuff"})
    for group in _group_timestamps(fang_removals, 750.0):
        players = sorted({
            player for player in (_target(event) for event in group)
            if _player_in_scope(context, player)
        })
        if not players:
            continue
        safe = len(players) <= 2
        for player in players:
            observations.append(_observation(
                context,
                mechanic_id="fang-pacing",
                player=player,
                outcome=OUTCOME_SUCCESS if safe else OUTCOME_MISTAKE,
                label="Controlled Fangs break" if safe else "Too many Fangs broken",
                description=f"{len(players)} Grasping Fangs tether(s) broke together; Heroic strategy allows at most two.",
                event=group[0],
                ability_label="Grasping Fangs",
                value=float(len(players)),
                value_label="Simultaneous breaks",
            ))

    interrupt_labels = {
        1290779: "Malice",
        1305650: "Anguished Cry",
        1310764: "Vicious Echoes",
    }
    successful_interrupts = [
        event for event in interrupts if _extra_ability_id(event) in interrupt_labels
    ]
    for event in successful_interrupts:
        ability_id = _extra_ability_id(event)
        ability_label = interrupt_labels[ability_id]
        player = _source(event)
        if _player_in_scope(context, player):
            observations.append(_observation(
                context,
                mechanic_id="interrupt-control",
                player=player,
                outcome=OUTCOME_CONTRIBUTION,
                label=f"{ability_label} interrupted",
                description=f"Successfully stopped {ability_label}.",
                event=event,
                ability_id=ability_id,
                ability_label=ability_label,
                target=_target(event),
            ))
        observations.append(_observation(
            context,
            mechanic_id="interrupt-control",
            player=TEAM_PLAYER,
            outcome=OUTCOME_SUCCESS,
            label=f"{ability_label} stopped",
            description=f"Interrupted by {player or 'an unknown player'}.",
            event=event,
            ability_id=ability_id,
            ability_label=ability_label,
        ))
    for ability_id, ability_label in interrupt_labels.items():
        for group in _group_timestamps(
            _filter(damage, ability_ids={ability_id}, event_types={"damage"}),
            250.0,
        ):
            observations.append(_observation(
                context,
                mechanic_id="interrupt-control",
                player=TEAM_PLAYER,
                outcome=OUTCOME_MISTAKE,
                label=f"{ability_label} completed",
                description=f"{ability_label} dealt raid damage after not being interrupted.",
                event=group[0],
                ability_label=ability_label,
            ))

    calcified_by_target = _events_by_target(
        _filter(debuffs, ability_ids={1306119}, event_types={"applydebuff"})
    )
    bite_removals = _events_by_target(
        _filter(debuffs, ability_ids={1288879}, event_types={"removedebuff"})
    )
    for app in _filter(debuffs, ability_ids={1288879}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        failure = _first_after(calcified_by_target.get(player, []), start, 16_000.0)
        removal = _first_after(bite_removals.get(player, []), start, 16_000.0)
        # A wipe can end the log before the Bite resolves, which is not enough
        # evidence to label the assigned player a failure.
        if failure is None and removal is None:
            continue
        success = failure is None
        end = _timestamp(failure or removal) or start
        duration = (end - start) / 1000.0
        observations.append(_observation(
            context,
            mechanic_id="bite-rescue",
            player=player,
            outcome=OUTCOME_SUCCESS if success else OUTCOME_MISTAKE,
            label="Bite fully leeched" if success else "Became Calcified Corpse",
            description=(
                f"Serpent's Bite was removed after {duration:.1f}s."
                if success else f"Serpent's Bite was not fully leeched within {duration:.1f}s."
            ),
            event=failure or removal or app,
            ability_label="Serpent's Bite",
            value=duration,
            value_label="Resolution time",
        ))

    purge_stacks = _events_by_target(
        _filter(debuffs, ability_ids={1316356}, event_types={"applydebuffstack"})
    )
    for app in _filter(debuffs, ability_ids={1316356}, event_types={"applydebuff"}):
        player = _target(app)
        if not _player_in_scope(context, player):
            continue
        start = _timestamp(app) or 0.0
        overlaps = [
            event for event in purge_stacks.get(player, [])
            if start <= (_timestamp(event) or 0.0) <= start + 18_500.0
        ]
        clean = not overlaps
        maximum_stack = max((_stack(event) or 1 for event in overlaps), default=1)
        observations.append(_observation(
            context,
            mechanic_id="purge-spread",
            player=player,
            outcome=OUTCOME_SUCCESS if clean else OUTCOME_MISTAKE,
            label="Clean Purge spread" if clean else "Overlapping Volatile Purge",
            description=(
                "No overlapping purge stack was logged during the debuff window."
                if clean else f"Volatile Purge reached {maximum_stack} stacks from nearby players."
            ),
            event=overlaps[0] if overlaps else app,
            ability_label="Volatile Purge",
            value=float(maximum_stack),
            value_label="Maximum stacks",
        ))
    return observations


ANALYZERS: Dict[str, Callable[[FightMechanicContext], List[MechanicObservation]]] = {
    "nek-zali-the-soulcoiler": _analyze_nek_zali,
    "entombed-sentinels": _analyze_entombed,
    "the-lost-explorers": _analyze_lost_explorers,
    "vashnik-the-malignant": _analyze_vashnik,
    "sszorak": _analyze_sszorak,
    "the-twin-fangs": _analyze_twin_fangs,
    "the-coiled-altar": _analyze_coiled_altar,
    "ula-tek": _analyze_ula_tek,
}


def _filter(events: Iterable[dict], *, ability_ids: Set[int], event_types: Set[str]) -> List[dict]:
    return [event for event in events if _ability_id(event) in ability_ids and str(event.get("type") or "").lower() in event_types]


def _events_by_target(events: Iterable[dict], *, include_ability: bool = False):
    grouped: DefaultDict[object, List[dict]] = defaultdict(list)
    for event in events:
        key: object = (_target(event), _ability_id(event)) if include_ability else _target(event)
        if key is not None:
            grouped[key].append(event)
    for values in grouped.values():
        values.sort(key=_event_sort_key)
    return grouped


def _group_timestamps(events: Iterable[dict], window_ms: float) -> List[List[dict]]:
    groups: List[List[dict]] = []
    for event in sorted(events, key=_event_sort_key):
        timestamp = _timestamp(event)
        if timestamp is None:
            continue
        if not groups or timestamp - (_timestamp(groups[-1][0]) or 0.0) > window_ms:
            groups.append([event])
        else:
            groups[-1].append(event)
    return groups


def _group_sequences(events: Iterable[dict], maximum_gap_ms: float) -> List[List[dict]]:
    """Group periodic event trains by the gap from the preceding event."""
    groups: List[List[dict]] = []
    for event in sorted(events, key=_event_sort_key):
        timestamp = _timestamp(event)
        if timestamp is None:
            continue
        previous = _timestamp(groups[-1][-1]) if groups else None
        if previous is None or timestamp - previous > maximum_gap_ms:
            groups.append([event])
        else:
            groups[-1].append(event)
    return groups


def _first_after(events: Iterable[dict], start: float, max_delay_ms: float) -> Optional[dict]:
    return next((event for event in sorted(events, key=_event_sort_key) if 0.0 <= (_timestamp(event) or 0.0) - start <= max_delay_ms), None)


def _first_between(events: Iterable[dict], start: float, end: float) -> Optional[dict]:
    return next((event for event in sorted(events, key=_event_sort_key) if start <= (_timestamp(event) or 0.0) <= end), None)


def _nearest_event(events: Iterable[dict], timestamp: float, window_ms: float) -> Optional[dict]:
    candidates = [event for event in events if abs((_timestamp(event) or 0.0) - timestamp) <= window_ms]
    return min(candidates, key=lambda event: abs((_timestamp(event) or 0.0) - timestamp), default=None)


def _aura_windows(events: Iterable[dict], ability_id: int) -> Dict[str, List[tuple[float, float]]]:
    starts: DefaultDict[str, List[float]] = defaultdict(list)
    windows: DefaultDict[str, List[tuple[float, float]]] = defaultdict(list)
    relevant = [event for event in events if _ability_id(event) == ability_id]
    for event in sorted(relevant, key=_event_sort_key):
        player = _target(event)
        timestamp = _timestamp(event)
        if not player or timestamp is None:
            continue
        event_type = str(event.get("type") or "").lower()
        if event_type == "applydebuff":
            starts[player].append(timestamp)
        elif event_type == "removedebuff" and starts[player]:
            windows[player].append((starts[player].pop(0), timestamp))
    for player, values in starts.items():
        for start in values:
            windows[player].append((start, float("inf")))
    return windows


def _window_active(windows: Iterable[tuple[float, float]], timestamp: float, *, minimum_age_ms: float = 0.0) -> bool:
    return any(start + minimum_age_ms <= timestamp <= end for start, end in windows)


def _player_in_scope(context: FightMechanicContext, player: Optional[str]) -> bool:
    return bool(player and player in context.known_players and (not context.participants or player in context.participants))


def _event_sort_key(event: dict) -> float:
    return _timestamp(event) or 0.0


def _timestamp(event: Optional[dict]) -> Optional[float]:
    if not event:
        return None
    try:
        return float(event.get("timestamp"))
    except (TypeError, ValueError):
        return None


def _ability_id(event: Optional[dict]) -> Optional[int]:
    if not event:
        return None
    raw = event.get("abilityGameID")
    if raw is None and isinstance(event.get("ability"), dict):
        raw = event["ability"].get("id") or event["ability"].get("gameID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _extra_ability_id(event: dict) -> Optional[int]:
    raw = event.get("extraAbilityGameID")
    if raw is None and isinstance(event.get("extraAbility"), dict):
        raw = event["extraAbility"].get("id") or event["extraAbility"].get("gameID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _target(event: Optional[dict]) -> Optional[str]:
    if not event:
        return None
    value = event.get("targetName")
    if not value and isinstance(event.get("target"), dict):
        value = event["target"].get("name")
    return str(value) if value else None


def _source(event: Optional[dict]) -> Optional[str]:
    if not event:
        return None
    value = event.get("sourceName")
    if not value and isinstance(event.get("source"), dict):
        value = event["source"].get("name")
    return str(value) if value else None


def _ability_name(event: Optional[dict]) -> Optional[str]:
    if not event:
        return None
    ability = event.get("ability")
    if isinstance(ability, dict) and ability.get("name"):
        return str(ability["name"])
    return None


def _stack(event: Optional[dict]) -> Optional[int]:
    if not event:
        return None
    try:
        return int(event.get("stack") or 1)
    except (TypeError, ValueError):
        return None


__all__ = [
    "FightMechanicContext",
    "MECHANICS_BY_BOSS",
    "REQUIRED_DATA_TYPES",
    "TEAM_PLAYER",
    "analyze_fight",
]
