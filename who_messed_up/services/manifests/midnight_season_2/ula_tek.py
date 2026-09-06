"""Heroic Ula'tek ability and target metadata for Midnight Season 2.

Observed across Warcraft Logs report xK1bZJTLdrVhqHDg, fights 1-6
(encounter 3492), then cross-checked against Method's and Mythic Trap's
Heroic guides plus live spell descriptions.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


ULA_TEK_HEROIC_MANIFEST = BossManifest(
    boss_id="ula-tek",
    boss_name="Ula'tek",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="ula_tek",
            label="Ula'tek",
            enemy_name="Ula'tek",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="gore_rattle",
            label="Gore Rattle",
            enemy_name="Gore Rattle",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="venomous_heart",
            label="Venomous Heart",
            enemy_name="Venomous Heart",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="doomscale_warden",
            label="Doomscale Warden",
            enemy_name="Doomscale Warden",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="blightscale_clutch",
            label="Blightscale Clutch",
            enemy_name="Blightscale Clutch",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="weakened_doomscale",
            label="Weakened Doomscale",
            enemy_name="Weakened Doomscale",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="blightscale_shrieker",
            label="Blightscale Shrieker",
            enemy_name="Blightscale Shrieker",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="blightscale_viper",
            label="Blightscale Viper",
            enemy_name="Blightscale Viper",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="blightscale_rawling",
            label="Blightscale Rawling",
            enemy_name="Blightscale Rawling",
            bucket=EncounterTargetBucket.PAD_ADD,
            default_enabled=False,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Necrotic Vapors",
            game_id=1286835,
            description="Ula'tek's prison inflicts constant, stacking raid-wide Nature damage throughout the encounter.",
            url="https://www.wowhead.com/spell=1286835",
            tags=("Raid Damage", "Unavoidable", "Periodic", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Stone Venom",
            game_id=1298418,
            description="Mother's Wrath applies an unavoidable stacking Nature damage-over-time effect to the active tank.",
            url="https://www.wowhead.com/spell=1298418",
            tags=("Tank Mechanic", "Unavoidable", "Stacking DoT"),
        ),
        BossAbilityMetadata(
            name="Spectral Coils",
            game_id=1287265,
            description="Two assigned groups split successive tail impacts; every raid member still takes required soak damage.",
            url="https://www.wowhead.com/spell=1287265",
            tags=("Required Mechanic", "Group Soak", "Raid Damage"),
        ),
        BossAbilityMetadata(
            name="Rage of the Shackled",
            game_id=1307367,
            description="Ula'tek deals unavoidable raid-wide damage while her Venomous Heart is exposed for the burn window.",
            url="https://www.wowhead.com/spell=1307367",
            tags=("Raid Damage", "Unavoidable", "Damage Amp"),
        ),
        BossAbilityMetadata(
            name="Volatile Purge (Periodic)",
            game_id=1316357,
            description=(
                "Players who leech Serpent's Bite carry a purge that damages nearby players. Its baseline self-damage "
                "and overlap damage share one log ID, so it is tracked by the mechanics scorecard rather than personally scored."
            ),
            url="https://www.wowhead.com/spell=1316357",
            tags=("Spread", "Proximity", "Periodic", "Unscored"),
        ),
        BossAbilityMetadata(
            name="Acidic Expulsion",
            game_id=1313531,
            description="Each Blightscale Shrieker applies an unavoidable, long raid-wide Nature damage-over-time effect.",
            url="https://www.wowhead.com/spell=1313531",
            tags=("Raid Damage", "Priority Add", "Stacking DoT"),
        ),
        BossAbilityMetadata(
            name="Blight Vein",
            game_id=1317955,
            description="Breaking Grasping Fangs applies a required raid-wide DoT; simultaneous breaks stack the effect.",
            url="https://www.wowhead.com/spell=1317955",
            tags=("Raid Damage", "Required Mechanic", "Tether", "Stacking DoT"),
        ),
        BossAbilityMetadata(
            name="Serpent's Bite (Leech)",
            game_id=1293146,
            description="The raid shares required periodic damage while leeching venom from the three bitten players.",
            url="https://www.wowhead.com/spell=1293146",
            tags=("Required Mechanic", "Group Soak", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Mephitic Thrash",
            game_id=1296301,
            description=(
                "The tail hits players inside 35 yards and applies a different unavoidable hit plus DoT outside the circle; "
                "because both distance bands share one log ID, this damage is not personally scored."
            ),
            url="https://www.wowhead.com/spell=1296301",
            tags=("Raid Mechanic", "Distance Band", "Knockback", "Unscored"),
        ),
        BossAbilityMetadata(
            name="Malignant Shell",
            game_id=1297213,
            description="Players carrying ordinary eggs take required periodic Nature damage until the shell is removed.",
            url="https://www.wowhead.com/spell=1297213",
            tags=("Required Mechanic", "Egg Carrier", "DoT"),
        ),
        BossAbilityMetadata(
            name="Volatile Purge (Impact)",
            game_id=1305878,
            description=(
                "The five-second purge expiration deals baseline damage to every carrier and can punish nearby players; "
                "the shared event does not safely separate those cases for personal scoring."
            ),
            url="https://www.wowhead.com/spell=1305878",
            tags=("Spread", "Proximity", "Impact", "Unscored"),
        ),
        BossAbilityMetadata(
            name="Caustic Waves",
            game_id=1292403,
            description="Dodgeable venom waves deal an impact and stacking periodic damage to players in their path.",
            url="https://www.wowhead.com/spell=1292403",
            tags=("Avoidable", "Wave", "DoT", "Egg Hazard"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Circling Prey",
            game_id=1301510,
            description=(
                "Ula'tek destroys a platform, dealing a lethal inner hit and a required outer hit under the same log ID; "
                "the mixed event is not personally scored."
            ),
            url="https://www.wowhead.com/spell=1301510",
            tags=("Platform Break", "Distance Band", "Knockback", "Unscored"),
        ),
        BossAbilityMetadata(
            name="Mother's Wrath (Tank)",
            game_id=1298369,
            description="Ula'tek bites and knocks back her current tank, applying Stone Venom and Hobbled.",
            url="https://www.wowhead.com/spell=1298369",
            tags=("Tank Mechanic", "Unavoidable", "Tank Swap"),
        ),
        BossAbilityMetadata(
            name="Deadly Venom",
            game_id=1297338,
            description="The venom surrounding the safe platforms damages players crossing or remaining inside it; assigned movement can require contact.",
            url="https://www.wowhead.com/spell=1297338",
            tags=("Area Denial", "Periodic", "Forced Movement", "Unscored"),
        ),
        BossAbilityMetadata(
            name="Poisonous Bite",
            game_id=1287032,
            description="Blightscale Rawlings apply a stacking poison DoT to their current targets until the adds die.",
            url="https://www.wowhead.com/spell=1287032",
            tags=("Add Damage", "Stacking DoT"),
        ),
        BossAbilityMetadata(
            name="Putrid Membrane",
            game_id=1308275,
            description="Every uncontrolled Blightscale Viper hatch applies a long raid-wide DoT; victims do not identify the egg handler.",
            url="https://www.wowhead.com/spell=1308275",
            tags=("Raid Damage", "Viper Hatch", "Team Failure", "DoT"),
        ),
        BossAbilityMetadata(
            name="Calcified Corpse (Raid Toxin)",
            game_id=1318329,
            description="An unresolved Serpent's Bite radiates lethal raid-wide damage from the calcified player.",
            url="https://www.wowhead.com/spell=1318329",
            tags=("Raid Damage", "Soak Failure", "Team Responsibility", "Lethal"),
        ),
        BossAbilityMetadata(
            name="Virulent Spit",
            game_id=1302982,
            description="Ula'tek's Phase Two venom impacts damage players within four yards of the marked destinations.",
            url="https://www.wowhead.com/spell=1302982",
            tags=("Avoidable", "Swirl", "Ground Impact"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Rattler Slam",
            game_id=1299206,
            description="The Gore Rattle punishes the entire raid when no tank remains in melee range of the tail.",
            url="https://www.wowhead.com/spell=1299206",
            tags=("Raid Damage", "Tank Uptime Failure", "Team Responsibility"),
        ),
        BossAbilityMetadata(
            name="Unchecked Rage",
            game_id=1301007,
            description="Ula'tek punishes the entire raid when no tank remains in her melee range.",
            url="https://www.wowhead.com/spell=1301007",
            tags=("Raid Damage", "Tank Uptime Failure", "Team Responsibility"),
        ),
        BossAbilityMetadata(
            name="Grasping Fangs",
            game_id=1311612,
            description="Tethered players take required periodic damage until they break their fangs in controlled pairs.",
            url="https://www.wowhead.com/spell=1311612",
            tags=("Required Mechanic", "Tether", "DoT", "Slow"),
        ),
        BossAbilityMetadata(
            name="Mother's Wrath (Raid Failure)",
            game_id=1301122,
            description="If Ula'tek's target is out of melee range, Mother's Wrath strikes the entire raid instead.",
            url="https://www.wowhead.com/spell=1301122",
            tags=("Raid Damage", "Tank Uptime Failure", "Team Responsibility"),
        ),
        BossAbilityMetadata(
            name="Serpent's Bite (Initial)",
            game_id=1295838,
            description="Three assigned players receive the initial bite before the raid leeches away its venom.",
            url="https://www.wowhead.com/spell=1295838",
            tags=("Targeted", "Required Mechanic", "Soak Assignment"),
        ),
        BossAbilityMetadata(
            name="Falling Debris",
            game_id=1286885,
            description="Rocks during Rage of the Shackled damage players within seven yards of each impact.",
            url="https://www.wowhead.com/spell=1286885",
            tags=("Avoidable", "Swirl", "Ground Impact"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Vicious Echoes",
            game_id=1310764,
            description="A completed Blightscale Shrieker cast deals raid-wide damage and stuns the raid.",
            url="https://www.wowhead.com/spell=1310764",
            tags=("Raid Damage", "Interrupt Failure", "Team Responsibility", "Stun"),
        ),
        BossAbilityMetadata(
            name="Fury Unleashed (Raid)",
            game_id=1286905,
            description="The hard enrage begins with a massive raid-wide hit and rapidly escalating damage.",
            url="https://www.wowhead.com/spell=1286905",
            tags=("Raid Damage", "Hard Enrage", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Desperate Thrash",
            game_id=1305709,
            description="The Weakened Doomscale's tank cone is required on its tank but avoidable for non-tanks caught in front.",
            url="https://www.wowhead.com/spell=1305709",
            tags=("Avoidable", "Tank Soak", "Frontal", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Fury Unleashed (Focused)",
            game_id=1295004,
            description="The hard enrage also deals escalating focused damage as the encounter ends.",
            url="https://www.wowhead.com/spell=1295004",
            tags=("Hard Enrage", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Blightscale Clutch (Impact)",
            game_id=1290409,
            description="Falling clutch eggs damage players within four yards of their impact locations.",
            url="https://www.wowhead.com/spell=1290409",
            tags=("Avoidable", "Ground Impact", "Egg Spawn"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Warden's Protection",
            game_id=1306858,
            description="The Doomscale Warden damages players within seven yards of protected eggs while it remains alive.",
            url="https://www.wowhead.com/spell=1306858",
            tags=("Priority Add", "Proximity", "Area Denial"),
        ),
        BossAbilityMetadata(
            name="Calcified Corpse (Petrification)",
            game_id=1306119,
            description="A bitten player who is not fully leeched is petrified and takes lethal periodic damage.",
            url="https://www.wowhead.com/spell=1306119",
            tags=("Avoidable", "Soak Failure", "Lethal", "Stun"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Acidic Burst",
            game_id=1301800,
            description="An uncontrolled Blightscale Viper spits at a random player, applying a long poison DoT.",
            url="https://www.wowhead.com/spell=1301800",
            tags=("Targeted", "Viper Hatch", "Poison DoT"),
        ),
        BossAbilityMetadata(
            name="Doomscale Shell",
            game_id=1300314,
            description="Players carrying the large Doomscale eggs take required periodic Nature damage until delivery.",
            url="https://www.wowhead.com/spell=1300314",
            tags=("Required Mechanic", "Egg Carrier", "DoT"),
        ),
    ),
)


__all__ = ["ULA_TEK_HEROIC_MANIFEST"]
