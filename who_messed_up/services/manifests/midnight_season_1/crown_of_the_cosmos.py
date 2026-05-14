"""
Crown of the Cosmos ability metadata for Midnight Season 1.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


ECHOING_DARKNESS_DESCRIPTION = (
    "The Undying Sentinels pulse Void damage into the raid every 2 sec. The damage increases when a Sentinel "
    "is not covered by a player in melee range."
)

SILVERSTRIKE_ARROW_DESCRIPTION = (
    "Alleria marks players and fires silver-lined arrows through them, damaging players in the line and removing "
    "Void effects from players and Voidspawn struck."
)

GRASP_OF_EMPTINESS_DESCRIPTION = (
    "Alleria anchors players to ancient obelisks with Void energy, applying a periodic damage effect and a slow. "
    "When the effect ends, the assigned player takes the final unavoidable pulse and the obelisks fire lines that "
    "should be aimed away from the raid."
)

BURSTING_EMPTINESS_DESCRIPTION = (
    "When Grasp of Emptiness expires, projectiles fire along the displayed obelisk lines. Damage taken by the "
    "assigned player as the debuff expires is excluded from avoidable attribution; other players clipped by the "
    "outgoing lines are counted as avoidable."
)

VOID_EXPULSION_DESCRIPTION = (
    "Alleria calls Void energy down near players. The impact damages the raid and leaves expanding Void Remnants "
    "where the circles were placed."
)

NULL_CORONA_DESCRIPTION = (
    "Alleria applies a large healing absorb to players. When removed, the remaining absorb jumps to another player, "
    "so dispels are normally held until the target is low or another immediate danger justifies clearing it."
)

CORRUPTING_ESSENCE_DESCRIPTION = (
    "Void Droplets erupt on death, splashing nearby players or Sentinels with Void damage and a stacking damage "
    "taken increase."
)

INTERRUPTING_TREMOR_DESCRIPTION = (
    "Demiar releases shuddering waves that damage players within the encounter area and interrupt players who "
    "are still casting."
)

RAVENOUS_ABYSS_DESCRIPTION = (
    "Vorelus devours the essence of nearby players, damaging them and sharply reducing their damage done."
)

DARK_HAND_DESCRIPTION = (
    "Morium strikes the current tank with a heavy Physical and Shadow hit and knocks them back."
)

SILVERSTRIKE_BARRAGE_DESCRIPTION = (
    "During intermissions, uncontrolled silver-lined arrows cross the room. Players intentionally take selected "
    "arrows to reset Stellar Emission, but repeated hits are dangerous."
)

STELLAR_EMISSION_DESCRIPTION = (
    "Raw Void energy pulses during intermissions, dealing periodic raid damage while increasing the pull toward "
    "the center of the arena."
)

SINGULARITY_ERUPTION_DESCRIPTION = (
    "Wild pockets of gravity erupt on the platform, damaging and knocking away players caught in the impact."
)

ORBITING_MATTER_DESCRIPTION = (
    "Stellar mass orbits Alleria during the second intermission, pulling and damaging players who collide with it."
)

COSMIC_BARRIER_DESCRIPTION = (
    "The Rift Simulacrum shields itself. While the barrier is active, it pulses damage into the raid every 1 sec."
)

SIMULACRUM_BACKLASH_DESCRIPTION = (
    "The simulacrum releases Void energy into the raid, observed in the reports as repeated raid-wide damage "
    "during the Alleria and Rift Simulacrum phase."
)

RIFT_SLASH_DESCRIPTION = (
    "The Rift Simulacrum slashes its current tank, dealing a heavy hit and applying stacking stat reduction."
)

SILVERSTRIKE_RICOCHET_DESCRIPTION = (
    "Ranger Captain's Mark sends a silver-lined arrow ricocheting through marked players. The chain is used to "
    "strip Void effects from Undying Voidspawns so they can be killed."
)

VOIDSTALKER_STING_DESCRIPTION = (
    "Alleria applies a Void-tipped arrow wound to random players, inflicting Shadow damage every 1 sec. In Phase "
    "2 it can be removed by silver arrows; in Phase 3 it must expire naturally."
)

VOID_BARRAGE_DESCRIPTION = (
    "Undying Voidspawns cast Void Barrage at players. The cast is interruptible until the Voidspawn reaches full "
    "energy, but the hit is not necessarily attributable to the targeted player."
)

GRAVITY_COLLAPSE_DESCRIPTION = (
    "Breaking an Aspect of the End tether triggers a raid-wide Gravity Collapse and leaves the tethered player "
    "vulnerable to Physical damage."
)

COSMIC_RADIATION_DESCRIPTION = (
    "Alleria radiates cosmic energy late in the encounter, observed in the reports as repeated raid-wide damage."
)

DEVOURING_COSMOS_DESCRIPTION = (
    "Alleria consumes the active platform section, covering it in a lethal void field that deals heavy damage and "
    "prevents healing until players leave the section."
)

DARK_RUSH_DESCRIPTION = (
    "Players touch a feather before a platform jump to gain Dark Rush, taking a small periodic damage effect while "
    "gaining the movement needed to cross to the next platform."
)


CROWN_OF_THE_COSMOS_MANIFEST = BossManifest(
    boss_id="crown-of-the-cosmos",
    boss_name="Crown of the Cosmos",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig(
            slug="demiar",
            label="Demiar",
            enemy_name="Demiar",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="morium",
            label="Morium",
            enemy_name="Morium",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="vorelus",
            label="Vorelus",
            enemy_name="Vorelus",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="alleria_windrunner",
            label="Alleria Windrunner",
            enemy_name="Alleria Windrunner",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="rift_simulacrum",
            label="Rift Simulacrum",
            enemy_name="Rift Simulacrum",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="undying_voidspawn",
            label="Undying Voidspawn",
            enemy_name="Undying Voidspawn",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="void_droplet",
            label="Void Droplet",
            enemy_name="Void Droplet",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="silver_simulacrum",
            label="Silver Simulacrum",
            enemy_name="Silver Simulacrum",
            bucket=EncounterTargetBucket.PAD_ADD,
            default_enabled=False,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Echoing Darkness",
            game_id=1281707,
            description=ECHOING_DARKNESS_DESCRIPTION,
            url="https://www.wowhead.com/spell=1281707/echoing-darkness",
            tags=("Phase 1", "Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Silverstrike Arrow",
            game_id=1233649,
            description=SILVERSTRIKE_ARROW_DESCRIPTION,
            url="https://www.wowhead.com/spell=1233649/silverstrike-arrow",
            tags=("Phase 1", "Targeted Line", "Required Mechanic"),
        ),
        BossAbilityMetadata(
            name="Grasp of Emptiness",
            game_id=1260027,
            description=GRASP_OF_EMPTINESS_DESCRIPTION,
            url="https://www.wowhead.com/spell=1260027/grasp-of-emptiness",
            tags=("Phase 1", "Phase 3", "Targeted DoT", "Slow", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Bursting Emptiness",
            game_id=1255378,
            description=BURSTING_EMPTINESS_DESCRIPTION,
            url="https://www.wowhead.com/spell=1255378/bursting-emptiness",
            tags=("Phase 1", "Phase 3", "Avoidable", "Line", "Projectile"),
            avoidable=True,
            avoidable_exclusion_debuff_ability_id=1260027,
            avoidable_exclusion_debuff_event_types=("removedebuff", "removedebuffstack"),
            avoidable_exclusion_debuff_window_ms=50.0,
        ),
        BossAbilityMetadata(
            name="Void Expulsion",
            game_id=1233826,
            description=VOID_EXPULSION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1233826/void-expulsion",
            tags=("Phase 1", "Phase 2", "Phase 3", "Raid Damage", "Bait", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Remnants",
            game_id=1242553,
            description=VOID_EXPULSION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242553/void-remnants",
            tags=("Phase 1", "Phase 2", "Phase 3", "Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Null Corona",
            game_id=1233865,
            description=NULL_CORONA_DESCRIPTION,
            url="https://www.wowhead.com/spell=1233865/null-corona",
            tags=("Phase 1", "Phase 3", "Dispel", "Heal Absorb", "Jump"),
        ),
        BossAbilityMetadata(
            name="Null Corona (Jump)",
            game_id=1233887,
            description=NULL_CORONA_DESCRIPTION,
            url="https://www.wowhead.com/spell=1233887/null-corona",
            tags=("Phase 1", "Phase 3", "Dispel", "Heal Absorb", "Jump"),
        ),
        BossAbilityMetadata(
            name="Corrupting Essence",
            game_id=1261531,
            description=CORRUPTING_ESSENCE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1261531/corrupting-essence",
            tags=("Phase 1", "Avoidable", "Add Death", "Splash"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Interrupting Tremor",
            game_id=1243743,
            description=INTERRUPTING_TREMOR_DESCRIPTION,
            url="https://www.wowhead.com/spell=1243743/interrupting-tremor",
            tags=("Phase 1", "Raid Damage", "Interrupt", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Ravenous Abyss",
            game_id=1243753,
            description=RAVENOUS_ABYSS_DESCRIPTION,
            url="https://www.wowhead.com/spell=1243753/ravenous-abyss",
            tags=("Phase 1", "Avoidable", "Area Denial", "Damage Down"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Dark Hand (Physical)",
            game_id=1233787,
            description=DARK_HAND_DESCRIPTION,
            url="https://www.wowhead.com/spell=1233787/dark-hand",
            tags=("Phase 1", "Tank Mechanic", "Knockback", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Dark Hand (Shadow)",
            game_id=1233789,
            description=DARK_HAND_DESCRIPTION,
            url="https://www.wowhead.com/spell=1233789/dark-hand",
            tags=("Phase 1", "Tank Mechanic", "Knockback", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Silverstrike Barrage",
            game_id=1243981,
            description=SILVERSTRIKE_BARRAGE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1243981/silverstrike-barrage",
            tags=("Intermission 1", "Intermission 2", "Targeted Line", "Required Mechanic"),
        ),
        BossAbilityMetadata(
            name="Stellar Emission",
            game_id=1234570,
            description=STELLAR_EMISSION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1234570/stellar-emission",
            tags=("Intermission 1", "Intermission 2", "Raid Damage", "DoT", "Forced Movement", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Singularity Eruption",
            game_id=1235631,
            description=SINGULARITY_ERUPTION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1235631/singularity-eruption",
            tags=("Intermission 1", "Intermission 2", "Avoidable", "Swirl", "Knockback"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Orbiting Matter",
            game_id=1246001,
            description=ORBITING_MATTER_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246001/orbiting-matter",
            tags=("Intermission 2", "Avoidable", "Orbs", "Pull"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Cosmic Barrier",
            game_id=1261289,
            description=COSMIC_BARRIER_DESCRIPTION,
            url="https://www.wowhead.com/spell=1261289/cosmic-barrier",
            tags=("Phase 2", "Raid Damage", "DoT", "Shield", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Simulacrum Backlash",
            game_id=1260019,
            description=SIMULACRUM_BACKLASH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1260019/simulacrum-backlash",
            tags=("Phase 2", "Raid Damage", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Rift Slash",
            game_id=1246461,
            description=RIFT_SLASH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246461/rift-slash",
            tags=("Phase 2", "Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Silverstrike Ricochet",
            game_id=1259869,
            description=SILVERSTRIKE_RICOCHET_DESCRIPTION,
            url="https://www.wowhead.com/spell=1259869/silverstrike-ricochet",
            tags=("Phase 2", "Targeted Chain", "Required Mechanic"),
        ),
        BossAbilityMetadata(
            name="Voidstalker Sting",
            game_id=1237040,
            description=VOIDSTALKER_STING_DESCRIPTION,
            url="https://www.wowhead.com/spell=1237040/voidstalker-sting",
            tags=("Phase 2", "Phase 3", "Targeted DoT", "Cleanse", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Call of the Void",
            game_id=1237875,
            description="Alleria calls Voidspawns from impact locations; players clipped by the spawn impact take damage.",
            url="https://www.wowhead.com/spell=1237875/call-of-the-void",
            tags=("Phase 2", "Avoidable", "Add Spawn", "Impact"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Void Barrage",
            game_id=1260000,
            description=VOID_BARRAGE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1260000/void-barrage",
            tags=("Phase 2", "Interruptible", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Gravity Collapse",
            game_id=1239095,
            description=GRAVITY_COLLAPSE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1239095/gravity-collapse",
            tags=("Phase 3", "Raid Damage", "Tether Break", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Cosmic Radiation",
            game_id=1260771,
            description=COSMIC_RADIATION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1260771/cosmic-radiation",
            tags=("Phase 3", "Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Devouring Cosmos",
            game_id=1238882,
            description=DEVOURING_COSMOS_DESCRIPTION,
            url="https://www.wowhead.com/spell=1238882/devouring-cosmos",
            tags=("Phase 3", "Avoidable", "Area Denial", "Healing Reduction", "Enrage"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Dark Rush",
            game_id=1238709,
            description=DARK_RUSH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1238709/dark-rush",
            tags=("Phase 3", "Movement", "Feather", "DoT"),
        ),
        BossAbilityMetadata(
            name="Dimensional Slash (Initial)",
            game_id=1260838,
            description="A rare slash effect observed in the reports as isolated player hits during platform movement.",
            url="https://www.wowhead.com/spell=1260838/dimensional-slash",
            tags=("Phase 3", "Avoidable", "Platform Movement"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Dimensional Slash (Follow-up)",
            game_id=1260839,
            description="A rare follow-up slash effect observed in the reports as isolated player hits during platform movement.",
            url="https://www.wowhead.com/spell=1260839/dimensional-slash",
            tags=("Phase 3", "Avoidable", "Platform Movement"),
            avoidable=True,
        ),
    ),
)


__all__ = [
    "CROWN_OF_THE_COSMOS_MANIFEST",
]
