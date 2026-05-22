"""
Belo'ren, Child of Al'ar ability metadata for Midnight Season 1.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


VOIDLIGHT_CONVERGENCE_DESCRIPTION = (
    "Belo'ren continuously radiates Voidlight damage into the raid. In the scraped reports this appears as "
    "frequent full-raid ticks from the boss."
)

BURNING_HEART_DESCRIPTION = (
    "Belo'ren's heart burns the raid throughout the encounter. The reports show repeated full-raid periodic "
    "damage ticks on a steady cadence."
)

FLAMES_DESCRIPTION = (
    "Belo'ren's intermission Flames pulse damage to players standing in the matching color. This baseline pulse "
    "is treated as unavoidable raid damage; wrong-color penalty debuffs are tracked separately."
)

WRONG_FLAMES_DESCRIPTION = (
    "Light and Void Flames apply an extra stacking penalty when a player stands in the opposite color during the "
    "intermission pulse. The avoidable report counts only those wrong-Feather debuff windows and their damage ticks."
)

DEATH_DROP_DESCRIPTION = (
    "Belo'ren drops the raid for a synchronized burst of damage. In the reports this hit nearly every living "
    "player at predictable timestamps."
)

ASHEN_BENEDICTION_DESCRIPTION = (
    "Belo'ren applies Ashen Benediction to the raid, observed as a synchronized raid-wide damage and debuff event."
)

EDICT_DESCRIPTION = (
    "Belo'ren strikes the active tanks with alternating Light and Void Edicts. The scraped reports show these "
    "hits almost exclusively on tank players."
)

QUILL_DESCRIPTION = (
    "Light and Void Quill mark an opposite-Feather target, then fire a line that should be soaked by one "
    "matching-color non-target. The avoidable report only counts non-target players hit while carrying the "
    "wrong Feather; correct-color Quill hits are ignored."
)

BURN_DESCRIPTION = (
    "Light and Void Burn are heal absorbs that deal periodic damage until the absorb is healed off. The damage "
    "is assigned encounter pressure rather than avoidable personal failure."
)

ECHO_DESCRIPTION = (
    "Light and Void Echoes are assigned orb soaks. Correct-color Echo soak damage is expected, while wrong-color "
    "orb mistakes are represented by Voidlight Rupture events."
)

DIVE_DESCRIPTION = (
    "Light and Void Dive are full-raid soak events. The reports show synchronized raid damage rather than "
    "individual avoidable line-soak failures."
)

PATCH_DESCRIPTION = (
    "Light and Void patches left on the battlefield apply short-lived damage effects to players who stand in them."
)

VOIDLIGHT_RUPTURE_DESCRIPTION = (
    "Voidlight Rupture occurs when a player soaks an orb with the wrong Feather. It is treated as avoidable "
    "wrong-color soak damage and is also counted in the Light/Void mistake report."
)

ERUPTION_DESCRIPTION = (
    "Light and Void Eruption occur when an Ember cast resolves. The resulting raid damage is not attributed "
    "to a single player in the avoidable damage report; wrong-Feather interrupts of those casts are tracked "
    "separately in the Light/Void mistake report."
)

ERUPTING_ECHO_DESCRIPTION = (
    "Light and Void Echo orbs erupt when they reach Belo'ren, producing large raid-wide damage bursts. The "
    "damage is treated as unavoidable at the individual-player level because the failure is not attributable "
    "to one damaged player."
)

EMBER_BLAST_DESCRIPTION = (
    "A minor Light or Void Ember blast observed as isolated add damage in the scraped reports. It is included "
    "for death-report context but is not attributed as avoidable in this first pass."
)

BELOREN_BOSS_DAMAGE_FILTER = 'target.name = "Belo\'ren" and encounterPhase = 1'
BELOREN_BOSS_EGG_DAMAGE_FILTER = 'target.name = "Belo\'ren" and encounterPhase = 2'
BELOREN_ADD_EGG_WINDOW_FILTER = (
    'IN RANGE FROM type = "begincast" and ability.id = 1263412 '
    'TO ((type = "cast" and ability.id = 1263412) OR '
    '(type = "damage" and overkill > 0 and target.id in (246729, 246728))) END'
)
BELOREN_ADD_EGG_DAMAGE_FILTER = f"target.id in (246729, 246728) AND {BELOREN_ADD_EGG_WINDOW_FILTER}"
BELOREN_LIGHT_EMBER_DAMAGE_FILTER = f"target.id = 246729 and NOT ({BELOREN_ADD_EGG_WINDOW_FILTER})"
BELOREN_VOID_EMBER_DAMAGE_FILTER = f"target.id = 246728 and NOT ({BELOREN_ADD_EGG_WINDOW_FILTER})"


BELOREN_CHILD_OF_ALAR_MANIFEST = BossManifest(
    boss_id="beloren-child-of-alar",
    boss_name="Belo'ren, Child of Al'ar",
    difficulty="mythic",
    targets=(
        EncounterTargetConfig(
            slug="beloren",
            label="Belo'ren",
            enemy_name="Belo'ren",
            bucket=EncounterTargetBucket.BOSS,
            damage_filter=BELOREN_BOSS_DAMAGE_FILTER,
        ),
        EncounterTargetConfig(
            slug="boss_egg",
            label="Boss Egg Damage",
            enemy_name="Belo'ren",
            damage_filter=BELOREN_BOSS_EGG_DAMAGE_FILTER,
        ),
        EncounterTargetConfig(
            slug="light_ember",
            label="Light Ember",
            enemy_name="Light Ember",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
            damage_filter=BELOREN_LIGHT_EMBER_DAMAGE_FILTER,
        ),
        EncounterTargetConfig(
            slug="void_ember",
            label="Void Ember",
            enemy_name="Void Ember",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
            damage_filter=BELOREN_VOID_EMBER_DAMAGE_FILTER,
        ),
        EncounterTargetConfig(
            slug="add_egg",
            label="Add Egg Damage",
            enemy_name="Light/Void Ember Egg",
            damage_filter=BELOREN_ADD_EGG_DAMAGE_FILTER,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Voidlight Convergence",
            game_id=1241932,
            description=VOIDLIGHT_CONVERGENCE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241932/voidlight-convergence",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Burning Heart",
            game_id=1264650,
            description=BURNING_HEART_DESCRIPTION,
            url="https://www.wowhead.com/spell=1264650/burning-heart",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Flames",
            game_id=1242803,
            description=FLAMES_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242803/light-flames",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Flames",
            game_id=1242815,
            description=FLAMES_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242815/void-flames",
            tags=("Raid Damage", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Flames (Wrong Feather)",
            game_id=1242803,
            description=WRONG_FLAMES_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242803/light-flames",
            tags=("Avoidable", "Flames", "Wrong Feather", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Void Flames (Wrong Feather)",
            game_id=1242815,
            description=WRONG_FLAMES_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242815/void-flames",
            tags=("Avoidable", "Flames", "Wrong Feather", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Death Drop",
            game_id=1241333,
            description=DEATH_DROP_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241333/death-drop",
            tags=("Raid Damage", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Ashen Benediction",
            game_id=1262573,
            description=ASHEN_BENEDICTION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1262573/ashen-benediction",
            tags=("Raid Damage", "Debuff", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Edict",
            game_id=1241646,
            description=EDICT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241646/light-edict",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Edict (Follow-up)",
            game_id=1265781,
            description=EDICT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1265781/light-edict",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Edict",
            game_id=1241676,
            description=EDICT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241676/void-edict",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Edict (Follow-up)",
            game_id=1265793,
            description=EDICT_DESCRIPTION,
            url="https://www.wowhead.com/spell=1265793/void-edict",
            tags=("Tank Mechanic", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Quill (Wrong Feather)",
            game_id=1242093,
            description=QUILL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242093/light-quill",
            tags=("Avoidable", "Line Soak", "Wrong Feather"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Void Quill (Wrong Feather)",
            game_id=1242094,
            description=QUILL_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242094/void-quill",
            tags=("Avoidable", "Line Soak", "Wrong Feather"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Light Burn",
            game_id=1244348,
            description=BURN_DESCRIPTION,
            url="https://www.wowhead.com/spell=1244348/light-burn",
            tags=("Heal Absorb", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Burn",
            game_id=1266404,
            description=BURN_DESCRIPTION,
            url="https://www.wowhead.com/spell=1266404/void-burn",
            tags=("Heal Absorb", "DoT", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Echo",
            game_id=1242991,
            description=ECHO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242991/light-echo",
            tags=("Orb Soak", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Echo",
            game_id=1242996,
            description=ECHO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1242996/void-echo",
            tags=("Orb Soak", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Dive",
            game_id=1241291,
            description=DIVE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241291/light-dive",
            tags=("Raid Damage", "Full Raid Soak", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Dive",
            game_id=1241340,
            description=DIVE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241340/void-dive",
            tags=("Raid Damage", "Full Raid Soak", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Patch",
            game_id=1241840,
            description=PATCH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241840/light-patch",
            tags=("Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Void Patch",
            game_id=1241841,
            description=PATCH_DESCRIPTION,
            url="https://www.wowhead.com/spell=1241841/void-patch",
            tags=("Avoidable", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Voidlight Rupture",
            game_id=1243866,
            description=VOIDLIGHT_RUPTURE_DESCRIPTION,
            url="https://www.wowhead.com/spell=1243866/voidlight-rupture",
            tags=("Avoidable", "Orb Soak", "Wrong Feather"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Light Eruption",
            game_id=1243852,
            description=ERUPTION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1243852/light-eruption",
            tags=("Raid Damage", "Orb Failure", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Void Eruption",
            game_id=1243854,
            description=ERUPTION_DESCRIPTION,
            url="https://www.wowhead.com/spell=1243854/void-eruption",
            tags=("Raid Damage", "Orb Failure", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Erupting Light Echo",
            game_id=1262736,
            description=ERUPTING_ECHO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1262736/erupting-light-echo",
            tags=("Raid Damage", "Echo", "Orb Failure", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Erupting Void Echo",
            game_id=1262737,
            description=ERUPTING_ECHO_DESCRIPTION,
            url="https://www.wowhead.com/spell=1262737/erupting-void-echo",
            tags=("Raid Damage", "Echo", "Orb Failure", "Unavoidable"),
        ),
        BossAbilityMetadata(
            name="Light Blast",
            game_id=1264696,
            description=EMBER_BLAST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1264696/light-blast",
            tags=("Add Cast",),
        ),
        BossAbilityMetadata(
            name="Void Blast",
            game_id=1264698,
            description=EMBER_BLAST_DESCRIPTION,
            url="https://www.wowhead.com/spell=1264698/void-blast",
            tags=("Add Cast",),
        ),
    ),
)


__all__ = [
    "BELOREN_CHILD_OF_ALAR_MANIFEST",
]
