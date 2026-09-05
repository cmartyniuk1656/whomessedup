"""Shared data types for player mechanic scorecards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


OUTCOME_SUCCESS = "success"
OUTCOME_MISTAKE = "mistake"
OUTCOME_CONTRIBUTION = "contribution"


@dataclass(frozen=True)
class MechanicDefinition:
    id: str
    label: str
    description: str
    confidence: str
    optional: bool = False


@dataclass
class MechanicObservation:
    mechanic_id: str
    player: str
    outcome: str
    label: str
    description: str
    fight_id: int
    fight_name: str
    pull_index: int
    timestamp: float
    offset_ms: float
    ability_id: Optional[int] = None
    ability_label: Optional[str] = None
    target: Optional[str] = None
    value: Optional[float] = None
    value_label: Optional[str] = None
    source_report_code: Optional[str] = None
    pull_duration_ms: Optional[float] = None


@dataclass
class MechanicScoreEntry:
    player: str
    role: str
    class_name: Optional[str]
    pulls: int
    opportunities: int
    successes: int
    mistakes: int
    contributions: int
    success_rate: Optional[float]
    events: List[MechanicObservation] = field(default_factory=list)


@dataclass
class MechanicScoreView:
    mechanic: MechanicDefinition
    entries: List[MechanicScoreEntry]

    @property
    def opportunities(self) -> int:
        return sum(entry.opportunities for entry in self.entries)

    @property
    def successes(self) -> int:
        return sum(entry.successes for entry in self.entries)

    @property
    def mistakes(self) -> int:
        return sum(entry.mistakes for entry in self.entries)

    @property
    def contributions(self) -> int:
        return sum(entry.contributions for entry in self.entries)


@dataclass
class MechanicScorecardSummary:
    report_code: str
    boss_id: str
    boss_name: str
    fight_filter: str
    fight_ids: Optional[List[int]]
    fight_selection: str
    pull_count: int
    ignore_after_deaths: Optional[int]
    views: List[MechanicScoreView]
    player_classes: Dict[str, Optional[str]]
    player_roles: Dict[str, str]
    player_specs: Dict[str, Optional[str]]
    source_reports: List[str] = field(default_factory=list)


__all__ = [
    "MechanicDefinition",
    "MechanicObservation",
    "MechanicScoreEntry",
    "MechanicScoreView",
    "MechanicScorecardSummary",
    "OUTCOME_CONTRIBUTION",
    "OUTCOME_MISTAKE",
    "OUTCOME_SUCCESS",
]
