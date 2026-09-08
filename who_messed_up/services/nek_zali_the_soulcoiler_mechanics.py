"""Mechanics analysis for Mythic Nek'zali the Soulcoiler.

Mechanics reports describe encounter events without assigning scores.  A
Grasping Depths damage window is the authoritative clock for each Drowned Echo
set.  A player's first Immortal Coil tick is the first log-observable signal
that they entered the downstairs realm.

Hungering Pyre sets are anchored to completed enemy casts, then matched to the
friendly-player damage events at that impact.  Cast anchoring retains unsoaked
Pyres instead of silently dropping them from the report.

Essence Rend sets are anchored to each tight application wave.  Successful
dispels are matched by target so aura expiry is never mistaken for a healer
action.
"""
from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

from ..api import Fight, fetch_events_grouped, fetch_fights
from ..env import load_env
from .common import (
    _resolve_event_source_player,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
)
from .report_pulls import ReportPull, build_report_pulls, merge_report_pulls


REPORT_ID = "nek-zali-the-soulcoiler-mythic-mechanics"
REPORT_TITLE = "Mythic Nek'zali the Soulcoiler - Mechanics"
REPORT_DESCRIPTION = "Review pull-by-pull mechanic execution for Nek'zali."
REPORT_DEFAULT_FIGHT = "Nek'zali the Soulcoiler"
REPORT_FOOTNOTES = (
    "Kill Squad sets are reconstructed from Grasping Depths damage windows; short transition-only log fragments are omitted.",
    "Entry time is the player's first logged Immortal Coil damage tick, the earliest reliable downstairs signal exposed by Warcraft Logs.",
    "Soul Exhaustion remaining is calculated from aura application/removal events and its 60-second duration.",
    "A skull marks a logged death after that player's entry within the set window; the ejection marker uses the resulting Soulcoiled aura as the definitive signal that Soulcoiler's Curse removed the player from downstairs.",
    "Drowned Echo damage is matched by target instance, stops at the killing blow, excludes one-point post-death residue, and credits pet damage to the owning player.",
    "Pyre sets are anchored to completed Hungering Pyre casts; a soaker is a friendly player hit by that cast, and its skull marks a death attributed to Hungering Pyre.",
    "Cremation carriers are matched from Slithering Flame or Cremation aura applications after each Pyre; their application and removal times are shown in the details.",
    "Corpse opportunities count unique Restless Amani deaths in that Pyre's burn window. Confirmed misses count distinct Amani instances that later produced Vessel of Awakening damage; Warcraft Logs does not expose successful corpse-burn events or the exact number simultaneously present.",
    "Essence Rend waves are grouped from near-simultaneous aura applications. A dispel is credited only when Warcraft Logs records an Essence Rend dispel event for that target; ordinary aura removal is not treated as a dispel.",
    "Add Damage includes Restless Amani waves and the intermission Echoes of Jawae. Drowned Echo damage remains in Kill Squads. Warcraft Logs does not expose encounter-NPC summons, so Amani waves are reconstructed from distinct target lives whose first player damage occurs within the same 15-second cluster.",
)

KILL_SQUADS_VIEW_ID = "kill-squads"
PYRE_SOAKS_VIEW_ID = "pyre-soaks"
ESSENCE_REND_DISPELS_VIEW_ID = "essence-rend-dispels"
ADD_DAMAGE_VIEW_ID = "add-damage"
GRASPING_DEPTHS_ID = 1293214
IMMORTAL_COIL_ID = 1308227
HUNGERING_PYRE_ID = 1289855
ESSENCE_REND_ID = 1287434
CREMATION_ID = 1289875
SLITHERING_FLAME_ID = 1294933
VESSEL_OF_AWAKENING_ID = 1297630
RESTLESS_AMANI_NAME = "Restless Amani"
ECHO_OF_JAWAE_NAME = "Echo of Jawae"
DROWNED_ECHO_NAME = "Drowned Echo"
SOUL_EXHAUSTION_ID = 1300235
SOULCOILED_IDS = frozenset({1290361, 1292751, 1311788})
SOUL_EXHAUSTION_DURATION_MS = 60_000.0
_GRASP_CLUSTER_GAP_MS = 5_000.0
_MIN_FULL_SET_WINDOW_MS = 15_000.0
_MIN_SHORT_SET_ENTRANTS = 3
_MIN_SHORT_SET_DAMAGE = 1_000_000.0
_DROWNED_STREAM_GAP_MS = 15_000.0
_PYRE_IMPACT_MATCH_WINDOW_MS = 2_000.0
_PYRE_DEATH_MATCH_WINDOW_MS = 1_500.0
_PYRE_CARRIER_APPLICATION_WINDOW_MS = 12_000.0
_PYRE_CARRIER_DURATION_MS = 20_000.0
_PYRE_BURN_WINDOW_FALLBACK_MS = 30_000.0
_ENEMY_DEATH_DEDUP_WINDOW_MS = 1_000.0
_ESSENCE_REND_SET_GAP_MS = 1_000.0
_ESSENCE_REND_MAX_DURATION_MS = 30_000.0
_DISPEL_REMOVAL_MATCH_TOLERANCE_MS = 250.0
_ADD_WAVE_CLUSTER_GAP_MS = 15_000.0
_EVENT_PAGE_LIMIT = 10_000
_EVENT_FETCH_WORKERS = 4


@dataclass(frozen=True)
class KillSquadEntrant:
    player: str
    class_name: Optional[str]
    entry_timestamp: float
    entry_offset_ms: float
    last_tick_timestamp: float
    last_tick_offset_ms: float
    exhaustion_remaining_ms: Optional[float] = None
    death_timestamp: Optional[float] = None
    death_offset_ms: Optional[float] = None
    ejection_timestamp: Optional[float] = None
    ejection_offset_ms: Optional[float] = None

    @property
    def entered_exhausted(self) -> bool:
        return self.exhaustion_remaining_ms is not None and self.exhaustion_remaining_ms > 0

    @property
    def died(self) -> bool:
        return self.death_timestamp is not None

    @property
    def was_ejected(self) -> bool:
        return self.ejection_timestamp is not None


@dataclass(frozen=True)
class KillSquadDamageContribution:
    player: str
    class_name: Optional[str]
    damage: float


@dataclass(frozen=True)
class _DrownedDamageSegment:
    target_key: Tuple[Optional[int], Optional[int]]
    start_timestamp: float
    end_timestamp: float
    events: Sequence[Dict[str, Any]] = ()


@dataclass(frozen=True)
class KillSquadSet:
    source_report_code: str
    fight_id: int
    fight_name: str
    pull_index: int
    pull_duration_ms: float
    set_index: int
    start_timestamp: float
    start_offset_ms: float
    duration_ms: float
    entrants: Sequence[KillSquadEntrant] = ()
    damage_contributions: Sequence[KillSquadDamageContribution] = ()

    @property
    def exhausted_count(self) -> int:
        return sum(entrant.entered_exhausted for entrant in self.entrants)


