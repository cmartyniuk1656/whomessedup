"""
Heroic Nek'zali the Soulcoiler ability and target metadata for Midnight Season 2.

Observed from Warcraft Logs report ZARtb8Dxjhg9H4BF, fight 3 (encounter 3470),
then cross-checked against the Wowhead encounter journal and Method's Heroic guide.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


CORPSE_BLIGHT_DESCRIPTION = (
    "A defeated Restless Amani erupts, damaging the raid immediately and applying stacking periodic Plague "
    "damage. On Heroic, defeated Amani leave a Vessel of Awakening behind."
)

LATENT_CULTIST_DESCRIPTION = (
    "A Latent Cultist materializes when Essence Rend ends, damaging players near its appearance and leaving "
    "persistent necrotic area denial that damages and slows players standing within it."
)

CREMATION_DESCRIPTION = (
    "Soul fire erupts around affected players, damaging them over time and incinerating Restless Amani or "
    "Vessels of Awakening within the impact area."
)


NEK_ZALI_THE_SOULCOILER_HEROIC_MANIFEST = BossManifest(
    boss_id="nek-zali-the-soulcoiler",
    boss_name="Nek'zali the Soulcoiler",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="nek_zali_the_soulcoiler",
            label="Nek'zali the Soulcoiler",
            enemy_name="Nek'zali the Soulcoiler",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="restless_amani",
            label="Restless Amani",
            enemy_name="Restless Amani",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="echo_of_jawae",
            label="Echo of Jawae",
            enemy_name="Echo of Jawae",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        # This clean kill had no Soulcoil Well damage events. The live damage
        # subspell and its avoidability come from the guide/journal cross-check.
        BossAbilityMetadata(
            name="Soulcoil Well",
            game_id=1290390,
            description=(
                "Standing in the central Soulcoil Well inflicts periodic Shadow damage. A player who dies inside "
                "the well is Soulcoiled and triggers another Soulcoil Rite."
            ),
            url="https://www.wowhead.com/spell=1290390/soulcoil-well",
            tags=("Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Soulcoil Rite",
            game_id=1288772,
            description=(
                "The Soulcoil Well grants Nek'zali energy and inflicts an immediate raid-wide hit followed by "
                "stacking periodic damage. On Heroic, each rite also applies Ritual Burn."
            ),
            url="https://www.wowhead.com/spell=1288772/soulcoil-rite",
            tags=("Raid Damage", "DoT", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Corpse Blight (Burst)",
            game_id=1294729,
            description=CORPSE_BLIGHT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1294729/corpse-blight",
            tags=("Raid Damage",),
        ),
        BossAbilityMetadata(
            name="Corpse Blight (DoT)",
            game_id=1307939,
            description=CORPSE_BLIGHT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1307939/corpse-blight",
            tags=("Raid Damage", "DoT", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Possession Barrage",
            game_id=1292034,
            description=(
                "Nek'zali fires spectral echoes toward the active tank. Each impact damages the raid, with damage "
                "reduced by the distance traveled; players between the boss and tank can detonate an echo early."
            ),
            url="https://www.wowhead.com/spell=1292034/possession-barrage",
            tags=("Raid Damage", "Tank Mechanic", "Distance Check"),
        ),
        BossAbilityMetadata(
            name="Uncoiling",
            game_id=1292315,
            description=(
                "After the intermission, Nek'zali overflows the Soulcoil Well and continuously damages the raid "
                "until defeated."
            ),
            url="https://www.wowhead.com/spell=1292315/uncoiling",
            tags=("Raid Damage", "DoT", "Final Phase"),
        ),
        BossAbilityMetadata(
            name="Latent Cultist (Manifestation)",
            game_id=1292899,
            description=LATENT_CULTIST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1292899/latent-cultist",
            tags=("Avoidable", "Area Denial", "Impact"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Latent Cultist (Area)",
            game_id=1288554,
            description=LATENT_CULTIST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1288554/latent-cultist",
            tags=("Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Vessel of Awakening",
            game_id=1297630,
            description=(
                "A Restless Amani that repossesses a Heroic corpse becomes empowered and inflicts repeated "
                "raid-wide Shadow damage."
            ),
            url="https://www.wowhead.com/spell=1297630/vessel-of-awakening",
            tags=("Raid Damage", "DoT", "Add Failure"),
        ),
        BossAbilityMetadata(
            name="Hollowing Strikes",
            game_id=1284109,
            description=(
                "Nek'zali's attacks apply stacking periodic Shadow damage to the tank and reduce healing and "
                "absorption received."
            ),
            url="https://www.wowhead.com/spell=1284109/hollowing-strikes",
            tags=("Tank Mechanic", "Unavoidable", "DoT"),
        ),
        BossAbilityMetadata(
            name="Cremation",
            game_id=1289875,
            description=CREMATION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1289875/cremation",
            tags=("Targeted", "DoT", "Corpse Burn"),
        ),
        BossAbilityMetadata(
            name="Slithering Flame",
            game_id=1294933,
            description=(
                "Players not struck by Hungering Pyre receive a targeted fire DoT. On Heroic it expires into "
                "Cremation, allowing assigned players to burn remaining corpses."
            ),
            url="https://www.wowhead.com/spell=1294933/slithering-flame",
            tags=("Targeted", "DoT", "Corpse Burn"),
        ),
        BossAbilityMetadata(
            name="Essence Rend",
            game_id=1287434,
            description=(
                "Nek'zali pulls selected players inward, knocks them away, and leaves a dispellable damage-over-time "
                "effect. A Latent Cultist appears when the effect ends."
            ),
            url="https://www.wowhead.com/spell=1287434/essence-rend",
            tags=("Targeted", "DoT", "Dispel"),
        ),
        BossAbilityMetadata(
            name="Hungering Pyre",
            game_id=1289855,
            description=(
                "An Echo of Jawae creates a group soak whose damage is split among players within it. The impact "
                "also burns nearby Restless Amani corpses."
            ),
            url="https://www.wowhead.com/spell=1289855/hungering-pyre",
            tags=("Soak", "Corpse Burn"),
        ),
        BossAbilityMetadata(
            name="Anguished Echoes",
            game_id=1294846,
            description=(
                "During Soulcoil Ignition, spirits emerge from the well and damage and knock back players within "
                "their impact areas."
            ),
            url="https://www.wowhead.com/spell=1294846/anguished-echoes",
            tags=("Avoidable", "Impact", "Knockback"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Soul Transfer (Blast)",
            game_id=1295085,
            description=(
                "At the end of Soul Transfer, a surge of soul energy damages players who remain in the Echo of "
                "Jawae's blast area."
            ),
            url="https://www.wowhead.com/spell=1295085/soul-transfer",
            tags=("Avoidable", "Blast", "Intermission"),
            avoidable=True,
        ),
    ),
)


__all__ = [
    "NEK_ZALI_THE_SOULCOILER_HEROIC_MANIFEST",
]
