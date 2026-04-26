"""
Vorasius ability metadata for Midnight Season 1.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


VOID_BREATH_DESCRIPTION = (
    "Vorasius sweeps a deadly beam across the battlefield, immediately inflicting 3108037 Shadow damage to all "
    "players in front of him and 388505 Shadow damage every 1 sec to players caught in its path. The beam "
    "radiates Dark Energy while active, inflicting 34965 Shadow damage every 0.5 sec for 15 sec."
)

PARASITE_EXPULSION_DESCRIPTION = (
    "Vorasius shakes off parasitic Blistercreeps, spraying the battlefield with globs of dark ichor that inflict "
    "271953 Shadow damage to players within 3 yards upon impact."
)

SHADOWCLAW_SLAM_DESCRIPTION = (
    "Vorasius slams a giant claw into the ground, inflicting 699308 Shadow and 699308 Physical damage to players "
    "in the impact area and 271953 Shadow damage to all players. If the central impact fails to hit at least 1 "
    "player, Vorasius inflicts 777009 Shadow damage to all players instead. The impact of the larger claws "
    "applies Smashed and creates Void Crystals."
)

BLISTERBURST_DESCRIPTION = (
    "The Blistercreep explodes upon death, inflicting 271953 Shadow damage to players within 8 yards, increasing "
    "their damage taken by 100% for 30 sec and knocking them away. The explosion also inflicts 97126 Shadow "
    "damage to all players."
)


VORASIUS_MANIFEST = BossManifest(
    boss_id="vorasius",
    boss_name="Vorasius",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig(
            slug="vorasius",
            label="Vorasius",
            enemy_name="Vorasius",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="blistercreep",
            label="Blistercreep",
            enemy_name="Blistercreep",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Void Breath",
            game_id=1256855,
            description=VOID_BREATH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1256855/void-breath",
            tags=("Beam",),
        ),
        BossAbilityMetadata(
            name="Dark Energy",
            game_id=1280101,
            description=VOID_BREATH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1280101/dark-energy",
            tags=("Raid Damage", "DoT"),
        ),
        BossAbilityMetadata(
            name="Parasite Expulsion (Swirl)",
            game_id=1275556,
            description=PARASITE_EXPULSION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1275556/parasite-expulsion",
            tags=("Avoidable", "Swirl"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Parasite Expulsion (DoT)",
            game_id=1275558,
            description=PARASITE_EXPULSION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1275558/parasite-expulsion",
            tags=("Raid Damage", "DoT"),
        ),
        BossAbilityMetadata(
            name="Shadowclaw Slam (Raid Damage)",
            game_id=1272328,
            description=SHADOWCLAW_SLAM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1272328/shadowclaw-slam",
            tags=("Raid Damage",),
        ),
        BossAbilityMetadata(
            name="Shadowclaw Slam (Raid Damage)",
            game_id=1421808,
            description=SHADOWCLAW_SLAM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1421808/shadowclaw-slam",
            tags=("Raid Damage",),
        ),
        BossAbilityMetadata(
            name="Shadowclaw Slam (Tank Soak)",
            game_id=1281954,
            description=SHADOWCLAW_SLAM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1281954/shadowclaw-slam",
            tags=("Tank Soak", "Avoidable"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Shadowclaw Slam (Tank Soak)",
            game_id=1281906,
            description=SHADOWCLAW_SLAM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1281906/shadowclaw-slam",
            tags=("Tank Soak", "Avoidable"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Blisterburst (Swirl)",
            game_id=1269302,
            description=BLISTERBURST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1269302/blisterburst",
            tags=("Avoidable", "Swirl", "Knockback"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Blisterburst (Raid Damage)",
            game_id=1259186,
            description=BLISTERBURST_DESCRIPTION,
            tags=("Raid Damage",),
        ),
        BossAbilityMetadata(
            name="Dark Goo",
            game_id=1243270,
            description="Dark ichor that inflicts 77701 Shadow damage to players within the area every 1 sec.",
            url="https://www.wowhead.com/spell=1243270/dark-goo",
            tags=("Avoidable", "Area Denial"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Aftershock",
            game_id=1273067,
            description=(
                "Shadowclaw Slam creates seismic aftershocks that reverberate from the impact location, "
                "inflicting 466206 Physical damage to players within the area."
            ),
            url="https://www.wowhead.com/spell=1273067/aftershock",
            tags=("Avoidable", "Rings"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Primordial Roar",
            game_id=1260052,
            description=(
                "Vorasius takes a deep breath, pulling players closer before unleashing a deafening roar that "
                "inflicts 349654 Physical damage to all players and knocks them away."
            ),
            url="https://www.wowhead.com/spell=1260052/primordial-roar",
            tags=("Raid Damage", "Knockback"),
        ),
        BossAbilityMetadata(
            name="Primordial Power",
            game_id=1272950,
            description=(
                "Vorasius gathers power with each roar, radiating 17405 Shadow damage to all players every 2 sec."
            ),
            url="https://www.wowhead.com/spell=1272950/primordial-power",
            tags=("Raid Damage", "DoT"),
        ),
        BossAbilityMetadata(
            name="Overpowering Pulse",
            game_id=1244419,
            description="If no player is within reach, Vorasius pulses with deadly void energy.",
            url="https://www.wowhead.com/spell=1244419/overpowering-pulse",
            tags=("Range Enrage",),
        ),
    ),
)


__all__ = [
    "VORASIUS_MANIFEST",
]
