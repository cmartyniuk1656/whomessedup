"""Heroic The Coiled Altar ability and target metadata for Midnight Season 2.

Observed across Warcraft Logs report p4mPajMdJRgKqQBT, fights 11-30
(encounter 3429), then cross-checked against Method's Heroic guide.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


THE_COILED_ALTAR_HEROIC_MANIFEST = BossManifest(
    boss_id="the-coiled-altar",
    boss_name="The Coiled Altar",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="zuljan",
            label="Zul'jan",
            enemy_name="Zul'jan",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="hex_lord_malacrass",
            label="Hex Lord Malacrass",
            enemy_name="Hex Lord Malacrass",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="spiteful_soulcoiler",
            label="Spiteful Soulcoiler",
            enemy_name="Spiteful Soulcoiler",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Fangs of the Coiled Altar",
            game_id=1282512,
            description="Zul'jan channels unavoidable raid-wide Nature damage and empowers his following melee attacks.",
            url="https://www.wowhead.com/spell=1282512",
            tags=("Raid Damage", "Unavoidable", "Channel"),
        ),
        BossAbilityMetadata(
            name="Twinfang Toxin",
            game_id=1300322,
            description="Empowered melee attacks consume Twinfang Toxin to deal unavoidable bonus damage to the tank.",
            url="https://www.wowhead.com/spell=1300322",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Noxious Ground",
            game_id=1283290,
            description="Puddles beneath the altar mouths damage players who remain in them.",
            url="https://www.wowhead.com/spell=1283290",
            tags=("Avoidable", "Ground Effect", "Area Denial"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Toxic Deluge (Impact)",
            game_id=1300137,
            description="The crucible's dodgeable venom impacts damage players before forming Coalesced Venom globules.",
            url="https://www.wowhead.com/spell=1300137",
            tags=("Avoidable", "Ground Impact", "Orb Spawn"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Coalesced Venom",
            game_id=1282408,
            description="Active venom globules pulse unavoidable raid damage until an assigned player collects them.",
            url="https://www.wowhead.com/spell=1282408",
            tags=("Raid Damage", "Orb Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Volatile Venom",
            game_id=1282288,
            description=(
                "An assigned orb carrier necessarily takes the pulse while moving venom. Other players struck by "
                "that carrier's five-yard pulse are scored as avoidable proximity hits."
            ),
            url="https://www.wowhead.com/spell=1282288",
            tags=("Avoidable", "Conditional", "Proximity", "Orb Carrier"),
            avoidable=True,
            avoidable_excludes_active_debuff_ability_id=1282419,
        ),
        BossAbilityMetadata(
            name="Venom Rupture",
            game_id=1299838,
            description="Destroying Coalesced Venom with a tank frontal applies required stacking raid damage.",
            url="https://www.wowhead.com/spell=1299838",
            tags=("Raid Damage", "Required Mechanic", "Stacking DoT"),
        ),
        BossAbilityMetadata(
            name="Sever",
            game_id=1299684,
            description="Zul'jan's tank frontal also clears Coalesced Venom; only non-tanks struck are personally at fault.",
            url="https://www.wowhead.com/spell=1299684",
            tags=("Avoidable", "Tank Soak", "Frontal", "Orb Clear"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Guillotine",
            game_id=1283594,
            description="At least five assigned players split the required axe impact.",
            url="https://www.wowhead.com/spell=1283594",
            tags=("Required Mechanic", "Group Soak"),
        ),
        BossAbilityMetadata(
            name="Execution",
            game_id=1283606,
            description="An undersoaked Guillotine punishes the raid; logged victims do not identify the failed assignee.",
            url="https://www.wowhead.com/spell=1283606",
            tags=("Soak Failure", "Raid Damage", "Assignment Responsibility"),
        ),
        BossAbilityMetadata(
            name="Widow's Kiss",
            game_id=1283623,
            description="The post-Guillotine eruption hits players in the inner distance band.",
            url="https://www.wowhead.com/spell=1283623",
            tags=("Raid Mechanic", "Distance Band"),
        ),
        BossAbilityMetadata(
            name="Widow's Touch",
            game_id=1283631,
            description="The post-Guillotine eruption hits players in the outer distance band.",
            url="https://www.wowhead.com/spell=1283631",
            tags=("Raid Mechanic", "Distance Band"),
        ),
        BossAbilityMetadata(
            name="Venomfang",
            game_id=1306906,
            description="Several selected players receive an unavoidable poison DoT that healers must dispel.",
            url="https://www.wowhead.com/spell=1306906",
            tags=("Targeted", "Poison", "Dispel"),
        ),
        BossAbilityMetadata(
            name="Axegrinder",
            game_id=1285017,
            description="Wandering axes deal armor-ignoring damage when a player touches them.",
            url="https://www.wowhead.com/spell=1285017",
            tags=("Avoidable", "Moving Hazard", "Knockback"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Dreadful Presence",
            game_id=1288635,
            description="Malacrass deals constant unavoidable raid-wide Shadow damage while active.",
            url="https://www.wowhead.com/spell=1288635",
            tags=("Raid Damage", "Unavoidable", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Dread Bolt",
            game_id=1307184,
            description="Malacrass's unavoidable single-target filler attack against his current tank.",
            url="https://www.wowhead.com/spell=1307184",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Gloombomb",
            game_id=1310883,
            description=(
                "Marked players necessarily take their own explosion. Additional players caught within fifteen "
                "yards are excluded from the marked-target set and scored as avoidable collateral hits."
            ),
            url="https://www.wowhead.com/spell=1310883",
            tags=("Avoidable", "Conditional", "Spread", "Circle Overlap"),
            avoidable=True,
            avoidable_exclusion_debuff_ability_id=1310881,
            avoidable_exclusion_debuff_event_types=("removedebuff",),
            avoidable_exclusion_debuff_window_ms=200.0,
        ),
        BossAbilityMetadata(
            name="Gravebound (Fragment Collection)",
            game_id=1308330,
            description="Required damage follows Gravebound while the affected player reclaims their Soul Fragments.",
            url="https://www.wowhead.com/spell=1308330",
            tags=("Targeted", "Soul Fragments", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Gravebound (Expired)",
            game_id=1297906,
            description="Failing to reclaim every Soul Fragment before Gravebound expires deals lethal damage.",
            url="https://www.wowhead.com/spell=1297906",
            tags=("Avoidable", "Failure", "Soul Fragments", "Lethal"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Soul Sever",
            game_id=1286620,
            description="Malacrass's tank frontal clears parked manifestations; only non-tanks struck are avoidable.",
            url="https://www.wowhead.com/spell=1286620",
            tags=("Avoidable", "Tank Soak", "Frontal", "Ghost Clear"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Soul Sever (DoT)",
            game_id=1312630,
            description="The Soul Sever DoT is required on its tank target but avoidable on non-tanks clipped by the frontal.",
            url="https://www.wowhead.com/spell=1312630",
            tags=("Avoidable", "Tank Soak", "Frontal", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Eternal Nightfall",
            game_id=1286918,
            description="A raid-ending channel continues until the raid breaks Veil of Twilight; victims are not individually blamed.",
            url="https://www.wowhead.com/spell=1286918",
            tags=("Raid Damage", "Damage Check", "Interrupt by Shield Break"),
        ),
        BossAbilityMetadata(
            name="Suffocating Darkness",
            game_id=1286947,
            description="Veil of Twilight applies a stacking healing absorb to the raid until its shield is broken.",
            url="https://www.wowhead.com/spell=1286947",
            tags=("Raid Mechanic", "Healing Absorb", "Damage Check"),
        ),
        BossAbilityMetadata(
            name="Retaliatory Malice",
            game_id=1308323,
            description="Spiteful Soulcoilers passively deal unavoidable raid damage while the priority add remains alive.",
            url="https://www.wowhead.com/spell=1308323",
            tags=("Raid Damage", "Priority Add", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Spirit Erasure",
            game_id=1287722,
            description="Intercepting required Fragments of Malacrass deals stacking raid-wide damage that must be staggered.",
            url="https://www.wowhead.com/spell=1287722",
            tags=("Raid Damage", "Required Intercept", "Stacking"),
        ),
        BossAbilityMetadata(
            name="Corrupted Toxin",
            game_id=1298795,
            description="Zul'jan's Phase Three melee attacks apply an unavoidable stacking Shadow DoT to the tank.",
            url="https://www.wowhead.com/spell=1298795",
            tags=("Tank Mechanic", "Unavoidable", "Stacking DoT"),
        ),
        BossAbilityMetadata(
            name="Defilement of the Coiled Altar",
            game_id=1298594,
            description="Zul'jan applies a heavy raid-wide healing absorb during Phase Three.",
            url="https://www.wowhead.com/spell=1298594",
            tags=("Raid Mechanic", "Healing Absorb", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Defiled Ground",
            game_id=1298591,
            description="Phase Three ground zones absorb healing while a player remains inside them.",
            url="https://www.wowhead.com/spell=1298591",
            tags=("Area Denial", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Grim Guillotine",
            game_id=1299296,
            description="At least five assigned players split the required Phase Three axe impact.",
            url="https://www.wowhead.com/spell=1299296",
            tags=("Required Mechanic", "Group Soak", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Grim Execution",
            game_id=1299301,
            description="An undersoaked Grim Guillotine punishes the raid without identifying the failed assignee.",
            url="https://www.wowhead.com/spell=1299301",
            tags=("Soak Failure", "Raid Damage", "Assignment Responsibility"),
        ),
        BossAbilityMetadata(
            name="Death's Embrace",
            game_id=1299396,
            description="The Grim Guillotine eruption affects the inner distance band.",
            url="https://www.wowhead.com/spell=1299396",
            tags=("Raid Mechanic", "Distance Band", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Death's Whisper",
            game_id=1299401,
            description="The Grim Guillotine eruption affects the outer distance band.",
            url="https://www.wowhead.com/spell=1299401",
            tags=("Raid Mechanic", "Distance Band", "Healing Absorb"),
        ),
        BossAbilityMetadata(
            name="Blighted Sever",
            game_id=1307292,
            description="The Phase Three tank frontal clears venom and manifestations; non-tank hits are avoidable.",
            url="https://www.wowhead.com/spell=1307292",
            tags=("Avoidable", "Tank Soak", "Frontal", "Combined Clear"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Unworthy",
            game_id=1312424,
            description="Falling from the platform during the Malacrass phase transition deals lethal damage.",
            url="https://www.wowhead.com/spell=1312424",
            tags=("Avoidable", "Positioning", "Fall", "Lethal"),
            avoidable=True,
        ),
    ),
)


__all__ = ["THE_COILED_ALTAR_HEROIC_MANIFEST"]
