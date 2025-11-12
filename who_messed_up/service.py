"""
Compatibility layer that re-exports the public backend services.
"""
from __future__ import annotations

from .services.common import (
    DEFAULT_GHOST_MISS_MODE,
    FightSelectionError,
    GhostMissMode,
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    TokenError,
    normalize_ghost_miss_mode,
)
from .services.dimensius import (
    AddDamageEntry,
    AddDamageSummary,
    fetch_dimensius_add_damage_summary,
)
from .services.ghosts import (
    GhostEntry,
    GhostEvent,
    GhostSummary,
    fetch_ghost_summary,
)
from .services.hits import HitSummary, fetch_hit_summary
from .services.phase_damage import (
    PhaseDamageEntry,
    PhaseDamageSummary,
    PhaseMetric,
    fetch_phase_damage_summary,
)
from .services.phases import PhasePlayerEntry, PhaseSummary, fetch_phase_summary

__all__ = [
    "AddDamageEntry",
    "AddDamageSummary",
    "DEFAULT_GHOST_MISS_MODE",
    "FightSelectionError",
    "GhostEntry",
    "GhostEvent",
    "GhostMissMode",
    "GhostSummary",
    "HitSummary",
    "PhaseDamageEntry",
    "PhaseDamageSummary",
    "PhaseMetric",
    "PhasePlayerEntry",
    "PhaseSummary",
    "ROLE_PRIORITY",
    "ROLE_UNKNOWN",
    "TokenError",
    "fetch_dimensius_add_damage_summary",
    "fetch_ghost_summary",
    "fetch_hit_summary",
    "fetch_phase_damage_summary",
    "fetch_phase_summary",
    "normalize_ghost_miss_mode",
]
