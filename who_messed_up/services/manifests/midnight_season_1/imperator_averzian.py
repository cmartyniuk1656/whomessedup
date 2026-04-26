"""
Imperator Averzian ability metadata for Midnight Season 1.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


IMPERATOR_AVERZIAN_MANIFEST = BossManifest(
    boss_id="imperator-averzian",
    boss_name="Imperator Averzian",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig(
            slug="imperator_averzian",
            label="Imperator Averzian",
            enemy_name="Imperator Averzian",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="abyssal_voidshaper",
            label="Abyssal Voidshaper",
            enemy_name="Abyssal Voidshaper",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="abyssal_annihilator",
            label="Voidbound Annihilator",
            enemy_name="Voidbound Annihilator",
            bucket=EncounterTargetBucket.PAD_ADD,
        ),
        EncounterTargetConfig(
            slug="abyssal_malus",
            label="Abyssal Malus",
            enemy_name="Abyssal Malus",
            bucket=EncounterTargetBucket.PAD_ADD,
        ),
        EncounterTargetConfig(
            slug="voidmaw",
            label="Voidmaw",
            enemy_name="Voidmaw",
            bucket=EncounterTargetBucket.PAD_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Void Fall",
            game_id=1258883,
            description=(
                "Averzian knocks back players and rains destruction onto the field at several destinations, "
                "inflicting 350466 Shadow damage to players within 7 yards of the impact locations."
            ),
            url="https://www.wowhead.com/spell=1258883/void-fall",
            tags=("Avoidable", "Swirls"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Shadow Phalanx",
            game_id=1284786,
            description=(
                "A column of Averzian's troops march across the field, inflicting 427355 Shadow damage every "
                "1 sec to players in their path."
            ),
            url="https://www.wowhead.com/spell=1284786/shadow-phalanx",
            tags=("Avoidable", "Lines"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Umbral Collapse",
            game_id=1249262,
            description=(
                "Averzian collapses void energy around his target, inflicting 555562 Shadow damage to all "
                "players. This damage is reduced by the number of players within 10 yards of the impact location."
            ),
            url="https://www.wowhead.com/spell=1249262/umbral-collapse",
            tags=("Soak",),
        ),
        BossAbilityMetadata(
            name="Shadow's Advance",
            game_id=1251361,
            description=(
                "Averzian summons Abyssal Voidshapers onto the battlefield. As his minions emerge, they inflict "
                "291378 Shadow damage to players within 10 yards and knocks them away."
            ),
            url="https://www.wowhead.com/spell=1251361/shadows-advance",
            tags=("Avoidable", "Swirls", "Knockback"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Oblivion's Wrath",
            game_id=1260712,
            description=(
                "Averzian launches void lances outward, inflicting 350466 Shadow damage to players in their path "
                "and knocking them back."
            ),
            url="https://www.wowhead.com/spell=1260712/oblivions-wrath",
            tags=("Avoidable", "Projectiles"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="March of the Endless",
            game_id=1251583,
            description=(
                "With three adjacent portals empowering each other, Averzian tears open the void unleashing the "
                "endless march, inflicting 427355 Shadow damage every 1 sec to players in its path."
            ),
            url="https://www.wowhead.com/spell=1251583/march-of-the-endless",
            tags=("Enrage",),
        ),
        BossAbilityMetadata(
            name="Dark Upheaval",
            game_id=1249251,
            description=(
                "Averzian harnesses the Void, inflicting 143747 Shadow damage to all players. He then continues "
                "to radiate energy, inflicting 30303 Shadow damage every 1 sec."
            ),
            url="https://www.wowhead.com/spell=1249251/dark-upheaval",
            tags=("Raid Damage", "DoT"),
        ),
    ),
)


__all__ = [
    "IMPERATOR_AVERZIAN_MANIFEST",
]