@dataclass(frozen=True)
class PyreSoaker:
    player: str
    class_name: Optional[str]
    timestamp: float
    offset_ms: float
    damage: float
    death_timestamp: Optional[float] = None
    death_offset_ms: Optional[float] = None

    @property
    def died(self) -> bool:
        return self.death_timestamp is not None


@dataclass(frozen=True)
class CremationCarrier:
    player: str
    class_name: Optional[str]
    ability_id: int
    ability_name: str
    application_timestamp: float
    application_offset_ms: float
    removal_timestamp: Optional[float] = None
    removal_offset_ms: Optional[float] = None

    @property
    def duration_ms(self) -> float:
        if self.removal_timestamp is not None:
            return max(self.removal_timestamp - self.application_timestamp, 0.0)
        return _PYRE_CARRIER_DURATION_MS


@dataclass(frozen=True)
class PyreCorpseMiss:
    source_instance: Optional[int]
    timestamp: float
    offset_ms: float


@dataclass(frozen=True)
class PyreSet:
    source_report_code: str
    fight_id: int
    fight_name: str
    pull_index: int
    pull_duration_ms: float
    set_index: int
    cast_timestamp: float
    cast_offset_ms: float
    impact_timestamp: float
    impact_offset_ms: float
    soakers: Sequence[PyreSoaker] = ()
    cremation_carriers: Sequence[CremationCarrier] = ()
    corpse_opportunity_count: int = 0
    confirmed_misses: Sequence[PyreCorpseMiss] = ()

    @property
    def total_damage(self) -> float:
        return sum(soaker.damage for soaker in self.soakers)

    @property
    def death_count(self) -> int:
        return sum(soaker.died for soaker in self.soakers)

    @property
    def confirmed_miss_count(self) -> int:
        return len(self.confirmed_misses)


@dataclass(frozen=True)
class EssenceRendApplication:
    player: str
    class_name: Optional[str]
    application_timestamp: float
    application_offset_ms: float
    removal_timestamp: Optional[float] = None
    removal_offset_ms: Optional[float] = None
    dispeller: Optional[str] = None
    dispeller_class_name: Optional[str] = None
    dispel_timestamp: Optional[float] = None
    dispel_offset_ms: Optional[float] = None
    dispel_delay_ms: Optional[float] = None
    dispel_ability_id: Optional[int] = None

    @property
    def was_dispelled(self) -> bool:
        return self.dispel_timestamp is not None


@dataclass(frozen=True)
class EssenceRendSet:
    source_report_code: str
    fight_id: int
    fight_name: str
    pull_index: int
    pull_duration_ms: float
    set_index: int
    application_timestamp: float
    application_offset_ms: float
    applications: Sequence[EssenceRendApplication] = ()

    @property
    def dispelled_count(self) -> int:
        return sum(application.was_dispelled for application in self.applications)

    @property
    def undispelled_count(self) -> int:
        return len(self.applications) - self.dispelled_count


@dataclass(frozen=True)
class AddDamageSet:
    source_report_code: str
    fight_id: int
    fight_name: str
    pull_index: int
    pull_duration_ms: float
    set_index: int
    add_name: str
    start_timestamp: float
    start_offset_ms: float
    end_timestamp: float
    end_offset_ms: float
    add_count: int
    damage_contributions: Sequence[KillSquadDamageContribution] = ()

    @property
    def total_damage(self) -> float:
        return sum(
            contribution.damage for contribution in self.damage_contributions
        )

    @property
    def duration_ms(self) -> float:
        return max(self.end_timestamp - self.start_timestamp, 0.0)


@dataclass(frozen=True)
class MechanicsReportView:
    id: str
    label: str
    description: str
    sets: Sequence[KillSquadSet | PyreSet | EssenceRendSet | AddDamageSet] = ()


@dataclass
class NekZaliMechanicsSummary:
    report_code: str
    fight_filter: str
    pull_count: int
    views: List[MechanicsReportView]
    pulls: List[ReportPull] = field(default_factory=list)
    player_classes: Dict[str, Optional[str]] = field(default_factory=dict)
    source_reports: List[str] = field(default_factory=list)


def _event_ability_id(event: Dict[str, Any]) -> Optional[int]:
    value = event.get("abilityGameID")
    if value is None and isinstance(event.get("ability"), dict):
        value = event["ability"].get("gameID") or event["ability"].get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _event_extra_ability_id(event: Dict[str, Any]) -> Optional[int]:
    value = event.get("extraAbilityGameID")
    if value is None and isinstance(event.get("extraAbility"), dict):
        value = event["extraAbility"].get("gameID") or event["extraAbility"].get(
            "id"
        )
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _event_killing_ability_id(event: Dict[str, Any]) -> Optional[int]:
    value = event.get("killingAbilityGameID")
    if value is None and isinstance(event.get("killingAbility"), dict):
        value = event["killingAbility"].get("gameID") or event["killingAbility"].get(
            "id"
        )
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _event_actor_id(event: Dict[str, Any], side: str) -> Optional[int]:
    value = event.get(f"{side}ID")
    if value is None and isinstance(event.get(side), dict):
        value = event[side].get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _event_actor_name(
    event: Dict[str, Any], side: str, actor_names: Dict[int, str]
) -> Optional[str]:
    value = event.get(f"{side}Name")
    if not value and isinstance(event.get(side), dict):
        value = event[side].get("name")
    actor_id = _event_actor_id(event, side)
    if not value and actor_id is not None:
        value = actor_names.get(actor_id)
    return str(value) if value else None


