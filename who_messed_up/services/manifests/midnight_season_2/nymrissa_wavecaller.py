"""Mythic Nymrissa metadata audited against fCqgJN7QMWA2vFbT, fights 15-19.

See docs/analysis/nymrissa-mythic.md for spell attribution and exclusions.
Orb timing is contextual; receiving Frost Burst is never personal soak credit.
"""
from ...boss_manifest_types import BossAbilityMetadata, BossManifest, EncounterTargetBucket, EncounterTargetConfig


NYMRISSA_WAVECALLER_MYTHIC_MANIFEST = BossManifest(
    boss_id="nymrissa-wavecaller",
    boss_name="Nymrissa Wavecaller",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig("nymrissa_wavecaller", "Nymrissa Wavecaller", "Nymrissa Wavecaller", EncounterTargetBucket.BOSS),
        EncounterTargetConfig("bubblefin_frostscale", "Bubblefin Frostscale", "Bubblefin Frostscale", EncounterTargetBucket.PRIORITY_ADD),
        EncounterTargetConfig("bubblefin_shorerunner", "Bubblefin Shorerunner", "Bubblefin Shorerunner", EncounterTargetBucket.PRIORITY_ADD),
        EncounterTargetConfig("bubblefin_berserker", "Bubblefin Berserker", "Bubblefin Berserker", EncounterTargetBucket.PRIORITY_ADD),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Abyssal Rain", game_id=1260843,
            description="Raid-wide pulses followed by lingering periodic damage. Orb soaks during this damage add raid pressure.",
            url="https://www.wowhead.com/spell=1260843", tags=("Raid Damage", "DoT", "Unavoidable")),
        BossAbilityMetadata(
            name="Frost Orb", game_id=1313448,
            description="Contact soaks an orb, applies a stacking vulnerability and DoT, and leaves Lingering Frost. Only the initial impact identifies an orb soak.",
            url="https://www.wowhead.com/spell=1313448", tags=("Soak", "DoT", "Stacking")),
        BossAbilityMetadata(
            name="Frost Burst", game_id=1313450,
            description="Mythic raid damage triggered by an orb soak. Damage recipients are not necessarily the player who soaked the orb.",
            url="https://www.wowhead.com/spell=1313450", tags=("Raid Damage", "Soak", "Mythic")),
        BossAbilityMetadata(
            name="Shatter", game_id=1313456,
            description="An uncollected orb explodes into raid damage and a stacking DoT. Raid victims are not individually responsible for the missed orb.",
            url="https://www.wowhead.com/spell=1313456", tags=("Raid Damage", "Missed Soak", "DoT")),
        BossAbilityMetadata(
            name="Lingering Frost", game_id=1257654,
            description="Ice left by a soaked orb damages players standing in it.",
            url="https://www.wowhead.com/spell=1257654", tags=("Avoidable", "Area Denial"), avoidable=True),
        BossAbilityMetadata(
            name="Chilling Frost", game_id=1313393,
            description="Targeted damage that produces Frost Orbs around the affected player.",
            url="https://www.wowhead.com/spell=1313393", tags=("Targeted", "DoT")),
        BossAbilityMetadata(
            name="Water Jet", game_id=1271458,
            description="A frontal beam aimed at the current target pushes players, stacks vulnerability, and clears ice. Tank participation is expected; this ID is not blanket personal avoidable damage.",
            url="https://www.wowhead.com/spell=1271458", tags=("Tank Mechanic", "Frontal", "Stacking")),
        BossAbilityMetadata(
            name="Swirling Whirlpools", game_id=1258677,
            description="Moving whirlpools damage players in their path.",
            url="https://www.wowhead.com/spell=1258677", tags=("Avoidable", "Area Denial"), avoidable=True),
        BossAbilityMetadata(
            name="Pop! (Central Bubble)", game_id=1266340,
            description="The large central bubble bursts and damages the raid. This is distinct from soaking a Frost Orb.",
            url="https://www.wowhead.com/spell=1266340", tags=("Raid Damage", "Knockback")),
        BossAbilityMetadata(
            name="Pop! (Knockback)", game_id=1258154,
            description="Central-bubble knockback event; observed zero-damage hits are not Frost Orb soaks.",
            url="https://www.wowhead.com/spell=1258154", tags=("Knockback",)),
        BossAbilityMetadata(
            name="Pulsing Tides", game_id=1271380,
            description="An empowered Bubblefin Berserker pulses damage into the raid. Receiving these pulses does not identify who allowed the add to reach the bubble.",
            url="https://www.wowhead.com/spell=1271380", tags=("Raid Damage", "Priority Add")),
        BossAbilityMetadata(
            name="Wild Bite", game_id=1265425,
            description="Remaining in the water causes shark bites and a lingering bleed.",
            url="https://www.wowhead.com/spell=1265425", tags=("Avoidable", "Environment", "DoT"), avoidable=True),
    ),
)
