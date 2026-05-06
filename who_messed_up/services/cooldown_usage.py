"""
Shared cooldown-usage report helpers.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

import requests

from ..api import REPORT_OVERVIEW_QUERY, fetch_events, fetch_fights, fetch_player_details, gql
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_event_source_player,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
    compute_fight_duration_ms,
)


COOLDOWN_STATUS_CORRECT = "correct"
COOLDOWN_STATUS_INCORRECT = "incorrect"
COOLDOWN_STATUS_MISSED = "missed"
COOLDOWN_STATUS_IGNORED_DEAD = "ignored_dead"
COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH = "ignored_after_healer_death"
COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT = "ignored_after_death_count"
COOLDOWN_STATUS_IGNORED_MISSING_PHASE = "ignored_missing_phase"
COOLDOWN_STATUS_IGNORED_NOT_IN_PULL = "ignored_not_in_pull"
COOLDOWN_STATUS_IGNORED_AFTER_PULL_END = "ignored_after_pull_end"

ELIGIBLE_STATUSES = {
    COOLDOWN_STATUS_CORRECT,
    COOLDOWN_STATUS_INCORRECT,
    COOLDOWN_STATUS_MISSED,
}
IGNORED_STATUSES = {
    COOLDOWN_STATUS_IGNORED_DEAD,
    COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH,
    COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT,
    COOLDOWN_STATUS_IGNORED_MISSING_PHASE,
    COOLDOWN_STATUS_IGNORED_NOT_IN_PULL,
    COOLDOWN_STATUS_IGNORED_AFTER_PULL_END,
}

BATTLE_RESURRECTION_SPELL_IDS = {
    20484,  # Rebirth
    61999,  # Raise Ally
    20707,  # Soulstone
    391054,  # Intercession
}
STASIS_SPELL_IDS = {
    370537,  # Stasis (Store)
    370564,  # Stasis (Release)
}


@dataclass(frozen=True)
class CooldownReminderHeader:
    encounter_id: int
    difficulty: str
    name: Optional[str]
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CooldownReminderAssignment:
    line_number: int
    time_seconds: float
    phase: int
    player: str
    spell_id: int
    boss_spell_id: Optional[int] = None
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CooldownReminderPlan:
    header: CooldownReminderHeader
    assignments: List[CooldownReminderAssignment]


@dataclass(frozen=True)
class CooldownCastEvent:
    player: str
    spell_id: int
    timestamp: float
    offset_ms: float
    ability_label: Optional[str]
    target: Optional[str] = None


@dataclass(frozen=True)
class CooldownLifeEvent:
    timestamp: float
    event_type: str


@dataclass
class CooldownUsageEvent:
    source_report_code: Optional[str]
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    pull_view_id: str
    status: str
    line_number: int
    spell_id: int
    ability_label: Optional[str]
    scheduled_timestamp: Optional[float]
    scheduled_offset_ms: Optional[float]
    phase: int
    phase_time_seconds: float
    actual_timestamp: Optional[float] = None
    actual_offset_ms: Optional[float] = None
    delta_seconds: Optional[float] = None
    boss_spell_id: Optional[int] = None
    boss_ability_label: Optional[str] = None
    ignore_reason: Optional[str] = None
    pull_duration_ms: Optional[float] = None
    intended_target: Optional[str] = None
    actual_target: Optional[str] = None
    target_was_alive: Optional[bool] = None
    target_mismatch: bool = False


@dataclass
class CooldownUsageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    assignments: int
    correct: int
    incorrect: int
    missed: int
    ignored: int
    on_time_rate: float
    average_delta_seconds: Optional[float]
    events: List[CooldownUsageEvent] = field(default_factory=list)


@dataclass
class CooldownUsagePull:
    source_report_code: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    view_id: str
    label: str
    duration_ms: Optional[float]
    death_count_cutoff_timestamp: Optional[float] = None
    healer_death_cutoff_timestamp: Optional[float] = None


@dataclass
class CooldownUsageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    pull_count: int
    tolerance_seconds: float
    ignore_after_deaths: Optional[int]
    ignore_after_healer_death: bool
    ignore_stasis: bool
    plan: CooldownReminderPlan
    pulls: List[CooldownUsagePull]
    entries: List[CooldownUsageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[CooldownUsageEvent]]
    pulls_by_player: Dict[str, int]
    source_reports: List[str] = field(default_factory=list)

    @property
    def total_assignments(self) -> int:
        return sum(entry.assignments for entry in self.entries)

    @property
    def checked_assignments(self) -> int:
        return sum(entry.correct + entry.incorrect + entry.missed for entry in self.entries)

    @property
    def total_correct(self) -> int:
        return sum(entry.correct for entry in self.entries)

    @property
    def total_incorrect(self) -> int:
        return sum(entry.incorrect for entry in self.entries)

    @property
    def total_missed(self) -> int:
        return sum(entry.missed for entry in self.entries)

    @property
    def total_ignored(self) -> int:
        return sum(entry.ignored for entry in self.entries)

    @property
    def on_time_rate(self) -> float:
        checked = self.checked_assignments
        return self.total_correct / checked if checked else 0.0


def parse_nsrt_cooldown_reminders(text: str) -> CooldownReminderPlan:
    lines = [(index + 1, line.strip()) for index, line in enumerate(str(text or "").splitlines())]
    lines = [(line_number, line) for line_number, line in lines if line]
    if not lines:
        raise ValueError("Paste an NSRT cooldown reminder string.")

    header_line, header_text = lines[0]
    header_fields = _parse_nsrt_fields(header_text, line_number=header_line)
    encounter_id = _coerce_required_int(header_fields, "encounterid", line_number=header_line)
    difficulty = header_fields.get("difficulty", "").strip()
    if not difficulty:
        raise ValueError(f"Line {header_line}: Difficulty is required.")

    assignments: List[CooldownReminderAssignment] = []
    for line_number, line in lines[1:]:
        fields = _parse_nsrt_fields(line, line_number=line_number)
        assignments.append(
            CooldownReminderAssignment(
                line_number=line_number,
                time_seconds=_coerce_required_float(fields, "time", line_number=line_number),
                phase=_coerce_required_int(fields, "ph", line_number=line_number),
                player=_coerce_required_text(fields, "tag", line_number=line_number),
                spell_id=_coerce_required_int(fields, "spellid", line_number=line_number),
                boss_spell_id=_coerce_optional_int(fields.get("bossspell"), line_number=line_number, field_id="bossSpell"),
                fields=fields,
            )
        )

    if not assignments:
        raise ValueError("No cooldown assignments were found in the pasted reminder.")

    return CooldownReminderPlan(
        header=CooldownReminderHeader(
            encounter_id=encounter_id,
            difficulty=difficulty,
            name=header_fields.get("name"),
            fields=header_fields,
        ),
        assignments=assignments,
    )


def validate_cooldown_plan(
    plan: CooldownReminderPlan,
    *,
    expected_encounter_id: Optional[int],
    expected_difficulty: str,
) -> None:
    if expected_encounter_id is not None and int(plan.header.encounter_id) != int(expected_encounter_id):
        raise ValueError(
            f"This reminder is for EncounterID {plan.header.encounter_id}, but this report expects {expected_encounter_id}."
        )
    actual_difficulty = _normalize_difficulty_label(plan.header.difficulty)
    expected = _normalize_difficulty_label(expected_difficulty)
    if actual_difficulty != expected:
        raise ValueError(
            f"This reminder is for {plan.header.difficulty}, but this report only supports {expected_difficulty.title()}."
        )


def _filter_cooldown_plan(
    plan: CooldownReminderPlan,
    *,
    ignored_spell_ids: Set[int],
) -> CooldownReminderPlan:
    if not ignored_spell_ids:
        return plan
    ignored = {int(spell_id) for spell_id in ignored_spell_ids}
    assignments = [assignment for assignment in plan.assignments if int(assignment.spell_id) not in ignored]
    if len(assignments) == len(plan.assignments):
        return plan
    return CooldownReminderPlan(
        header=plan.header,
        assignments=assignments,
    )


def fetch_cooldown_usage_summary(
    *,
    report_code: str,
    reminder_text: str,
    expected_encounter_id: Optional[int] = None,
    expected_difficulty: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    tolerance_seconds: float = 7.5,
    ignore_after_deaths: Optional[int] = None,
    ignore_after_healer_death: bool = False,
    ignore_stasis: bool = True,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> CooldownUsageSummary:
    plan = parse_nsrt_cooldown_reminders(reminder_text)
    validate_cooldown_plan(
        plan,
        expected_encounter_id=expected_encounter_id,
        expected_difficulty=expected_difficulty,
    )
    if ignore_stasis:
        plan = _filter_cooldown_plan(plan, ignored_spell_ids=STASIS_SPELL_IDS)

    primary_code = _sanitize_report_code(report_code)
    normalized_tolerance = _normalize_tolerance_seconds(tolerance_seconds)
    primary_summary = _fetch_single_cooldown_usage_summary(
        report_code=primary_code,
        plan=plan,
        fight_name=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
        tolerance_seconds=normalized_tolerance,
        ignore_after_deaths=ignore_after_deaths,
        ignore_after_healer_death=ignore_after_healer_death,
        ignore_stasis=ignore_stasis,
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
            _fetch_single_cooldown_usage_summary(
                report_code=code,
                plan=plan,
                fight_name=fight_name,
                fight_ids=fight_ids,
                difficulty=difficulty,
                tolerance_seconds=normalized_tolerance,
                ignore_after_deaths=ignore_after_deaths,
                ignore_after_healer_death=ignore_after_healer_death,
                ignore_stasis=ignore_stasis,
                token=token,
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    return _merge_cooldown_usage_summaries(summaries)


def _fetch_single_cooldown_usage_summary(
    *,
    report_code: str,
    plan: CooldownReminderPlan,
    fight_name: Optional[str],
    fight_ids: Optional[Iterable[int]],
    difficulty: Optional[str | int],
    tolerance_seconds: float,
    ignore_after_deaths: Optional[int],
    ignore_after_healer_death: bool,
    ignore_stasis: bool,
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> CooldownUsageSummary:
    load_env()

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_ids, difficulty=difficulty)
    _validate_selected_fight_encounter(plan, chosen)
    fight_id_list = [fight.id for fight in chosen]

    note_players = _note_players(plan)
    player_lookup = _player_lookup_for_names(actor_names, note_players)
    target_player_lookup = _player_lookup_for_names(actor_names, [*note_players, *_assignment_target_players(plan)])
    player_classes = _player_classes_for_note_players(actor_names, actor_classes, note_players)

    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)
    roles_by_fight: Dict[int, Dict[str, str]] = {}
    participants_by_fight: Dict[int, Set[str]] = {}
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)

    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, fight_specs = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        for player, spec in fight_specs.items():
            if player not in player_specs_global or player_specs_global[player] is None:
                player_specs_global[player] = spec
        participants = {_normalize_player_name(name) for name in _players_from_details(details) if name}
        participants_by_fight[fight.id] = participants
        for player_key in participants:
            player = player_lookup.get(player_key)
            if player:
                pulls_by_player[player] += 1

    player_roles = _roles_for_note_players(note_players, player_roles_global, roles_by_fight)
    player_specs = {player: _lookup_by_normalized(player_specs_global, player) for player in note_players}

    ability_labels = _fetch_ability_labels(session, bearer, report_code)
    cast_events = _collect_cast_events(
        session,
        bearer,
        report_code=report_code,
        fights=chosen,
        actor_names=actor_names,
        actor_owners=actor_owners,
        spell_ids={assignment.spell_id for assignment in plan.assignments},
        note_player_lookup=player_lookup,
        ability_labels=ability_labels,
    )
    life_events_by_fight, death_count_cutoffs, healer_death_cutoffs = _collect_life_events_and_cutoffs(
        session,
        bearer,
        report_code=report_code,
        fights=chosen,
        actor_names=actor_names,
        participants_by_fight=participants_by_fight,
        roles_by_fight=roles_by_fight,
        player_roles_global=player_roles_global,
        watched_player_lookup=target_player_lookup,
        ignore_after_deaths=ignore_after_deaths,
        ignore_after_healer_death=ignore_after_healer_death,
    )

    pulls: List[CooldownUsagePull] = []
    events_by_player: DefaultDict[str, List[CooldownUsageEvent]] = defaultdict(list)

    for pull_index, fight in enumerate(chosen, start=1):
        view_id = _pull_view_id(report_code, fight.id)
        pull = CooldownUsagePull(
            source_report_code=report_code,
            fight_id=fight.id,
            fight_name=fight.name,
            pull_index=pull_index,
            view_id=view_id,
            label=f"Pull {pull_index}",
            duration_ms=compute_fight_duration_ms(fight),
            death_count_cutoff_timestamp=death_count_cutoffs.get(fight.id),
            healer_death_cutoff_timestamp=healer_death_cutoffs.get(fight.id),
        )
        pulls.append(pull)
        fight_events = _match_assignments_for_fight(
            report_code=report_code,
            fight=fight,
            pull=pull,
            plan=plan,
            note_player_lookup=player_lookup,
            target_player_lookup=target_player_lookup,
            participants=participants_by_fight.get(fight.id, set()),
            cast_events=cast_events,
            life_events=life_events_by_fight.get(fight.id, {}),
            ability_labels=ability_labels,
            tolerance_seconds=tolerance_seconds,
            death_count_cutoff=death_count_cutoffs.get(fight.id),
            healer_death_cutoff=healer_death_cutoffs.get(fight.id),
        )
        for event in fight_events:
            events_by_player[event.player].append(event)

    entries, player_events = _build_entries(
        note_players=note_players,
        events_by_player=events_by_player,
        player_classes=player_classes,
        player_roles=player_roles,
        pulls_by_player=dict(pulls_by_player),
    )

    return CooldownUsageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=[int(fid) for fid in fight_ids] if fight_ids else None,
        pull_count=len(chosen),
        tolerance_seconds=tolerance_seconds,
        ignore_after_deaths=ignore_after_deaths,
        ignore_after_healer_death=ignore_after_healer_death,
        ignore_stasis=ignore_stasis,
        plan=plan,
        pulls=pulls,
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        player_events=player_events,
        pulls_by_player=dict(pulls_by_player),
        source_reports=[report_code],
    )


def _match_assignments_for_fight(
    *,
    report_code: str,
    fight: Any,
    pull: CooldownUsagePull,
    plan: CooldownReminderPlan,
    note_player_lookup: Dict[str, str],
    target_player_lookup: Dict[str, str],
    participants: Set[str],
    cast_events: Dict[Tuple[int, str, int], List[CooldownCastEvent]],
    life_events: Dict[str, List[CooldownLifeEvent]],
    ability_labels: Dict[int, str],
    tolerance_seconds: float,
    death_count_cutoff: Optional[float],
    healer_death_cutoff: Optional[float],
) -> List[CooldownUsageEvent]:
    grouped: DefaultDict[Tuple[str, int], List[Tuple[CooldownReminderAssignment, float]]] = defaultdict(list)
    events: List[CooldownUsageEvent] = []

    for assignment in sorted(plan.assignments, key=lambda item: (item.player.lower(), item.spell_id, item.time_seconds, item.line_number)):
        player_key = _normalize_player_name(assignment.player)
        player = note_player_lookup.get(player_key, assignment.player)
        phase_start = _phase_start_timestamp(fight, assignment.phase)
        scheduled_timestamp = phase_start + assignment.time_seconds * 1000.0 if phase_start is not None else None
        if phase_start is None or scheduled_timestamp is None:
            events.append(
                _build_usage_event(
                    report_code=report_code,
                    fight=fight,
                    pull=pull,
                    assignment=assignment,
                    player=player,
                    status=COOLDOWN_STATUS_IGNORED_MISSING_PHASE,
                    ability_labels=ability_labels,
                    scheduled_timestamp=None,
                    ignore_reason="missing_phase",
                )
            )
            continue
        if player_key not in participants:
            events.append(
                _build_usage_event(
                    report_code=report_code,
                    fight=fight,
                    pull=pull,
                    assignment=assignment,
                    player=player,
                    status=COOLDOWN_STATUS_IGNORED_NOT_IN_PULL,
                    ability_labels=ability_labels,
                    scheduled_timestamp=scheduled_timestamp,
                    ignore_reason="not_in_pull",
                )
            )
            continue
        if scheduled_timestamp > float(fight.end):
            events.append(
                _build_usage_event(
                    report_code=report_code,
                    fight=fight,
                    pull=pull,
                    assignment=assignment,
                    player=player,
                    status=COOLDOWN_STATUS_IGNORED_AFTER_PULL_END,
                    ability_labels=ability_labels,
                    scheduled_timestamp=scheduled_timestamp,
                    ignore_reason="after_pull_end",
                )
            )
            continue
        cutoff_status, cutoff_reason = _assignment_cutoff_status(
            scheduled_timestamp=scheduled_timestamp,
            death_count_cutoff=death_count_cutoff,
            healer_death_cutoff=healer_death_cutoff,
        )
        if cutoff_status:
            events.append(
                _build_usage_event(
                    report_code=report_code,
                    fight=fight,
                    pull=pull,
                    assignment=assignment,
                    player=player,
                    status=cutoff_status,
                    ability_labels=ability_labels,
                    scheduled_timestamp=scheduled_timestamp,
                    ignore_reason=cutoff_reason,
                )
            )
            continue
        grouped[(player_key, assignment.spell_id)].append((assignment, scheduled_timestamp))

    for (player_key, spell_id), assignment_items in grouped.items():
        casts = list(cast_events.get((fight.id, player_key, spell_id), []))
        used_cast_indexes: Set[int] = set()
        matched_line_numbers: Set[int] = set()
        ordered_assignments = sorted(assignment_items, key=lambda item: (item[1], item[0].line_number))

        for assignment, scheduled_timestamp in ordered_assignments:
            intended_target, intended_target_key, target_was_alive = _assignment_target_state(
                assignment,
                target_player_lookup=target_player_lookup,
                participants=participants,
                life_events=life_events,
                scheduled_timestamp=scheduled_timestamp,
            )
            window_start = scheduled_timestamp - tolerance_seconds * 1000.0
            window_end = scheduled_timestamp + tolerance_seconds * 1000.0
            candidate = _nearest_cast_index(
                casts,
                scheduled_timestamp=scheduled_timestamp,
                used_cast_indexes=used_cast_indexes,
                min_timestamp=window_start,
                max_timestamp=window_end,
                required_target_key=intended_target_key if target_was_alive else None,
            )
            if candidate is None:
                continue
            used_cast_indexes.add(candidate)
            matched_line_numbers.add(assignment.line_number)
            cast = casts[candidate]
            events.append(
                _build_usage_event(
                    report_code=report_code,
                    fight=fight,
                    pull=pull,
                    assignment=assignment,
                    player=note_player_lookup.get(player_key, assignment.player),
                    status=COOLDOWN_STATUS_CORRECT,
                    ability_labels=ability_labels,
                    scheduled_timestamp=scheduled_timestamp,
                    cast=cast,
                    intended_target=intended_target,
                    target_was_alive=target_was_alive,
                )
            )

        for assignment, scheduled_timestamp in ordered_assignments:
            if assignment.line_number in matched_line_numbers:
                continue
            intended_target, intended_target_key, target_was_alive = _assignment_target_state(
                assignment,
                target_player_lookup=target_player_lookup,
                participants=participants,
                life_events=life_events,
                scheduled_timestamp=scheduled_timestamp,
            )
            dead_at_scheduled_time = _is_dead_at(life_events.get(player_key, []), scheduled_timestamp)
            candidate = _nearest_cast_index(
                casts,
                scheduled_timestamp=scheduled_timestamp,
                used_cast_indexes=used_cast_indexes,
            )
            if candidate is None:
                if dead_at_scheduled_time:
                    events.append(
                        _build_usage_event(
                            report_code=report_code,
                            fight=fight,
                            pull=pull,
                            assignment=assignment,
                            player=note_player_lookup.get(player_key, assignment.player),
                            status=COOLDOWN_STATUS_IGNORED_DEAD,
                            ability_labels=ability_labels,
                            scheduled_timestamp=scheduled_timestamp,
                            ignore_reason="dead",
                            intended_target=intended_target,
                            target_was_alive=target_was_alive,
                        )
                    )
                    continue
                events.append(
                    _build_usage_event(
                        report_code=report_code,
                        fight=fight,
                        pull=pull,
                        assignment=assignment,
                        player=note_player_lookup.get(player_key, assignment.player),
                        status=COOLDOWN_STATUS_MISSED,
                        ability_labels=ability_labels,
                        scheduled_timestamp=scheduled_timestamp,
                        intended_target=intended_target,
                        target_was_alive=target_was_alive,
                    )
                )
                continue
            used_cast_indexes.add(candidate)
            cast = casts[candidate]
            target_mismatch = bool(
                intended_target_key
                and target_was_alive
                and not _cast_matches_target(cast, intended_target_key)
            )
            events.append(
                _build_usage_event(
                    report_code=report_code,
                    fight=fight,
                    pull=pull,
                    assignment=assignment,
                    player=note_player_lookup.get(player_key, assignment.player),
                    status=COOLDOWN_STATUS_INCORRECT,
                    ability_labels=ability_labels,
                    scheduled_timestamp=scheduled_timestamp,
                    cast=cast,
                    intended_target=intended_target,
                    target_was_alive=target_was_alive,
                    target_mismatch=target_mismatch,
                )
            )

    return sorted(events, key=lambda item: (item.player.lower(), item.pull_index, item.scheduled_offset_ms or 0.0, item.line_number))


def _build_usage_event(
    *,
    report_code: str,
    fight: Any,
    pull: CooldownUsagePull,
    assignment: CooldownReminderAssignment,
    player: str,
    status: str,
    ability_labels: Dict[int, str],
    scheduled_timestamp: Optional[float],
    cast: Optional[CooldownCastEvent] = None,
    ignore_reason: Optional[str] = None,
    intended_target: Optional[str] = None,
    target_was_alive: Optional[bool] = None,
    target_mismatch: bool = False,
) -> CooldownUsageEvent:
    scheduled_offset = scheduled_timestamp - float(fight.start) if scheduled_timestamp is not None else None
    delta_seconds = None
    if cast is not None and scheduled_timestamp is not None:
        delta_seconds = (cast.timestamp - scheduled_timestamp) / 1000.0
    return CooldownUsageEvent(
        source_report_code=report_code,
        player=player,
        fight_id=int(fight.id),
        fight_name=getattr(fight, "name", None),
        pull_index=pull.pull_index,
        pull_view_id=pull.view_id,
        status=status,
        line_number=assignment.line_number,
        spell_id=assignment.spell_id,
        ability_label=(cast.ability_label if cast and cast.ability_label else ability_labels.get(assignment.spell_id)),
        scheduled_timestamp=scheduled_timestamp,
        scheduled_offset_ms=scheduled_offset,
        phase=assignment.phase,
        phase_time_seconds=assignment.time_seconds,
        actual_timestamp=cast.timestamp if cast else None,
        actual_offset_ms=cast.offset_ms if cast else None,
        delta_seconds=delta_seconds,
        boss_spell_id=assignment.boss_spell_id,
        boss_ability_label=ability_labels.get(assignment.boss_spell_id) if assignment.boss_spell_id is not None else None,
        ignore_reason=ignore_reason,
        pull_duration_ms=pull.duration_ms,
        intended_target=intended_target,
        actual_target=cast.target if cast else None,
        target_was_alive=target_was_alive,
        target_mismatch=target_mismatch,
    )


def _build_entries(
    *,
    note_players: List[str],
    events_by_player: Dict[str, List[CooldownUsageEvent]],
    player_classes: Dict[str, Optional[str]],
    player_roles: Dict[str, str],
    pulls_by_player: Dict[str, int],
) -> Tuple[List[CooldownUsageEntry], Dict[str, List[CooldownUsageEvent]]]:
    entries: List[CooldownUsageEntry] = []
    player_events: Dict[str, List[CooldownUsageEvent]] = {}
    for player in sorted(
        note_players,
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            name.lower(),
        ),
    ):
        events = sorted(
            events_by_player.get(player, []),
            key=lambda item: (item.source_report_code or "", item.pull_index, item.fight_id, item.scheduled_offset_ms or 0.0, item.line_number),
        )
        player_events[player] = events
        correct = sum(1 for event in events if event.status == COOLDOWN_STATUS_CORRECT)
        incorrect = sum(1 for event in events if event.status == COOLDOWN_STATUS_INCORRECT)
        missed = sum(1 for event in events if event.status == COOLDOWN_STATUS_MISSED)
        ignored = sum(1 for event in events if event.status in IGNORED_STATUSES)
        checked = correct + incorrect + missed
        deltas = [abs(event.delta_seconds) for event in events if event.delta_seconds is not None]
        entries.append(
            CooldownUsageEntry(
                player=player,
                role=player_roles.get(player) or ROLE_UNKNOWN,
                class_name=player_classes.get(player),
                pulls=pulls_by_player.get(player, 0),
                assignments=len(events),
                correct=correct,
                incorrect=incorrect,
                missed=missed,
                ignored=ignored,
                on_time_rate=correct / checked if checked else 0.0,
                average_delta_seconds=sum(deltas) / len(deltas) if deltas else None,
                events=events,
            )
        )

    entries.sort(
        key=lambda entry: (
            entry.on_time_rate if (entry.correct + entry.incorrect + entry.missed) else 1.0,
            -entry.missed,
            ROLE_PRIORITY.get(entry.role or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            entry.player.lower(),
        )
    )
    return entries, player_events


def _merge_cooldown_usage_summaries(summaries: List[CooldownUsageSummary]) -> CooldownUsageSummary:
    primary = summaries[0]
    source_reports: List[str] = []
    pulls: List[CooldownUsagePull] = []
    combined_classes: Dict[str, Optional[str]] = {}
    combined_roles: Dict[str, str] = {}
    combined_specs: Dict[str, Optional[str]] = {}
    combined_pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    combined_events: DefaultDict[str, List[CooldownUsageEvent]] = defaultdict(list)

    for summary in summaries:
        for code in summary.source_reports or [summary.report_code]:
            if code not in source_reports:
                source_reports.append(code)
        for pull in summary.pulls:
            label = pull.label if len(summaries) == 1 else f"{pull.source_report_code} {pull.label}"
            pulls.append(
                CooldownUsagePull(
                    source_report_code=pull.source_report_code,
                    fight_id=pull.fight_id,
                    fight_name=pull.fight_name,
                    pull_index=pull.pull_index,
                    view_id=pull.view_id,
                    label=label,
                    duration_ms=pull.duration_ms,
                    death_count_cutoff_timestamp=pull.death_count_cutoff_timestamp,
                    healer_death_cutoff_timestamp=pull.healer_death_cutoff_timestamp,
                )
            )
        for player, class_name in summary.player_classes.items():
            if player not in combined_classes or combined_classes[player] is None:
                combined_classes[player] = class_name
        for player, role in summary.player_roles.items():
            if combined_roles.get(player) in (None, ROLE_UNKNOWN):
                combined_roles[player] = role or ROLE_UNKNOWN
        for player, spec in summary.player_specs.items():
            if player not in combined_specs or combined_specs[player] is None:
                combined_specs[player] = spec
        for player, pulls_count in summary.pulls_by_player.items():
            combined_pulls_by_player[player] += pulls_count
        for player, events in summary.player_events.items():
            combined_events[player].extend(events)

    entries, player_events = _build_entries(
        note_players=_note_players(primary.plan),
        events_by_player=combined_events,
        player_classes=combined_classes,
        player_roles=combined_roles,
        pulls_by_player=dict(combined_pulls_by_player),
    )

    return CooldownUsageSummary(
        report_code=primary.report_code,
        fight_filter=primary.fight_filter,
        fight_ids=primary.fight_ids,
        pull_count=sum(summary.pull_count for summary in summaries),
        tolerance_seconds=primary.tolerance_seconds,
        ignore_after_deaths=primary.ignore_after_deaths,
        ignore_after_healer_death=primary.ignore_after_healer_death,
        ignore_stasis=primary.ignore_stasis,
        plan=primary.plan,
        pulls=pulls,
        entries=entries,
        player_classes=combined_classes,
        player_roles=combined_roles,
        player_specs=combined_specs,
        player_events=player_events,
        pulls_by_player=dict(combined_pulls_by_player),
        source_reports=source_reports,
    )


def _collect_cast_events(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[Any],
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
    spell_ids: Set[int],
    note_player_lookup: Dict[str, str],
    ability_labels: Dict[int, str],
) -> Dict[Tuple[int, str, int], List[CooldownCastEvent]]:
    casts: DefaultDict[Tuple[int, str, int], List[CooldownCastEvent]] = defaultdict(list)
    if not spell_ids:
        return {}
    filter_expr = _build_spell_filter(spell_ids)
    for fight in fights:
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Casts",
            start=fight.start,
            end=fight.end,
            limit=5000,
            extra_filter=filter_expr,
            actor_names=actor_names,
        ):
            spell_id = _event_ability_id(event)
            if spell_id is None or spell_id not in spell_ids:
                continue
            source_name, _source_id = _resolve_event_source_player(event, actor_names, actor_owners)
            if not source_name:
                continue
            player_key = _normalize_player_name(source_name)
            player = note_player_lookup.get(player_key)
            if not player:
                continue
            ability_label = _event_ability_label(event) or ability_labels.get(spell_id)
            if ability_label:
                ability_labels.setdefault(spell_id, ability_label)
            timestamp = _event_timestamp(event)
            target_name = _event_target_name(event, actor_names)
            casts[(fight.id, player_key, spell_id)].append(
                CooldownCastEvent(
                    player=player,
                    spell_id=spell_id,
                    timestamp=timestamp,
                    offset_ms=timestamp - float(fight.start),
                    ability_label=ability_label,
                    target=target_name,
                )
            )
    for events in casts.values():
        events.sort(key=lambda item: item.timestamp)
    return dict(casts)


def _collect_life_events_and_cutoffs(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fights: Iterable[Any],
    actor_names: Dict[int, str],
    participants_by_fight: Dict[int, Set[str]],
    roles_by_fight: Dict[int, Dict[str, str]],
    player_roles_global: Dict[str, str],
    watched_player_lookup: Dict[str, str],
    ignore_after_deaths: Optional[int],
    ignore_after_healer_death: bool,
) -> Tuple[Dict[int, Dict[str, List[CooldownLifeEvent]]], Dict[int, float], Dict[int, float]]:
    life_events_by_fight: Dict[int, Dict[str, List[CooldownLifeEvent]]] = {}
    death_count_cutoffs: Dict[int, float] = {}
    healer_death_cutoffs: Dict[int, float] = {}
    death_limit = int(ignore_after_deaths) if ignore_after_deaths and ignore_after_deaths > 0 else None

    for fight in fights:
        life_events: DefaultDict[str, List[CooldownLifeEvent]] = defaultdict(list)
        death_count = 0
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Deaths",
            start=fight.start,
            end=fight.end,
            limit=1000,
            actor_names=actor_names,
        ):
            event_type = (event.get("type") or "").lower()
            if event_type not in {"death", "instakill", "resurrect"}:
                continue
            target_name = _event_target_name(event, actor_names)
            if not target_name:
                continue
            target_key = _normalize_player_name(target_name)
            timestamp = _event_timestamp(event)
            if target_key in watched_player_lookup:
                normalized_type = "resurrect" if event_type == "resurrect" else "death"
                life_events[target_key].append(CooldownLifeEvent(timestamp=timestamp, event_type=normalized_type))

            if event_type in {"death", "instakill"} and target_key in participants_by_fight.get(fight.id, set()):
                death_count += 1
                if death_limit is not None and fight.id not in death_count_cutoffs and death_count >= death_limit:
                    death_count_cutoffs[fight.id] = timestamp
                if ignore_after_healer_death and fight.id not in healer_death_cutoffs:
                    role = _role_for_player_key(target_key, roles_by_fight.get(fight.id, {}), player_roles_global)
                    if role == "Healer":
                        healer_death_cutoffs[fight.id] = timestamp

        _append_resurrection_cast_life_events(
            session,
            bearer,
            report_code=report_code,
            fight=fight,
            actor_names=actor_names,
            watched_player_lookup=watched_player_lookup,
            life_events=life_events,
        )
        life_events_by_fight[fight.id] = {
            player_key: sorted(events, key=lambda item: item.timestamp)
            for player_key, events in life_events.items()
        }

    return life_events_by_fight, death_count_cutoffs, healer_death_cutoffs


def _append_resurrection_cast_life_events(
    session: requests.Session,
    bearer: str,
    *,
    report_code: str,
    fight: Any,
    actor_names: Dict[int, str],
    watched_player_lookup: Dict[str, str],
    life_events: DefaultDict[str, List[CooldownLifeEvent]],
) -> None:
    filter_expr = _build_spell_filter(BATTLE_RESURRECTION_SPELL_IDS)
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Casts",
        start=fight.start,
        end=fight.end,
        limit=1000,
        extra_filter=filter_expr,
        actor_names=actor_names,
    ):
        target_name = _event_target_name(event, actor_names)
        if not target_name:
            continue
        target_key = _normalize_player_name(target_name)
        if target_key not in watched_player_lookup:
            continue
        life_events[target_key].append(CooldownLifeEvent(timestamp=_event_timestamp(event), event_type="resurrect"))


def _parse_nsrt_fields(line: str, *, line_number: int) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for raw_part in line.split(";"):
        part = raw_part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"Line {line_number}: expected key:value fields separated by semicolons.")
        key, value = part.split(":", 1)
        normalized_key = key.strip().lower()
        if not normalized_key:
            raise ValueError(f"Line {line_number}: field key cannot be empty.")
        fields[normalized_key] = value.strip()
    return fields


def _coerce_required_text(fields: Dict[str, str], field_id: str, *, line_number: int) -> str:
    value = fields.get(field_id, "").strip()
    if not value:
        raise ValueError(f"Line {line_number}: {field_id} is required.")
    return value


def _coerce_required_int(fields: Dict[str, str], field_id: str, *, line_number: int) -> int:
    value = _coerce_required_text(fields, field_id, line_number=line_number)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Line {line_number}: {field_id} must be a whole number.") from exc


def _coerce_required_float(fields: Dict[str, str], field_id: str, *, line_number: int) -> float:
    value = _coerce_required_text(fields, field_id, line_number=line_number)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Line {line_number}: {field_id} must be a number.") from exc


def _coerce_optional_int(value: Optional[str], *, line_number: int, field_id: str) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Line {line_number}: {field_id} must be a whole number.") from exc


def _normalize_difficulty_label(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_tolerance_seconds(value: Any) -> float:
    try:
        tolerance = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("tolerance_seconds must be a number.") from exc
    if tolerance < 0 or tolerance > 15:
        raise ValueError("tolerance_seconds must be between 0 and 15.")
    return tolerance


def _validate_selected_fight_encounter(plan: CooldownReminderPlan, fights: Iterable[Any]) -> None:
    mismatches: List[Tuple[int, Optional[str], int]] = []
    saw_encounter_metadata = False
    expected = int(plan.header.encounter_id)
    for fight in fights:
        encounter_id = getattr(fight, "encounter_id", None)
        if encounter_id is None:
            continue
        saw_encounter_metadata = True
        try:
            actual = int(encounter_id)
        except (TypeError, ValueError):
            continue
        if actual != expected:
            mismatches.append((int(getattr(fight, "id", 0) or 0), getattr(fight, "name", None), actual))
    if saw_encounter_metadata and mismatches:
        fight_id, fight_name, actual = mismatches[0]
        label = f"{fight_name or 'selected fight'} (fight {fight_id})" if fight_id else (fight_name or "selected fight")
        raise ValueError(
            f"This reminder is for EncounterID {expected}, but {label} is EncounterID {actual}."
        )


def _normalize_player_name(value: Any) -> str:
    return str(value or "").strip().casefold()


def _note_players(plan: CooldownReminderPlan) -> List[str]:
    players: List[str] = []
    seen: Set[str] = set()
    for assignment in plan.assignments:
        key = _normalize_player_name(assignment.player)
        if not key or key in seen:
            continue
        players.append(assignment.player)
        seen.add(key)
    return players


def _assignment_target_players(plan: CooldownReminderPlan) -> List[str]:
    players: List[str] = []
    seen: Set[str] = set()
    for assignment in plan.assignments:
        target = _assignment_target_text(assignment)
        key = _normalize_player_name(target)
        if not key or key in seen:
            continue
        players.append(str(target).strip())
        seen.add(key)
    return players


def _assignment_target_text(assignment: CooldownReminderAssignment) -> Optional[str]:
    target = assignment.fields.get("glowunit")
    if target is None:
        return None
    text = str(target).strip()
    return text or None


def _player_lookup_for_names(actor_names: Dict[int, str], players: Iterable[str]) -> Dict[str, str]:
    actor_lookup = {
        _normalize_player_name(name): name
        for name in actor_names.values()
        if name and _normalize_player_name(name)
    }
    lookup: Dict[str, str] = {}
    for player in players:
        key = _normalize_player_name(player)
        if not key:
            continue
        lookup[key] = actor_lookup.get(key, str(player).strip())
    return lookup


def _assignment_target_state(
    assignment: CooldownReminderAssignment,
    *,
    target_player_lookup: Dict[str, str],
    participants: Set[str],
    life_events: Dict[str, List[CooldownLifeEvent]],
    scheduled_timestamp: float,
) -> Tuple[Optional[str], Optional[str], Optional[bool]]:
    target = _assignment_target_text(assignment)
    if not target:
        return None, None, None
    target_key = _normalize_player_name(target)
    if not target_key:
        return None, None, None
    target_name = target_player_lookup.get(target_key, str(target).strip())
    target_is_alive = target_key in participants and not _is_dead_at(life_events.get(target_key, []), scheduled_timestamp)
    return target_name, target_key, target_is_alive


def _cast_matches_target(cast: CooldownCastEvent, target_key: str) -> bool:
    return bool(target_key) and _normalize_player_name(cast.target) == target_key


def _lookup_by_normalized(mapping: Dict[str, Any], player: str) -> Any:
    player_key = _normalize_player_name(player)
    for key, value in mapping.items():
        if _normalize_player_name(key) == player_key:
            return value
    return None


def _player_classes_for_note_players(
    actor_names: Dict[int, str],
    actor_classes: Dict[int, Optional[str]],
    note_players: Iterable[str],
) -> Dict[str, Optional[str]]:
    class_by_key = {
        _normalize_player_name(name): actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }
    return {player: class_by_key.get(_normalize_player_name(player)) for player in note_players}


def _roles_for_note_players(
    note_players: Iterable[str],
    player_roles_global: Dict[str, str],
    roles_by_fight: Dict[int, Dict[str, str]],
) -> Dict[str, str]:
    roles: Dict[str, str] = {}
    for player in note_players:
        role = _lookup_by_normalized(player_roles_global, player)
        if not role:
            for fight_roles in roles_by_fight.values():
                role = _lookup_by_normalized(fight_roles, player)
                if role:
                    break
        roles[player] = role or ROLE_UNKNOWN
    return roles


def _role_for_player_key(
    player_key: str,
    fight_roles: Dict[str, str],
    player_roles_global: Dict[str, str],
) -> str:
    for name, role in fight_roles.items():
        if _normalize_player_name(name) == player_key:
            return role or ROLE_UNKNOWN
    for name, role in player_roles_global.items():
        if _normalize_player_name(name) == player_key:
            return role or ROLE_UNKNOWN
    return ROLE_UNKNOWN


def _fetch_ability_labels(session: requests.Session, bearer: str, report_code: str) -> Dict[int, str]:
    labels: Dict[int, str] = {}
    try:
        data = gql(session, bearer, REPORT_OVERVIEW_QUERY, {"code": report_code})
        abilities = data["reportData"]["report"].get("masterData", {}).get("abilities", []) or []
        for ability in abilities:
            game_id = ability.get("gameID")
            name = ability.get("name")
            if game_id is None or not name:
                continue
            try:
                labels[int(game_id)] = str(name)
            except (TypeError, ValueError):
                continue
    except Exception:
        pass
    return labels


def _build_spell_filter(spell_ids: Set[int]) -> str:
    parts = []
    for spell_id in sorted(spell_ids):
        parts.append(f"(ability.id = {int(spell_id)} or abilityGameID = {int(spell_id)})")
    return " or ".join(parts)


def _event_ability_id(event: Dict[str, Any]) -> Optional[int]:
    candidates = [event.get("abilityGameID")]
    ability = event.get("ability")
    if isinstance(ability, dict):
        candidates.extend([ability.get("gameID"), ability.get("guid"), ability.get("id")])
    for candidate in candidates:
        try:
            if candidate is not None:
                return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _event_ability_label(event: Dict[str, Any]) -> Optional[str]:
    ability = event.get("ability")
    if isinstance(ability, dict):
        name = ability.get("name")
        if name:
            return str(name)
    return None


def _event_target_name(event: Dict[str, Any], actor_names: Dict[int, str]) -> Optional[str]:
    target = event.get("target")
    if isinstance(target, dict):
        name = target.get("name")
        if name:
            return str(name)
    name = event.get("targetName")
    if name:
        return str(name)
    target_id = event.get("targetID")
    try:
        target_id_int = int(target_id)
    except (TypeError, ValueError):
        return None
    return actor_names.get(target_id_int)


def _event_timestamp(event: Dict[str, Any]) -> float:
    try:
        return float(event.get("timestamp") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _phase_start_timestamp(fight: Any, phase: int) -> Optional[float]:
    if int(phase) == 1:
        return float(fight.start)
    return None


def _is_dead_at(events: List[CooldownLifeEvent], timestamp: float) -> bool:
    dead = False
    for event in events:
        if event.timestamp > timestamp:
            break
        if event.event_type == "death":
            dead = True
        elif event.event_type == "resurrect":
            dead = False
    return dead


def _assignment_cutoff_status(
    *,
    scheduled_timestamp: float,
    death_count_cutoff: Optional[float],
    healer_death_cutoff: Optional[float],
) -> Tuple[Optional[str], Optional[str]]:
    candidates: List[Tuple[float, str, str]] = []
    if death_count_cutoff is not None and scheduled_timestamp >= death_count_cutoff:
        candidates.append((death_count_cutoff, COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT, "death_count_cutoff"))
    if healer_death_cutoff is not None and scheduled_timestamp >= healer_death_cutoff:
        candidates.append((healer_death_cutoff, COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH, "healer_death_cutoff"))
    if not candidates:
        return None, None
    _timestamp, status, reason = min(candidates, key=lambda item: item[0])
    return status, reason


def _nearest_cast_index(
    casts: List[CooldownCastEvent],
    *,
    scheduled_timestamp: float,
    used_cast_indexes: Set[int],
    min_timestamp: Optional[float] = None,
    max_timestamp: Optional[float] = None,
    required_target_key: Optional[str] = None,
) -> Optional[int]:
    candidates: List[Tuple[float, int]] = []
    for index, cast in enumerate(casts):
        if index in used_cast_indexes:
            continue
        if required_target_key and not _cast_matches_target(cast, required_target_key):
            continue
        if min_timestamp is not None and cast.timestamp < min_timestamp:
            continue
        if max_timestamp is not None and cast.timestamp > max_timestamp:
            continue
        candidates.append((abs(cast.timestamp - scheduled_timestamp), index))
    if not candidates:
        return None
    _distance, index = min(candidates, key=lambda item: (item[0], casts[item[1]].timestamp))
    return index


def _pull_view_id(report_code: str, fight_id: int) -> str:
    return f"pull:{report_code}:{int(fight_id)}"


__all__ = [
    "COOLDOWN_STATUS_CORRECT",
    "COOLDOWN_STATUS_INCORRECT",
    "COOLDOWN_STATUS_MISSED",
    "COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT",
    "COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH",
    "COOLDOWN_STATUS_IGNORED_AFTER_PULL_END",
    "COOLDOWN_STATUS_IGNORED_DEAD",
    "COOLDOWN_STATUS_IGNORED_MISSING_PHASE",
    "COOLDOWN_STATUS_IGNORED_NOT_IN_PULL",
    "CooldownReminderAssignment",
    "CooldownReminderHeader",
    "CooldownReminderPlan",
    "CooldownUsageEntry",
    "CooldownUsageEvent",
    "CooldownUsagePull",
    "CooldownUsageSummary",
    "fetch_cooldown_usage_summary",
    "parse_nsrt_cooldown_reminders",
    "validate_cooldown_plan",
]
