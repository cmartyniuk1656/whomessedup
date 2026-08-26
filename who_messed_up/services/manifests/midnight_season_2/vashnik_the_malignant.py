"""
Heroic Vashnik the Malignant ability and target metadata for Midnight Season 2.

Observed in Warcraft Logs report ZARtb8Dxjhg9H4BF, fights 23, 28, and 35
(encounter 3455), then cross-checked against Method's Heroic guide and live
spell descriptions.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST = BossManifest(
    boss_id="vashnik-the-malignant",
    boss_name="Vashnik the Malignant",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="vashnik_the_malignant",
            label="Vashnik the Malignant",
            enemy_name="Vashnik",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="burning_venom",
            label="Burning Venom",
            enemy_name="Burning Venom",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="clotting_venom",
            label="Clotting Venom",
            enemy_name="Clotting Venom",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
        EncounterTargetConfig(
            slug="shrouded_venom",
            label="Shrouded Venom",
            enemy_name="Shrouded Venom",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Toxic Vapor",
            game_id=1284561,
            description=(
                "The chamber inflicts periodic Nature damage on the entire raid. Every Imbibe permanently "
                "increases the strength of this soft-enrage damage."
            ),
            url="https://www.wowhead.com/spell=1284561",
            tags=("Raid Damage", "Unavoidable", "Soft Enrage", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Plague Froth",
            game_id=1281925,
            description=(
                "Marked players pulse Plague damage within 4.5 yards before releasing cardinal Plague Waves. The "
                "same damage ID includes unavoidable damage on the marked player and proximity damage caused by "
                "another player's positioning, so it is not assigned to victims as personal avoidable damage."
            ),
            url="https://www.wowhead.com/spell=1281925",
            tags=("Targeted", "Proximity", "DoT", "Spread"),
        ),
        BossAbilityMetadata(
            name="Caustic Explosion",
            game_id=1295209,
            description=(
                "Removing Exploding Infection detonates the infected player for raid-wide Fire damage. Healers "
                "stagger dispels so multiple explosions do not overlap."
            ),
            url="https://www.wowhead.com/spell=1295209",
            tags=("Raid Damage", "Dispel", "Staggered"),
        ),
        BossAbilityMetadata(
            name="Burning Presence",
            game_id=1305901,
            description="Burning Venom pulses Fire damage into the raid every three seconds while alive.",
            url="https://www.wowhead.com/spell=1305901",
            tags=("Raid Damage", "Priority Add", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Caustic Surge",
            game_id=1285979,
            description=(
                "A Burning Venom explodes when defeated, dealing raid-wide Fire damage and applying a short "
                "stacking damage-over-time effect. The pair is killed at staggered times."
            ),
            url="https://www.wowhead.com/spell=1285979",
            tags=("Raid Damage", "Add Death", "DoT", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Malignant Catalyst",
            game_id=1282525,
            description=(
                "Vashnik detonates an orb above the central cavity, dealing unavoidable raid damage before "
                "launching Catalytic Bile around the room."
            ),
            url="https://www.wowhead.com/spell=1282525",
            tags=("Raid Damage", "Unavoidable", "Bile Setup"),
        ),
        BossAbilityMetadata(
            name="Siphon Blood",
            game_id=1295229,
            description=(
                "A player with Siphoning Infection damages nearby allies and heals from each target hit. Nearby "
                "players intentionally feed the siphon to overcome the infected player's healing block."
            ),
            url="https://www.wowhead.com/spell=1295229",
            tags=("Required Mechanic", "Proximity", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Gloom Expulsion",
            game_id=1298583,
            description="Drinking from the Fountain of Shadow deals Shadow damage to the entire raid.",
            url="https://www.wowhead.com/spell=1298583",
            tags=("Raid Damage", "Unavoidable", "Imbibe", "Shadow Fountain"),
        ),
        BossAbilityMetadata(
            name="Malignant Burst",
            game_id=1280189,
            description=(
                "A Living Venom reaching the central cavity inflicts heavy raid-wide Nature damage followed by a "
                "stacking 30-second damage-over-time effect. This is an add-control failure, not personal damage "
                "assigned to each victim."
            ),
            url="https://www.wowhead.com/spell=1280189",
            tags=("Raid Damage", "Add Leak", "Raid Failure", "DoT"),
        ),
        BossAbilityMetadata(
            name="Conflagrating Expulsion",
            game_id=1298587,
            description="Drinking from the Fountain of Flame deals Fire damage to the entire raid.",
            url="https://www.wowhead.com/spell=1298587",
            tags=("Raid Damage", "Unavoidable", "Imbibe", "Flame Fountain"),
        ),
        BossAbilityMetadata(
            name="Dripping Fangs (DoT)",
            game_id=1280934,
            description=(
                "Vashnik's bite leaves his current target with a long Nature damage-over-time effect and a severe "
                "Physical damage vulnerability. Tanks swap every cast."
            ),
            url="https://www.wowhead.com/spell=1280934",
            tags=("Tank Mechanic", "Unavoidable", "DoT", "Tank Swap"),
        ),
        BossAbilityMetadata(
            name="Hemo Expulsion",
            game_id=1298582,
            description="Drinking from the Fountain of Blood deals Shadow damage to the entire raid.",
            url="https://www.wowhead.com/spell=1298582",
            tags=("Raid Damage", "Unavoidable", "Imbibe", "Blood Fountain"),
        ),
        BossAbilityMetadata(
            name="Catalytic Bile (Soak)",
            game_id=1282602,
            description=(
                "Catalytic Bile deals Nature damage to players within six yards of its impact. At least one player "
                "must cover each impact to prevent the larger raid-wide failure hit."
            ),
            url="https://www.wowhead.com/spell=1282602",
            tags=("Soak", "Required Mechanic", "Impact"),
        ),
        BossAbilityMetadata(
            name="Catalytic Bile (Missed Soak)",
            game_id=1282616,
            description=(
                "A Catalytic Bile landing without a nearby player inflicts heavy Nature damage on the entire raid. "
                "This is a group soak failure rather than personal avoidable damage for every victim."
            ),
            url="https://www.wowhead.com/spell=1282616",
            tags=("Raid Damage", "Missed Soak", "Raid Failure"),
        ),
        BossAbilityMetadata(
            name="Exploding Infection",
            game_id=1295173,
            description=(
                "Flame-infused players take periodic Fire damage until the infection is removed, triggering a "
                "raid-wide Caustic Explosion."
            ),
            url="https://www.wowhead.com/spell=1295173",
            tags=("Targeted", "DoT", "Dispel"),
        ),
        BossAbilityMetadata(
            name="Congealing Bolt",
            game_id=1305833,
            description=(
                "Shrouded Venom ejects dark globs at players, dealing Shadow damage on impact and applying a short "
                "stacking slow. The Heroic guide does not identify these targeted bolts as a dodge mechanic."
            ),
            url="https://www.wowhead.com/spell=1305833",
            tags=("Targeted", "Priority Add", "Slow", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Stygian Burst",
            game_id=1302489,
            description=(
                "Players with Stygian Infection periodically erupt near their position. Because responsibility "
                "belongs primarily to the marked player's spread and the log attributes damage only to victims, "
                "it is not scored as personal avoidable damage."
            ),
            url="https://www.wowhead.com/spell=1302489",
            tags=("Proximity", "Spread", "Marked Player Responsibility"),
        ),
        BossAbilityMetadata(
            name="Stygian Infection",
            game_id=1294994,
            description=(
                "Shadow-infused players take periodic Shadow damage and receive a healing absorb while periodically "
                "triggering Stygian Burst."
            ),
            url="https://www.wowhead.com/spell=1294994",
            tags=("Targeted", "DoT", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Dripping Fangs (Impact)",
            game_id=1280935,
            description=(
                "Vashnik bites his current target for heavy Physical damage and applies the Dripping Fangs tank "
                "swap effect."
            ),
            url="https://www.wowhead.com/spell=1280935",
            tags=("Tank Mechanic", "Unavoidable", "Tank Swap"),
        ),
        BossAbilityMetadata(
            name="Siphoning Infection",
            game_id=1295224,
            description=(
                "Blood-infused players take periodic Shadow damage, absorb incoming healing, and cannot receive "
                "healing until Siphon Blood restores them."
            ),
            url="https://www.wowhead.com/spell=1295224",
            tags=("Targeted", "DoT", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Plague Wave",
            game_id=1295798,
            description=(
                "When Plague Froth expires, waves travel from the marked player in the four cardinal directions. "
                "Players hit by the visible lines can move off their axes."
            ),
            url="https://www.wowhead.com/spell=1295798",
            tags=("Avoidable", "Line", "Cardinal", "Projectile"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Virulent Fumes",
            game_id=1291467,
            description=(
                "Fumes rise below each fountain and periodically damage players who remain standing over them."
            ),
            url="https://www.wowhead.com/spell=1291467",
            tags=("Avoidable", "Area Denial", "Fountain", "Periodic"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Umbral Ejection",
            game_id=1286737,
            description=(
                "A defeated Shrouded Venom sprays dark impact zones that deal Shadow damage within three yards."
            ),
            url="https://www.wowhead.com/spell=1286737",
            tags=("Avoidable", "Ground Impact", "Add Death"),
            avoidable=True,
        ),
    ),
)


__all__ = ["VASHNIK_THE_MALIGNANT_HEROIC_MANIFEST"]
