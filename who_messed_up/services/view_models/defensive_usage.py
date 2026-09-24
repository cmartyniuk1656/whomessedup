"""Separate defensive timeline contract, sharing boss and death presentation data."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from .cooldown_coverage import ViewModelBase, CoverageLaneModel, CoverageDeathModel


class DefensiveProtectionModel(ViewModelBase):
    damage_taken: float = Field(alias="damageTaken")
    absorbed: float
    mitigated: float
    overkill: float
    immune_events: int = Field(alias="immuneEvents")
    damage_events: int = Field(alias="damageEvents")
    mitigation_events: int = Field(alias="mitigationEvents")
    spell_absorbed: float = Field(alias="spellAbsorbed")
    subject: str


class DefensiveAttributionModel(ViewModelBase):
    estimated_reduction: Optional[float] = Field(None, alias="estimatedReduction")
    matched_absorbed: float = Field(alias="matchedAbsorbed")
    evaluated_hits: int = Field(alias="evaluatedHits")
    status: Literal["estimated", "unavailable"]
    note: str


class DefensiveReadinessModel(ViewModelBase):
    cooldown: Optional[float] = None
    charges: Optional[int] = None
    status: Literal["estimated", "unavailable"]
    note: str


class DefensiveEventModel(ViewModelBase):
    time: float
    end: float
    duration_basis: str = Field(alias="durationBasis")
    ready: Optional[float] = None
    ready_basis: Optional[str] = Field(None, alias="readyBasis")
    ready_note: Optional[str] = Field(None, alias="readyNote")
    target: str
    target_id: Optional[int] = Field(None, alias="targetId")
    self_use: bool = Field(alias="selfUse")
    origin: str
    damage_taken: float = Field(alias="damageTaken")
    protection: DefensiveProtectionModel
    attribution: Optional[DefensiveAttributionModel] = None
    observation_seconds: float = Field(alias="observationSeconds")
    effective_healing: float = Field(alias="effectiveHealing")
    overhealing: float
    nearby_boss: Optional[Dict[str, Any]] = Field(None, alias="nearbyBoss")


class DefensiveAbilityModel(ViewModelBase):
    id: str
    spell_id: int = Field(alias="spellId")
    name: str
    category: str
    icon: str
    description: str
    duration: Optional[float] = None
    access: str
    modifiers: List[str]
    spec: str
    readiness: Optional[DefensiveReadinessModel] = None
    events: List[DefensiveEventModel]


class DefensiveHealthPointModel(ViewModelBase):
    time: float
    percent: float
    break_before: bool = Field(False, alias="breakBefore")


class DefensivePlayerModel(ViewModelBase):
    id: str
    actor_id: int = Field(alias="actorId")
    name: str
    spec_id: Optional[int] = Field(None, alias="specId")
    spec: str
    role: str
    lanes: List[DefensiveAbilityModel]
    pressure: List[Dict[str, Any]]
    health: List[DefensiveHealthPointModel] = Field(default_factory=list)
    deaths: List[CoverageDeathModel]
    build_known: bool = Field(alias="buildKnown")


class DefensivePullModel(ViewModelBase):
    id: str
    label: str
    fight_id: int = Field(alias="fightId")
    report_code: str = Field(alias="reportCode")
    duration: float
    kill: bool
    url: str
    players: List[DefensivePlayerModel]
    boss_lanes: List[CoverageLaneModel] = Field(alias="bossLanes")
    deaths: List[CoverageDeathModel]
    pressure: List[Dict[str, Any]]


class DefensiveTimelineModel(ViewModelBase):
    boss: str
    patch: str
    catalogue_date: str = Field(alias="catalogueDate")
    bin_seconds: int = Field(alias="binSeconds")
    pulls: List[DefensivePullModel]
    references: Dict[str, Dict[str, Any]]


class DefensiveContentModel(ViewModelBase):
    variant: Literal["defensive_timeline"] = "defensive_timeline"
    timeline: DefensiveTimelineModel


def build_defensive_usage_page(timeline, report_id):
    from .common import ReportPageModel, ReportHeaderModel
    return ReportPageModel(reportId=report_id, title="Defensive Usage Report",
        reportCode=", ".join(dict.fromkeys(p["reportCode"] for p in timeline["pulls"])),
        header=ReportHeaderModel(subtitle=f"{timeline['boss']} · Personal defensives, consumables and actual damage timings"),
        content=DefensiveContentModel(timeline=DefensiveTimelineModel(**timeline)),
        footnotes=[
            "Uses are recorded casts. Self defensives, raid/group casts and casts on other players remain distinct. Pre-pull casts and effects without a cast event are not counted. A cast event alone does not prove whether a proc made it free or automatic.",
            "Windows use paired same-source/recipient auras when available; otherwise the research duration is nominal. Diamonds estimate talent-adjusted readiness or sequential charge replenishment after recorded uses. Charge estimates assume full charges at pull start. Unsupported recovery, resets, free/proc activations and unvalidated stacking remain unknown; no inventory or missed-use verdict is inferred.",
            "By default, blue shows shielding matched to tracked casts, grey shows other shielding and green estimates supported cooldown damage reduction during confirmed recipient buffs. Armor and passive mitigation are excluded from green; Show all mitigation restores WCL's all-source totals. Unsupported effects have no estimate, not a zero-value score.",
            "Reduction estimates remove the supported cooldown multiplier from post-reduction, pre-absorb damage while holding other effects fixed. Talent changes and observed Sentinel stacks are applied. Each estimate is bounded by recorded mitigation. Overlapping casts have separate marginal estimates that must not be added; the graph uses a combined estimate. Immunity, avoidance, death-save and deferred-damage benefits are not priced.",
            "Known baseline/selected abilities and recorded casts are shown. Missing talent data is unknown. No observed healthstone or potion use does not prove one was carried or available.",
            "Across-pull rows preserve each pull's actual timings. Mechanic alignment uses the selected occurrence in each pull; pulls without that occurrence are excluded explicitly. Players are keyed by report and actor ID to avoid merging namesakes.",
        ])
