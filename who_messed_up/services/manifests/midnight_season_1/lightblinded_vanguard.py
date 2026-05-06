"""
Lightblinded Vanguard ability metadata for Midnight Season 1.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


LIGHT_INFUSION_DESCRIPTION = (
    "General Amias Bellamy radiates Holy damage to all players every 2 sec. The damage ramps whenever a "
    "Vanguard member unleashes an aura."
)

SEARING_RADIANCE_DESCRIPTION = (
    "War Chaplain Senn channels Holy energy for 15 sec, pulsing damage into the full raid every 1 sec. On "
    "Mythic, Zealous Spirit empowerment increases the pulse damage each second."
)

SACRED_TOLL_DESCRIPTION = (
    "Commander Venel Lightblood deems nearby players unworthy, inflicting a large Holy burst to players within "
    "the encounter area."
)

AVENGERS_SHIELD_DESCRIPTION = (
    "General Amias Bellamy marks players with holy shields that explode on impact and apply a Magic periodic "
    "damage effect to nearby players."
)

DIVINE_TOLL_DESCRIPTION = (
    "General Amias Bellamy or a Zealous Spirit unleashes waves of holy shields. The shields travel before "
    "hitting players for Holy damage and a silence."
)

EXECUTION_SENTENCE_DESCRIPTION = (
    "Commander Venel Lightblood marks players for execution, then detonates a soak a few seconds later. The "
    "Holy damage is split between players in the impact area."
)

DIVINE_HAMMER_DESCRIPTION = (
    "Execution Sentence sends holy hammers spiraling out from the impact location, damaging players in their "
    "path."
)

DIVINE_STORM_DESCRIPTION = (
    "Commander Venel Lightblood unleashes Holy energy around himself, damaging players within 8 yards."
)

DIVINE_STORM_OVERLAP_DESCRIPTION = (
    "Players receive holy circles during Divine Storm. Players who overlap another player's circle take Holy "
    "damage."
)

DIVINE_TEMPEST_DESCRIPTION = (
    "Mythic empowered Divine Storm creates holy vortices that converge on Lightblood, ticking damage and "
    "slowing players caught inside."
)

DIVINE_CONSECRATION_DESCRIPTION = (
    "After a Vanguard aura expires, the boss consecrates the ground beneath them. Players standing in it take "
    "periodic Holy damage, are pacified, and take increased damage."
)

TRAMPLED_DESCRIPTION = (
    "War Chaplain Senn charges forward on her elekk, damaging players in her path."
)

BLINDING_LIGHT_DESCRIPTION = (
    "War Chaplain Senn emits an interruptible flash that damages and disorients the raid if the cast completes."
)

BELLAMY_TANK_COMBO_DESCRIPTION = (
    "General Amias Bellamy passes judgment on her current target, increasing their damage taken from Shield of "
    "the Righteous before immediately following up with the shield strike."
)

LIGHTBLOOD_TANK_COMBO_DESCRIPTION = (
    "Commander Venel Lightblood passes judgment on his current target, increasing their damage taken from Final "
    "Verdict before immediately following up with the finishing strike."
)

EXORCISM_DESCRIPTION = (
    "War Chaplain Senn exorcises her current target with a direct Holy hit."
)


LIGHTBLINDED_VANGUARD_MANIFEST = BossManifest(
    boss_id="lightblinded-vanguard",
    boss_name="Lightblinded Vanguard",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig(
            slug="general_amias_bellamy",
            label="General Amias Bellamy",
            enemy_name="General Amias Bellamy",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="commander_venel_lightblood",
            label="Commander Venel Lightblood",
            enemy_name="Commander Venel Lightblood",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="war_chaplain_senn",
            label="War Chaplain Senn",
            enemy_name="War Chaplain Senn",
            bucket=EncounterTargetBucket.BOSS,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Light Infusion",
            game_id=1258661,
            description=LIGHT_INFUSION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1258661/light-infusion",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Searing Radiance",
            game_id=1255739,
            description=SEARING_RADIANCE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1255739/searing-radiance",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Sacred Toll",
            game_id=1246749,
            description=SACRED_TOLL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246749/sacred-toll",
            tags=("Raid Damage", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Avenger's Shield",
            game_id=1246502,
            description=AVENGERS_SHIELD_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246502/avengers-shield",
            tags=("Dispel", "DoT", "Spread"),
        ),
        BossAbilityMetadata(
            name="Execution Sentence",
            game_id=1249024,
            description=EXECUTION_SENTENCE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249024/execution-sentence",
            tags=("Soak",),
        ),
        BossAbilityMetadata(
            name="Divine Toll",
            game_id=1248652,
            description=DIVINE_TOLL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1248652/divine-toll",
            tags=("Avoidable", "Projectiles", "Silence"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Divine Hammer",
            game_id=1249047,
            description=DIVINE_HAMMER_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249047/divine-hammer",
            tags=("Avoidable", "Projectiles"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Divine Storm",
            game_id=1246765,
            description=DIVINE_STORM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246765/divine-storm",
            tags=("Raid Damage", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Divine Storm (Circle Overlap)",
            game_id=1272310,
            description=DIVINE_STORM_OVERLAP_DESCRIPTION,
            url="https://www.wowhead.com/spell=1272310/divine-storm",
            tags=("Avoidable", "Circle Overlap"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Divine Tempest",
            game_id=1272324,
            description=DIVINE_TEMPEST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1272324/divine-tempest",
            tags=("Avoidable", "Area Denial", "DoT", "Slow"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Divine Consecration",
            game_id=1276982,
            description=DIVINE_CONSECRATION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1276982/divine-consecration",
            tags=("Avoidable", "Area Denial", "DoT", "Pacify"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Trampled",
            game_id=1249135,
            description=TRAMPLED_DESCRIPTION,
            url="https://www.wowhead.com/spell=1249135/trampled",
            tags=("Avoidable", "Charge"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Blinding Light",
            game_id=1258514,
            description=BLINDING_LIGHT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1258514/blinding-light",
            tags=("Avoidable", "Interrupt Failure", "Raid Damage", "Disorient"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Judgment (Bellamy)",
            game_id=1251857,
            description=BELLAMY_TANK_COMBO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1251857/judgment",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Shield of the Righteous",
            game_id=1251859,
            description=BELLAMY_TANK_COMBO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1251859/shield-of-the-righteous",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Judgment (Lightblood)",
            game_id=1246736,
            description=LIGHTBLOOD_TANK_COMBO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246736/judgment",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Final Verdict",
            game_id=1251812,
            description=LIGHTBLOOD_TANK_COMBO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1251812/final-verdict",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Exorcism",
            game_id=1246745,
            description=EXORCISM_DESCRIPTION,
            url="https://www.wowhead.com/spell=1246745/exorcism",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
    ),
)


__all__ = [
    "LIGHTBLINDED_VANGUARD_MANIFEST",
]
