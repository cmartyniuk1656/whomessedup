"""
Dimensius-specific add damage summaries.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import requests

from ..api import fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    DIMENSIUS_INITIAL_ADD_IGNORE_COUNT,
    DIMENSIUS_LIVING_MASS_FILTER,
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    TokenError,
    FightSelectionError,
    _extract_target_key,
    _infer_player_roles,
    _players_from_details,
    _resolve_event_source_player,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
)


@dataclass
class AddDamageEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float


@dataclass
class AddDamageSummary:
    report_code: str
    fight_filter: Optional[str]
    fight_ids: Optional[List[int]]
    entries: List[AddDamageEntry]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    pull_count: int
    total_damage: float
    avg_damage_per_pull: float
    source_reports: List[str]
    fight_signature: List[Tuple[str, bool, int]]
    ignore_first_add_set: bool


def _fetch_dimensius_add_damage_single(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    ignore_first_add_set: bool = False,
) -> AddDamageSummary:
    load_env()

    fight_id_filter = [int(fid) for fid in fight_ids] if fight_ids else None

    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, actor_owners = fetch_fights(session, bearer, report_code)
    chosen = _select_fights(fights, name_filter=fight_name, fight_ids=fight_id_filter)
    fight_signature = [(fight.name, bool(fight.kill), int(fight.end - fight.start)) for fight in chosen]

    fight_id_list = [fight.id for fight in chosen]
    aggregated_details = fetch_player_details(session, bearer, code=report_code, fight_ids=fight_id_list)
    player_roles_global, player_specs_global = _infer_player_roles(aggregated_details)

    roles_by_fight: Dict[int, Dict[str, str]] = {}
    pulls_by_player: Dict[str, int] = defaultdict(int)
    for fight in chosen:
        details = fetch_player_details(session, bearer, code=report_code, fight_ids=[fight.id])
        fight_roles, _ = _infer_player_roles(details)
        if fight_roles:
            roles_by_fight[fight.id] = fight_roles
        for name in set(_players_from_details(details)):
            if name:
                pulls_by_player[name] += 1

    player_classes: Dict[str, Optional[str]] = {}
    for actor_id, name in actor_names.items():
        if name:
            player_classes[name] = actor_classes.get(actor_id)

    player_roles = dict(player_roles_global)
    player_specs = dict(player_specs_global)
    for fight_roles in roles_by_fight.values():
        for player, role in fight_roles.items():
            if player not in player_roles or player_roles[player] in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
            player_specs.setdefault(player, player_specs_global.get(player))

    damage_totals: Dict[str, float] = defaultdict(float)

    for fight in chosen:
        ignored_targets: Set[Tuple[Any, ...]] = set()
        target_order: List[Tuple[Any, ...]] = []
        unknown_targets_remaining = DIMENSIUS_INITIAL_ADD_IGNORE_COUNT

        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="DamageDone",
            start=fight.start,
            end=fight.end,
            limit=10000,
            extra_filter=DIMENSIUS_LIVING_MASS_FILTER,
            actor_names=actor_names,
        ):
            target_key = _extract_target_key(event)
            if ignore_first_add_set:
                if target_key is not None:
                    if target_key not in target_order and len(target_order) < DIMENSIUS_INITIAL_ADD_IGNORE_COUNT:
                        target_order.append(target_key)
                        ignored_targets.add(target_key)
                    if target_key in ignored_targets:
                        continue
                else:
                    if unknown_targets_remaining > 0:
                        unknown_targets_remaining -= 1
                        continue

            source_name, owner_id = _resolve_event_source_player(event, actor_names, actor_owners)
            if not source_name:
                continue
            if owner_id is not None:
                player_classes.setdefault(source_name, actor_classes.get(owner_id))
            player_roles.setdefault(
                source_name,
                roles_by_fight.get(fight.id, {}).get(source_name)
                or player_roles_global.get(source_name)
                or ROLE_UNKNOWN,
            )
            amount = event.get("amount") or 0
            absorbed = event.get("absorbed") or 0
            overkill = event.get("overkill") or 0
            try:
                total_amount = float(amount) + float(absorbed) - float(overkill or 0)
            except (TypeError, ValueError):
                continue
            if total_amount <= 0:
                continue
            damage_totals[source_name] += total_amount

    pull_count = len(chosen)
    if pull_count <= 0:
        pull_count = 1

    entries: List[AddDamageEntry] = []
    total_damage_sum = 0.0

    for player in sorted(
        set(pulls_by_player.keys()) | set(damage_totals.keys()) | set(player_roles.keys()),
        key=lambda name: (
            ROLE_PRIORITY.get(player_roles.get(name, ROLE_UNKNOWN), ROLE_PRIORITY[ROLE_UNKNOWN]),
            name.lower(),
        ),
    ):
        role = player_roles.get(player) or ROLE_UNKNOWN
        pulls = pulls_by_player.get(player, pull_count)
        if pulls <= 0:
            pulls = pull_count
        total_damage = float(damage_totals.get(player, 0.0))
        average_damage = total_damage / pulls if pulls else 0.0
        total_damage_sum += total_damage
        player_classes.setdefault(player, None)
        player_roles.setdefault(player, role)
        player_specs.setdefault(player, player_specs_global.get(player))
        entries.append(
            AddDamageEntry(
                player=player,
                role=role,
                class_name=player_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=average_damage,
            )
        )

    return AddDamageSummary(
        report_code=report_code,
        fight_filter=fight_name,
        fight_ids=fight_id_filter,
        entries=entries,
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        pull_count=len(chosen),
        total_damage=total_damage_sum,
        avg_damage_per_pull=total_damage_sum / len(chosen) if len(chosen) else 0.0,
        source_reports=[report_code],
        fight_signature=fight_signature,
        ignore_first_add_set=ignore_first_add_set,
    )


def fetch_dimensius_add_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    ignore_first_add_set: Optional[bool] = False,
) -> AddDamageSummary:
    primary_code = _sanitize_report_code(report_code)
    ignore_flag = bool(ignore_first_add_set)
    primary_summary = _fetch_dimensius_add_damage_single(
        report_code=primary_code,
        fight_name=fight_name,
        fight_ids=fight_ids,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        ignore_first_add_set=ignore_flag,
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

    summaries: List[AddDamageSummary] = [primary_summary]
    for code in extra_codes:
        summary = _fetch_dimensius_add_damage_single(
            report_code=code,
            fight_name=fight_name,
            fight_ids=fight_ids,
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            ignore_first_add_set=ignore_flag,
        )
        summaries.append(summary)

    base_signature = primary_summary.fight_signature
    for other in summaries[1:]:
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

    combined_totals: Dict[Tuple[str, str], float] = {}
    combined_pulls: Dict[Tuple[str, str], int] = {}
    combined_classes: Dict[str, Optional[str]] = dict(primary_summary.player_classes)
    combined_roles: Dict[str, str] = dict(primary_summary.player_roles)
    combined_specs: Dict[str, Optional[str]] = dict(primary_summary.player_specs)

    def merge_summary(summary: AddDamageSummary) -> None:
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
            key = (entry.player, entry.role)
            combined_pulls[key] = max(combined_pulls.get(key, 0), entry.pulls)
            existing_total = combined_totals.get(key, 0.0)
            combined_totals[key] = max(existing_total, entry.total_damage)

    for summary in summaries:
        merge_summary(summary)

    merged_entries: List[AddDamageEntry] = []
    total_damage_sum = 0.0
    for (player, role), total_damage in combined_totals.items():
        pulls = combined_pulls.get((player, role), primary_summary.pull_count)
        average_damage = total_damage / pulls if pulls else 0.0
        total_damage_sum += total_damage
        merged_entries.append(
            AddDamageEntry(
                player=player,
                role=role,
                class_name=combined_classes.get(player),
                pulls=pulls,
                total_damage=total_damage,
                average_damage=average_damage,
            )
        )

    merged_entries.sort(
        key=lambda entry: (
            ROLE_PRIORITY.get(entry.role or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            -entry.total_damage,
            entry.player.lower(),
        )
    )

    all_reports = [primary_code] + extra_codes

    return AddDamageSummary(
        report_code=primary_code,
        fight_filter=primary_summary.fight_filter,
        fight_ids=primary_summary.fight_ids,
        entries=merged_entries,
        player_classes=combined_classes,
        player_roles=combined_roles,
        player_specs=combined_specs,
        pull_count=primary_summary.pull_count,
        total_damage=total_damage_sum,
        avg_damage_per_pull=total_damage_sum / primary_summary.pull_count if primary_summary.pull_count else 0.0,
        source_reports=all_reports,
        fight_signature=base_signature,
        ignore_first_add_set=ignore_flag,
    )


__all__ = [
    "AddDamageEntry",
    "AddDamageSummary",
    "fetch_dimensius_add_damage_summary",
]
