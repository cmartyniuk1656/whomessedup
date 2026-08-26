"""
Heroic The Lost Explorers ability and target metadata for Midnight Season 2.

Observed in Warcraft Logs report ZARtb8Dxjhg9H4BF, fights 40-41
(encounter 3497), then cross-checked against Method's Heroic guide.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


THE_LOST_EXPLORERS_HEROIC_MANIFEST = BossManifest(
    boss_id="the-lost-explorers",
    boss_name="The Lost Explorers",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="first_mate_nama",
            label="First Mate Nama",
            enemy_name="First Mate Nama",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="scrollsage_iku",
            label="Scrollsage Iku",
            enemy_name="Scrollsage Iku",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="trader_gebbo",
            label="Trader Gebbo",
            enemy_name="Trader Gebbo",
            bucket=EncounterTargetBucket.BOSS,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Malevolent Presence",
            game_id=1295450,
            description="Mor'zahi deals steady Shadow damage to the entire raid every two seconds.",
            url="https://www.wowhead.com/spell=1295450",
            tags=("Raid Damage", "Unavoidable", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Splinters",
            game_id=1308853,
            description=(
                "Breaking Gebbo's crates applies a stacking eight-second bleed. Crates must be broken to recover "
                "the Disgusting Fish and prevent Relic Rupture, so the assigned cleanup players take this damage."
            ),
            url="https://www.wowhead.com/spell=1308853",
            tags=("Required Mechanic", "Bleed", "Stacking", "Crate Duty"),
        ),
        BossAbilityMetadata(
            name="Blink Nova",
            game_id=1294334,
            description=(
                "Iku blinks to a player and deals falloff Arcane damage to the raid. Players reduce the damage by "
                "spreading away from her destination."
            ),
            url="https://www.wowhead.com/spell=1294334",
            tags=("Raid Damage", "Distance Falloff", "Spread"),
        ),
        BossAbilityMetadata(
            name="Mighty Thud",
            game_id=1300237,
            description=(
                "Nama leaps to three marked players and splits each Physical impact among players within six "
                "yards. Empty marks instead deal the full impact to the raid."
            ),
            url="https://www.wowhead.com/spell=1300237",
            tags=("Soak", "Split Damage", "Knockback"),
        ),
        BossAbilityMetadata(
            name="Elemental Explosion",
            game_id=1295952,
            description=(
                "A player struck by the opposite Frostfire element before clearing their existing debuff triggers "
                "a heavy raid-wide explosion. This is a group failure rather than avoidable damage assigned to "
                "every victim."
            ),
            url="https://www.wowhead.com/spell=1295952",
            tags=("Raid Damage", "Elemental Failure", "Raid Failure"),
        ),
        BossAbilityMetadata(
            name="Shredding Shards",
            game_id=1310616,
            description=(
                "Iku strikes her current target with repeated ice shards, with each shard increasing damage from "
                "subsequent shards until the tanks swap."
            ),
            url="https://www.wowhead.com/spell=1310616",
            tags=("Tank Mechanic", "Unavoidable", "Tank Swap", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Final Ascension",
            game_id=1292780,
            description=(
                "When Mor'zahi reaches full energy he begins pulsing Shadow damage into the raid. A Disgusting "
                "Fish interrupts the channel and resets his energy; the fourth channel is the hard enrage."
            ),
            url="https://www.wowhead.com/spell=1292780",
            tags=("Raid Damage", "Fish Timing", "Enrage"),
        ),
        BossAbilityMetadata(
            name="Relic Rupture",
            game_id=1310027,
            description=(
                "A crate left untouched for 25 seconds erupts for raid-wide Shadow damage. This is an assigned "
                "crate-handling failure rather than damage attributable to each victim."
            ),
            url="https://www.wowhead.com/spell=1310027",
            tags=("Raid Damage", "Crate Failure", "Raid Failure"),
        ),
        BossAbilityMetadata(
            name="Burning Flames",
            game_id=1310667,
            description=(
                "Frostfire Volley applies a long Fire damage-over-time effect that is removed by entering a Frost "
                "Patch before the next volley."
            ),
            url="https://www.wowhead.com/spell=1310667",
            tags=("Targeted", "DoT", "Elemental Pairing"),
        ),
        BossAbilityMetadata(
            name="Frostfire Volley (Missile)",
            game_id=1295893,
            description="One of Iku's elemental missiles strikes selected players and creates a matching patch.",
            url="https://www.wowhead.com/spell=1295893",
            tags=("Targeted", "Elemental Pairing", "Missile"),
        ),
        BossAbilityMetadata(
            name="Fire Patch",
            game_id=1297649,
            description=(
                "A Fire Patch left by Frostfire Volley removes Piercing Frost. Entering the opposite patch is a "
                "required part of resolving the mechanic."
            ),
            url="https://www.wowhead.com/spell=1297649",
            tags=("Required Mechanic", "Ground Effect", "Elemental Pairing"),
        ),
        BossAbilityMetadata(
            name="Piercing Frost",
            game_id=1310662,
            description=(
                "Frostfire Volley applies a long Frost damage-over-time effect and slow that is removed by entering "
                "a Fire Patch before the next volley."
            ),
            url="https://www.wowhead.com/spell=1310662",
            tags=("Targeted", "DoT", "Slow", "Elemental Pairing"),
        ),
        BossAbilityMetadata(
            name="Frost Patch",
            game_id=1297648,
            description=(
                "A Frost Patch left by Frostfire Volley removes Burning Flames. Entering the opposite patch is a "
                "required part of resolving the mechanic."
            ),
            url="https://www.wowhead.com/spell=1297648",
            tags=("Required Mechanic", "Ground Effect", "Elemental Pairing"),
        ),
        BossAbilityMetadata(
            name="Frostfire Volley (Impact)",
            game_id=1295985,
            description="One of Iku's elemental volley impacts strikes selected players.",
            url="https://www.wowhead.com/spell=1295985",
            tags=("Targeted", "Elemental Pairing"),
        ),
        BossAbilityMetadata(
            name="Smashing Shovel",
            game_id=1296251,
            description=(
                "After another explorer dies, Gebbo gains a heavy Physical attack with a knockback. The explorers "
                "should be defeated together to avoid this death-triggered enrage."
            ),
            url="https://www.wowhead.com/spell=1296251",
            tags=("Tank Damage", "Death Enrage", "Knockback"),
        ),
        BossAbilityMetadata(
            name="Evil Eyes",
            game_id=1292764,
            description="Creepy statues launch spirit flames that damage players within three yards of the impact.",
            url="https://www.wowhead.com/spell=1292764",
            tags=("Avoidable", "Ground Impact", "Area Denial"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Throw Junk",
            game_id=1291935,
            description=(
                "Gebbo throws a crate at a player location, dealing heavy Physical damage near its landing point. "
                "Players move out of the impact before deliberately breaking the landed crate."
            ),
            url="https://www.wowhead.com/spell=1291935",
            tags=("Avoidable", "Ground Impact", "Crate"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Fungal Burst",
            game_id=1305618,
            description=(
                "A Bouncy Mushroom bursts shortly after it is used, damaging players who remain within five yards."
            ),
            url="https://www.wowhead.com/spell=1305618",
            tags=("Avoidable", "Area Denial", "Mushroom"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Explosive Surprise",
            game_id=1296245,
            description=(
                "Gebbo's bomb deals Physical damage at its landing point before emitting Blast Wave. The marked "
                "player places it at the edge and moves clear of the impact."
            ),
            url="https://www.wowhead.com/spell=1296245",
            tags=("Avoidable", "Ground Impact", "Bomb"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Blast Wave",
            game_id=1305844,
            description=(
                "A lethal Fire shockwave expands from Gebbo's bomb. Players use Bouncy Mushrooms or movement "
                "abilities to pass over the wave."
            ),
            url="https://www.wowhead.com/spell=1305844",
            tags=("Avoidable", "Shockwave", "Bomb", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Icebound Flames",
            game_id=1286922,
            description=(
                "Iku's interruptible cast deals Frostfire damage and leaves a dispellable damage-over-time effect "
                "and slow when the raid misses the interrupt."
            ),
            url="https://www.wowhead.com/spell=1286922",
            tags=("Interrupt Failure", "Team Responsibility", "DoT", "Dispel"),
        ),
        BossAbilityMetadata(
            name="Aftershock",
            game_id=1310500,
            description=(
                "Each Mighty Thud landing leaves a crater that deals periodic Physical damage within six yards for "
                "30 seconds. Players leave the impact areas after completing their soaks."
            ),
            url="https://www.wowhead.com/spell=1310500",
            tags=("Avoidable", "Area Denial", "DoT", "After Soak"),
            avoidable=True,
        ),
    ),
)


__all__ = ["THE_LOST_EXPLORERS_HEROIC_MANIFEST"]
