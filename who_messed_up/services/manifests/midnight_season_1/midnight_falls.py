"""
Midnight Falls ability metadata for Midnight Season 1.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


SHATTERED_SKY_DESCRIPTION = (
    "L'ura blankets the raid in recurring Shadow damage. The scraped reports show this as steady full-raid "
    "periodic damage from L'ura."
)

DEATHS_DIRGE_DESCRIPTION = (
    "Death's Dirge assigns Dark Runes that must be activated in the melody order. Correct activations create "
    "localized Resonance damage; failed ordering creates Dissonance raid damage."
)

PRISM_DESCRIPTION = (
    "When L'ura's prism sequence resolves, the raid takes Disintegration damage and crystals can fracture into "
    "raid-wide shrapnel and follow-up periodic damage."
)

DAWN_CRYSTAL_DESCRIPTION = (
    "Dawn Crystal effects are tied to crystal handling. Radiance occurs while a crystal is not held, Glimmering "
    "damages the crystal holder, and crystal failure effects can damage the raid."
)

HEAVENS_LANCE_DESCRIPTION = (
    "L'ura fires glass spikes into her current tank target, applying Impaled and increasing subsequent Heaven's "
    "Lance damage."
)

STARSPLINTER_DESCRIPTION = (
    "L'ura targets players with falling spikes. The initial target impact is expected, while the shards that fire "
    "out from the target should be dodged by nearby players."
)

GALVANIZE_DESCRIPTION = (
    "In the Dark Reactor, Galvanize beams interact with Void Cores, triggering Cosmic Fission and related "
    "raid-wide reactor damage."
)

DARKWELL_DESCRIPTION = (
    "Darkwell effects cover late encounter movement and phase pressure, including the Dark Reactor pool, "
    "Thunderous Well, and the final darkness mechanics."
)

DARK_CONSTELLATION_DESCRIPTION = (
    "L'ura calls down dark stars that damage impact areas and then connect into patterns that players should "
    "avoid."
)


MIDNIGHT_FALLS_MANIFEST = BossManifest(
    boss_id="midnight-falls",
    boss_name="Midnight Falls",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig(
            slug="lura",
            label="L'ura",
            enemy_name="L'ura",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="midnight_crystal",
            label="Midnight Crystal",
            enemy_name="Midnight Crystal",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="termination_matrix",
            label="Termination Matrix",
            enemy_name="Termination Matrix",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Dark Quasar",
            game_id=1282469,
            description="Jets of void energy from the Darkwell damage players standing in their path.",
            url="https://www.wowhead.com/spell=1282469/dark-quasar",
            tags=("Intermission", "Avoidable", "Beam", "Area Denial"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Heaven's Glaives",
            game_id=1254076,
            description=(
                "L'ura sends whirling glaives through the chamber. Report hits were sparse and uneven, matching "
                "a dodgeable blade mechanic."
            ),
            url="https://www.wowhead.com/spell=1254076/heavens-glaives",
            tags=("Phase 1", "Avoidable", "Blades", "Projectile"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Death's Dirge: Dark Rune",
            game_id=1249594,
            description=DEATHS_DIRGE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249594/dark-rune",
            tags=("Phase 1", "Phase 3", "Assignment", "DoT"),
        ),
        BossAbilityMetadata(
            name="Death's Dirge: Resonance",
            game_id=1249582,
            description=DEATHS_DIRGE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249582/resonance",
            tags=("Phase 1", "Phase 3", "Assignment", "Localized Damage"),
        ),
        BossAbilityMetadata(
            name="Death's Dirge: Dissonance",
            game_id=1249585,
            description=DEATHS_DIRGE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249585/dissonance",
            tags=("Phase 1", "Phase 3", "Raid Damage", "Mechanic Failure"),
        ),
        BossAbilityMetadata(
            name="Disintegration",
            game_id=1251649,
            description=PRISM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1251649/disintegration",
            tags=("Phase 1", "Raid Damage", "Prism"),
        ),
        BossAbilityMetadata(
            name="Cosmic Fracture",
            game_id=1251789,
            description=PRISM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1251789/cosmic-fracture",
            tags=("Phase 1", "Raid Damage", "Crystal", "DoT"),
        ),
        BossAbilityMetadata(
            name="Radiance",
            game_id=1282458,
            description=DAWN_CRYSTAL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1282458/radiance",
            tags=("Dawn Crystal", "Raid Damage", "Crystal Handling"),
        ),
        BossAbilityMetadata(
            name="Glimmering",
            game_id=1254398,
            description=DAWN_CRYSTAL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1254398/glimmering",
            tags=("Dawn Crystal", "Crystal Holder", "DoT"),
        ),
        BossAbilityMetadata(
            name="Light's End",
            game_id=1284699,
            description=DAWN_CRYSTAL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284699/lights-end",
            tags=("Dawn Crystal", "Raid Damage", "Mechanic Failure"),
        ),
        BossAbilityMetadata(
            name="Tears of L'ura",
            game_id=1254257,
            description=DAWN_CRYSTAL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1254257/tears-of-lura",
            tags=("Dawn Crystal", "Soak", "Crystal Handling"),
        ),
        BossAbilityMetadata(
            name="Naaru's Lament",
            game_id=1254256,
            description=DAWN_CRYSTAL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1254256/naarus-lament",
            tags=("Dawn Crystal", "Raid Damage", "Mechanic Failure"),
        ),
        BossAbilityMetadata(
            name="Terminate",
            game_id=1286276,
            description=(
                "Termination Matrix completes an interruptible frontal execution. Players hit in front of the "
                "Matrix are counted as avoidable damage."
            ),
            url="https://www.wowhead.com/spell=1286276/terminate",
            tags=("Phase 1", "Avoidable", "Frontal", "Interrupt Failure"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Heaven's Lance",
            game_id=1253878,
            description=HEAVENS_LANCE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1253878/heavens-lance",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Impaled",
            game_id=1253879,
            description=HEAVENS_LANCE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1253879/impaled",
            tags=("Tank Mechanic", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Shattered Sky",
            game_id=1249797,
            description=SHATTERED_SKY_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249797/shattered-sky",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Starsplinter (Target Impact)",
            game_id=1279581,
            description=STARSPLINTER_DESCRIPTION,
            url="https://www.wowhead.com/spell=1279581/starsplinter",
            tags=("Intermission", "Targeted", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Starsplinter (Shards)",
            game_id=1281473,
            description=STARSPLINTER_DESCRIPTION,
            url="https://www.wowhead.com/spell=1281473/starsplinter",
            tags=("Intermission", "Avoidable", "Projectiles"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Criticality",
            game_id=1281178,
            description=(
                "A chain reaction damages players near other players. Report hits clustered around repeated "
                "proximity hits, so it is treated as spread failure damage."
            ),
            url="https://www.wowhead.com/spell=1281178/criticality",
            tags=("Phase 2", "Avoidable", "Spread", "Proximity"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Galvanize",
            game_id=1284530,
            description=GALVANIZE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284530/galvanize",
            tags=("Phase 2", "Beam", "Void Core"),
        ),
        BossAbilityMetadata(
            name="Overkill Current",
            game_id=1285827,
            description=GALVANIZE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1285827/overkill-current",
            tags=("Phase 2", "Raid Damage", "Soak"),
        ),
        BossAbilityMetadata(
            name="Cosmic Fission",
            game_id=1282372,
            description=GALVANIZE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1282372/cosmic-fission",
            tags=("Phase 2", "Raid Damage", "Void Core", "DoT"),
        ),
        BossAbilityMetadata(
            name="Core Harvest",
            game_id=1282425,
            description=GALVANIZE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1282425/core-harvest",
            tags=("Phase 2", "Raid Damage", "Void Core"),
        ),
        BossAbilityMetadata(
            name="Dark Meltdown",
            game_id=1281123,
            description="L'ura expels the raid from the Dark Reactor with synchronized phase-transition damage.",
            url="https://www.wowhead.com/spell=1281123/dark-meltdown",
            tags=("Phase 2", "Raid Damage", "Phase Transition"),
        ),
        BossAbilityMetadata(
            name="Abyssal Pool",
            game_id=1282004,
            description=DARKWELL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1282004/abyssal-pool",
            tags=("Phase 2", "Raid Damage", "DoT"),
        ),
        BossAbilityMetadata(
            name="Thunderous Well",
            game_id=1254644,
            description=DARKWELL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1254644/thunderous-well",
            tags=("Phase 3", "Raid Damage", "DoT"),
        ),
        BossAbilityMetadata(
            name="The Dark Archangel",
            game_id=1251080,
            description="L'ura fires a synchronized cataclysmic blast into the raid during the final phase.",
            url="https://www.wowhead.com/spell=1251080/the-dark-archangel",
            tags=("Phase 3", "Raid Damage"),
        ),
        BossAbilityMetadata(
            name="Black Tide",
            game_id=1285719,
            description="Aftershocks from The Dark Archangel cascade from the Darkwell and damage players caught in them.",
            url="https://www.wowhead.com/spell=1285719/black-tide",
            tags=("Phase 3", "Avoidable", "Wave", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Midnight",
            game_id=1263514,
            description="Final-phase darkness damages players who are not protected by nearby Torchbearer light.",
            url="https://www.wowhead.com/spell=1263514/midnight",
            tags=("Phase 3", "Avoidable", "Darkness", "Positioning", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Dark Constellation (Impact)",
            game_id=1266584,
            description=DARK_CONSTELLATION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1266584/dark-constellation",
            tags=("Phase 3", "Avoidable", "Impact", "Swirl"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Dark Constellation (Pattern)",
            game_id=1266586,
            description=DARK_CONSTELLATION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1266586/dark-constellation",
            tags=("Phase 3", "Avoidable", "Lines", "Pattern"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Light Siphon",
            game_id=1266810,
            description=(
                "Late-fight light rifts damage nearby players while they are being handled. The report profile "
                "looked like a required soak or handling mechanic rather than personal avoidable damage."
            ),
            url="https://www.wowhead.com/spell=1266810/light-siphon",
            tags=("Phase 3", "Soak", "DoT"),
        ),
        BossAbilityMetadata(
            name="Severance",
            game_id=1276173,
            description="Mythic dimension splitting inflicts synchronized raid damage before players separate realities.",
            url="https://www.wowhead.com/spell=1276173/severance",
            tags=("Phase 3", "Raid Damage", "Mythic"),
        ),
        BossAbilityMetadata(
            name="Severed Surge",
            game_id=1287702,
            description="L'ura punishes an empty dimension with increasing raid damage.",
            url="https://www.wowhead.com/spell=1287702/severed-surge",
            tags=("Phase 3", "Raid Damage", "Mechanic Failure"),
        ),
        BossAbilityMetadata(
            name="Heaven & Hell",
            game_id=1287445,
            description="A late encounter full-raid damage effect observed during the kill pull.",
            url="https://www.wowhead.com/spell=1287445/heaven-hell",
            tags=("Phase 3", "Raid Damage"),
        ),
        BossAbilityMetadata(
            name="Void Swarm",
            game_id=1273033,
            description="A rare late encounter Shadow damage effect observed during the kill pull.",
            url="https://www.wowhead.com/spell=1273033/void-swarm",
            tags=("Phase 3", "DoT"),
        ),
    ),
)


__all__ = [
    "MIDNIGHT_FALLS_MANIFEST",
]
