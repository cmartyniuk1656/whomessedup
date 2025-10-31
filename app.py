"""
FastAPI application entry point exposing Warcraft Logs hit summaries.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from who_messed_up import load_env
from who_messed_up.api import Fight
from who_messed_up.service import FightSelectionError, HitSummary, TokenError, fetch_hit_summary

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


def _client_credentials() -> Dict[str, Optional[str]]:
    return {
        "client_id": os.getenv("WCL_CLIENT_ID"),
        "client_secret": os.getenv("WCL_CLIENT_SECRET"),
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


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
