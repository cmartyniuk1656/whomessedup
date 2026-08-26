"""
Heroic Sszorak ability and target metadata for Midnight Season 2.

Observed in Warcraft Logs report bHB9CK3yQnN2AmYq, fight 7
(encounter 3420), then cross-checked against Method's Heroic guide and live
spell descriptions.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


SSZORAK_HEROIC_MANIFEST = BossManifest(
    boss_id="sszorak",
    boss_name="Sszorak",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="sszorak",
            label="Sszorak",
            enemy_name="Sszorak",
            bucket=EncounterTargetBucket.BOSS,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Ula'tek's Presence",
            game_id=1285965,
            description="The Altar of the Six Winds deals Nature damage to the entire raid every two seconds.",
            url="https://www.wowhead.com/spell=1285965",
            tags=("Raid Damage", "Unavoidable", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Mutilated Gash",
            game_id=1285998,
            description=(
                "Players who intentionally soak Mutilate share a long Nature damage-over-time effect and become "
                "highly vulnerable to the next Mutilate, requiring two alternating soak groups."
            ),
            url="https://www.wowhead.com/spell=1285998",
            tags=("Soak", "Required Mechanic", "DoT", "Alternating Groups"),
        ),
        BossAbilityMetadata(
            name="Viscous Cyst",
            game_id=1287205,
            description=(
                "Touching or expiring a cyst knocks players away, deals Nature damage, and applies a stacking slow. "
                "The raid deliberately uses cysts to counter Howling Maelstrom and clears the spare as a group."
            ),
            url="https://www.wowhead.com/spell=1287205",
            tags=("Required Mechanic", "Knockback", "Intermission", "Slow"),
        ),
        BossAbilityMetadata(
            name="Mutilate",
            game_id=1285999,
            description=(
                "Sszorak's frontal deals Nature damage split among the assigned soak group. Fewer than five "
                "players makes the hit deadly, so two groups alternate casts. A hit is counted as avoidable only "
                "when the player already had Mutilated Gash before this cast."
            ),
            url="https://www.wowhead.com/spell=1285999",
            tags=("Avoidable", "Conditional", "Soak", "Frontal", "Repeat Soak"),
            avoidable=True,
            avoidable_requires_active_debuff_ability_id=1277051,
            avoidable_requires_active_debuff_min_age_ms=100.0,
        ),
        BossAbilityMetadata(
            name="Venomous Surge (Detonation)",
            game_id=1306120,
            description=(
                "When Venomous Surge expires it forms a Viscous Cyst and damages the entire raid, with damage "
                "decreasing as players move farther from the marked player."
            ),
            url="https://www.wowhead.com/spell=1306120",
            tags=("Raid Damage", "Distance Falloff", "Cyst Placement"),
        ),
        BossAbilityMetadata(
            name="Raging Crosswinds (Proximity Burst)",
            game_id=1285616,
            description=(
                "When Raging Crosswinds expires on a marked player it damages players within six yards before "
                "launching the marked player. The marked player is responsible for spreading, so victims are not "
                "personally scored for this damage."
            ),
            url="https://www.wowhead.com/spell=1285616",
            tags=("Proximity", "Spread", "Marked Player Responsibility"),
        ),
        BossAbilityMetadata(
            name="Raging Crosswinds (DoT)",
            game_id=1312219,
            description="Marked players take periodic Nature damage for eight seconds before being launched.",
            url="https://www.wowhead.com/spell=1312219",
            tags=("Targeted", "DoT", "Knockup"),
        ),
        BossAbilityMetadata(
            name="Venomous Surge (DoT)",
            game_id=1312156,
            description=(
                "Marked players take unavoidable Nature damage for ten seconds while moving out to place their "
                "Viscous Cysts."
            ),
            url="https://www.wowhead.com/spell=1312156",
            tags=("Targeted", "DoT", "Cyst Placement"),
        ),
        BossAbilityMetadata(
            name="Ravage",
            game_id=1277101,
            description=(
                "Sszorak repeatedly slashes in a frontal cone. Tanks taunt between casts; anyone else struck by "
                "the tank frontal has taken avoidable damage."
            ),
            url="https://www.wowhead.com/spell=1277101",
            tags=("Avoidable", "Tank Soak", "Frontal", "Tank Swap"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Tempest",
            game_id=1287083,
            description=(
                "Poisonous vortices spiral around the arena, damaging, slowing, and applying a stacking "
                "damage-over-time effect to players who touch them."
            ),
            url="https://www.wowhead.com/spell=1287083",
            tags=("Avoidable", "Tornado", "DoT", "Slow"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Caustic Residue",
            game_id=1296667,
            description=(
                "Pools left by Caustic Claws deal periodic Nature damage and increase damage taken while a player "
                "remains inside."
            ),
            url="https://www.wowhead.com/spell=1296667",
            tags=("Avoidable", "Area Denial", "DoT", "Damage Taken Increase"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Caustic Claws",
            game_id=1305998,
            description=(
                "Sszorak flings toxin at player locations, damaging anyone within six yards of the impact and "
                "leaving Caustic Residue behind."
            ),
            url="https://www.wowhead.com/spell=1305998",
            tags=("Avoidable", "Ground Impact", "Area Denial"),
            avoidable=True,
        ),
    ),
)


__all__ = ["SSZORAK_HEROIC_MANIFEST"]
