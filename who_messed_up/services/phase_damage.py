"""
Phase damage summary helpers.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import requests

from ..env import load_env
from ..api import fetch_fights, fetch_player_details, fetch_table
from .common import (
    FightSelectionError,
    NEXUS_PHASE_LABELS,
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _normalize_phase_ids,
    _resolve_phase_labels,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
)


@dataclass
class PhaseMetric:
    phase_id: str
    phase_label: str
    total_amount: float
    average_per_pull: float


@dataclass
class PhaseDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    metrics: List[PhaseMetric]


@dataclass
class PhaseDamageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    phases: List[str]
    phase_labels: Dict[str, str]
    entries: List[PhaseDamageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    pull_count: int
    source_reports: List[str]
    fight_signature: List[Tuple[str, bool, int]]


def _fetch_phase_damage_summary_single(
    *,
    report_code: str,
    phases: Optional[Iterable[str]] = None,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    phase_labels: Optional[Dict[str, str]] = None,
) -> PhaseDamageSummary:
    load_env()

    if phase_labels is None:
        phase_labels = NEXUS_PHASE_LABELS

    fight_id_filter = [int(fid) for fid in fight_ids] if fight_ids else None

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_id_filter)

    selected_phases = _normalize_phase_ids(phases, phase_labels=phase_labels)

    fight_id_list = [fight.id for fight in chosen]
    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles

    valid_players: Set[str] = set(player_roles_global.keys())
    for fight_roles in roles_by_fight.values():
        valid_players.update(name for name in fight_roles if name)

    player_classes: Dict[str, Optional[str]] = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name
    }
    player_roles: Dict[str, str] = dict(player_roles_global)
    player_specs: Dict[str, Optional[str]] = dict(player_specs_global)

    fight_ids_by_player_role: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    for fight in chosen:
        fight_roles = roles_by_fight.get(fight.id, {})
        for player, role in fight_roles.items():
            fight_ids_by_player_role[(player, role)].add(fight.id)

    damage_roles = {"Tank", "Melee", "Ranged", ROLE_UNKNOWN}
    healing_roles = {"Healer"}

    def resolve_actor(actor_key: Any) -> Tuple[Optional[int], Optional[str]]:
        if isinstance(actor_key, int):
            current = actor_key
            seen: Set[int] = set()
            while True:
                owner = actor_owners.get(current)
                if owner in (None, 0) or owner in seen:
                    break
                seen.add(current)
                current = owner
            name = actor_names.get(current) or actor_names.get(actor_key)
            return current, name
        if isinstance(actor_key, str):
            return None, actor_key
        return None, None

    def sum_entry_total(entry: Dict[str, Any]) -> float:
        value = entry.get("total")
        if value is None:
            value = entry.get("totalReduced")
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    phase_totals: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for phase_id in selected_phases:
        filter_expr = None
        if phase_id != "full":
            try:
                numeric_phase = int(phase_id)
                filter_expr = f"encounterPhase = {numeric_phase}"
            except ValueError:
                filter_expr = None

        for fight in chosen:
            def consume_entries(entries: Iterable[Dict[str, Any]], *, allowed_roles: Set[str]) -> None:
                for entry in entries:
                    actor_key = entry.get("id")
                    if actor_key is None:
                        continue
                    total_amount = sum_entry_total(entry)
                    if total_amount <= 0:
                        continue
                    owner_id, owner_name = resolve_actor(actor_key)
                    if not owner_name:
                        owner_name = entry.get("name")
                    if not owner_name:
                        continue
                    role = (
                        roles_by_fight.get(fight.id, {}).get(owner_name)
                        or player_roles_global.get(owner_name)
                        or ROLE_UNKNOWN
                    )
                    if role not in allowed_roles:
                        continue
                    key = (owner_name, role)
                    phase_totals[key][phase_id] += float(total_amount)
                    if owner_name not in player_classes and owner_id is not None:
                        player_classes[owner_name] = actor_classes.get(owner_id)
                    player_roles.setdefault(owner_name, role)
                    valid_players.add(owner_name)

            damage_table = fetch_table(
                session,
                bearer,
                code=report_code,
                data_type="DamageDone",
                fight_id=fight.id,
                start=fight.start,
                end=fight.end,
                filter_expr=filter_expr,
            )
            consume_entries(damage_table.get("entries") or [], allowed_roles=damage_roles)

            healing_table = fetch_table(
                session,
                bearer,
                code=report_code,
                data_type="Healing",
                fight_id=fight.id,
                start=fight.start,
                end=fight.end,
                filter_expr=filter_expr,
            )
            consume_entries(healing_table.get("entries") or [], allowed_roles=healing_roles)

    for player, role in list(fight_ids_by_player_role.keys()):
        if player not in valid_players:
            continue
        key = (player, role)
        phase_totals.setdefault(key, defaultdict(float))
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, None)

    entries: List[PhaseDamageEntry] = []
    for player, role in sorted(
        phase_totals.keys(),
        key=lambda item: (
            ROLE_PRIORITY.get(item[1] or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            item[0].lower(),
        ),
    ):
        if player not in valid_players:
            continue
        pulls = len(fight_ids_by_player_role.get((player, role), set()))
        if pulls <= 0:
            continue
        totals_for_player = phase_totals[(player, role)]
        metrics: List[PhaseMetric] = []
        for phase_id in selected_phases:
            total_amount = totals_for_player.get(phase_id, 0.0)
            average_per_pull = total_amount / pulls if pulls else 0.0
            metrics.append(
                PhaseMetric(
                    phase_id=phase_id,
                    phase_label=phase_labels.get(phase_id, phase_id),
                    total_amount=total_amount,
                    average_per_pull=average_per_pull,
                )
            )
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, None)
        entries.append(
            PhaseDamageEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                metrics=metrics,
            )
        )

    return PhaseDamageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=fight_id_filter,
        phases=selected_phases,
        phase_labels={phase: phase_labels.get(phase, phase) for phase in selected_phases},
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        pull_count=len(chosen),
        source_reports=[report_code],
        fight_signature=[
            (fight.name, bool(fight.kill), int(fight.end - fight.start)) for fight in chosen
        ],
    )


def fetch_phase_damage_summary(
    *,
    report_code: str,
    phases: Optional[Iterable[str]] = None,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    phase_profile: Optional[str] = None,
) -> PhaseDamageSummary:
    phase_labels = _resolve_phase_labels(phase_profile)
    primary_code = _sanitize_report_code(report_code)
    primary_summary = _fetch_phase_damage_summary_single(
        report_code=primary_code,
        phases=phases,
        fight_name=fight_name,
        fight_ids=fight_ids,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        phase_labels=phase_labels,
    )

    extra_codes: List[str] = []
    if extra_report_codes:
        for code in extra_report_codes:
            if not code:
                continue
            try:
                code_str = _sanitize_report_code(code)
            except ValueError:
                continue
            if code_str == primary_code or code_str in extra_codes:
                continue
            extra_codes.append(code_str)

    if not extra_codes:
        return primary_summary

    summaries: List[PhaseDamageSummary] = [primary_summary]
    for extra_code in extra_codes:
        extra_summary = _fetch_phase_damage_summary_single(
            report_code=extra_code,
            phases=phases,
            fight_name=fight_name,
            fight_ids=fight_ids,
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            phase_labels=phase_labels,
        )
        summaries.append(extra_summary)

    base_signature = primary_summary.fight_signature
    base_phases = list(primary_summary.phases)
    for other in summaries[1:]:
        if base_phases != list(other.phases):
            raise FightSelectionError(
                "Additional report uses a different phase configuration than the primary report."
            )
        if len(base_signature) != len(other.fight_signature):
            raise FightSelectionError(
                "Additional report does not contain the same number of pulls as the primary report."
            )
        for idx, (base_fight, other_fight) in enumerate(zip(base_signature, other.fight_signature), start=1):
            base_name, base_kill, base_duration = base_fight
            other_name, other_kill, other_duration = other_fight
            if base_name != other_name or base_kill != other_kill:
                raise FightSelectionError(
                    f"Additional report pull #{idx} does not match the primary report (encounter mismatch)."
                )
            duration_delta = abs(base_duration - other_duration)
            if duration_delta > 15000:
                raise FightSelectionError(
                    f"Additional report pull #{idx} duration differs significantly from the primary report."
                )

    phase_ids = list(primary_summary.phases)
    phase_labels = dict(primary_summary.phase_labels)
    combined_totals: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    combined_pulls: Dict[Tuple[str, str], int] = {}
    combined_classes: Dict[str, Optional[str]] = dict(primary_summary.player_classes)
    combined_roles: Dict[str, str] = dict(primary_summary.player_roles)
    combined_specs: Dict[str, Optional[str]] = dict(primary_summary.player_specs)

    def merge_entry(summary: PhaseDamageSummary, entry: PhaseDamageEntry) -> None:
        key = (entry.player, entry.role)
        combined_pulls[key] = max(combined_pulls.get(key, 0), entry.pulls)
        if entry.player not in combined_classes or combined_classes[entry.player] is None:
            combined_classes[entry.player] = summary.player_classes.get(entry.player)
        if entry.player not in combined_roles or combined_roles.get(entry.player) in (None, ROLE_UNKNOWN):
            combined_roles[entry.player] = entry.role
        combined_specs.setdefault(entry.player, summary.player_specs.get(entry.player))
        totals = combined_totals[key]
        for metric in entry.metrics:
            if metric.phase_id not in phase_ids:
                continue
            totals[metric.phase_id] = max(totals.get(metric.phase_id, 0.0), metric.total_amount)

    for summary in summaries:
        for player, class_name in summary.player_classes.items():
            if player not in combined_classes or combined_classes[player] is None:
                combined_classes[player] = class_name
        for player, role in summary.player_roles.items():
            if player not in combined_roles or combined_roles[player] in (None, ROLE_UNKNOWN):
                combined_roles[player] = role
        for player, spec in summary.player_specs.items():
            if player not in combined_specs or combined_specs[player] is None:
                combined_specs[player] = spec
        for entry in summary.entries:
            merge_entry(summary, entry)

    merged_entries: List[PhaseDamageEntry] = []
    for (player, role), totals in combined_totals.items():
        pulls = combined_pulls.get((player, role), primary_summary.pull_count)
        metrics: List[PhaseMetric] = []
        for phase_id in phase_ids:
            total_amount = totals.get(phase_id, 0.0)
            average = total_amount / pulls if pulls else 0.0
            metrics.append(
                PhaseMetric(
                    phase_id=phase_id,
                    phase_label=phase_labels.get(phase_id, NEXUS_PHASE_LABELS.get(phase_id, phase_id)),
                    total_amount=total_amount,
                    average_per_pull=average,
                )
            )
        merged_entries.append(
            PhaseDamageEntry(
                player=player,
                role=role,
                class_name=combined_classes.get(player),
                pulls=pulls,
                metrics=metrics,
            )
        )

    merged_entries.sort(
        key=lambda entry: (
            ROLE_PRIORITY.get(entry.role or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            entry.player.lower(),
        )
    )

    all_reports = [primary_code] + extra_codes

    return PhaseDamageSummary(
        report_code=primary_code,
        fight_filter=primary_summary.fight_filter,
        fight_ids=primary_summary.fight_ids,
        phases=phase_ids,
        phase_labels=phase_labels,
        entries=merged_entries,
        player_classes=combined_classes,
        player_roles=combined_roles,
        player_specs=combined_specs,
        pull_count=primary_summary.pull_count,
        source_reports=all_reports,
        fight_signature=base_signature,
    )


__all__ = [
    "PhaseMetric",
    "PhaseDamageEntry",
    "PhaseDamageSummary",
    "fetch_phase_damage_summary",
]
