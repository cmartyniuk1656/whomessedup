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
    healing_consumable_ability_names,
)
from .services.wcl_report_discovery import (
    DiscoveredGuild,
    DiscoveredReport,
    GuildNotFoundError,
    GuildReportDiscovery,
    WarcraftLogsCredentialsError,
    discover_guild_reports,
)
from .services.boss_manifests import (
    BELOREN_CHILD_OF_ALAR_MANIFEST,
    BOSS_MANIFESTS,
    CROWN_OF_THE_COSMOS_MANIFEST,
    ENTOMBED_SENTINELS_HEROIC_MANIFEST,
    IMPERATOR_AVERZIAN_MANIFEST,
    LIGHTBLINDED_VANGUARD_MANIFEST,
    MANIFEST_TIERS,
    MIDNIGHT_FALLS_MANIFEST,
    NEK_ZALI_THE_SOULCOILER_HEROIC_MANIFEST,
    NEK_ZALI_THE_SOULCOILER_MYTHIC_MANIFEST,
    THE_LOST_EXPLORERS_HEROIC_MANIFEST,
    VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST,
    SSZORAK_HEROIC_MANIFEST,
    THE_TWIN_FANGS_HEROIC_MANIFEST,
    THE_COILED_ALTAR_HEROIC_MANIFEST,
    ULA_TEK_HEROIC_MANIFEST,
    VORASIUS_MANIFEST,
    BossAbilityMetadata,
    BossManifest,
    get_boss_manifest,
)
from .services.avoidable_damage import AvoidableDamageEntry, AvoidableDamageEvent, AvoidableDamageSummary
from .services.beloren_child_of_alar_damage import fetch_beloren_child_of_alar_damage_summary
from .services.beloren_child_of_alar_avoidable_damage import (
    fetch_beloren_child_of_alar_avoidable_damage_summary,
)
from .services.beloren_child_of_alar_deaths import fetch_beloren_child_of_alar_death_summary
from .services.beloren_child_of_alar_light_void_mistakes import (
    BelorenLightVoidMistakeEntry,
    BelorenLightVoidMistakeEvent,
    BelorenLightVoidMistakeSummary,
    fetch_beloren_child_of_alar_light_void_mistake_summary,
)
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
from .services.crown_of_the_cosmos_avoidable_damage import fetch_crown_of_the_cosmos_avoidable_damage_summary
from .services.crown_of_the_cosmos_deaths import fetch_crown_of_the_cosmos_death_summary
from .services.crown_of_the_cosmos_silver_hits import (
    CrownSilverHitEntry,
    CrownSilverHitEvent,
    CrownSilverHitSummary,
    fetch_crown_of_the_cosmos_silver_hit_summary,
)
from .services.crown_of_the_cosmos_null_corona_dispels import (
    CrownNullCoronaDispelEntry,
    CrownNullCoronaDispelEvent,
    CrownNullCoronaDispelSummary,
    fetch_crown_of_the_cosmos_null_corona_dispel_summary,
)
from .services.lightblinded_vanguard_cooldowns import fetch_lightblinded_vanguard_cooldown_summary
from .services.lightblinded_vanguard_deaths import fetch_lightblinded_vanguard_death_summary
from .services.midnight_falls_fuckups import (
    MidnightFallsFuckupEntry,
    MidnightFallsFuckupEvent,
    MidnightFallsFuckupSummary,
    fetch_midnight_falls_fuckup_summary,
)
from .services.the_twin_fangs_fuckups import (
    TwinFangsFuckupEntry,
    TwinFangsFuckupEvent,
    TwinFangsFuckupSummary,
    fetch_the_twin_fangs_fuckup_summary,
)
from .services.nek_zali_the_soulcoiler_avoidable_damage import (
    fetch_nek_zali_the_soulcoiler_avoidable_damage_summary,
)
from .services.nek_zali_the_soulcoiler_damage import fetch_nek_zali_the_soulcoiler_damage_summary
from .services.nek_zali_the_soulcoiler_deaths import fetch_nek_zali_the_soulcoiler_death_summary
from .services.nek_zali_the_soulcoiler_mechanics import (
    AddDamageSet,
    CremationCarrier,
    EssenceRendApplication,
    EssenceRendSet,
    KillSquadDamageContribution,
    KillSquadEntrant,
    KillSquadSet,
    MechanicsReportView,
    NekZaliMechanicsSummary,
    PyreSet,
    PyreCorpseMiss,
    PyreSoaker,
    fetch_nek_zali_mechanics_summary,
)
from .services.entombed_sentinels_avoidable_damage import (
    fetch_entombed_sentinels_avoidable_damage_summary,
)
from .services.entombed_sentinels_damage import fetch_entombed_sentinels_damage_summary
from .services.entombed_sentinels_deaths import fetch_entombed_sentinels_death_summary
from .services.the_lost_explorers_avoidable_damage import fetch_the_lost_explorers_avoidable_damage_summary
from .services.the_lost_explorers_damage import fetch_the_lost_explorers_damage_summary
from .services.the_lost_explorers_deaths import fetch_the_lost_explorers_death_summary
from .services.vashnik_the_malignant_avoidable_damage import fetch_vashnik_the_malignant_avoidable_damage_summary
from .services.vashnik_the_malignant_damage import fetch_vashnik_the_malignant_damage_summary
from .services.vashnik_the_malignant_deaths import fetch_vashnik_the_malignant_death_summary
from .services.sszorak_avoidable_damage import fetch_sszorak_avoidable_damage_summary
from .services.sszorak_damage import fetch_sszorak_damage_summary
from .services.sszorak_deaths import fetch_sszorak_death_summary
from .services.sszorak_tempest import (
    SszorakTempestEntry,
    SszorakTempestEvent,
    SszorakTempestSummary,
    fetch_sszorak_tempest_summary,
)
from .services.mechanic_scorecard_types import (
    MechanicDefinition,
    MechanicObservation,
    MechanicScoreEntry,
    MechanicScoreView,
    MechanicScorecardSummary,
)
from .services.mechanic_scorecards import fetch_mechanic_scorecard_summary
from .services.the_twin_fangs_avoidable_damage import fetch_the_twin_fangs_avoidable_damage_summary
from .services.the_twin_fangs_damage import fetch_the_twin_fangs_damage_summary
from .services.the_twin_fangs_deaths import fetch_the_twin_fangs_death_summary
from .services.the_coiled_altar_avoidable_damage import fetch_the_coiled_altar_avoidable_damage_summary
from .services.the_coiled_altar_damage import fetch_the_coiled_altar_damage_summary
from .services.the_coiled_altar_deaths import fetch_the_coiled_altar_death_summary
from .services.ula_tek_avoidable_damage import fetch_ula_tek_avoidable_damage_summary
from .services.ula_tek_damage import fetch_ula_tek_damage_summary
from .services.ula_tek_deaths import fetch_ula_tek_death_summary
from .services.ula_tek_fuckups import (
    UlaTekFuckupEntry,
    UlaTekFuckupEvent,
    UlaTekFuckupSummary,
    fetch_ula_tek_fuckup_summary,
)
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
from .services.report_monitoring import (
    ReportWatchFight,
    ReportWatchSnapshot,
    clear_report_watch_cache,
    fetch_report_watch_snapshot,
)
from .services.report_pulls import ReportPull, build_report_pulls, report_pull_view_id
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
    "BELOREN_CHILD_OF_ALAR_MANIFEST",
    "BelorenLightVoidMistakeEntry",
    "BelorenLightVoidMistakeEvent",
    "BelorenLightVoidMistakeSummary",
    "BOSS_MANIFESTS",
    "BossAbilityMetadata",
    "BossManifest",
    "CROWN_OF_THE_COSMOS_MANIFEST",
    "ENTOMBED_SENTINELS_HEROIC_MANIFEST",
    "CrownNullCoronaDispelEntry",
    "CrownNullCoronaDispelEvent",
    "CrownNullCoronaDispelSummary",
    "CrownSilverHitEntry",
    "CrownSilverHitEvent",
    "CrownSilverHitSummary",
    "DEFAULT_GHOST_MISS_MODE",
    "DEATH_REPORT_HEALING_CONSUMABLES",
    "DeathReportEntry",
    "DeathReportEvent",
    "DeathReportDamageHit",
    "DeathReportSummary",
    "DiscoveredGuild",
    "DiscoveredReport",
    "FightSelectionError",
    "GuildNotFoundError",
    "GuildReportDiscovery",
    "GhostEntry",
    "GhostEvent",
    "GhostMissMode",
    "GhostSummary",
    "HitSummary",
    "LightblindedVanguardDispelEntry",
    "LightblindedVanguardDispelEvent",
    "LightblindedVanguardDispelSummary",
    "LIGHTBLINDED_VANGUARD_MANIFEST",
    "MIDNIGHT_FALLS_MANIFEST",
    "NEK_ZALI_THE_SOULCOILER_HEROIC_MANIFEST",
    "NEK_ZALI_THE_SOULCOILER_MYTHIC_MANIFEST",
    "THE_LOST_EXPLORERS_HEROIC_MANIFEST",
    "VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST",
    "SSZORAK_HEROIC_MANIFEST",
    "THE_TWIN_FANGS_HEROIC_MANIFEST",
    "THE_COILED_ALTAR_HEROIC_MANIFEST",
    "ULA_TEK_HEROIC_MANIFEST",
    "CooldownUsageEntry",
    "CooldownUsageEvent",
    "CooldownUsageSummary",
    "HealingConsumable",
    "HealingConsumableStatus",
    "healing_consumable_ability_names",
    "IMPERATOR_AVERZIAN_MANIFEST",
    "MANIFEST_TIERS",
    "MidnightFallsFuckupEntry",
    "MidnightFallsFuckupEvent",
    "MidnightFallsFuckupSummary",
    "TwinFangsFuckupEntry",
    "TwinFangsFuckupEvent",
    "TwinFangsFuckupSummary",
    "UlaTekFuckupEntry",
    "UlaTekFuckupEvent",
    "UlaTekFuckupSummary",
    "PhaseDamageEntry",
    "PhaseDamageSummary",
    "PhaseMetric",
    "PhasePlayerEntry",
    "PhaseSummary",
    "ROLE_PRIORITY",
    "ROLE_UNKNOWN",
    "ReportPull",
    "ReportWatchFight",
    "ReportWatchSnapshot",
    "TokenError",
    "VORASIUS_MANIFEST",
    "WarcraftLogsCredentialsError",
    "OBLIVION_FILTER_DEFAULT",
    "fetch_dimensius_add_damage_summary",
    "build_report_pulls",
    "clear_report_watch_cache",
    "discover_guild_reports",
    "fetch_report_watch_snapshot",
    "fetch_dimensius_phase_one_summary",
    "fetch_dimensius_priority_damage_summary",
    "fetch_dimensius_death_summary",
    "fetch_cooldown_usage_summary",
    "fetch_crown_of_the_cosmos_avoidable_damage_summary",
    "fetch_crown_of_the_cosmos_death_summary",
    "fetch_crown_of_the_cosmos_null_corona_dispel_summary",
    "fetch_crown_of_the_cosmos_silver_hit_summary",
    "fetch_beloren_child_of_alar_avoidable_damage_summary",
    "fetch_beloren_child_of_alar_damage_summary",
    "fetch_beloren_child_of_alar_death_summary",
    "fetch_beloren_child_of_alar_light_void_mistake_summary",
    "fetch_ghost_summary",
    "fetch_hit_summary",
    "fetch_phase_damage_summary",
    "fetch_phase_summary",
    "normalize_ghost_miss_mode",
    "report_pull_view_id",
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
    "fetch_midnight_falls_fuckup_summary",
    "fetch_the_twin_fangs_fuckup_summary",
    "fetch_nek_zali_the_soulcoiler_avoidable_damage_summary",
    "fetch_nek_zali_the_soulcoiler_damage_summary",
    "fetch_nek_zali_the_soulcoiler_death_summary",
    "fetch_nek_zali_mechanics_summary",
    "fetch_entombed_sentinels_avoidable_damage_summary",
    "fetch_entombed_sentinels_damage_summary",
    "fetch_entombed_sentinels_death_summary",
    "fetch_the_lost_explorers_avoidable_damage_summary",
    "fetch_the_lost_explorers_damage_summary",
    "fetch_the_lost_explorers_death_summary",
    "fetch_vashnik_the_malignant_avoidable_damage_summary",
    "fetch_vashnik_the_malignant_damage_summary",
    "fetch_vashnik_the_malignant_death_summary",
    "fetch_sszorak_avoidable_damage_summary",
    "fetch_sszorak_damage_summary",
    "fetch_sszorak_death_summary",
    "SszorakTempestEntry",
    "SszorakTempestEvent",
    "SszorakTempestSummary",
    "fetch_sszorak_tempest_summary",
    "MechanicDefinition",
    "MechanicObservation",
    "MechanicScoreEntry",
    "MechanicScoreView",
    "MechanicScorecardSummary",
    "MechanicsReportView",
    "AddDamageSet",
    "NekZaliMechanicsSummary",
    "EssenceRendApplication",
    "EssenceRendSet",
    "KillSquadDamageContribution",
    "KillSquadEntrant",
    "KillSquadSet",
    "fetch_mechanic_scorecard_summary",
    "fetch_the_twin_fangs_avoidable_damage_summary",
    "fetch_the_twin_fangs_damage_summary",
    "fetch_the_twin_fangs_death_summary",
    "fetch_the_coiled_altar_avoidable_damage_summary",
    "fetch_the_coiled_altar_damage_summary",
    "fetch_the_coiled_altar_death_summary",
    "fetch_ula_tek_avoidable_damage_summary",
    "fetch_ula_tek_damage_summary",
    "fetch_ula_tek_death_summary",
    "fetch_ula_tek_fuckup_summary",
    "fetch_vorasius_avoidable_damage_summary",
    "fetch_vorasius_damage_summary",
    "fetch_vorasius_death_summary",
    "get_boss_manifest",
]
