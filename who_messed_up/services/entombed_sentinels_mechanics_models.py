"""Analysis records shared by the Sentinels calculators and report renderer.

Sets retain observed evidence rather than assigning player scores. A detail's
timestamp is report-relative; the renderer converts it to a pull offset.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .report_pulls import ReportPull


REPORT_ID = "entombed-sentinels-mythic-mechanics"
REPORT_TITLE = "Mythic Entombed Sentinels - Mechanics"
REPORT_DESCRIPTION = "Review assignments, soaks, puzzle resolutions, and adds."
REPORT_DEFAULT_FIGHT = "Entombed Sentinels"
VIEWS = {
    "protovenom": "Protovenom Pairing",
    "helical-toxins": "Helical Toxins",
    "miasma": "Miasma Soaks",
    "droplets": "Droplet Handling",
    "coagulations": "Coagulation Kills",
    "dispels": "Dispels",
    "intermission": "Intermission Resolution",
}
REPORT_FOOTNOTES = (
    "Blighted Blood dispels are grouped by cast, including staggered applications. Only logged dispel events receive credit; an aura removal alone is not a dispel.",
    "Intermission clear time runs from the first Helical Toxins application to the last successful removal. Deaths, bursts, expiry, and missing removals exclude a window from completion averages. Boss healing includes the full observed Vitriolic Stasis window, including its final heal, which may follow the last toxin clear.",
    "Assignments come from aura applications, not damage ticks. Removed alive means an early aura removal was observed without a nearby death; it does not identify a pairing partner or prove the removal method. Death, expiry, and pull-end cleanup are not counted as successful resolutions.",
    "Protovenom Eruption and Cultivated Burst damage identifies victims, not who caused the collision. Helical Toxins initial stacks are shown only when explicitly logged; this report often exposes stack changes without initial counts.",
    "Miasma soakers are players with an impact damage event, including fully absorbed hits. Deaths within two seconds of impact are temporal associations, not necessarily kills by Miasma. No absent-player blame is inferred without assignments.",
    "Droplet pop hits are observed player damage events, not guaranteed unique droplets. Noxious Blast bursts group hits within 100 ms; simultaneous explosions may share a burst. Victim counts are not missed-droplet counts.",
    "Coagulations are matched by actor, instance, and separate lives when IDs are reused. Observed lifetime begins at the first instance-specific signal. Summon-to-first-hit delay includes spawn travel time. Buff-only signals do not confirm an additional add. Damage includes pets credited to their owners, excludes overkill and post-death residue, and Contaminate damage is matched to that life.",
)


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
class SentinelsMechanicsSummary:
    report_code: str
    sets: Dict[str, List[MechanicSet]]
    pulls: List[ReportPull] = field(default_factory=list)
    player_classes: Dict[str, Optional[str]] = field(default_factory=dict)
    source_reports: List[str] = field(default_factory=list)

    @property
    def pull_count(self) -> int:
        return len(self.pulls)
