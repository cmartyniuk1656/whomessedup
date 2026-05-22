"""
Belo'ren Light/Void wrong-Feather event report.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, Iterable, List, Optional, Set

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .beloren_child_of_alar_mechanics import (
    ERUPTION_REQUIRED_FEATHER,
    ERUPTION_WRONG_FEATHER,
    LIGHT_ERUPTION_ID,
    VOID_ERUPTION_ID,
    ability_id_from_event,
    ability_label,
    active_feather_at,
    collect_feather_timelines,
    collect_flame_penalty_applications,
    collect_quill_assignments,
    collect_quill_damage_classifications,
    collect_rupture_mistake_classifications,
    damage_amount_from_event,
    event_timestamp,
    extra_ability_id_from_event,
    feather_label,
    source_name_from_event,
    target_name_from_event,
)
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

REPORT_DEFAULT_FIGHT = "Belo'ren, Child of Al'ar"

MECHANIC_QUILL = "quill"
MECHANIC_FLAMES = "flames"
MECHANIC_RUPTURE = "rupture"
MECHANIC_ERUPTION = "eruption"

INTERRUPT_ABILITY_LABELS: Dict[int, str] = {
    1766: "Kick",
    2139: "Counterspell",
    47528: "Mind Freeze",
    57994: "Wind Shear",
    6552: "Pummel",
    93985: "Skull Bash",
    96231: "Rebuke",
    97547: "Solar Beam",
    147362: "Counter Shot",
    183752: "Disrupt",
    351338: "Quell",
}

@dataclass
class BelorenLightVoidMistakeEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    timestamp: float
    offset_ms: float
    mechanic_type: str
    mechanic_label: str
    ability_id: int
    ability_label: str
    expected_feather_id: int
    expected_feather_label: str
    actual_feather_id: int
    actual_feather_label: str
    target: Optional[str] = None
    assigned_target: Optional[str] = None
    damage_amount: Optional[float] = None
    interrupt_ability_id: Optional[int] = None
    interrupt_ability_label: Optional[str] = None
    pull_duration_ms: Optional[float] = None


@dataclass
class BelorenLightVoidMistakeEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_mistakes: int
    quill_mistakes: int
    flame_mistakes: int
    rupture_mistakes: int
    eruption_mistakes: int
    mistakes_per_pull: float
    events: List[BelorenLightVoidMistakeEvent] = field(default_factory=list)


@dataclass
class BelorenLightVoidMistakeSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    ignore_after_deaths: Optional[int]
    total_mistakes: int
    quill_mistakes: int
    flame_mistakes: int
    rupture_mistakes: int
    eruption_mistakes: int
    entries: List[BelorenLightVoidMistakeEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[BelorenLightVoidMistakeEvent]]
    source_reports: List[str] = field(default_factory=list)

    @property
    def mistakes_per_pull(self) -> float:
        if not self.pull_count:
            return 0.0
        return self.total_mistakes / self.pull_count


def fetch_beloren_child_of_alar_light_void_mistake_summary(
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
) -> BelorenLightVoidMistakeSummary:
    primary_code = _sanitize_report_code(report_code)
    primary_summary = _fetch_single_beloren_light_void_mistake_summary(
        report_code=primary_code,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        ignore_after_deaths=ignore_after_deaths,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
    )

    extra_codes: List[str] = []
    if extra_report_codes:
        for candidate in extra_report_codes:
            if not candidate:
                continue
            try:
                normalized = _sanitize_report_code(candidate)
            except ValueError:
                continue
            if normalized == primary_code or normalized in extra_codes:
                continue
            extra_codes.append(normalized)
    if not extra_codes:
        return primary_summary

    summaries = [primary_summary]
    for code in extra_codes:
        summaries.append(
            _fetch_single_beloren_light_void_mistake_summary(
                report_code=code,
                fight_name=fight_name or REPORT_DEFAULT_FIGHT,
                fight_ids=fight_ids,
                difficulty=difficulty,
                ignore_after_deaths=ignore_after_deaths,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    return _merge_beloren_light_void_mistake_summaries(summaries)


def _fetch_single_beloren_light_void_mistake_summary(
    *,
    report_code: str,
    fight_name: Optional[str],
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    ignore_after_deaths: Optional[int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> BelorenLightVoidMistakeSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, _ = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    fight_id_list = [fight.id for fight in chosen]
    known_players = {
        name
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles, player_specs = _infer_player_roles(aggregated_details)

    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    participants_by_fight: Dict[int, Set[str]] = {}
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        participants = {name for name in _players_from_details(details) if name in known_players}
        participants_by_fight[fight.id] = participants
        for name in participants:
            pulls_by_player[name] += 1
    for fight_roles in roles_by_fight.values():
        for player, role in fight_roles.items():
            if player not in player_roles or player_roles[player] in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN

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
    events_by_player: DefaultDict[str, List[BelorenLightVoidMistakeEvent]] = defaultdict(list)

    for fight in chosen:
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else fight.end
        pull_duration_ms = compute_fight_duration_ms(fight)
        participants = participants_by_fight.get(fight.id, set())
        feather_timelines = collect_feather_timelines(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            event_end=event_end,
        )
        quill_assignments = collect_quill_assignments(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            event_end=event_end,
        )
        for event_model in _collect_flame_mistakes(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
            participants=participants,
            feather_timelines=feather_timelines,
            pull_index=pull_index_by_fight.get(fight.id, 0),
            pull_duration_ms=pull_duration_ms,
        ):
            events_by_player[event_model.player].append(event_model)
        for event_model in _collect_quill_mistakes(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
            participants=participants,
            feather_timelines=feather_timelines,
            quill_assignments=quill_assignments,
            pull_index=pull_index_by_fight.get(fight.id, 0),
            pull_duration_ms=pull_duration_ms,
        ):
            events_by_player[event_model.player].append(event_model)
        for event_model in _collect_rupture_mistakes(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
            participants=participants,
            feather_timelines=feather_timelines,
            pull_index=pull_index_by_fight.get(fight.id, 0),
            pull_duration_ms=pull_duration_ms,
        ):
            events_by_player[event_model.player].append(event_model)
        for event_model in _collect_eruption_mistakes(
            session=session,
            bearer=bearer,
            report_code=report_code,
            fight=fight,
            event_end=event_end,
            actor_names=actor_names,
            known_players=known_players,
            participants=participants,
            feather_timelines=feather_timelines,
            pull_index=pull_index_by_fight.get(fight.id, 0),
            pull_duration_ms=pull_duration_ms,
        ):
            events_by_player[event_model.player].append(event_model)

    players = set(events_by_player.keys())
    entries = _build_entries(
        players=players,
        events_by_player=events_by_player,
        pulls_by_player=pulls_by_player,
        player_roles=player_roles,
        player_classes=player_classes,
    )
    totals = _summarize_totals(entries)

    return BelorenLightVoidMistakeSummary(
        report_code=report_code,
        fight_filter=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        total_mistakes=totals["total"],
        quill_mistakes=totals["quill"],
        flame_mistakes=totals["flames"],
        rupture_mistakes=totals["rupture"],
        eruption_mistakes=totals["eruption"],
        entries=entries,
        player_classes={player: player_classes.get(player) for player in players},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players},
        player_specs={player: player_specs.get(player) for player in players},
        player_events={entry.player: entry.events for entry in entries},
        source_reports=[report_code],
    )


def _collect_flame_mistakes(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
    feather_timelines: Dict[str, List[tuple]],
    pull_index: int,
    pull_duration_ms: Optional[float],
) -> List[BelorenLightVoidMistakeEvent]:
    mistakes: List[BelorenLightVoidMistakeEvent] = []
    applications = collect_flame_penalty_applications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
    )
    for application in applications:
        mistakes.append(
            _build_mistake_event(
                source_report_code=report_code,
                player=application.player,
                fight=fight,
                pull_index=pull_index,
                timestamp=application.timestamp,
                mechanic_type=MECHANIC_FLAMES,
                mechanic_label="Wrong Flames Color",
                ability_id=application.ability_id,
                expected_feather_id=application.expected_feather_id,
                actual_feather_id=application.actual_feather_id,
                target=application.player,
                pull_duration_ms=pull_duration_ms,
            )
        )
    return mistakes


def _collect_quill_mistakes(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
    feather_timelines: Dict[str, List[tuple]],
    quill_assignments: Dict[int, List[tuple]],
    pull_index: int,
    pull_duration_ms: Optional[float],
) -> List[BelorenLightVoidMistakeEvent]:
    mistakes: List[BelorenLightVoidMistakeEvent] = []
    classifications = collect_quill_damage_classifications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
        quill_assignments=quill_assignments,
    )
    for classification in sorted(classifications.values(), key=lambda item: (item.timestamp, item.ability_id, item.player)):
        mistakes.append(
            _build_mistake_event(
                source_report_code=report_code,
                player=classification.player,
                fight=fight,
                pull_index=pull_index,
                timestamp=classification.timestamp,
                mechanic_type=MECHANIC_QUILL,
                mechanic_label=classification.mistake_label,
                ability_id=classification.ability_id,
                expected_feather_id=classification.expected_feather_id,
                actual_feather_id=classification.actual_feather_id,
                target=classification.player,
                assigned_target=classification.assigned_target,
                damage_amount=classification.damage_amount,
                pull_duration_ms=pull_duration_ms,
            )
        )
    return mistakes


def _collect_rupture_mistakes(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
    feather_timelines: Dict[str, List[tuple]],
    pull_index: int,
    pull_duration_ms: Optional[float],
) -> List[BelorenLightVoidMistakeEvent]:
    mistakes: List[BelorenLightVoidMistakeEvent] = []
    classifications = collect_rupture_mistake_classifications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
    )
    for classification in classifications:
        mistakes.append(
            _build_mistake_event(
                source_report_code=report_code,
                player=classification.player,
                fight=fight,
                pull_index=pull_index,
                timestamp=classification.timestamp,
                mechanic_type=MECHANIC_RUPTURE,
                mechanic_label="Wrong Orb Soak",
                ability_id=classification.ability_id,
                expected_feather_id=classification.expected_feather_id,
                actual_feather_id=classification.actual_feather_id,
                target=classification.player,
                damage_amount=classification.damage_amount,
                pull_duration_ms=pull_duration_ms,
            )
        )
    return mistakes


def _collect_eruption_mistakes(
    *,
    session: requests.Session,
    bearer: str,
    report_code: str,
    fight: Fight,
    event_end: float,
    actor_names: Dict[int, str],
    known_players: Set[str],
    participants: Set[str],
    feather_timelines: Dict[str, List[tuple]],
    pull_index: int,
    pull_duration_ms: Optional[float],
) -> List[BelorenLightVoidMistakeEvent]:
    mistakes: List[BelorenLightVoidMistakeEvent] = []
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Interrupts",
        start=fight.start,
        end=event_end,
        limit=5000,
        actor_names=actor_names,
    ):
        if str(event.get("type") or "").lower() != "interrupt":
            continue
        interrupted_ability_id = extra_ability_id_from_event(event)
        if interrupted_ability_id not in (LIGHT_ERUPTION_ID, VOID_ERUPTION_ID):
            continue
        timestamp = event_timestamp(event)
        player = source_name_from_event(event)
        if timestamp is None or not _is_player_in_scope(player, known_players, participants):
            continue
        actual_feather_id = active_feather_at(feather_timelines.get(player, []), timestamp)
        wrong_feather_id = ERUPTION_WRONG_FEATHER.get(interrupted_ability_id)
        if actual_feather_id != wrong_feather_id:
            continue
        interrupt_ability_id = ability_id_from_event(event)
        mistakes.append(
            _build_mistake_event(
                source_report_code=report_code,
                player=player,
                fight=fight,
                pull_index=pull_index,
                timestamp=timestamp,
                mechanic_type=MECHANIC_ERUPTION,
                mechanic_label="Wrong Eruption Interrupt",
                ability_id=interrupted_ability_id,
                expected_feather_id=ERUPTION_REQUIRED_FEATHER[interrupted_ability_id],
                actual_feather_id=actual_feather_id,
                target=target_name_from_event(event),
                interrupt_ability_id=interrupt_ability_id,
                interrupt_ability_label=_interrupt_ability_label(interrupt_ability_id),
                pull_duration_ms=pull_duration_ms,
            )
        )
    return mistakes


def _build_mistake_event(
    *,
    source_report_code: str,
    player: str,
    fight: Fight,
    pull_index: int,
    timestamp: float,
    mechanic_type: str,
    mechanic_label: str,
    ability_id: int,
    expected_feather_id: int,
    actual_feather_id: int,
    target: Optional[str] = None,
    assigned_target: Optional[str] = None,
    damage_amount: Optional[float] = None,
    interrupt_ability_id: Optional[int] = None,
    interrupt_ability_label: Optional[str] = None,
    pull_duration_ms: Optional[float] = None,
) -> BelorenLightVoidMistakeEvent:
    return BelorenLightVoidMistakeEvent(
        source_report_code=source_report_code,
        player=player,
        fight_id=fight.id,
        fight_name=fight.name or "",
        pull_index=pull_index,
        timestamp=timestamp,
        offset_ms=timestamp - float(fight.start),
        mechanic_type=mechanic_type,
        mechanic_label=mechanic_label,
        ability_id=ability_id,
        ability_label=ability_label(ability_id),
        expected_feather_id=expected_feather_id,
        expected_feather_label=feather_label(expected_feather_id),
        actual_feather_id=actual_feather_id,
        actual_feather_label=feather_label(actual_feather_id),
        target=target,
        assigned_target=assigned_target,
        damage_amount=damage_amount,
        interrupt_ability_id=interrupt_ability_id,
        interrupt_ability_label=interrupt_ability_label,
        pull_duration_ms=pull_duration_ms,
    )


def _is_player_in_scope(player: Optional[str], known_players: Set[str], participants: Set[str]) -> bool:
    if not player or player not in known_players:
        return False
    return not participants or player in participants


def _build_entries(
    *,
    players: Set[str],
    events_by_player: Dict[str, List[BelorenLightVoidMistakeEvent]],
    pulls_by_player: Dict[str, int],
    player_roles: Dict[str, str],
    player_classes: Dict[str, Optional[str]],
) -> List[BelorenLightVoidMistakeEntry]:
    entries: List[BelorenLightVoidMistakeEntry] = []
    for player in sorted(
        players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            -len(events_by_player.get(name, [])),
            name.lower(),
        ),
    ):
        events = sorted(events_by_player.get(player, []), key=lambda item: (item.source_report_code or "", item.timestamp))
        total = len(events)
        if total <= 0:
            continue
        pulls = pulls_by_player.get(player, 0) or 1
        quill = sum(1 for event in events if event.mechanic_type == MECHANIC_QUILL)
        flames = sum(1 for event in events if event.mechanic_type == MECHANIC_FLAMES)
        rupture = sum(1 for event in events if event.mechanic_type == MECHANIC_RUPTURE)
        eruption = sum(1 for event in events if event.mechanic_type == MECHANIC_ERUPTION)
        entries.append(
            BelorenLightVoidMistakeEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_mistakes=total,
                quill_mistakes=quill,
                flame_mistakes=flames,
                rupture_mistakes=rupture,
                eruption_mistakes=eruption,
                mistakes_per_pull=total / pulls if pulls else 0.0,
                events=events,
            )
        )
    return entries


def _merge_beloren_light_void_mistake_summaries(
    summaries: List[BelorenLightVoidMistakeSummary],
) -> BelorenLightVoidMistakeSummary:
    primary = summaries[0]
    combined_player_classes: Dict[str, Optional[str]] = {}
    combined_player_roles: Dict[str, str] = {}
    combined_player_specs: Dict[str, Optional[str]] = {}
    combined_pulls: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[BelorenLightVoidMistakeEvent]] = defaultdict(list)
    source_reports: List[str] = []
    pull_count = 0

    for summary in summaries:
        pull_count += summary.pull_count
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for player, class_name in summary.player_classes.items():
            if player not in combined_player_classes or combined_player_classes[player] is None:
                combined_player_classes[player] = class_name
        for player, role in summary.player_roles.items():
            current_role = combined_player_roles.get(player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if player not in combined_player_specs or combined_player_specs[player] is None:
                combined_player_specs[player] = spec
        for entry in summary.entries:
            combined_pulls[entry.player] += entry.pulls
            combined_events[entry.player].extend(entry.events)
            if combined_player_classes.get(entry.player) is None:
                combined_player_classes[entry.player] = entry.class_name
            current_role = combined_player_roles.get(entry.player)
            if current_role in (None, ROLE_UNKNOWN):
                combined_player_roles[entry.player] = entry.role or ROLE_UNKNOWN

    players = set(combined_events.keys())
    entries = _build_entries(
        players=players,
        events_by_player=combined_events,
        pulls_by_player=combined_pulls,
        player_roles=combined_player_roles,
        player_classes=combined_player_classes,
    )
    totals = _summarize_totals(entries)

    return BelorenLightVoidMistakeSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=pull_count,
        ignore_after_deaths=primary.ignore_after_deaths,
        total_mistakes=totals["total"],
        quill_mistakes=totals["quill"],
        flame_mistakes=totals["flames"],
        rupture_mistakes=totals["rupture"],
        eruption_mistakes=totals["eruption"],
        entries=entries,
        player_classes=combined_player_classes,
        player_roles=combined_player_roles,
        player_specs=combined_player_specs,
        player_events={entry.player: entry.events for entry in entries},
        source_reports=source_reports,
    )


def _summarize_totals(entries: List[BelorenLightVoidMistakeEntry]) -> Dict[str, int]:
    return {
        "total": sum(entry.total_mistakes for entry in entries),
        "quill": sum(entry.quill_mistakes for entry in entries),
        "flames": sum(entry.flame_mistakes for entry in entries),
        "rupture": sum(entry.rupture_mistakes for entry in entries),
        "eruption": sum(entry.eruption_mistakes for entry in entries),
    }


def _interrupt_ability_label(ability_id: Optional[int]) -> Optional[str]:
    if ability_id is None:
        return None
    return INTERRUPT_ABILITY_LABELS.get(ability_id, f"Interrupt #{ability_id}")


__all__ = [
    "BelorenLightVoidMistakeEntry",
    "BelorenLightVoidMistakeEvent",
    "BelorenLightVoidMistakeSummary",
    "REPORT_DEFAULT_FIGHT",
    "fetch_beloren_child_of_alar_light_void_mistake_summary",
]