def _event_actor_instance(event: Dict[str, Any], side: str) -> Optional[int]:
    value = event.get(f"{side}Instance")
    if value is None:
        value = event.get(f"{side}InstanceID")
    if value is None and isinstance(event.get(side), dict):
        value = event[side].get("instance")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _event_effective_damage(event: Dict[str, Any]) -> float:
    """Return damage that reduced target health, excluding absorbs and overkill."""
    try:
        return max(float(event.get("amount") or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _event_target_key(
    event: Dict[str, Any],
) -> Tuple[Optional[int], Optional[int]]:
    target_id = _event_actor_id(event, "target")
    instance_value = event.get("targetInstance")
    if instance_value is None:
        instance_value = event.get("targetInstanceID")
    if instance_value is None and isinstance(event.get("target"), dict):
        instance_value = event["target"].get("instance")
    try:
        instance_id = int(instance_value) if instance_value is not None else None
    except (TypeError, ValueError):
        instance_id = None
    return target_id, instance_id


def _build_drowned_damage_segments(
    events: Sequence[Dict[str, Any]],
) -> List[_DrownedDamageSegment]:
    """Split Echo damage by target identity and stop each life at its kill blow."""
    events_by_target: Dict[
        Tuple[Optional[int], Optional[int]], List[Dict[str, Any]]
    ] = defaultdict(list)
    for event in events:
        if _event_effective_damage(event) <= 0:
            continue
        events_by_target[_event_target_key(event)].append(event)

    segments: List[_DrownedDamageSegment] = []
    for target_key, target_events in events_by_target.items():
        current: List[Dict[str, Any]] = []
        target_dead = False
        previous_timestamp: Optional[float] = None
        for event in sorted(
            target_events, key=lambda item: float(item.get("timestamp") or 0)
        ):
            timestamp = float(event.get("timestamp") or 0)
            if (
                previous_timestamp is not None
                and timestamp - previous_timestamp > _DROWNED_STREAM_GAP_MS
            ):
                if current:
                    segments.append(
                        _DrownedDamageSegment(
                            target_key=target_key,
                            start_timestamp=float(current[0].get("timestamp") or 0),
                            end_timestamp=float(current[-1].get("timestamp") or 0),
                            events=current,
                        )
                    )
                current = []
                target_dead = False
            previous_timestamp = timestamp
            if target_dead:
                continue
            current.append(event)
            try:
                overkill = float(event.get("overkill") or 0)
            except (TypeError, ValueError):
                overkill = 0.0
            if overkill > 0:
                segments.append(
                    _DrownedDamageSegment(
                        target_key=target_key,
                        start_timestamp=float(current[0].get("timestamp") or 0),
                        end_timestamp=timestamp,
                        events=current,
                    )
                )
                current = []
                target_dead = True
        if current:
            segments.append(
                _DrownedDamageSegment(
                    target_key=target_key,
                    start_timestamp=float(current[0].get("timestamp") or 0),
                    end_timestamp=float(current[-1].get("timestamp") or 0),
                    events=current,
                )
            )
    return sorted(segments, key=lambda segment: segment.start_timestamp)


def _drowned_events_for_window(
    segments: Sequence[_DrownedDamageSegment],
    *,
    start: float,
    end: float,
) -> List[Dict[str, Any]]:
    return [
        event
        for segment in segments
        if segment.end_timestamp >= start and segment.start_timestamp < end
        for event in segment.events
        if start <= float(event.get("timestamp") or 0) < end
    ]


def _cluster_timestamps(
    timestamps: Iterable[float], *, max_gap_ms: float
) -> List[List[float]]:
    clusters: List[List[float]] = []
    for timestamp in sorted(float(value) for value in timestamps):
        if not clusters or timestamp - clusters[-1][-1] > max_gap_ms:
            clusters.append([timestamp])
        else:
            clusters[-1].append(timestamp)
    return clusters


def _first_player_event_timestamp(
    events: Sequence[Dict[str, Any]],
    *,
    target_id: int,
    start: float,
    end: float,
    ability_ids: Optional[Iterable[int]] = None,
    event_types: Optional[Iterable[str]] = None,
) -> Optional[float]:
    allowed_abilities = set(ability_ids) if ability_ids is not None else None
    allowed_types = (
        {event_type.lower() for event_type in event_types}
        if event_types is not None
        else None
    )
    matches = []
    for event in events:
        timestamp = float(event.get("timestamp") or 0)
        if not start <= timestamp < end:
            continue
        if _event_actor_id(event, "target") != target_id:
            continue
        if allowed_abilities is not None and _event_ability_id(event) not in allowed_abilities:
            continue
        if (
            allowed_types is not None
            and str(event.get("type") or "").lower() not in allowed_types
        ):
            continue
        matches.append(timestamp)
    return min(matches) if matches else None


def _exhaustion_remaining_ms(
    aura_events: Sequence[Dict[str, Any]],
    *,
    target_id: int,
    timestamp: float,
) -> Optional[float]:
    applied_at: Optional[float] = None
    active = False
    for event in aura_events:
        event_timestamp = float(event.get("timestamp") or 0)
        if event_timestamp > timestamp:
            break
        if _event_actor_id(event, "target") != target_id:
            continue
        if _event_ability_id(event) != SOUL_EXHAUSTION_ID:
            continue
        event_type = str(event.get("type") or "").lower()
        if event_type in {"applydebuff", "refreshdebuff", "applydebuffstack"}:
            active = True
            applied_at = event_timestamp
        elif event_type == "removedebuff":
            active = False
            applied_at = None

    if not active or applied_at is None:
        return None

    estimated_expiry = applied_at + SOUL_EXHAUSTION_DURATION_MS
    removal = next(
        (
            float(event["timestamp"])
            for event in aura_events
            if _event_actor_id(event, "target") == target_id
            and _event_ability_id(event) == SOUL_EXHAUSTION_ID
            and float(event.get("timestamp") or 0) > timestamp
            and str(event.get("type") or "").lower() == "removedebuff"
        ),
        None,
    )
    expiry = min(removal, estimated_expiry) if removal is not None else estimated_expiry
    return max(expiry - timestamp, 0.0)


def _damage_contributions_for_events(
    events: Sequence[Dict[str, Any]],
    *,
    player_ids: set[int],
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
    actor_owners: Dict[int, Optional[int]],
) -> List[KillSquadDamageContribution]:
    damage_by_player: Dict[tuple[str, Optional[str]], float] = defaultdict(float)
    for event in events:
        source_name, source_id = _resolve_event_source_player(
            event, actor_names, actor_owners
        )
        if not source_name or source_id not in player_ids:
            continue
        amount = _event_effective_damage(event)
        if amount <= 0:
            continue
        damage_by_player[(source_name, actor_classes.get(source_id))] += amount
    return [
        KillSquadDamageContribution(
            player=player,
            class_name=class_name,
            damage=damage,
        )
        for (player, class_name), damage in sorted(
            damage_by_player.items(),
            key=lambda item: (-item[1], item[0][0]),
        )
    ]


def build_kill_squad_sets(
    *,
    report_code: str,
    fights: Sequence[Fight],
    damage_taken_by_fight: Dict[int, List[Dict[str, Any]]],
    exhaustion_by_fight: Dict[int, List[Dict[str, Any]]],
    drowned_damage_by_fight: Dict[int, List[Dict[str, Any]]],
    deaths_by_fight: Dict[int, List[Dict[str, Any]]],
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
    actor_owners: Dict[int, Optional[int]],
) -> List[KillSquadSet]:
    """Reconstruct Drowned Echo sets while retaining late recovery entrants."""
    sets: List[KillSquadSet] = []
    for pull_index, fight in enumerate(fights, start=1):
        player_ids = set(fight.friendly_player_ids) or set(actor_classes)
        damage_events = damage_taken_by_fight.get(fight.id, [])
        aura_events = sorted(
            exhaustion_by_fight.get(fight.id, []),
            key=lambda event: float(event.get("timestamp") or 0),
        )
        drowned_segments = _build_drowned_damage_segments(
            drowned_damage_by_fight.get(fight.id, [])
        )
        grasp_clusters = _cluster_timestamps(
            (
                float(event["timestamp"])
                for event in damage_events
                if _event_ability_id(event) == GRASPING_DEPTHS_ID
                and _event_actor_id(event, "target") in player_ids
            ),
            max_gap_ms=_GRASP_CLUSTER_GAP_MS,
        )
        windows = [
            (cluster[0], cluster[-1] + 1_000.0)
            for cluster in grasp_clusters
            if cluster
        ]
        candidates: List[KillSquadSet] = []
        for window_index, (start_ms, end_ms) in enumerate(windows):
            analysis_start = start_ms - 3_000.0
            analysis_end = end_ms + 15_000.0
            if window_index:
                analysis_start = max(
                    analysis_start,
                    (windows[window_index - 1][1] + start_ms) / 2,
                )
            if window_index + 1 < len(windows):
                analysis_end = min(
                    analysis_end,
                    (end_ms + windows[window_index + 1][0]) / 2,
                )

            immortal_ticks: Dict[int, List[float]] = defaultdict(list)
            for event in damage_events:
                if _event_ability_id(event) != IMMORTAL_COIL_ID:
                    continue
                timestamp = float(event.get("timestamp") or 0)
                if not analysis_start <= timestamp < analysis_end:
                    continue
                target_id = _event_actor_id(event, "target")
                if target_id not in player_ids:
                    continue
                immortal_ticks[target_id].append(timestamp)
            entry_times = {
                target_id: min(timestamps)
                for target_id, timestamps in immortal_ticks.items()
            }

            drowned_events = _drowned_events_for_window(
                drowned_segments,
                start=analysis_start,
                end=analysis_end,
            )
            drowned_damage = sum(
                _event_effective_damage(event) for event in drowned_events
            )
            duration_ms = end_ms - start_ms
            if (
                duration_ms < _MIN_FULL_SET_WINDOW_MS
                and len(entry_times) < _MIN_SHORT_SET_ENTRANTS
                and drowned_damage < _MIN_SHORT_SET_DAMAGE
            ):
                continue

            damage_contributions = _damage_contributions_for_events(
                drowned_events,
                player_ids=player_ids,
                actor_names=actor_names,
                actor_classes=actor_classes,
                actor_owners=actor_owners,
            )

            entrants: List[KillSquadEntrant] = []
            for target_id, timestamp in sorted(
                entry_times.items(),
                key=lambda item: (item[1], actor_names.get(item[0], "")),
            ):
                death_timestamp = _first_player_event_timestamp(
                    deaths_by_fight.get(fight.id, []),
                    target_id=target_id,
                    start=timestamp,
                    end=analysis_end,
                )
                ejection_timestamp = _first_player_event_timestamp(
                    aura_events,
                    target_id=target_id,
                    start=timestamp,
                    end=analysis_end,
                    ability_ids=SOULCOILED_IDS,
                    event_types={
                        "applydebuff",
                        "refreshdebuff",
                        "applydebuffstack",
                    },
                )
                entrants.append(
                    KillSquadEntrant(
                        player=actor_names.get(target_id, str(target_id)),
                        class_name=actor_classes.get(target_id),
                        entry_timestamp=timestamp,
                        entry_offset_ms=timestamp - fight.start,
                        last_tick_timestamp=max(immortal_ticks[target_id]),
                        last_tick_offset_ms=(
                            max(immortal_ticks[target_id]) - fight.start
                        ),
                        exhaustion_remaining_ms=_exhaustion_remaining_ms(
                            aura_events,
                            target_id=target_id,
                            timestamp=timestamp,
                        ),
                        death_timestamp=death_timestamp,
                        death_offset_ms=(
                            death_timestamp - fight.start
                            if death_timestamp is not None
                            else None
                        ),
                        ejection_timestamp=ejection_timestamp,
                        ejection_offset_ms=(
                            ejection_timestamp - fight.start
                            if ejection_timestamp is not None
                            else None
                        ),
                    )
                )
            candidates.append(
                KillSquadSet(
                    source_report_code=report_code,
                    fight_id=fight.id,
                    fight_name=fight.name,
                    pull_index=pull_index,
                    pull_duration_ms=max(fight.end - fight.start, 0.0),
                    set_index=0,
                    start_timestamp=start_ms,
                    start_offset_ms=start_ms - fight.start,
                    duration_ms=duration_ms,
                    entrants=entrants,
                    damage_contributions=damage_contributions,
                )
            )

        sets.extend(
            replace(candidate, set_index=set_index)
            for set_index, candidate in enumerate(candidates, start=1)
        )
    return sets


def _deduplicated_restless_amani_deaths(
    events: Sequence[Dict[str, Any]], actor_names: Dict[int, str]
) -> List[Dict[str, Any]]:
    """Collapse duplicate enemy death rows without merging reused actor instances."""
    unique: List[Dict[str, Any]] = []
    last_timestamp_by_actor: Dict[Tuple[Optional[int], Optional[int]], float] = {}
    for event in sorted(events, key=lambda item: float(item.get("timestamp") or 0)):
        target_id = _event_actor_id(event, "target")
        if actor_names.get(target_id) != RESTLESS_AMANI_NAME:
            continue
        timestamp = float(event.get("timestamp") or 0)
        actor_key = (target_id, _event_actor_instance(event, "target"))
        previous_timestamp = last_timestamp_by_actor.get(actor_key)
        if (
            previous_timestamp is not None
            and timestamp - previous_timestamp <= _ENEMY_DEATH_DEDUP_WINDOW_MS
        ):
            continue
        last_timestamp_by_actor[actor_key] = timestamp
        unique.append(event)
    return unique


def _pyre_carriers(
    *,
    cast_timestamp: float,
    next_cast_timestamp: Optional[float],
    fight: Fight,
    aura_events: Sequence[Dict[str, Any]],
    player_ids: set[int],
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
) -> List[CremationCarrier]:
    application_end = cast_timestamp + _PYRE_CARRIER_APPLICATION_WINDOW_MS
    if next_cast_timestamp is not None:
        application_end = min(application_end, next_cast_timestamp)
    applications_by_target: Dict[int, Dict[str, Any]] = {}
    for event in aura_events:
        timestamp = float(event.get("timestamp") or 0)
        if timestamp < cast_timestamp - 500.0 or timestamp >= application_end:
            continue
        if _event_ability_id(event) not in {CREMATION_ID, SLITHERING_FLAME_ID}:
            continue
        if str(event.get("type") or "").lower() not in {
            "applydebuff",
            "refreshdebuff",
        }:
            continue
        target_id = _event_actor_id(event, "target")
        if target_id not in player_ids:
            continue
        existing = applications_by_target.get(target_id)
        if existing is None or timestamp < float(existing.get("timestamp") or 0):
            applications_by_target[target_id] = event

    carriers: List[CremationCarrier] = []
    for target_id, application in applications_by_target.items():
        ability_id = _event_ability_id(application) or CREMATION_ID
        application_timestamp = float(application.get("timestamp") or 0)
        removal_timestamp = next(
            (
                float(event.get("timestamp") or 0)
                for event in aura_events
                if float(event.get("timestamp") or 0) > application_timestamp
                and float(event.get("timestamp") or 0)
                <= application_timestamp + _PYRE_CARRIER_DURATION_MS + 2_000.0
                and _event_actor_id(event, "target") == target_id
                and _event_ability_id(event) == ability_id
                and str(event.get("type") or "").lower() == "removedebuff"
            ),
            None,
        )
        carriers.append(
            CremationCarrier(
                player=actor_names.get(target_id, str(target_id)),
                class_name=actor_classes.get(target_id),
                ability_id=ability_id,
                ability_name=(
                    "Slithering Flame"
                    if ability_id == SLITHERING_FLAME_ID
                    else "Cremation"
                ),
                application_timestamp=application_timestamp,
                application_offset_ms=application_timestamp - fight.start,
                removal_timestamp=removal_timestamp,
                removal_offset_ms=(
                    removal_timestamp - fight.start
                    if removal_timestamp is not None
                    else None
                ),
            )
        )
    return sorted(
        carriers,
        key=lambda carrier: (carrier.application_timestamp, carrier.player),
    )


def build_pyre_sets(
    *,
    report_code: str,
    fights: Sequence[Fight],
    casts_by_fight: Dict[int, List[Dict[str, Any]]],
    damage_taken_by_fight: Dict[int, List[Dict[str, Any]]],
    deaths_by_fight: Dict[int, List[Dict[str, Any]]],
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
    aura_events_by_fight: Optional[Dict[int, List[Dict[str, Any]]]] = None,
    enemy_deaths_by_fight: Optional[Dict[int, List[Dict[str, Any]]]] = None,
    vessel_damage_by_fight: Optional[Dict[int, List[Dict[str, Any]]]] = None,
) -> List[PyreSet]:
    """Build Pyre participation and the corpse signals Warcraft Logs exposes."""
    aura_events_by_fight = aura_events_by_fight or {}
    enemy_deaths_by_fight = enemy_deaths_by_fight or {}
    vessel_damage_by_fight = vessel_damage_by_fight or {}
    sets: List[PyreSet] = []
    for pull_index, fight in enumerate(fights, start=1):
        player_ids = set(fight.friendly_player_ids) or set(actor_classes)
        cast_timestamps = sorted(
            float(event.get("timestamp") or 0)
            for event in casts_by_fight.get(fight.id, [])
            if _event_ability_id(event) == HUNGERING_PYRE_ID
            and str(event.get("type") or "").lower() == "cast"
        )
        damage_events = [
            event
            for event in damage_taken_by_fight.get(fight.id, [])
            if _event_ability_id(event) == HUNGERING_PYRE_ID
            and _event_actor_id(event, "target") in player_ids
        ]
        deaths = deaths_by_fight.get(fight.id, [])
        aura_events = sorted(
            aura_events_by_fight.get(fight.id, []),
            key=lambda event: float(event.get("timestamp") or 0),
        )
        carriers_by_cast_index: Dict[int, List[CremationCarrier]] = {}
        burn_end_by_cast_index: Dict[int, float] = {}
        for cast_index, cast_timestamp in enumerate(cast_timestamps):
            next_cast_timestamp = (
                cast_timestamps[cast_index + 1]
                if cast_index + 1 < len(cast_timestamps)
                else None
            )
            carriers = _pyre_carriers(
                cast_timestamp=cast_timestamp,
                next_cast_timestamp=next_cast_timestamp,
                fight=fight,
                aura_events=aura_events,
                player_ids=player_ids,
                actor_names=actor_names,
                actor_classes=actor_classes,
            )
            carriers_by_cast_index[cast_index] = carriers
            burn_end = max(
                (
                    carrier.removal_timestamp
                    or carrier.application_timestamp + _PYRE_CARRIER_DURATION_MS
                    for carrier in carriers
                ),
                default=cast_timestamp + _PYRE_BURN_WINDOW_FALLBACK_MS,
            )
            if next_cast_timestamp is not None:
                burn_end = min(burn_end, next_cast_timestamp)
            burn_end_by_cast_index[cast_index] = min(burn_end, fight.end)

        corpse_deaths = _deduplicated_restless_amani_deaths(
            enemy_deaths_by_fight.get(fight.id, []), actor_names
        )
        corpse_opportunities_by_cast_index: Dict[int, int] = {}
        burn_window_start = fight.start
        for cast_index, cast_timestamp in enumerate(cast_timestamps):
            burn_window_end = burn_end_by_cast_index[cast_index]
            corpse_opportunities_by_cast_index[cast_index] = sum(
                burn_window_start
                <= float(event.get("timestamp") or 0)
                < burn_window_end
                for event in corpse_deaths
            )
            burn_window_start = burn_window_end

        confirmed_misses_by_cast_index: Dict[int, List[PyreCorpseMiss]] = {}
        vessel_events = vessel_damage_by_fight.get(fight.id, [])
        for cast_index, cast_timestamp in enumerate(cast_timestamps):
            miss_window_end = (
                cast_timestamps[cast_index + 1]
                if cast_index + 1 < len(cast_timestamps)
                else fight.end
            )
            first_event_by_source: Dict[
                Tuple[Optional[int], Optional[int]], Dict[str, Any]
            ] = {}
            for event in vessel_events:
                timestamp = float(event.get("timestamp") or 0)
                if not cast_timestamp <= timestamp < miss_window_end:
                    continue
                if _event_ability_id(event) != VESSEL_OF_AWAKENING_ID:
                    continue
                if _event_actor_id(event, "target") not in player_ids:
                    continue
                source_id = _event_actor_id(event, "source")
                if actor_names.get(source_id) != RESTLESS_AMANI_NAME:
                    continue
                source_key = (
                    source_id,
                    _event_actor_instance(event, "source"),
                )
                existing = first_event_by_source.get(source_key)
                if existing is None or timestamp < float(
                    existing.get("timestamp") or 0
                ):
                    first_event_by_source[source_key] = event
            confirmed_misses_by_cast_index[cast_index] = [
                PyreCorpseMiss(
                    source_instance=source_key[1],
                    timestamp=float(event.get("timestamp") or 0),
                    offset_ms=float(event.get("timestamp") or 0) - fight.start,
                )
                for source_key, event in sorted(
                    first_event_by_source.items(),
                    key=lambda item: float(item[1].get("timestamp") or 0),
                )
            ]

        damage_by_cast_index: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for event in damage_events:
            event_timestamp = float(event.get("timestamp") or 0)
            if not cast_timestamps:
                continue
            closest_index, closest_timestamp = min(
                enumerate(cast_timestamps),
                key=lambda item: abs(event_timestamp - item[1]),
            )
            if (
                abs(event_timestamp - closest_timestamp)
                <= _PYRE_IMPACT_MATCH_WINDOW_MS
            ):
                damage_by_cast_index[closest_index].append(event)

        for cast_index, cast_timestamp in enumerate(cast_timestamps):
            set_index = cast_index + 1
            matched_damage = damage_by_cast_index.get(cast_index, [])
            impact_timestamp = min(
                (
                    float(event.get("timestamp") or 0)
                    for event in matched_damage
                ),
                default=cast_timestamp,
            )
            hits_by_player: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
            for event in matched_damage:
                target_id = _event_actor_id(event, "target")
                if target_id is not None:
                    hits_by_player[target_id].append(event)

            soakers: List[PyreSoaker] = []
            for target_id, hits in hits_by_player.items():
                timestamp = min(float(hit.get("timestamp") or 0) for hit in hits)
                damage = sum(_event_effective_damage(hit) for hit in hits)
                death_timestamp = next(
                    (
                        float(death.get("timestamp") or 0)
                        for death in deaths
                        if _event_actor_id(death, "target") == target_id
                        and _event_killing_ability_id(death) == HUNGERING_PYRE_ID
                        and abs(
                            float(death.get("timestamp") or 0) - impact_timestamp
                        )
                        <= _PYRE_DEATH_MATCH_WINDOW_MS
                    ),
                    None,
                )
                soakers.append(
                    PyreSoaker(
                        player=actor_names.get(target_id, str(target_id)),
                        class_name=actor_classes.get(target_id),
                        timestamp=timestamp,
                        offset_ms=timestamp - fight.start,
                        damage=damage,
                        death_timestamp=death_timestamp,
                        death_offset_ms=(
                            death_timestamp - fight.start
                            if death_timestamp is not None
                            else None
                        ),
                    )
                )

            sets.append(
                PyreSet(
                    source_report_code=report_code,
                    fight_id=fight.id,
                    fight_name=fight.name,
                    pull_index=pull_index,
                    pull_duration_ms=max(fight.end - fight.start, 0.0),
                    set_index=set_index,
                    cast_timestamp=cast_timestamp,
                    cast_offset_ms=cast_timestamp - fight.start,
                    impact_timestamp=impact_timestamp,
                    impact_offset_ms=impact_timestamp - fight.start,
                    soakers=tuple(
                        sorted(
                            soakers,
                            key=lambda soaker: (soaker.timestamp, soaker.player),
                        )
                    ),
                    cremation_carriers=tuple(
                        carriers_by_cast_index.get(cast_index, [])
                    ),
                    corpse_opportunity_count=corpse_opportunities_by_cast_index.get(
                        cast_index, 0
                    ),
                    confirmed_misses=tuple(
                        confirmed_misses_by_cast_index.get(cast_index, [])
                    ),
                )
            )
    return sets


def build_essence_rend_sets(
    *,
    report_code: str,
    fights: Sequence[Fight],
    aura_events_by_fight: Dict[int, List[Dict[str, Any]]],
    dispels_by_fight: Dict[int, List[Dict[str, Any]]],
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
) -> List[EssenceRendSet]:
    """Group Essence Rend applications into waves and match real dispels."""
    sets: List[EssenceRendSet] = []
    for pull_index, fight in enumerate(fights, start=1):
        player_ids = set(fight.friendly_player_ids) or set(actor_classes)
        application_events = sorted(
            (
                event
                for event in aura_events_by_fight.get(fight.id, [])
                if _event_ability_id(event) == ESSENCE_REND_ID
                and str(event.get("type") or "").lower() == "applydebuff"
                and _event_actor_id(event, "target") in player_ids
            ),
            key=lambda event: float(event.get("timestamp") or 0),
        )
        if not application_events:
            continue

        application_batches: List[List[Dict[str, Any]]] = []
        for event in application_events:
            timestamp = float(event.get("timestamp") or 0)
            if (
                not application_batches
                or timestamp
                - float(application_batches[-1][-1].get("timestamp") or 0)
                > _ESSENCE_REND_SET_GAP_MS
            ):
                application_batches.append([event])
            else:
                application_batches[-1].append(event)

        applications_by_target: Dict[int, List[float]] = defaultdict(list)
        for event in application_events:
            target_id = _event_actor_id(event, "target")
            if target_id is not None:
                applications_by_target[target_id].append(
                    float(event.get("timestamp") or 0)
                )

        removals_by_target: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for event in aura_events_by_fight.get(fight.id, []):
            target_id = _event_actor_id(event, "target")
            if (
                target_id in player_ids
                and _event_ability_id(event) == ESSENCE_REND_ID
                and str(event.get("type") or "").lower() == "removedebuff"
            ):
                removals_by_target[target_id].append(event)
        for events in removals_by_target.values():
            events.sort(key=lambda event: float(event.get("timestamp") or 0))

        dispels_by_target: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for event in dispels_by_fight.get(fight.id, []):
            target_id = _event_actor_id(event, "target")
            if (
                target_id in player_ids
                and (
                    _event_extra_ability_id(event) == ESSENCE_REND_ID
                    or _event_ability_id(event) == ESSENCE_REND_ID
                )
                and str(event.get("type") or "").lower() == "dispel"
            ):
                dispels_by_target[target_id].append(event)
        for events in dispels_by_target.values():
            events.sort(key=lambda event: float(event.get("timestamp") or 0))

        for set_index, batch in enumerate(application_batches, start=1):
            rend_applications: List[EssenceRendApplication] = []
            seen_targets: set[int] = set()
            for event in batch:
                target_id = _event_actor_id(event, "target")
                if target_id is None or target_id in seen_targets:
                    continue
                seen_targets.add(target_id)
                application_timestamp = float(event.get("timestamp") or 0)
                target_application_times = applications_by_target[target_id]
                next_application = next(
                    (
                        timestamp
                        for timestamp in target_application_times
                        if timestamp > application_timestamp
                    ),
                    None,
                )
                match_end = min(
                    application_timestamp + _ESSENCE_REND_MAX_DURATION_MS,
                    next_application if next_application is not None else fight.end,
                    fight.end,
                )
                removal_event = next(
                    (
                        removal
                        for removal in removals_by_target.get(target_id, [])
                        if application_timestamp
                        <= float(removal.get("timestamp") or 0)
                        <= match_end
                    ),
                    None,
                )
                removal_timestamp = (
                    float(removal_event.get("timestamp") or 0)
                    if removal_event is not None
                    else None
                )
                dispel_match_end = (
                    removal_timestamp + _DISPEL_REMOVAL_MATCH_TOLERANCE_MS
                    if removal_timestamp is not None
                    else match_end
                )
                dispel_event = next(
                    (
                        dispel
                        for dispel in dispels_by_target.get(target_id, [])
                        if application_timestamp
                        <= float(dispel.get("timestamp") or 0)
                        <= dispel_match_end
                    ),
                    None,
                )
                dispel_timestamp = (
                    float(dispel_event.get("timestamp") or 0)
                    if dispel_event is not None
                    else None
                )
                dispeller_id = (
                    _event_actor_id(dispel_event, "source")
                    if dispel_event is not None
                    else None
                )
                rend_applications.append(
                    EssenceRendApplication(
                        player=actor_names.get(target_id, str(target_id)),
                        class_name=actor_classes.get(target_id),
                        application_timestamp=application_timestamp,
                        application_offset_ms=application_timestamp - fight.start,
                        removal_timestamp=removal_timestamp,
                        removal_offset_ms=(
                            removal_timestamp - fight.start
                            if removal_timestamp is not None
                            else None
                        ),
                        dispeller=(
                            actor_names.get(dispeller_id, str(dispeller_id))
                            if dispeller_id is not None
                            else None
                        ),
                        dispeller_class_name=actor_classes.get(dispeller_id),
                        dispel_timestamp=dispel_timestamp,
                        dispel_offset_ms=(
                            dispel_timestamp - fight.start
                            if dispel_timestamp is not None
                            else None
                        ),
                        dispel_delay_ms=(
                            dispel_timestamp - application_timestamp
                            if dispel_timestamp is not None
                            else None
                        ),
                        dispel_ability_id=(
                            _event_ability_id(dispel_event)
                            if dispel_event is not None
                            else None
                        ),
                    )
                )

            batch_timestamp = min(
                float(event.get("timestamp") or 0) for event in batch
            )
            sets.append(
                EssenceRendSet(
                    source_report_code=report_code,
                    fight_id=fight.id,
                    fight_name=fight.name,
                    pull_index=pull_index,
                    pull_duration_ms=max(fight.end - fight.start, 0.0),
                    set_index=set_index,
                    application_timestamp=batch_timestamp,
                    application_offset_ms=batch_timestamp - fight.start,
                    applications=tuple(
                        sorted(
                            rend_applications,
                            key=lambda application: (
                                application.application_timestamp,
                                application.player,
                            ),
                        )
                    ),
                )
            )
    return sets


def _cluster_damage_segments(
    segments: Sequence[_DrownedDamageSegment], *, max_gap_ms: float
) -> List[List[_DrownedDamageSegment]]:
    clusters: List[List[_DrownedDamageSegment]] = []
    for segment in sorted(segments, key=lambda item: item.start_timestamp):
        if (
            not clusters
            or segment.start_timestamp - clusters[-1][-1].start_timestamp
            > max_gap_ms
        ):
            clusters.append([segment])
        else:
            clusters[-1].append(segment)
    return clusters


def build_add_damage_sets(
    *,
    report_code: str,
    fights: Sequence[Fight],
    damage_by_fight: Dict[int, List[Dict[str, Any]]],
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
    actor_owners: Dict[int, Optional[int]],
) -> List[AddDamageSet]:
    """Reconstruct normal add waves and aggregate owner-attributed damage."""
    sets: List[AddDamageSet] = []
    for pull_index, fight in enumerate(fights, start=1):
        player_ids = set(fight.friendly_player_ids) or set(actor_classes)
        events = damage_by_fight.get(fight.id, [])
        segments_by_name = {
            add_name: _build_drowned_damage_segments(
                [
                    event
                    for event in events
                    if _event_actor_name(event, "target", actor_names) == add_name
                ]
            )
            for add_name in (RESTLESS_AMANI_NAME, ECHO_OF_JAWAE_NAME)
        }
        wave_candidates: List[
            Tuple[str, Sequence[_DrownedDamageSegment]]
        ] = [
            (RESTLESS_AMANI_NAME, cluster)
            for cluster in _cluster_damage_segments(
                segments_by_name[RESTLESS_AMANI_NAME],
                max_gap_ms=_ADD_WAVE_CLUSTER_GAP_MS,
            )
        ]
        jawae_segments = segments_by_name[ECHO_OF_JAWAE_NAME]
        if jawae_segments:
            # Both Echoes spawn together for the only intermission, even when
            # the raid damages the second one much later than the first.
            wave_candidates.append((ECHO_OF_JAWAE_NAME, jawae_segments))

        for set_index, (add_name, segments) in enumerate(
            sorted(
                wave_candidates,
                key=lambda candidate: min(
                    segment.start_timestamp for segment in candidate[1]
                ),
            ),
            start=1,
        ):
            damage_events = [
                event for segment in segments for event in segment.events
            ]
            start_timestamp = min(
                segment.start_timestamp for segment in segments
            )
            end_timestamp = max(segment.end_timestamp for segment in segments)
            sets.append(
                AddDamageSet(
                    source_report_code=report_code,
                    fight_id=fight.id,
                    fight_name=fight.name,
                    pull_index=pull_index,
                    pull_duration_ms=max(fight.end - fight.start, 0.0),
                    set_index=set_index,
                    add_name=add_name,
                    start_timestamp=start_timestamp,
                    start_offset_ms=start_timestamp - fight.start,
                    end_timestamp=end_timestamp,
                    end_offset_ms=end_timestamp - fight.start,
                    add_count=len(segments),
                    damage_contributions=tuple(
                        _damage_contributions_for_events(
                            damage_events,
                            player_ids=player_ids,
                            actor_names=actor_names,
                            actor_classes=actor_classes,
                            actor_owners=actor_owners,
                        )
                    ),
                )
            )
    return sets


def _fetch_single_summary(
    *,
    report_code: str,
    fight_name: str,
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> NekZaliMechanicsSummary:
    load_env()
    bearer = _resolve_token(token, client_id, client_secret)
    with requests.Session() as session:
        fights, actor_names, actor_classes, actor_owners = fetch_fights(
            session, bearer, report_code
        )
    chosen = _select_fights(
        fights,
        name_filter=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
    )
    streams = _fetch_mechanics_event_streams(
        report_code=report_code,
        fights=chosen,
        bearer=bearer,
        actor_names=actor_names,
    )
    damage_taken = {
        fight.id: sorted(
            streams["grasp"].get(fight.id, [])
            + streams["immortal"].get(fight.id, []),
            key=lambda event: float(event.get("timestamp") or 0),
        )
        for fight in chosen
    }
    drowned_damage = {
        fight.id: [
            event
            for event in streams["add_damage"].get(fight.id, [])
            if _event_actor_name(event, "target", actor_names)
            == DROWNED_ECHO_NAME
        ]
        for fight in chosen
    }
    sets = build_kill_squad_sets(
        report_code=report_code,
        fights=chosen,
        damage_taken_by_fight=damage_taken,
        exhaustion_by_fight=streams["auras"],
        drowned_damage_by_fight=drowned_damage,
        deaths_by_fight=streams["deaths"],
        actor_names=actor_names,
        actor_classes=actor_classes,
        actor_owners=actor_owners,
    )
    pyre_sets = build_pyre_sets(
        report_code=report_code,
        fights=chosen,
        casts_by_fight=streams["pyre_casts"],
        damage_taken_by_fight=streams["pyre_damage"],
        deaths_by_fight=streams["deaths"],
        actor_names=actor_names,
        actor_classes=actor_classes,
        aura_events_by_fight=streams["auras"],
        enemy_deaths_by_fight=streams["enemy_deaths"],
        vessel_damage_by_fight=streams["vessel_damage"],
    )
    essence_rend_sets = build_essence_rend_sets(
        report_code=report_code,
        fights=chosen,
        aura_events_by_fight=streams["auras"],
        dispels_by_fight=streams["essence_rend_dispels"],
        actor_names=actor_names,
        actor_classes=actor_classes,
    )
    add_damage_sets = build_add_damage_sets(
        report_code=report_code,
        fights=chosen,
        damage_by_fight=streams["add_damage"],
        actor_names=actor_names,
        actor_classes=actor_classes,
        actor_owners=actor_owners,
    )
    return NekZaliMechanicsSummary(
        report_code=report_code,
        fight_filter=fight_name,
        pull_count=len(chosen),
        views=[
            MechanicsReportView(
                id=KILL_SQUADS_VIEW_ID,
                label="Kill Squads",
                description=(
                    "Drowned Echo sets with every observed downstairs entrant and "
                    "their Soul Exhaustion state at entry."
                ),
                sets=sets,
            ),
            MechanicsReportView(
                id=PYRE_SOAKS_VIEW_ID,
                label="Pyre Soaks",
                description=(
                    "Every Hungering Pyre cast and the players hit while soaking it."
                ),
                sets=pyre_sets,
            ),
            MechanicsReportView(
                id=ESSENCE_REND_DISPELS_VIEW_ID,
                label="Essence Rend Dispels",
                description=(
                    "Every Essence Rend application wave, who dispelled each "
                    "target, and the exact dispel timing."
                ),
                sets=essence_rend_sets,
            ),
            MechanicsReportView(
                id=ADD_DAMAGE_VIEW_ID,
                label="Add Damage",
                description=(
                    "Restless Amani spawn waves and the Echoes of Jawae, with "
                    "owner-attributed player damage for each set."
                ),
                sets=add_damage_sets,
            ),
        ],
        pulls=build_report_pulls(report_code, chosen, {}),
        player_classes={
            name: actor_classes.get(actor_id)
            for actor_id, name in actor_names.items()
            if actor_classes.get(actor_id)
        },
        source_reports=[report_code],
    )


def _fetch_mechanics_event_streams(
    *,
    report_code: str,
    fights: Sequence[Fight],
    bearer: str,
    actor_names: Dict[int, str],
) -> Dict[str, Dict[int, List[Dict[str, Any]]]]:
    """Fetch independent mechanics streams concurrently using bounded API slots."""
    aura_ids = sorted(
        {
            SOUL_EXHAUSTION_ID,
            CREMATION_ID,
            ESSENCE_REND_ID,
            SLITHERING_FLAME_ID,
            *SOULCOILED_IDS,
        }
    )
    specifications: Dict[str, Dict[str, Any]] = {
        "grasp": {
            "data_type": "DamageTaken",
            "ability_id": GRASPING_DEPTHS_ID,
        },
        "add_damage": {
            "data_type": "DamageDone",
            "extra_filter": (
                'target.name in ("Drowned Echo","Restless Amani",'
                '"Echo of Jawae") and effectiveDamage > 1'
            ),
            "split_by_fight": True,
        },
        "immortal": {
            "data_type": "DamageTaken",
            "ability_id": IMMORTAL_COIL_ID,
        },
        "pyre_casts": {
            "data_type": "Casts",
            "ability_id": HUNGERING_PYRE_ID,
            "hostility_type": "Enemies",
        },
        "pyre_damage": {
            "data_type": "DamageTaken",
            "ability_id": HUNGERING_PYRE_ID,
        },
        "enemy_deaths": {
            "data_type": "Deaths",
            "hostility_type": "Enemies",
            "extra_filter": 'target.name = "Restless Amani"',
        },
        "vessel_damage": {
            "data_type": "DamageDone",
            "ability_id": VESSEL_OF_AWAKENING_ID,
            "hostility_type": "Enemies",
        },
        "essence_rend_dispels": {
            "data_type": "Dispels",
            "ability_id": ESSENCE_REND_ID,
        },
        "auras": {
            "data_type": "Debuffs",
            "extra_filter": (
                "ability.id in ("
                + ",".join(str(ability_id) for ability_id in aura_ids)
                + ")"
            ),
        },
        "deaths": {"data_type": "Deaths"},
    }

    def fetch(specification: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
        request_specification = {
            key: value
            for key, value in specification.items()
            if key != "split_by_fight"
        }
        if specification.get("split_by_fight") and len(fights) > 1:
            def fetch_fight(fight: Fight) -> Tuple[int, List[Dict[str, Any]]]:
                with requests.Session() as fight_session:
                    grouped = fetch_events_grouped(
                        fight_session,
                        bearer,
                        code=report_code,
                        fights=[fight],
                        limit=_EVENT_PAGE_LIMIT,
                        actor_names=actor_names,
                        **request_specification,
                    )
                return fight.id, grouped.get(fight.id, [])

            with ThreadPoolExecutor(
                max_workers=min(_EVENT_FETCH_WORKERS, len(fights))
            ) as fight_executor:
                return dict(fight_executor.map(fetch_fight, fights))
        with requests.Session() as stream_session:
            return fetch_events_grouped(
                stream_session,
                bearer,
                code=report_code,
                fights=fights,
                limit=_EVENT_PAGE_LIMIT,
                actor_names=actor_names,
                **request_specification,
            )

    with ThreadPoolExecutor(
        max_workers=min(_EVENT_FETCH_WORKERS, len(specifications))
    ) as executor:
        futures = {
            name: executor.submit(fetch, specification)
            for name, specification in specifications.items()
        }
        return {name: future.result() for name, future in futures.items()}


def fetch_nek_zali_mechanics_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = "mythic",
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> NekZaliMechanicsSummary:
    """Fetch one or more reports and merge their non-scoring mechanics views."""
    primary_code = _sanitize_report_code(report_code)
    report_codes = [primary_code]
    for candidate in extra_report_codes or ():
        try:
            normalized = _sanitize_report_code(candidate)
        except ValueError:
            continue
        if normalized not in report_codes:
            report_codes.append(normalized)

    summaries = [
        _fetch_single_summary(
            report_code=code,
            fight_name=fight_name or REPORT_DEFAULT_FIGHT,
            fight_ids=fight_ids,
            difficulty=difficulty,
            token=token,
            client_id=client_id,
            client_secret=client_secret,
        )
        for code in report_codes
    ]
    if len(summaries) == 1:
        return summaries[0]

    merged_sets_by_view = {
        view.id: [
            mechanic_set
            for summary in summaries
            for candidate_view in summary.views
            if candidate_view.id == view.id
            for mechanic_set in candidate_view.sets
        ]
        for view in summaries[0].views
    }
    player_classes: Dict[str, Optional[str]] = {}
    for summary in summaries:
        player_classes.update(summary.player_classes)
    return NekZaliMechanicsSummary(
        report_code=primary_code,
        fight_filter=fight_name or REPORT_DEFAULT_FIGHT,
        pull_count=sum(summary.pull_count for summary in summaries),
        views=[
            MechanicsReportView(
                id=view.id,
                label=view.label,
                description=view.description,
                sets=merged_sets_by_view[view.id],
            )
            for view in summaries[0].views
        ],
        pulls=merge_report_pulls([summary.pulls for summary in summaries]),
        player_classes=player_classes,
        source_reports=report_codes,
    )


__all__ = [
    "ADD_DAMAGE_VIEW_ID",
    "AddDamageSet",
    "CREMATION_ID",
    "CremationCarrier",
    "ESSENCE_REND_DISPELS_VIEW_ID",
    "ESSENCE_REND_ID",
    "EssenceRendApplication",
    "EssenceRendSet",
    "HUNGERING_PYRE_ID",
    "KILL_SQUADS_VIEW_ID",
    "PYRE_SOAKS_VIEW_ID",
    "PyreCorpseMiss",
    "KillSquadEntrant",
    "KillSquadDamageContribution",
    "KillSquadSet",
    "PyreSet",
    "PyreSoaker",
    "MechanicsReportView",
    "NekZaliMechanicsSummary",
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "SOULCOILED_IDS",
    "SLITHERING_FLAME_ID",
    "VESSEL_OF_AWAKENING_ID",
    "build_kill_squad_sets",
    "build_add_damage_sets",
    "build_pyre_sets",
    "build_essence_rend_sets",
    "fetch_nek_zali_mechanics_summary",
]
