"""Shared evidence rows for mechanics reports; timestamps are report-relative.

Calculators retain observed facts and explicit uncertainty. Renderers select
pulls by report and fight before aggregating contributions or counts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .report_pulls import ReportPull


@dataclass
class MechanicDetail:
    section: str
    label: str
    timestamp: Optional[float] = None
    description: str = ""
    badges: List[str] = field(default_factory=list)
    tone: Optional[str] = None


@dataclass
class MechanicSet:
    source_report_code: str
    fight_id: int
    pull_index: int
    fight_start: float
    start: float
    index: int
    label: str
    values: Dict[str, object] = field(default_factory=dict)
    players: Dict[str, List[str]] = field(default_factory=dict)
    details: List[MechanicDetail] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)
    soak_counts: Dict[str, int] = field(default_factory=dict)
    dispels: List[DispelRecord] = field(default_factory=list)
    dispel_counts: Dict[str, int] = field(default_factory=dict)
    boss_healing: Dict[str, float] = field(default_factory=dict)


@dataclass
class DispelRecord:
    player: str
    dispeller: str
    timestamp: float
    delay: float


@dataclass
class MechanicsSummary:
    report_code: str
    sets: Dict[str, List[MechanicSet]]
    pulls: List[ReportPull] = field(default_factory=list)
    player_classes: Dict[str, Optional[str]] = field(default_factory=dict)
    source_reports: List[str] = field(default_factory=list)

    @property
    def pull_count(self) -> int:
        return len(self.pulls)
