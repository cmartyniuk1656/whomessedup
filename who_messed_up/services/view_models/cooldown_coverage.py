"""Typed timeline contract kept separate from the table report models."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ViewModelBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CoverageEventModel(ViewModelBase):
    time: float
    end: Optional[float] = None
    ready: Optional[float] = None
    label: Optional[str] = None
    effectiveness: Optional[Dict[str, Any]] = None
    duration_basis: str = Field(..., alias="durationBasis")
    ready_basis: Optional[str] = Field(None, alias="readyBasis")


class CoverageLaneModel(ViewModelBase):
    id: str
    spell_id: int = Field(..., alias="spellId")
    name: str
    icon: str
    description: str
    kind: Literal["boss", "healer"]
    events: List[CoverageEventModel]
    duration: Optional[float] = None
    cooldown: Optional[float] = None
    player: Optional[str] = None
    spec: Optional[str] = None
    timing_basis: str = Field(..., alias="timingBasis")
    dynamic: bool = False
    shown_by_default: bool = Field(True, alias="shownByDefault")
    notes: List[str] = Field(default_factory=list)
    modifiers: List[str] = Field(default_factory=list)


class CoveragePullModel(ViewModelBase):
    id: str
    label: str
    fight_id: int = Field(..., alias="fightId")
    report_code: str = Field(..., alias="reportCode")
    duration: float
    kill: bool
    lanes: List[CoverageLaneModel]
    url: str
    pressure: List[Dict[str, Any]]
    warnings: List[str]


class CoverageTimelineModel(ViewModelBase):
    boss: str
    patch: str
    bin_seconds: int = Field(..., alias="binSeconds")
    pulls: List[CoveragePullModel]


class CoverageContentModel(ViewModelBase):
    variant: Literal["timeline"] = "timeline"
    timeline: CoverageTimelineModel


def build_cooldown_coverage_page(timeline, report_id):
    # Imported here to avoid a cycle with ReportContentModel's timeline field.
    from .common import ReportPageModel, ReportHeaderModel
    return ReportPageModel(
        reportId=report_id, title="Cooldown Coverage Report",
        reportCode=", ".join(dict.fromkeys(p["reportCode"] for p in timeline["pulls"])),
        header=ReportHeaderModel(subtitle=f"{timeline['boss']} · Recorded casts, healing windows and raid pressure"),
        content=CoverageContentModel(timeline=CoverageTimelineModel(**timeline)),
        footnotes=[
            "Solid windows show nominal catalogue durations unless a matching self buff provides an observed duration. Channels can end early or scale with haste.",
            "Dashed recovery and ready markers are estimates from base values and recorded talents. Dynamic recovery, resets and unrecorded talents can change availability.",
            "Stasis distinguishes preparation (Store) from the recorded Release. Recovery is estimated from release; without a recorded release no ready marker is inferred.",
            "Raid pressure = health damage excluding overkill + healing absorbed when consumed, per second in 2-second bins. It does not measure outstanding heal-absorb shields or damage prevented by mitigation.",
            "Catalogue: supplied Midnight 12.1 research, 24 cooldowns and 68 tracked abilities. Boss markers are recorded casts; catalogue display durations are not treated as verified effect durations.",
        ],
    )
