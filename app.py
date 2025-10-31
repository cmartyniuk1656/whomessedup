"""
FastAPI application entry point exposing Warcraft Logs hit summaries.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from who_messed_up.api import Fight
from who_messed_up.service import FightSelectionError, HitSummary, TokenError, fetch_hit_summary

app = FastAPI(title="Who Messed Up", version="0.1.0")


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


class HitSummaryResponse(BaseModel):
    report: str
    data_type: str
    filters: Dict[str, Optional[str]]
    total_hits: Dict[str, int]
    per_player: Dict[str, int]
    breakdown: List[BreakdownRow]
    fights: List[FightModel]

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

        return cls(
            report=summary.report_code,
            data_type=summary.data_type,
            filters=filters,
            total_hits=dict(summary.total_hits),
            per_player=per_player,
            breakdown=[BreakdownRow(**row) for row in breakdown_rows],
            fights=fights,
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
