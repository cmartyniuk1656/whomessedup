"""Heroic The Twin Fangs avoidable Eternal Venom application report."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Set

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
    compute_death_cutoffs,
    compute_fight_duration_ms,
)

REPORT_DEFAULT_FIGHT = "The Twin Fangs"

ETERNAL_VENOM_AURA_ID = 1290336
LETHAL_STACK_THRESHOLD = 10
CAUSTIC_GLOBULE_ID = 1289201
CAUSTIC_GLOBULE_RUPTURE_ID = 1290338
CAUSTIC_DELUGE_SPLASH_ID = 1289994
CORROSIVE_SPIT_CAST_ID = 1291478
CORROSIVE_SPIT_DAMAGE_ID = 1293295
STIR_THE_DEPTHS_ID = 1292807
VILE_FLOOD_ID = 1294605
VENOMOUS_EMERGENCE_ID = 1308122
CAUSTIC_RAIN_ID = 1308841

CAUSE_LABELS = {
    CAUSTIC_GLOBULE_ID: "Caustic Globule",
    CAUSTIC_GLOBULE_RUPTURE_ID: "Unsoaked Caustic Globule",
    CAUSTIC_DELUGE_SPLASH_ID: "Caustic Deluge Splash",
    CORROSIVE_SPIT_DAMAGE_ID: "Corrosive Spit",
    STIR_THE_DEPTHS_ID: "Stir the Depths",
    VILE_FLOOD_ID: "Vile Flood",
    VENOMOUS_EMERGENCE_ID: "Venomous Emergence",
    CAUSTIC_RAIN_ID: "Caustic Rain",
}
RELEVANT_CAUSE_IDS = frozenset(CAUSE_LABELS)
EXACT_CAUSE_WINDOW_MS = 150.0
DELAYED_WAVE_WINDOW_MS = 1200.0


@dataclass(frozen=True)
class VenomApplicationClassification:
    mechanic_type: str
    mechanic_label: str
    reason: str


@dataclass
class TwinFangsFuckupEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    resulting_stack: int
    mechanic_type: str
    mechanic_label: str
    cause_ability_id: int
    cause_ability_label: str
    reason: str
    fatal_stack: bool
    corrosive_spit_target: Optional[str] = None
    pull_duration_ms: Optional[float] = None


@dataclass
class TwinFangsFuckupEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_fuckups: int
    fatal_stack_events: int
    corrosive_spit_collateral: int
    caustic_deluge_splashes: int
    stir_the_depths_hits: int
    vile_flood_hits: int
    fatal_globules: int
    fuckups_per_pull: float
    events: List[TwinFangsFuckupEvent] = field(default_factory=list)


@dataclass
class TwinFangsFuckupSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    lethal_stack_threshold: int
    total_fuckups: int
    fatal_stack_events: int
    corrosive_spit_collateral: int
    caustic_deluge_splashes: int
    stir_the_depths_hits: int
    vile_flood_hits: int
    fatal_globules: int
    entries: List[TwinFangsFuckupEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[TwinFangsFuckupEvent]]
    source_reports: List[str] = field(default_factory=list)

    @property
    def fuckups_per_pull(self) -> float:
        return self.total_fuckups / self.pull_count if self.pull_count else 0.0


def classify_eternal_venom_application(
    *,
    resulting_stack: int,
    cause_ability_id: Optional[int],
    player: str,
    corrosive_spit_target: Optional[str] = None,
) -> Optional[VenomApplicationClassification]:
    """Return a scored mistake only when the application has a player-owned cause."""
    if cause_ability_id == CAUSTIC_GLOBULE_ID:
        if resulting_stack < LETHAL_STACK_THRESHOLD:
            return None
        return VenomApplicationClassification(
            mechanic_type="fatal_globule",
            mechanic_label="Lethal Caustic Globule",
            reason=f"The required Globule soak raised Eternal Venom to the lethal {resulting_stack}-stack threshold.",
        )
    if cause_ability_id == CORROSIVE_SPIT_DAMAGE_ID:
        if not corrosive_spit_target or player == corrosive_spit_target:
            return None
        return VenomApplicationClassification(
            mechanic_type="corrosive_spit_collateral",
            mechanic_label="Corrosive Spit Collateral",
            reason=f"The line targeted {corrosive_spit_target}; {player} was an additional player struck.",
        )
    if cause_ability_id == CAUSTIC_DELUGE_SPLASH_ID:
        return VenomApplicationClassification(
            mechanic_type="caustic_deluge_splash",
            mechanic_label="Caustic Deluge Splash",
            reason="The player was within four yards of the Caustic Deluge target.",
        )
    if cause_ability_id == STIR_THE_DEPTHS_ID:
        return VenomApplicationClassification(
            mechanic_type="stir_the_depths",
            mechanic_label="Stir the Depths",
            reason="The player was struck by an avoidable venom wave.",
        )
    if cause_ability_id == VILE_FLOOD_ID:
        return VenomApplicationClassification(
            mechanic_type="vile_flood",
            mechanic_label="Vile Flood",
            reason="The player was struck by the avoidable sweeping beam.",
        )
    return None


def fetch_the_twin_fangs_fuckup_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> TwinFangsFuckupSummary:
    primary_code = _sanitize_report_code(report_code)
    normalized_fight_ids = [int(fight_id) for fight_id in fight_ids] if fight_ids else None
    primary = _fetch_single_summary(
        report_code=primary_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=normalized_fight_ids,
        difficulty=difficulty,
        ignore_after_deaths=ignore_after_deaths,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )
    extra_codes: List[str] = []
    for candidate in extra_report_codes or []:
        if not candidate:
            continue
        try:
            normalized = _sanitize_report_code(candidate)
        except ValueError:
            continue
        if normalized != primary_code and normalized not in extra_codes:
            extra_codes.append(normalized)
    if not extra_codes:
        return primary
    summaries = [primary]
    for code in extra_codes:
        summaries.append(
            _fetch_single_summary(
                report_code=code,
                fight_name=fight_name or REPORT_DEFAULT_FIGHT,
                fight_ids=normalized_fight_ids,
                difficulty=difficulty,
                ignore_after_deaths=ignore_after_deaths,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    return _merge_summaries(summaries)


def _fetch_single_summary(
    *,
    report_code: str,
    fight_name: str,
    fight_ids: Optional[List[int]],
    difficulty: Optional[str | int],
    ignore_after_deaths: Optional[int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> TwinFangsFuckupSummary:
    load_env()
    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    chosen_ids = [fight.id for fight in chosen]
    known_players = {
        name for actor_id, name in actor_names.items() if name and actor_classes.get(actor_id)
    }

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=chosen_ids)
    player_roles, player_specs = _infer_player_roles(aggregated_details)
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    participants_by_fight: Dict[int, Set[str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        for player, role in fight_roles.items():
            if player_roles.get(player) in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
        participants = {name for name in _players_from_details(details) if name in known_players}
        participants_by_fight[fight.id] = participants
        for player in participants:
            pulls_by_player[player] += 1

    death_limit = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    death_cutoffs = compute_death_cutoffs(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        actor_names=actor_names,
        max_deaths=death_limit,
    )
    player_classes = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name and name in known_players
    }
    pull_index_by_fight = {fight.id: index + 1 for index, fight in enumerate(chosen)}
    events_by_player: DefaultDict[str, List[TwinFangsFuckupEvent]] = defaultdict(list)

    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else float(fight.end)
        participants = participants_by_fight.get(fight.id, set())
        events = _collect_fight_events(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
            participants=participants,
            pull_index=pull_index_by_fight[fight.id],
        )
        for event in events:
            events_by_player[event.player].append(event)

    players = set(pulls_by_player) | set(events_by_player)
    entries = _build_entries(
        players=players,
        events_by_player=events_by_player,
        pulls_by_player=pulls_by_player,
        player_roles=player_roles,
        player_classes=player_classes,
    )
    totals = _summarize(entries)
    return TwinFangsFuckupSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=list(fight_ids) if fight_ids else None,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        lethal_stack_threshold=LETHAL_STACK_THRESHOLD,
        total_fuckups=totals["total"],
        fatal_stack_events=totals["fatal"],
        corrosive_spit_collateral=totals["spit"],
        caustic_deluge_splashes=totals["deluge"],
        stir_the_depths_hits=totals["wave"],
        vile_flood_hits=totals["flood"],
        fatal_globules=totals["globule"],
        entries=entries,
        player_classes={player: player_classes.get(player) for player in players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players},
        player_specs={player: player_specs.get(player) for player in players},
        player_events={entry.player: entry.events for entry in entries},
        source_reports=[report_code],
    )


def _collect_fight_events(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
    pull_index: int,
) -> List[TwinFangsFuckupEvent]:
    damage_events = [
        event
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="DamageTaken",
            start=fight.start,
            end=event_end,
            limit=5000,
            actor_names=actor_names,
        )
        if _ability_id(event) in RELEVANT_CAUSE_IDS and _event_timestamp(event) is not None
    ]
    applications = [
        event
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=event_end,
            limit=5000,
            ability_id=ETERNAL_VENOM_AURA_ID,
            actor_names=actor_names,
        )
        if str(event.get("type") or "").lower() in {"applydebuff", "applydebuffstack"}
    ]
    spit_casts = [
        event
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="All",
            start=fight.start,
            end=event_end,
            limit=5000,
            ability_id=CORROSIVE_SPIT_CAST_ID,
            actor_names=actor_names,
        )
        if str(event.get("type") or "").lower() == "cast" and _event_timestamp(event) is not None
    ]
    damage_by_player: DefaultDict[str, List[dict]] = defaultdict(list)
    for event in damage_events:
        player = _target_player_name(event)
        if player:
            damage_by_player[player].append(event)
    spit_targets = _build_spit_target_lookup(spit_casts)
    pull_duration_ms = compute_fight_duration_ms(fight)
    scored: List[TwinFangsFuckupEvent] = []

    for application in applications:
        player = _target_player_name(application)
        timestamp = _event_timestamp(application)
        if not _is_player_in_scope(player, known_players, participants) or timestamp is None:
            continue
        cause = _match_cause(timestamp, damage_by_player.get(player, []))
        cause_id = _ability_id(cause) if cause else None
        spit_target = _spit_target_for_event(cause, spit_targets) if cause_id == CORROSIVE_SPIT_DAMAGE_ID else None
        resulting_stack = _resulting_stack(application)
        classification = classify_eternal_venom_application(
            resulting_stack=resulting_stack,
            cause_ability_id=cause_id,
            player=player,
            corrosive_spit_target=spit_target,
        )
        if classification is None or cause_id is None:
            continue
        scored.append(
            TwinFangsFuckupEvent(
                source_report_code=report_code,
                player=player,
                fight_id=fight.id,
                fight_name=fight.name or "",
                pull_index=pull_index,
                timestamp=timestamp,
                offset_ms=timestamp - float(fight.start),
                resulting_stack=resulting_stack,
                mechanic_type=classification.mechanic_type,
                mechanic_label=classification.mechanic_label,
                cause_ability_id=cause_id,
                cause_ability_label=CAUSE_LABELS[cause_id],
                reason=classification.reason,
                fatal_stack=resulting_stack >= LETHAL_STACK_THRESHOLD,
                corrosive_spit_target=spit_target,
                pull_duration_ms=pull_duration_ms,
            )
        )
    return scored


def _match_cause(timestamp: float, events: List[dict]) -> Optional[dict]:
    exact = [
        event
        for event in events
        if abs((_event_timestamp(event) or 0.0) - timestamp) <= EXACT_CAUSE_WINDOW_MS
    ]
    if exact:
        return min(exact, key=lambda event: abs((_event_timestamp(event) or 0.0) - timestamp))
    delayed_waves = [
        event
        for event in events
        if _ability_id(event) == STIR_THE_DEPTHS_ID
        and 0.0 <= (_event_timestamp(event) or 0.0) - timestamp <= DELAYED_WAVE_WINDOW_MS
    ]
    if delayed_waves:
        return min(delayed_waves, key=lambda event: (_event_timestamp(event) or 0.0) - timestamp)
    return None


def _build_spit_target_lookup(casts: List[dict]) -> Dict[int, List[tuple[float, str]]]:
    lookup: DefaultDict[int, List[tuple[float, str]]] = defaultdict(list)
    for event in casts:
        instance = _source_instance(event)
        timestamp = _event_timestamp(event)
        target = _target_player_name(event)
        if instance is not None and timestamp is not None and target:
            lookup[instance].append((timestamp, target))
    return {instance: sorted(rows) for instance, rows in lookup.items()}


def _spit_target_for_event(event: Optional[dict], lookup: Dict[int, List[tuple[float, str]]]) -> Optional[str]:
    if not event:
        return None
    instance = _source_instance(event)
    timestamp = _event_timestamp(event)
    if instance is None or timestamp is None:
        return None
    candidates = [row for row in lookup.get(instance, []) if -100.0 <= timestamp - row[0] <= 2000.0]
    return max(candidates, default=(0.0, None), key=lambda row: row[0])[1]


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[TwinFangsFuckupEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[TwinFangsFuckupEntry]:
    entries: List[TwinFangsFuckupEntry] = []
    for player in sorted(
        players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -len(events_by_player.get(name, [])),
            name.lower(),
        ),
    ):
        events = sorted(events_by_player.get(player, []), key=lambda item: (item.source_report_code or "", item.timestamp))
        pulls = pulls_by_player.get(player, 0) or 1
        counts = defaultdict(int)
        for event in events:
            counts[event.mechanic_type] += 1
        entries.append(
            TwinFangsFuckupEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_fuckups=len(events),
                fatal_stack_events=sum(1 for event in events if event.fatal_stack),
                corrosive_spit_collateral=counts["corrosive_spit_collateral"],
                caustic_deluge_splashes=counts["caustic_deluge_splash"],
                stir_the_depths_hits=counts["stir_the_depths"],
                vile_flood_hits=counts["vile_flood"],
                fatal_globules=counts["fatal_globule"],
                fuckups_per_pull=len(events) / pulls if pulls else 0.0,
                events=events,
            )
        )
    return entries


def _merge_summaries(summaries: List[TwinFangsFuckupSummary]) -> TwinFangsFuckupSummary:
    primary = summaries[0]
    classes: Dict[str, Optional[str]] = {}
    roles: Dict[str, str] = {}
    specs: Dict[str, Optional[str]] = {}
    pulls: DefaultDict[str, int] = defaultdict(int)
    events: DefaultDict[str, List[TwinFangsFuckupEvent]] = defaultdict(list)
    source_reports: List[str] = []
    for summary in summaries:
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for player, class_name in summary.player_classes.items():
            if player not in classes or classes[player] is None:
                classes[player] = class_name
        for player, role in summary.player_roles.items():
            if roles.get(player) in (None, ROLE_UNKNOWN):
                roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if player not in specs or specs[player] is None:
                specs[player] = spec
        for entry in summary.entries:
            pulls[entry.player] += entry.pulls
            events[entry.player].extend(entry.events)
    players = set(pulls) | set(events)
    entries = _build_entries(
        players=players,
        events_by_player=events,
        pulls_by_player=pulls,
        player_roles=roles,
        player_classes=classes,
    )
    totals = _summarize(entries)
    return TwinFangsFuckupSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=sum(summary.pull_count for summary in summaries),
        ignore_after_deaths=primary.ignore_after_deaths,
        lethal_stack_threshold=LETHAL_STACK_THRESHOLD,
        total_fuckups=totals["total"],
        fatal_stack_events=totals["fatal"],
        corrosive_spit_collateral=totals["spit"],
        caustic_deluge_splashes=totals["deluge"],
        stir_the_depths_hits=totals["wave"],
        vile_flood_hits=totals["flood"],
        fatal_globules=totals["globule"],
        entries=entries,
        player_classes=classes,
        player_roles=roles,
        player_specs=specs,
        player_events={entry.player: entry.events for entry in entries},
        source_reports=source_reports,
    )


def _summarize(entries: List[TwinFangsFuckupEntry]) -> Dict[str, int]:
    return {
        "total": sum(entry.total_fuckups for entry in entries),
        "fatal": sum(entry.fatal_stack_events for entry in entries),
        "spit": sum(entry.corrosive_spit_collateral for entry in entries),
        "deluge": sum(entry.caustic_deluge_splashes for entry in entries),
        "wave": sum(entry.stir_the_depths_hits for entry in entries),
        "flood": sum(entry.vile_flood_hits for entry in entries),
        "globule": sum(entry.fatal_globules for entry in entries),
    }


def _target_player_name(event: dict) -> Optional[str]:
    target_name = event.get("targetName")
    if target_name:
        return str(target_name)
    target = event.get("target")
    if isinstance(target, dict) and target.get("name"):
        return str(target["name"])
    return None


def _is_player_in_scope(player: Optional[str], known_players: Set[str], participants: Set[str]) -> bool:
    return bool(player and player in known_players and (not participants or player in participants))


def _event_timestamp(event: dict) -> Optional[float]:
    try:
        return float(event.get("timestamp"))
    except (TypeError, ValueError):
        return None


def _ability_id(event: Optional[dict]) -> Optional[int]:
    if not event:
        return None
    raw = event.get("abilityGameID")
    if raw is None and isinstance(event.get("ability"), dict):
        raw = event["ability"].get("id")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _source_instance(event: dict) -> Optional[int]:
    try:
        return int(event.get("sourceInstance"))
    except (TypeError, ValueError):
        return None


def _resulting_stack(event: dict) -> int:
    try:
        return max(1, int(event.get("stack") or 1))
    except (TypeError, ValueError):
        return 1


__all__ = [
    "LETHAL_STACK_THRESHOLD",
    "TwinFangsFuckupEntry",
    "TwinFangsFuckupEvent",
    "TwinFangsFuckupSummary",
    "VenomApplicationClassification",
    "classify_eternal_venom_application",
    "fetch_the_twin_fangs_fuckup_summary",
]
