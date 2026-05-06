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
from .services.consumables import (
    DEATH_REPORT_HEALING_CONSUMABLES,
    HealingConsumable,
    HealingConsumableStatus,
)
from .services.boss_manifests import (
    BOSS_MANIFESTS,
    IMPERATOR_AVERZIAN_MANIFEST,
    LIGHTBLINDED_VANGUARD_MANIFEST,
    MANIFEST_TIERS,
    VORASIUS_MANIFEST,
    BossAbilityMetadata,
    BossManifest,
    get_boss_manifest,
)
from .services.avoidable_damage import AvoidableDamageEntry, AvoidableDamageEvent, AvoidableDamageSummary
from .services.dimensius import (
    AddDamageEntry,
    AddDamageSummary,
    fetch_dimensius_add_damage_summary,
)
from .services.dimensius_phase_one import (
    DimensiusPhaseOneEntry,
    DimensiusPhaseOneSummary,
    fetch_dimensius_phase_one_summary,
)
from .services.dimensius_priority_damage import (
    DimensiusPriorityDamageSummary,
    PriorityDamageEntry,
    fetch_dimensius_priority_damage_summary,
)
from .services.dimensius_deaths import (
    DimensiusDeathEntry,
    DimensiusDeathEvent,
    DimensiusDeathSummary,
    fetch_dimensius_death_summary,
    OBLIVION_FILTER_DEFAULT,
)
from .services.dimensius_bled_out import fetch_dimensius_bled_out_summary
from .services.death_reports import DeathReportDamageHit, DeathReportEntry, DeathReportEvent, DeathReportSummary
from .services.imperator_averzian_damage import fetch_imperator_averzian_damage_summary
from .services.imperator_averzian_avoidable_damage import fetch_imperator_averzian_avoidable_damage_summary
from .services.imperator_averzian_deaths import fetch_imperator_averzian_death_summary
from .services.lightblinded_vanguard_dispels import (
    LightblindedVanguardDispelEntry,
    LightblindedVanguardDispelEvent,
    LightblindedVanguardDispelSummary,
    fetch_lightblinded_vanguard_dispel_summary,
)
from .services.lightblinded_vanguard_avoidable_damage import (
    fetch_lightblinded_vanguard_avoidable_damage_summary,
)
from .services.cooldown_usage import (
    CooldownUsageEntry,
    CooldownUsageEvent,
    CooldownUsageSummary,
    fetch_cooldown_usage_summary,
)
from .services.lightblinded_vanguard_cooldowns import fetch_lightblinded_vanguard_cooldown_summary
from .services.lightblinded_vanguard_deaths import fetch_lightblinded_vanguard_death_summary
from .services.vorasius_avoidable_damage import fetch_vorasius_avoidable_damage_summary
from .services.vorasius_damage import fetch_vorasius_damage_summary
from .services.vorasius_deaths import fetch_vorasius_death_summary
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
from .services.target_damage import (
    EncounterTargetConfig,
    EncounterTargetDamageBreakdown,
    EncounterTargetDamageEntry,
    EncounterTargetDamageSummary,
    EncounterTargetSummary,
)

__all__ = [
    "AddDamageEntry",
    "AddDamageSummary",
    "AvoidableDamageEntry",
    "AvoidableDamageEvent",
    "AvoidableDamageSummary",
    "BOSS_MANIFESTS",
    "BossAbilityMetadata",
    "BossManifest",
    "DEFAULT_GHOST_MISS_MODE",
    "DEATH_REPORT_HEALING_CONSUMABLES",
    "DeathReportEntry",
    "DeathReportEvent",
    "DeathReportDamageHit",
    "DeathReportSummary",
    "FightSelectionError",
    "GhostEntry",
    "GhostEvent",
    "GhostMissMode",
    "GhostSummary",
    "HitSummary",
    "LightblindedVanguardDispelEntry",
    "LightblindedVanguardDispelEvent",
    "LightblindedVanguardDispelSummary",
    "LIGHTBLINDED_VANGUARD_MANIFEST",
    "CooldownUsageEntry",
    "CooldownUsageEvent",
    "CooldownUsageSummary",
    "HealingConsumable",
    "HealingConsumableStatus",
    "IMPERATOR_AVERZIAN_MANIFEST",
    "MANIFEST_TIERS",
    "PhaseDamageEntry",
    "PhaseDamageSummary",
    "PhaseMetric",
    "PhasePlayerEntry",
    "PhaseSummary",
    "ROLE_PRIORITY",
    "ROLE_UNKNOWN",
    "TokenError",
    "VORASIUS_MANIFEST",
    "OBLIVION_FILTER_DEFAULT",
    "fetch_dimensius_add_damage_summary",
    "fetch_dimensius_phase_one_summary",
    "fetch_dimensius_priority_damage_summary",
    "fetch_dimensius_death_summary",
    "fetch_cooldown_usage_summary",
    "fetch_ghost_summary",
    "fetch_hit_summary",
    "fetch_phase_damage_summary",
    "fetch_phase_summary",
    "normalize_ghost_miss_mode",
    "DimensiusPhaseOneEntry",
    "DimensiusPhaseOneSummary",
    "PriorityDamageEntry",
    "DimensiusPriorityDamageSummary",
    "DimensiusDeathEntry",
    "DimensiusDeathEvent",
    "DimensiusDeathSummary",
    "fetch_dimensius_bled_out_summary",
    "EncounterTargetConfig",
    "EncounterTargetDamageBreakdown",
    "EncounterTargetDamageEntry",
    "EncounterTargetDamageSummary",
    "EncounterTargetSummary",
    "fetch_imperator_averzian_damage_summary",
    "fetch_imperator_averzian_avoidable_damage_summary",
    "fetch_imperator_averzian_death_summary",
    "fetch_lightblinded_vanguard_avoidable_damage_summary",
    "fetch_lightblinded_vanguard_cooldown_summary",
    "fetch_lightblinded_vanguard_death_summary",
    "fetch_lightblinded_vanguard_dispel_summary",
    "fetch_vorasius_avoidable_damage_summary",
    "fetch_vorasius_damage_summary",
    "fetch_vorasius_death_summary",
    "get_boss_manifest",
]
