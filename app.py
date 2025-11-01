"""
FastAPI application entry point exposing Warcraft Logs hit summaries.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from who_messed_up import load_env
from who_messed_up.api import Fight
from who_messed_up.jobs import job_manager
from who_messed_up.service import (
    FightSelectionError,
    GhostSummary,
    HitSummary,
    PhaseDamageSummary,
    PhaseSummary,
    TokenError,
    fetch_ghost_summary,
    fetch_hit_summary,
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

    @classmethod
    def from_summary(cls, summary: GhostSummary) -> "GhostSummaryResponse":
        filters: Dict[str, Optional[str]] = {
            "fight_name": summary.fight_filter,
            "fight_ids": ",".join(str(fid) for fid in summary.fight_ids) if summary.fight_ids else None,
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


class PhaseSummaryResponse(BaseModel):
    report: str
    filters: Dict[str, Optional[str]]
    pull_count: int
    totals: Dict[str, float]
    entries: List[PhasePlayerModel]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    ability_ids: Dict[str, int]
    hit_filters: Dict[str, Optional[float]]

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
            "first_ghost_only": summary.first_hit_only_ghosts,
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
            ability_ids=ability_ids,
            hit_filters=hit_filters,
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


JOB_NEXUS_PHASE1 = "nexus_phase1"
JOB_PHASE_DAMAGE = "nexus_phase_damage"


def _execute_nexus_phase1_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    credentials = _client_credentials()
    fight_ids = payload.get("fight_ids") or None
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
        first_hit_only_ghosts=payload.get("first_ghost_only", True),
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
    )
    return PhaseDamageSummaryResponse.from_summary(summary).dict()


job_manager.register_handler(JOB_NEXUS_PHASE1, _execute_nexus_phase1_job)
job_manager.register_handler(JOB_PHASE_DAMAGE, _execute_phase_damage_job)


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
) -> GhostSummaryResponse:
    credentials = _client_credentials()
    try:
        summary = fetch_ghost_summary(
            report_code=report,
            ability_id=ability_id,
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
    first_ghost_only: bool = Query(True, description="Count only the first Ghost miss per pull."),
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> PhaseSummaryResponse:
    final_ms = float(ignore_final_seconds) * 1000.0 if ignore_final_seconds and ignore_final_seconds > 0 else None
    death_threshold = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
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
        "first_ghost_only": first_ghost_only,
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
    fresh: bool = Query(False, description="Skip cache and force a fresh report run."),
    token: Optional[str] = Query(None, description="Optional bearer token to override client credentials."),
) -> PhaseDamageSummaryResponse:
    phases = phase or ["full"]
    fight_ids_payload = sorted(int(fid) for fid in fight_id) if fight_id else []
    payload: Dict[str, Any] = {
        "report": report,
        "fight": fight,
        "fight_ids": fight_ids_payload,
        "phases": list(phases),
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
