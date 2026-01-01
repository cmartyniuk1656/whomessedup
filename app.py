"""
FastAPI application entry point exposing Warcraft Logs hit summaries.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from who_messed_up import load_env
from who_messed_up.api import Fight
from who_messed_up.jobs import job_manager
from who_messed_up.service import (
    AddDamageSummary,
    DimensiusPhaseOneSummary,
    DimensiusPriorityDamageSummary,
    DimensiusDeathSummary,
    FightSelectionError,
    GhostSummary,
    HitSummary,
    PhaseDamageSummary,
    PhaseSummary,
    TokenError,
    DEFAULT_GHOST_MISS_MODE,
    OBLIVION_FILTER_DEFAULT,
    GhostMissMode,
    normalize_ghost_miss_mode,
    fetch_ghost_summary,
    fetch_hit_summary,
    fetch_dimensius_phase_one_summary,
    fetch_dimensius_priority_damage_summary,
    fetch_dimensius_death_summary,
    fetch_dimensius_bled_out_summary,
    fetch_dimensius_add_damage_summary,
    fetch_phase_damage_summary,
    fetch_phase_summary,
)

app = FastAPI(title="Who Messed Up", version="0.1.0")
load_env()


class FightModel(BaseModel):
    id: int
    name: str
    start: float
    end: float
    kill: bool

    @classmethod
    def from_fight(cls, fight: Fight) -> "FightModel":
        return cls(id=fight.id, name=fight.name, start=fight.start, end=fight.end, kill=fight.kill)


class BreakdownRow(BaseModel):
    player: str
    ability: str
    hits: int
    damage: float


class FightTotalsModel(BaseModel):
    id: int
    name: str
    hits: int
    damage: float


class GhostEventModel(BaseModel):
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull: int
    timestamp: float
    offset_ms: float
    pull_duration_ms: Optional[float] = None


class HitSummaryResponse(BaseModel):
    report: str
    data_type: str
    filters: Dict[str, Optional[str]]
    total_hits: Dict[str, int]
    per_player: Dict[str, int]
    per_player_damage: Dict[str, float]
    per_player_hits_per_pull: Dict[str, float]
    total_damage: float
    pull_count: int
    average_hits_per_pull: float
    breakdown: List[BreakdownRow]
    fights: List[FightModel]
    fight_totals: List[FightTotalsModel]
    actors: Dict[int, str]
    actor_classes: Dict[int, Optional[str]]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]

    @classmethod
    def from_summary(cls, summary: HitSummary) -> "HitSummaryResponse":
        per_player = summary.per_player()
        breakdown_rows = summary.per_player_rows()
        fights = [FightModel.from_fight(fight) for fight in summary.fights_considered]

        filters: Dict[str, Optional[str]] = {
            "ability": summary.ability,
            "ability_regex": summary.ability_regex,
            "ability_id": str(summary.ability_id) if summary.ability_id is not None else None,
            "source": summary.source,
            "fight_name": summary.fight_filter,
        }
        if summary.fight_ids:
            filters["fight_ids"] = ",".join(str(fid) for fid in summary.fight_ids)

        per_player_damage = {player: float(amount) for player, amount in summary.damage_per_player.items()}
        per_player_hits_per_pull = {
            player: float(value) for player, value in summary.per_player_hits_per_pull().items()
        }

        fight_totals = []
        for fight in summary.fights_considered:
            fight_totals.append(
                FightTotalsModel(
                    id=fight.id,
                    name=fight.name,
                    hits=summary.fight_total_hits.get(fight.id, 0),
                    damage=float(summary.fight_total_damage.get(fight.id, 0.0)),
                )
            )

        return cls(
            report=summary.report_code,
            data_type=summary.data_type,
            filters=filters,
            total_hits=dict(summary.total_hits),
            per_player=per_player,
            per_player_damage=per_player_damage,
            per_player_hits_per_pull=per_player_hits_per_pull,
            total_damage=summary.total_damage,
            pull_count=summary.pull_count,
            average_hits_per_pull=summary.average_hits_per_pull,
            breakdown=[BreakdownRow(**row) for row in breakdown_rows],
            fights=fights,
            fight_totals=fight_totals,
            actors=summary.actor_names,
            actor_classes=summary.actor_classes,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
        )


class GhostEntryModel(BaseModel):
    player: str
    role: str
    pulls: int
    ghost_misses: int
    ghost_per_pull: float


class GhostSummaryResponse(BaseModel):
    report: str
    ability_id: int
    filters: Dict[str, Optional[str]]
    pull_count: int
    entries: List[GhostEntryModel]
    actors: Dict[int, str]
    actor_classes: Dict[int, Optional[str]]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    ghost_events: List[GhostEventModel]

    @classmethod
    def from_summary(cls, summary: GhostSummary) -> "GhostSummaryResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "ghost_miss_mode": summary.ghost_miss_mode,
            "ignore_after_deaths": (
                str(summary.ignore_after_deaths) if summary.ignore_after_deaths is not None else None
            ),
        }
        entries = [
            GhostEntryModel(
                player=entry.player,
                role=summary.player_roles.get(entry.player, "Unknown"),
                pulls=entry.pulls,
                ghost_misses=entry.misses,
                ghost_per_pull=entry.misses_per_pull,
            )
            for entry in summary.entries
        ]

        return cls(
            report=summary.report_code,
            ability_id=summary.ability_id,
            filters=filters,
            pull_count=summary.pull_count,
            entries=entries,
            actors=summary.actor_names,
            actor_classes=summary.actor_classes,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
            ghost_events=[
                GhostEventModel(
                    player=event.player,
                    fight_id=event.fight_id,
                    fight_name=event.fight_name or None,
                    pull=event.pull_index,
                    timestamp=event.timestamp,
                    offset_ms=event.offset_ms,
                    pull_duration_ms=event.pull_duration_ms,
                )
                for event in summary.ghost_events
            ],
        )


class PhasePlayerModel(BaseModel):
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    besiege_hits: int
    besiege_per_pull: float
    ghost_misses: int
    ghost_per_pull: float
    fuckup_rate: float


class TrackedEventModel(BaseModel):
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull: int
    timestamp: float
    offset_ms: float
    metric_id: str
    label: Optional[str]
    pull_duration_ms: Optional[float] = None


class PhaseSummaryResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    pull_count: int
    totals: Dict[str, float]
    entries: List[PhasePlayerModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    ghost_events: List[GhostEventModel]
    ability_ids: Dict[str, int]
    hit_filters: Dict[str, Optional[Any]]
    player_events: Dict[str, List[TrackedEventModel]]

    @classmethod
    def from_summary(cls, summary: PhaseSummary) -> "PhaseSummaryResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "ignore_after_deaths": str(summary.hit_ignore_after_deaths)
            if summary.hit_ignore_after_deaths
            else None,
            "ignore_final_seconds": str(summary.hit_exclude_final_ms / 1000.0)
            if summary.hit_exclude_final_ms
            else None,
            "ghost_miss_mode": summary.ghost_miss_mode,
        }
        entries = [
            PhasePlayerModel(
                player=row.player,
                role=row.role,
                class_name=row.class_name,
                pulls=row.pulls,
                besiege_hits=row.besiege_hits,
                besiege_per_pull=row.besiege_per_pull,
                ghost_misses=row.ghost_misses,
                ghost_per_pull=row.ghost_per_pull,
                fuckup_rate=row.fuckup_rate,
            )
            for row in summary.entries
        ]
        totals = {
            "total_besieges": float(summary.total_besieges),
            "total_ghosts": float(summary.total_ghosts),
            "avg_besieges_per_pull": summary.avg_besieges_per_pull,
            "avg_ghosts_per_pull": summary.avg_ghosts_per_pull,
            "combined_per_pull": summary.combined_per_pull,
        }
        ghost_events = [
            GhostEventModel(
                player=event.player,
                fight_id=event.fight_id,
                fight_name=event.fight_name or None,
                pull=event.pull_index,
                timestamp=event.timestamp,
                offset_ms=event.offset_ms,
                pull_duration_ms=event.pull_duration_ms,
            )
            for event in summary.ghost_events
        ]
        player_events_map: Dict[str, List[TrackedEventModel]] = {}
        for event in ghost_events:
            tracked = TrackedEventModel(
                player=event.player,
                fight_id=event.fight_id,
                fight_name=event.fight_name,
                pull=event.pull,
                timestamp=event.timestamp,
                offset_ms=event.offset_ms,
                metric_id="ghost_miss",
                label="Ghost miss",
                pull_duration_ms=event.pull_duration_ms,
            )
            player_events_map.setdefault(event.player, []).append(tracked)
        ability_ids = {
            "besiege": summary.besiege_ability_id,
            "ghost": summary.ghost_ability_id,
        }
        hit_filters = {
            "ignore_after_deaths": float(summary.hit_ignore_after_deaths)
            if summary.hit_ignore_after_deaths
            else None,
            "ignore_final_seconds": summary.hit_exclude_final_ms / 1000.0 if summary.hit_exclude_final_ms else None,
            "first_hit_only": summary.first_hit_only_hits,
            "ignore_zero_damage_hits": summary.hit_ignore_zero_damage_hits,
            "ghost_miss_mode": summary.ghost_miss_mode,
        }
        if summary.ghost_miss_mode == "first_per_pull":
            hit_filters["first_ghost_only"] = True
        elif summary.ghost_miss_mode == "all":
            hit_filters["first_ghost_only"] = False
        else:
            hit_filters["first_ghost_only"] = None
        return cls(
            report=summary.report_code,
            filters=filters,
            pull_count=summary.pull_count,
            totals=totals,
            entries=entries,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
            ghost_events=ghost_events,
            ability_ids=ability_ids,
            hit_filters=hit_filters,
            player_events=player_events_map,
        )


class AbilityDescriptorModel(BaseModel):
    id: int
    label: Optional[str]


class MetricValueModel(BaseModel):
    total: float
    per_pull: float


class DimensiusMetricModel(BaseModel):
    id: str
    label: str
    per_pull_label: str


class DimensiusPhaseOnePlayerModel(BaseModel):
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    metrics: Dict[str, MetricValueModel]
    fuckup_rate: float
    events: List[TrackedEventModel]


class DimensiusPhaseOneResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    pull_count: int
    metrics: List[DimensiusMetricModel]
    entries: List[DimensiusPhaseOnePlayerModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    metric_totals: Dict[str, MetricValueModel]
    combined_per_pull: float
    totals: Dict[str, float]
    ability_ids: Dict[str, AbilityDescriptorModel]
    player_events: Dict[str, List[TrackedEventModel]]

    @classmethod
    def from_summary(cls, summary: DimensiusPhaseOneSummary) -> "DimensiusPhaseOneResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "reverse_gravity_excess_mass": "true"
            if any(metric.id == "rg_em_overlap" for metric in summary.metrics)
            else "false",
            "early_mass_before_rg": "true"
            if any(metric.id == "early_mass" for metric in summary.metrics)
            else "false",
            "early_mass_window_seconds": str(summary.early_mass_window_seconds)
            if summary.early_mass_window_seconds is not None
            else None,
            "dark_energy_hits": "true"
            if any(metric.id == "dark_energy" for metric in summary.metrics)
            else "false",
            "ignore_after_deaths": str(summary.ignore_after_deaths)
            if summary.ignore_after_deaths is not None
            else None,
        }
        metric_models = [
            DimensiusMetricModel(id=metric.id, label=metric.label, per_pull_label=metric.per_pull_label)
            for metric in summary.metrics
        ]
        metric_label_lookup = {metric.id: metric.label for metric in summary.metrics}
        entry_models: List[DimensiusPhaseOnePlayerModel] = []
        for entry in summary.entries:
            metrics_map = {
                metric_id: MetricValueModel(total=value.total, per_pull=value.per_pull)
                for metric_id, value in entry.metrics.items()
            }
            event_models = [
                TrackedEventModel(
                    player=event.player,
                    fight_id=event.fight_id,
                    fight_name=event.fight_name,
                    pull=event.pull_index,
                    timestamp=event.timestamp,
                    offset_ms=event.offset_ms,
                    metric_id=event.metric_id,
                    label=metric_label_lookup.get(event.metric_id),
                    pull_duration_ms=event.pull_duration_ms,
                )
                for event in entry.events
            ]
            entry_models.append(
                DimensiusPhaseOnePlayerModel(
                    player=entry.player,
                    role=entry.role,
                    class_name=entry.class_name,
                    pulls=entry.pulls,
                    metrics=metrics_map,
                    fuckup_rate=entry.fuckup_rate,
                    events=event_models,
                )
            )
        metric_totals = {
            metric_id: MetricValueModel(total=value.total, per_pull=value.per_pull)
            for metric_id, value in summary.metric_totals.items()
        }
        ability_models: Dict[str, AbilityDescriptorModel] = {}
        for key, ability_id in summary.ability_ids.items():
            try:
                numeric_id = int(ability_id)
            except (TypeError, ValueError):
                continue
            label = " ".join(part.capitalize() for part in key.split("_"))
            ability_models[key] = AbilityDescriptorModel(id=numeric_id, label=label)
        player_events_map: Dict[str, List[TrackedEventModel]] = {}
        for player, events in summary.player_events.items():
            player_events_map[player] = [
                TrackedEventModel(
                    player=event.player,
                    fight_id=event.fight_id,
                    fight_name=event.fight_name,
                    pull=event.pull_index,
                    timestamp=event.timestamp,
                    offset_ms=event.offset_ms,
                    metric_id=event.metric_id,
                    label=metric_label_lookup.get(event.metric_id),
                    pull_duration_ms=event.pull_duration_ms,
                )
                for event in events
            ]
        return cls(
            report=summary.report_code,
            filters=filters,
            pull_count=summary.pull_count,
            metrics=metric_models,
            entries=entry_models,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
            metric_totals=metric_totals,
            combined_per_pull=summary.combined_per_pull,
            ability_ids=ability_models,
            totals={"combined_per_pull": summary.combined_per_pull},
            player_events=player_events_map,
        )


class DimensiusDeathEventModel(BaseModel):
    player: str
    fight_id: int
    fight_name: Optional[str]
    pull: int
    timestamp: float
    offset_ms: float
    ability_id: Optional[int]
    ability_label: Optional[str]
    label: Optional[str]
    description: Optional[str]
    pull_duration_ms: Optional[float] = None


class DimensiusDeathEntryModel(BaseModel):
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    deaths: int
    death_rate: float
    events: List[DimensiusDeathEventModel]


class DimensiusDeathSummaryResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    pull_count: int
    totals: Dict[str, float]
    entries: List[DimensiusDeathEntryModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    player_events: Dict[str, List[DimensiusDeathEventModel]]

    @classmethod
    def from_summary(cls, summary: DimensiusDeathSummary) -> "DimensiusDeathSummaryResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "ignore_after_deaths": str(summary.ignore_after_deaths) if summary.ignore_after_deaths else None,
            "oblivion_filter": summary.oblivion_filter,
        }
        if summary.bled_out_filter:
            filters["bled_out_filter"] = summary.bled_out_filter
        if summary.bled_out_mode:
            filters["bled_out_mode"] = summary.bled_out_mode
        entries: List[DimensiusDeathEntryModel] = []
        for entry in summary.entries:
            event_models = [
                DimensiusDeathEventModel(
                    player=event.player,
                    fight_id=event.fight_id,
                    fight_name=event.fight_name,
                    pull=event.pull_index,
                    timestamp=event.timestamp,
                    offset_ms=event.offset_ms,
                    ability_id=event.ability_id,
                    ability_label=event.ability_label,
                    label=event.label,
                    description=event.description,
                    pull_duration_ms=event.pull_duration_ms,
                )
                for event in entry.events
            ]
            entries.append(
                DimensiusDeathEntryModel(
                    player=entry.player,
                    role=entry.role,
                    class_name=entry.class_name,
                    pulls=entry.pulls,
                    deaths=entry.deaths,
                    death_rate=entry.death_rate,
                    events=event_models,
                )
            )
        totals = {
            "total_deaths": float(summary.total_deaths),
            "avg_deaths_per_pull": summary.total_deaths / summary.pull_count if summary.pull_count else 0.0,
        }
        player_events_map: Dict[str, List[DimensiusDeathEventModel]] = {}
        for player, events in summary.player_events.items():
            player_events_map[player] = [
                DimensiusDeathEventModel(
                    player=event.player,
                    fight_id=event.fight_id,
                    fight_name=event.fight_name,
                    pull=event.pull_index,
                    timestamp=event.timestamp,
                    offset_ms=event.offset_ms,
                    ability_id=event.ability_id,
                    ability_label=event.ability_label,
                    label=event.label,
                    description=event.description,
                    pull_duration_ms=event.pull_duration_ms,
                )
                for event in events
            ]
        return cls(
            report=summary.report_code,
            filters=filters,
            pull_count=summary.pull_count,
            totals=totals,
            entries=entries,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
            player_events=player_events_map,
        )


class PhaseMetricModel(BaseModel):
    phase_id: str
    phase_label: str
    total_amount: float
    average_per_pull: float


class PhaseDamageEntryModel(BaseModel):
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    metrics: List[PhaseMetricModel]


class PhaseDamageSummaryResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    phases: List[str]
    phase_labels: Dict[str, str]
    entries: List[PhaseDamageEntryModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]

    @classmethod
    def from_summary(cls, summary: PhaseDamageSummary) -> "PhaseDamageSummaryResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "additional_reports": ",".join(summary.source_reports[1:]) if len(summary.source_reports) > 1 else None,
        }
        entries = [
            PhaseDamageEntryModel(
                player=row.player,
                role=row.role,
                class_name=row.class_name,
                pulls=row.pulls,
                metrics=[
                    PhaseMetricModel(
                        phase_id=metric.phase_id,
                        phase_label=metric.phase_label,
                        total_amount=metric.total_amount,
                        average_per_pull=metric.average_per_pull,
                    )
                    for metric in row.metrics
                ],
            )
            for row in summary.entries
        ]
        return cls(
            report=summary.report_code,
            filters=filters,
            phases=list(summary.phases),
            phase_labels=dict(summary.phase_labels),
            entries=entries,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
        )


class AddDamageEntryModel(BaseModel):
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float


class DimensiusAddDamageResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    pull_count: int
    totals: Dict[str, float]
    entries: List[AddDamageEntryModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    source_reports: List[str]

    @classmethod
    def from_summary(cls, summary: AddDamageSummary) -> "DimensiusAddDamageResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "ignore_first_add_set": "true" if summary.ignore_first_add_set else None,
            "additional_reports": ",".join(summary.source_reports[1:]) if len(summary.source_reports) > 1 else None,
        }
        entries = [
            AddDamageEntryModel(
                player=row.player,
                role=row.role,
                class_name=row.class_name,
                pulls=row.pulls,
                total_damage=row.total_damage,
                average_damage=row.average_damage,
            )
            for row in summary.entries
        ]
        totals = {
            "total_damage": summary.total_damage,
            "avg_damage_per_pull": summary.avg_damage_per_pull,
        }
        return cls(
            report=summary.report_code,
            filters=filters,
            pull_count=summary.pull_count,
            totals=totals,
            entries=entries,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
            source_reports=summary.source_reports,
        )

class TargetBreakdownModel(BaseModel):
    target: str
    label: str
    total_damage: float
    average_damage: float
    pulls_with_damage: int


class PriorityTargetSummaryModel(BaseModel):
    target: str
    label: str
    averaging_mode: str
    total_damage: float
    avg_damage_per_pull: float


class PriorityDamageEntryModel(BaseModel):
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    total_damage: float
    average_damage: float
    target_totals: Dict[str, TargetBreakdownModel]


class DimensiusPriorityDamageResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    pull_count: int
    totals: Dict[str, float]
    entries: List[PriorityDamageEntryModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    targets: List[PriorityTargetSummaryModel]

    @classmethod
    def from_summary(cls, summary: DimensiusPriorityDamageSummary) -> "DimensiusPriorityDamageResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
            "targets": ",".join(target.target for target in summary.targets) if summary.targets else None,
            "ignored_source": summary.ignored_source,
        }
        entries = [
            PriorityDamageEntryModel(
                player=row.player,
                role=row.role,
                class_name=row.class_name,
                pulls=row.pulls,
                total_damage=row.total_damage,
                average_damage=row.average_damage,
                target_totals={
                    key: TargetBreakdownModel(
                        target=value.target,
                        label=value.label,
                        total_damage=value.total_damage,
                        average_damage=value.average_damage,
                        pulls_with_damage=value.pulls_with_damage,
                    )
                    for key, value in row.target_totals.items()
                },
            )
            for row in summary.entries
        ]
        totals = {
            "total_damage": summary.total_damage,
            "avg_damage_per_pull": summary.avg_damage_per_pull,
        }
        return cls(
            report=summary.report_code,
            filters=filters,
            pull_count=summary.pull_count,
            totals=totals,
            entries=entries,
            player_classes=summary.player_classes,
            player_roles=summary.player_roles,
            player_specs=summary.player_specs,
            targets=[
                PriorityTargetSummaryModel(
                    target=target.target,
                    label=target.label,
                    averaging_mode=target.averaging_mode,
                    total_damage=target.total_damage,
                    avg_damage_per_pull=target.avg_damage_per_pull,
                )
                for target in summary.targets
            ],
        )


class JobStatusModel(BaseModel):
    id: str
    type: str
    status: str
    position: Optional[int]
    created_at: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


def _client_credentials() -> Dict[str, Optional[str]]:
    return {
        "client_id": os.getenv("WCL_CLIENT_ID"),
        "client_secret": os.getenv("WCL_CLIENT_SECRET"),
    }


def _normalize_report_code(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Report code cannot be empty.")
    lowered = text.lower()
    if "warcraftlogs.com" in lowered:
        parts = text.split("/reports/", 1)
        if len(parts) == 2:
            remainder = parts[1]
            remainder = remainder.split("/", 1)[0]
            remainder = remainder.split("?", 1)[0]
            code = remainder.strip()
            if code:
                return code
    return text


JOB_NEXUS_PHASE1 = "nexus_phase1"
JOB_PHASE_DAMAGE = "nexus_phase_damage"
JOB_DIMENSIUS_ADD_DAMAGE = "dimensius_add_damage"
JOB_DIMENSIUS_PHASE1 = "dimensius_phase1"
JOB_DIMENSIUS_DEATHS = "dimensius_deaths"
JOB_DIMENSIUS_PRIORITY_DAMAGE = "dimensius_priority_damage"
JOB_DIMENSIUS_BLED_OUT = "dimensius_bled_out"


def _execute_nexus_phase1_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    ghost_mode_value = payload.get("ghost_miss_mode")
    if ghost_mode_value is None and "first_ghost_only" in payload:
        ghost_mode_value = payload.get("first_ghost_only")
    summary = fetch_phase_summary(
        report_code=payload["report"],
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        besiege_ability_id=payload["hit_ability_id"],
        ghost_ability_id=payload["ghost_ability_id"],
        hit_data_type=payload["data_type"],
        hit_dedupe_ms=payload.get("hit_dedupe_ms"),
        hit_exclude_final_ms=payload.get("ignore_final_ms"),
        hit_ignore_after_deaths=payload.get("ignore_after_deaths"),
        first_hit_only_hits=payload.get("first_hit_only", True),
        ignore_zero_damage_hits=payload.get("ignore_zero_damage_hits", False),
        ghost_miss_mode=ghost_mode_value,
    )
    return PhaseSummaryResponse.from_summary(summary).dict()


def _execute_phase_damage_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    summary = fetch_phase_damage_summary(
        report_code=payload["report"],
        phases=payload.get("phases"),
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        extra_report_codes=payload.get("extra_reports"),
        phase_profile=payload.get("phase_profile"),
    )
    return PhaseDamageSummaryResponse.from_summary(summary).dict()


def _execute_dimensius_add_damage_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    summary = fetch_dimensius_add_damage_summary(
        report_code=payload["report"],
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        extra_report_codes=payload.get("extra_reports"),
        ignore_first_add_set=payload.get("ignore_first_add_set"),
    )
    return DimensiusAddDamageResponse.from_summary(summary).dict()


def _execute_dimensius_phase1_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    summary = fetch_dimensius_phase_one_summary(
        report_code=payload["report"],
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        include_rg_em_overlap=bool(payload.get("reverse_gravity_excess_mass", False)),
        include_early_mass=bool(payload.get("early_mass_before_rg", False)),
        early_mass_window_seconds=payload.get("early_mass_window_seconds"),
        include_dark_energy_hits=bool(payload.get("dark_energy_hits", False)),
        ignore_after_deaths=payload.get("ignore_after_deaths"),
    )
    return DimensiusPhaseOneResponse.from_summary(summary).dict()


def _execute_dimensius_deaths_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    summary = fetch_dimensius_death_summary(
        report_code=payload["report"],
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        ignore_after_deaths=payload.get("ignore_after_deaths"),
        oblivion_filter=payload.get("oblivion_filter"),
    )
    return DimensiusDeathSummaryResponse.from_summary(summary).dict()


def _execute_dimensius_bled_out_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    summary = fetch_dimensius_bled_out_summary(
        report_code=payload["report"],
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        ignore_after_deaths=payload.get("ignore_after_deaths"),
    )
    return DimensiusDeathSummaryResponse.from_summary(summary).dict()


def _execute_dimensius_priority_damage_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
    summary = fetch_dimensius_priority_damage_summary(
        report_code=payload["report"],
        fight_name=payload.get("fight"),
        fight_ids=fight_ids,
        targets=payload.get("targets"),
        token=payload.get("token"),
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
    )
    return DimensiusPriorityDamageResponse.from_summary(summary).dict()


job_manager.register_handler(JOB_NEXUS_PHASE1, _execute_nexus_phase1_job)
job_manager.register_handler(JOB_PHASE_DAMAGE, _execute_phase_damage_job)
job_manager.register_handler(JOB_DIMENSIUS_ADD_DAMAGE, _execute_dimensius_add_damage_job)
job_manager.register_handler(JOB_DIMENSIUS_PHASE1, _execute_dimensius_phase1_job)
job_manager.register_handler(JOB_DIMENSIUS_DEATHS, _execute_dimensius_deaths_job)
job_manager.register_handler(JOB_DIMENSIUS_BLED_OUT, _execute_dimensius_bled_out_job)
job_manager.register_handler(JOB_DIMENSIUS_PRIORITY_DAMAGE, _execute_dimensius_priority_damage_job)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/jobs/{job_id}", response_model=JobStatusModel)
def get_job_status(job_id: str) -> JobStatusModel:
    snapshot = job_manager.snapshot(job_id, include_result=True)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusModel.parse_obj(snapshot)


@app.get("/api/hits", response_model=HitSummaryResponse)
def get_hits(
    report: str = Query(..., description="Warcraft Logs report code."),
    ability: Optional[str] = Query(None, description="Exact ability name to include."),
    ability_id: Optional[int] = Query(None, description="Ability GUID/ID to include."),
    ability_regex: Optional[str] = Query(None, description="Regex to match ability names."),
    source: Optional[str] = Query(None, description="Only include events from this source name."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    data_type: str = Query("DamageTaken", description="Warcraft Logs ReportDataType to fetch."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> HitSummaryResponse:
    if not ability and not ability_regex and ability_id is None:
        raise HTTPException(status_code=400, detail="Provide one of 'ability', 'ability_regex', or 'ability_id'.")

    credentials = _client_credentials()
    try:
        summary = fetch_hit_summary(
            report_code=report,
            data_type=data_type,
            ability=ability,
            ability_id=ability_id,
            ability_regex=ability_regex,
            source=source,
            fight_name=fight,
            fight_ids=fight_id,
            token=token,
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
        )
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except FightSelectionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch hits: {exc}") from exc

    return HitSummaryResponse.from_summary(summary)


@app.get("/api/ghosts", response_model=GhostSummaryResponse)
def get_ghosts(
    report: str = Query(..., description="Warcraft Logs report code."),
    ability_id: int = Query(1224737, description="Ability GUID/ID to track as a ghost miss."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
    ignore_after_deaths: Optional[int] = Query(
        None, description="Stop counting ghost misses after this many player deaths in a fight."
    ),
    ghost_miss_mode: GhostMissMode = Query(
        DEFAULT_GHOST_MISS_MODE, description="Ghost miss counting strategy (per set, per pull, or all)."
    ),
    legacy_first_ghost_only: Optional[bool] = Query(
        None,
        alias="first_ghost_only",
        include_in_schema=False,
        description="Deprecated: set true to count first per pull or false to count all ghost misses.",
    ),
) -> GhostSummaryResponse:
    credentials = _client_credentials()
    ghost_mode_value: Any = ghost_miss_mode
    if legacy_first_ghost_only is not None:
        ghost_mode_value = legacy_first_ghost_only
    try:
        summary = fetch_ghost_summary(
            report_code=report,
            ability_id=ability_id,
            fight_name=fight,
            fight_ids=fight_id,
            token=token,
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            ghost_miss_mode=ghost_mode_value,
            ignore_after_deaths=ignore_after_deaths,
        )
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except FightSelectionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch ghost misses: {exc}") from exc

    return GhostSummaryResponse.from_summary(summary)


@app.get("/api/nexus-phase1", response_model=PhaseSummaryResponse)
def get_nexus_phase1(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    hit_ability_id: int = Query(1227472, description="Ability ID for Besiege hits."),
    ghost_ability_id: int = Query(1224737, description="Ability ID for Oathbound ghost misses."),
    data_type: str = Query("DamageTaken", description="ReportDataType used to fetch hit events."),
    ignore_after_deaths: Optional[int] = Query(
        None, description="Stop counting hits after this many total player deaths in a pull."
    ),
    ignore_final_seconds: Optional[float] = Query(
        None, description="Ignore hits that occur within the final N seconds of each pull."
    ),
    first_hit_only: bool = Query(True, description="Count only the first Besiege hit per pull."),
    ignore_zero_damage_hits: bool = Query(
        True, description="Ignore Besiege hits that deal 0 damage (immunity/absorb)."
    ),
    ghost_miss_mode: GhostMissMode = Query(
        DEFAULT_GHOST_MISS_MODE,
        description="How to count ghost misses: per set (default), per pull, or all misses.",
    ),
    legacy_first_ghost_only: Optional[bool] = Query(
        None,
        alias="first_ghost_only",
        include_in_schema=False,
        description="Deprecated: set true to count first ghost per pull, false to count all ghost misses.",
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> PhaseSummaryResponse:
    final_ms = float(ignore_final_seconds) * 1000.0 if ignore_final_seconds and ignore_final_seconds > 0 else None
    death_threshold = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    ghost_mode_input: Any = ghost_miss_mode
    if legacy_first_ghost_only is not None:
        ghost_mode_input = legacy_first_ghost_only
    normalized_ghost_mode = normalize_ghost_miss_mode(ghost_mode_input)
    payload = {
        "report": report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "hit_ability_id": hit_ability_id,
        "ghost_ability_id": ghost_ability_id,
        "data_type": data_type,
        "ignore_after_deaths": death_threshold,
        "ignore_final_ms": final_ms,
        "hit_dedupe_ms": 1500.0,
        "first_hit_only": first_hit_only,
        "ignore_zero_damage_hits": ignore_zero_damage_hits,
        "ghost_miss_mode": normalized_ghost_mode,
    }
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_NEXUS_PHASE1, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return PhaseSummaryResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


@app.get("/api/nexus-phase-damage", response_model=PhaseDamageSummaryResponse)
def get_nexus_phase_damage(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    phase: Optional[List[str]] = Query(None, description="Phases to include (full, 1-5)."),
    phase_profile: str = Query(
        "nexus",
        description="Phase preset to use (e.g., 'nexus' or 'dimensius').",
    ),
    additional_report: Optional[List[str]] = Query(
        None, description="Optional additional report codes to merge for damage/healing totals."
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> PhaseDamageSummaryResponse:
    phases = phase or ["full"]
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    primary_report = _normalize_report_code(report)
    extra_reports: List[str] = []
    if additional_report:
        for candidate in additional_report:
            try:
                normalized = _normalize_report_code(candidate)
            except HTTPException:
                continue
            if normalized and normalized != primary_report and normalized not in extra_reports:
                extra_reports.append(normalized)
    payload: Dict[str, Any] = {
        "report": primary_report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "phases": list(phases),
        "extra_reports": extra_reports,
        "phase_profile": phase_profile,
    }
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_PHASE_DAMAGE, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return PhaseDamageSummaryResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


@app.get("/api/dimensius-add-damage", response_model=DimensiusAddDamageResponse)
def get_dimensius_add_damage(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    additional_report: Optional[List[str]] = Query(
        None, description="Optional additional report codes to merge for Living Mass damage totals."
    ),
    ignore_first_add_set: bool = Query(
        False, description="Ignore the first Living Mass set that spawns immediately on pull."
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> DimensiusAddDamageResponse:
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    primary_report = _normalize_report_code(report)
    extra_reports: List[str] = []
    if additional_report:
        for candidate in additional_report:
            try:
                normalized = _normalize_report_code(candidate)
            except HTTPException:
                continue
            if normalized and normalized != primary_report and normalized not in extra_reports:
                extra_reports.append(normalized)
    payload: Dict[str, Any] = {
        "report": primary_report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "extra_reports": extra_reports,
        "ignore_first_add_set": bool(ignore_first_add_set),
    }
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_DIMENSIUS_ADD_DAMAGE, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return DimensiusAddDamageResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


@app.get("/api/dimensius-phase1", response_model=DimensiusPhaseOneResponse)
def get_dimensius_phase_one(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    reverse_gravity_excess_mass: bool = Query(
        True, description="Track players who had Reverse Gravity and Excess Mass simultaneously."
    ),
    early_mass_before_rg: bool = Query(
        False,
        description="Track players who gained Excess Mass within a configurable window (default 1s) before Reverse Gravity sets.",
    ),
    early_mass_window_seconds: Optional[int] = Query(
        None,
        ge=1,
        le=15,
        description="Window (in seconds) before Reverse Gravity to count an Excess Mass pickup as early.",
    ),
    dark_energy_hits: bool = Query(
        False, description="Track each Dark Energy hit taken by a player during Stage One."
    ),
    ignore_after_deaths: Optional[int] = Query(
        None, description="Stop counting events after this many total player deaths in a pull."
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> DimensiusPhaseOneResponse:
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    primary_report = _normalize_report_code(report)
    death_threshold = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    payload: Dict[str, Any] = {
        "report": primary_report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "reverse_gravity_excess_mass": bool(reverse_gravity_excess_mass),
        "early_mass_before_rg": bool(early_mass_before_rg),
        "dark_energy_hits": bool(dark_energy_hits),
        "ignore_after_deaths": death_threshold,
    }
    if early_mass_window_seconds is not None:
        payload["early_mass_window_seconds"] = int(early_mass_window_seconds)
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_DIMENSIUS_PHASE1, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return DimensiusPhaseOneResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


@app.get("/api/dimensius-deaths", response_model=DimensiusDeathSummaryResponse)
def get_dimensius_deaths(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    ignore_after_deaths: Optional[int] = Query(
        None, description="Stop counting deaths after this many occurrences per pull."
    ),
    oblivion_filter: str = Query(
        OBLIVION_FILTER_DEFAULT,
        description="How to treat Oblivion deaths (include all, exclude without recent triggers, or exclude entirely).",
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> DimensiusDeathSummaryResponse:
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    primary_report = _normalize_report_code(report)
    death_threshold = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    payload: Dict[str, Any] = {
        "report": primary_report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "ignore_after_deaths": death_threshold,
        "oblivion_filter": oblivion_filter,
    }
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_DIMENSIUS_DEATHS, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return DimensiusDeathSummaryResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


@app.get("/api/dimensius-bled-out", response_model=DimensiusDeathSummaryResponse)
def get_dimensius_bled_out(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    ignore_after_deaths: Optional[int] = Query(
        None, description="Stop counting deaths after this many occurrences per pull."
    ),
    bled_out_mode: str = Query(
        "no_forgiveness",
        description="How strictly to exclude deaths based on consumable usage (no_forgiveness or lenient).",
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> DimensiusDeathSummaryResponse:
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    primary_report = _normalize_report_code(report)
    death_threshold = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    payload: Dict[str, Any] = {
        "report": primary_report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "ignore_after_deaths": death_threshold,
        "bled_out_mode": bled_out_mode,
    }
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_DIMENSIUS_BLED_OUT, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return DimensiusDeathSummaryResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


@app.get("/api/dimensius-priority-damage", response_model=DimensiusPriorityDamageResponse)
def get_dimensius_priority_damage(
    report: str = Query(..., description="Warcraft Logs report code."),
    fight: Optional[str] = Query(None, description="Substring match on fight name."),
    fight_id: Optional[List[int]] = Query(None, description="Restrict to one or more fight IDs."),
    target: Optional[List[str]] = Query(
        None,
        description="Include one or more priority targets (artoshion, pargoth, nullbinder, voidwarden).",
    ),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> DimensiusPriorityDamageResponse:
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    primary_report = _normalize_report_code(report)
    payload: Dict[str, Any] = {
        "report": primary_report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "targets": target or [],
    }
    if token:
        payload["token"] = token

    try:
        job, immediate = job_manager.enqueue(JOB_DIMENSIUS_PRIORITY_DAMAGE, payload, bust_cache=fresh)
    except KeyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job.status == "completed":
        return DimensiusPriorityDamageResponse.parse_obj(job.result)

    snapshot = job_manager.snapshot(job.id)
    if snapshot is None:
        raise HTTPException(status_code=500, detail="Job tracking failed.")
    return JSONResponse(status_code=202, content={"job": snapshot})


FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        candidate = FRONTEND_DIST / path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend build not found.")
else:

    @app.get("/", include_in_schema=False)
    async def frontend_placeholder() -> Dict[str, str]:
        return {
            "detail": "Frontend build not found. Run `npm install` and `npm run build` inside the frontend/ directory."
        }
