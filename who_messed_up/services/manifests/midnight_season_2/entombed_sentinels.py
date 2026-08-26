"""
Heroic Entombed Sentinels ability and target metadata for Midnight Season 2.

Observed across Warcraft Logs report ZARtb8Dxjhg9H4BF, fights 8-12
(encounter 3445), then cross-checked against Method's Heroic guide and live
spell descriptions.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


MARK_DESCRIPTION = (
    "Each Sentinel repeatedly marks nearby players with a stacking 40-second damage-over-time effect. Groups "
    "swap sides during intermissions so their previous mark can expire."
)

BLOODVENOM_INJECTION_DESCRIPTION = (
    "The Blood of Ula'tek strikes its current target and applies a stacking 40-second Shadow damage-over-time "
    "effect. Tanks reset the stacks by trading Sentinels during the intermission."
)

CULTIVATED_BURST_DESCRIPTION = (
    "Helical Toxins erupts when a player fails to neutralize it at exactly four applications, causing a large "
    "personal explosion followed by a long-lasting Plague damage-over-time effect."
)


ENTOMBED_SENTINELS_HEROIC_MANIFEST = BossManifest(
    boss_id="entombed-sentinels",
    boss_name="Entombed Sentinels",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="blood_of_ula_tek",
            label="Blood of Ula'tek",
            enemy_name="Blood of Ula'tek",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="breath_of_ula_tek",
            label="Breath of Ula'tek",
            enemy_name="Breath of Ula'tek",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="venom_coagulation",
            label="Venom Coagulation",
            enemy_name="Venom Coagulation",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Mark of Blood",
            game_id=1284506,
            description=MARK_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284506",
            tags=("Raid Damage", "DoT", "Stacking", "Side Assignment"),
        ),
        BossAbilityMetadata(
            name="Mark of Acid",
            game_id=1284500,
            description=MARK_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284500",
            tags=("Raid Damage", "DoT", "Stacking", "Side Assignment"),
        ),
        BossAbilityMetadata(
            name="Contaminate",
            game_id=1284258,
            description=(
                "Venom Coagulation pulses Nature damage into the entire raid every three seconds until the "
                "priority add is defeated."
            ),
            url="https://www.wowhead.com/spell=1284258",
            tags=("Raid Damage", "Priority Add", "DoT"),
        ),
        BossAbilityMetadata(
            name="Toxic Droplets",
            game_id=1284451,
            description=(
                "Players intentionally step on toxic droplets to destroy them before they erupt, taking Nature "
                "damage for each orb soaked."
            ),
            url="https://www.wowhead.com/spell=1284451",
            tags=("Soak", "Orb", "Targeted"),
        ),
        BossAbilityMetadata(
            name="Unstable Miasma",
            game_id=1288282,
            description=(
                "A marked player erupts after eight seconds, splitting heavy Shadow damage among players in the "
                "group soak and spreading Clinging Murk to those struck."
            ),
            url="https://www.wowhead.com/spell=1288282",
            tags=("Soak", "Split Damage"),
        ),
        BossAbilityMetadata(
            name="Blood Venom",
            game_id=1284210,
            description=(
                "When Blood Venom expires or is dispelled it leaves a toxic pool, damaging players who remain "
                "within it every second."
            ),
            url="https://www.wowhead.com/spell=1284210",
            tags=("Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Living Venom",
            game_id=1284209,
            description=(
                "Venom lines ejected by the Breath of Ula'tek return to the Sentinel after four seconds, damaging "
                "players caught in either path."
            ),
            url="https://www.wowhead.com/spell=1284209",
            tags=("Avoidable", "Line", "Projectile"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Bloodvenom Injection (DoT)",
            game_id=1310126,
            description=BLOODVENOM_INJECTION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1310126",
            tags=("Tank Mechanic", "Unavoidable", "DoT", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Clinging Murk",
            game_id=1303097,
            description=(
                "Players struck by the Unstable Miasma group soak receive a short stacking Shadow "
                "damage-over-time effect."
            ),
            url="https://www.wowhead.com/spell=1303097",
            tags=("Soak Aftereffect", "DoT", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Noxious Blast",
            game_id=1284452,
            description=(
                "A Toxic Droplet left alive erupts into heavy raid-wide Nature damage. This is a group orb-handling "
                "failure rather than damage assigned to an individual victim."
            ),
            url="https://www.wowhead.com/spell=1284452",
            tags=("Raid Damage", "Missed Orb", "Raid Failure"),
        ),
        BossAbilityMetadata(
            name="Empowering Slam",
            game_id=1284458,
            description=(
                "The Breath of Ula'tek slams its current target for heavy Physical damage and gains additional "
                "Physical damage each time it strikes the same tank consecutively."
            ),
            url="https://www.wowhead.com/spell=1284458",
            tags=("Tank Mechanic", "Unavoidable", "Tank Swap"),
        ),
        BossAbilityMetadata(
            name="Bloodvenom Injection (Impact)",
            game_id=1284487,
            description=BLOODVENOM_INJECTION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284487",
            tags=("Tank Mechanic", "Unavoidable", "Tank Swap"),
        ),
        BossAbilityMetadata(
            name="Helical Toxins",
            game_id=1284813,
            description=(
                "During Vitriolic Stasis every player receives a Plague damage-over-time effect. Players neutralize "
                "it by pairing so their combined toxin reaches exactly four applications."
            ),
            url="https://www.wowhead.com/spell=1284813",
            tags=("Raid Damage", "DoT", "Intermission", "Pairing Puzzle"),
        ),
        BossAbilityMetadata(
            name="Blighted Blood",
            game_id=1284471,
            description=(
                "Selected players receive a dispellable Shadow damage-over-time effect. On Heroic, its removal "
                "also creates a Blood Venom pool that must be placed safely."
            ),
            url="https://www.wowhead.com/spell=1284471",
            tags=("Targeted", "DoT", "Dispel"),
        ),
        BossAbilityMetadata(
            name="Cultivated Burst (DoT)",
            game_id=1284948,
            description=CULTIVATED_BURST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284948",
            tags=("Avoidable", "DoT", "Intermission Failure", "Pairing Failure"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Cultivated Burst (Explosion)",
            game_id=1284941,
            description=CULTIVATED_BURST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1284941",
            tags=("Avoidable", "Explosion", "Intermission Failure", "Pairing Failure"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Deadly Venom",
            game_id=1297338,
            description="Standing within lingering venom inflicts periodic Nature damage.",
            url="https://www.wowhead.com/spell=1297338",
            tags=("Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
    ),
)


__all__ = ["ENTOMBED_SENTINELS_HEROIC_MANIFEST"]
