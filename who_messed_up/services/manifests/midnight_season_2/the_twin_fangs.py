"""
Heroic The Twin Fangs ability and target metadata for Midnight Season 2.

Observed across Warcraft Logs report 6CqvafhpjRc9nrAX, fights 11-17
(encounter 3421), then cross-checked against Method's Heroic guide and live
spell descriptions.
"""
from __future__ import annotations

from ...boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
)


THE_TWIN_FANGS_HEROIC_MANIFEST = BossManifest(
    boss_id="the-twin-fangs",
    boss_name="The Twin Fangs",
    difficulty="heroic",
    targets=(
        EncounterTargetConfig(
            slug="vexhul",
            label="Vexhul",
            enemy_name="Vexhul",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="ithraz",
            label="Ithraz",
            enemy_name="Ithraz",
            bucket=EncounterTargetBucket.BOSS,
        ),
        EncounterTargetConfig(
            slug="spawn_of_vexhul",
            label="Spawn of Vexhul",
            enemy_name="Spawn of Vexhul",
            bucket=EncounterTargetBucket.PRIORITY_ADD,
        ),
    ),
    abilities=(
        BossAbilityMetadata(
            name="Toxic Fumes",
            game_id=1294976,
            description="The venom sea deals constant Nature damage to the entire raid throughout the encounter.",
            url="https://www.wowhead.com/spell=1294976",
            tags=("Raid Damage", "Unavoidable", "Periodic"),
        ),
        BossAbilityMetadata(
            name="Eternal Venom",
            game_id=1290480,
            description=(
                "Permanent venom stacks deal periodic Nature damage and kill a player at ten applications. "
                "Because stacks come from both required and avoidable mechanics, the periodic damage is not "
                "personally scored."
            ),
            url="https://www.wowhead.com/spell=1290480",
            tags=("Raid Mechanic", "Stacking DoT", "Venom Economy"),
        ),
        BossAbilityMetadata(
            name="Coiling Ichor",
            game_id=1290878,
            description=(
                "Marked players carry shrinking damage circles for twelve seconds before dropping Congealed "
                "Gore. The marked player's own ticks are required, and overlap damage cannot be assigned reliably "
                "to one player, so these ticks are not personally scored."
            ),
            url="https://www.wowhead.com/spell=1290878",
            tags=("Targeted", "Circle", "DoT", "Drop Mechanic"),
        ),
        BossAbilityMetadata(
            name="Ravenous Feast",
            game_id=1290662,
            description=(
                "Three assigned groups soak successive Feast strikes to remove Eternal Venom. A hit is avoidable "
                "only when the player already has Feasted from an earlier strike in the same sequence."
            ),
            url="https://www.wowhead.com/spell=1290662",
            tags=("Avoidable", "Conditional", "Soak", "Repeat Soak"),
            avoidable=True,
            avoidable_requires_active_debuff_ability_id=1310096,
            avoidable_requires_active_debuff_min_age_ms=100.0,
        ),
        BossAbilityMetadata(
            name="Caustic Globule (Soaked)",
            game_id=1289201,
            description=(
                "A player intentionally touches each globule before it ruptures, taking the hit and an Eternal "
                "Venom stack in place of the entire raid. This is positive venom management unless the new "
                "stack reaches the lethal ten-stack threshold."
            ),
            url="https://www.wowhead.com/spell=1289201",
            tags=("Required Mechanic", "Single-Player Soak", "Venom Economy"),
        ),
        BossAbilityMetadata(
            name="Caustic Deluge (Tank Channel)",
            game_id=1289237,
            description="Vexhul channels unavoidable Nature damage into her current tank for five seconds.",
            url="https://www.wowhead.com/spell=1289237",
            tags=("Tank Mechanic", "Unavoidable", "Channel"),
        ),
        BossAbilityMetadata(
            name="Venomous Emergence",
            game_id=1308122,
            description="Vexhul deals unavoidable raid damage, applies Eternal Venom, and summons three spawns.",
            url="https://www.wowhead.com/spell=1308122",
            tags=("Raid Damage", "Unavoidable", "Add Spawn"),
        ),
        BossAbilityMetadata(
            name="Corrosive Spit",
            game_id=1293295,
            description=(
                "A Spawn of Vexhul aims a frontal line at a player. Anyone struck takes Nature damage and gains "
                "Eternal Venom."
            ),
            url="https://www.wowhead.com/spell=1293295",
            tags=("Avoidable", "Frontal", "Line", "Add Mechanic"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Caustic Globule (Unsoaked Rupture)",
            game_id=1290338,
            description=(
                "An unsoaked globule ruptures into raid-wide damage and gives everyone Eternal Venom. The log "
                "records the raid as victims rather than the missed assignee, so this is not personally scored."
            ),
            url="https://www.wowhead.com/spell=1290338",
            tags=("Soak Failure", "Raid Damage", "Assignment Responsibility"),
        ),
        BossAbilityMetadata(
            name="Stone Breaker (Soaked Impact)",
            game_id=1310371,
            description=(
                "A tank must soak each slam. Assigned tank hits are required; any non-tank struck by the small "
                "impact has taken avoidable damage."
            ),
            url="https://www.wowhead.com/spell=1310371",
            tags=("Avoidable", "Tank Soak", "Ground Impact"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Stone Breaker (Missed Soak)",
            game_id=1289153,
            description=(
                "When nobody soaks a Stone Breaker impact, the raid takes armor-ignoring damage and a knockback. "
                "Victims are not personally responsible for the missed tank assignment."
            ),
            url="https://www.wowhead.com/spell=1289153",
            tags=("Soak Failure", "Raid Damage", "Tank Assignment"),
        ),
        BossAbilityMetadata(
            name="Sanguine Storm (Enrage Pulse)",
            game_id=1313533,
            description="The extended enrage version of Sanguine Storm deals unavoidable raid damage every three seconds.",
            url="https://www.wowhead.com/spell=1313533",
            tags=("Raid Damage", "Unavoidable", "Enrage"),
        ),
        BossAbilityMetadata(
            name="Caustic Rain (Enrage Pulse)",
            game_id=1308835,
            description="Caustic Rain deals unavoidable raid damage during the third-Submerge hard enrage.",
            url="https://www.wowhead.com/spell=1308835",
            tags=("Raid Damage", "Unavoidable", "Enrage"),
        ),
        BossAbilityMetadata(
            name="Sanguine Storm (Impact)",
            game_id=1306876,
            description="Falling gore strikes players within four yards and leaves a short-lived Congealed Gore pool.",
            url="https://www.wowhead.com/spell=1306876",
            tags=("Avoidable", "Ground Impact", "Intermission"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Caustic Deluge (Acid Splash)",
            game_id=1289994,
            description=(
                "Acid splashes around the Deluge target damage players within four yards, apply Eternal Venom, "
                "and form Caustic Globules."
            ),
            url="https://www.wowhead.com/spell=1289994",
            tags=("Avoidable", "Ground Impact", "Circle"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Vile Flood",
            game_id=1294605,
            description="Vexhul sweeps a lethal frontal torrent across the arena during Submerge.",
            url="https://www.wowhead.com/spell=1294605",
            tags=("Avoidable", "Frontal", "Beam", "Intermission"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Clotted Bolt",
            game_id=1295115,
            description=(
                "Ithraz uses this ranged attack when his current target is out of melee range. Logs can target "
                "other players after tank deaths, so the victim is not always personally responsible."
            ),
            url="https://www.wowhead.com/spell=1295115",
            tags=("Range Check", "Tank Positioning"),
        ),
        BossAbilityMetadata(
            name="Concentrated Spittle",
            game_id=1295107,
            description=(
                "Vexhul uses this ranged attack when her current target is out of melee range. Logs can target "
                "other players after tank deaths, so the victim is not always personally responsible."
            ),
            url="https://www.wowhead.com/spell=1295107",
            tags=("Range Check", "Tank Positioning"),
        ),
        BossAbilityMetadata(
            name="Deadly Venom",
            game_id=1297338,
            description="The venom surrounding the platform deals periodic damage while a player remains within it.",
            url="https://www.wowhead.com/spell=1297338",
            tags=("Avoidable", "Environment", "Area Denial", "DoT"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Congealed Gore (Persistent)",
            game_id=1292552,
            description="Pools left by expired Coiling Ichor deal periodic Shadow damage and slow players inside.",
            url="https://www.wowhead.com/spell=1292552",
            tags=("Avoidable", "Area Denial", "DoT", "Slow"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Stir the Depths (Wave)",
            game_id=1292807,
            description="Venom waves cross the platform, damaging players struck and applying Eternal Venom.",
            url="https://www.wowhead.com/spell=1292807",
            tags=("Avoidable", "Wave", "Venom Stack"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Stir the Depths (Raid Pulse)",
            game_id=1292806,
            description="Vexhul deals unavoidable raid-wide Nature damage every two seconds while forming waves.",
            url="https://www.wowhead.com/spell=1292806",
            tags=("Raid Damage", "Unavoidable", "Channel"),
        ),
        BossAbilityMetadata(
            name="Noxious Slick",
            game_id=1309471,
            description="Slicks formed by Submerge deal periodic Nature damage and increase damage taken by 30%.",
            url="https://www.wowhead.com/spell=1309471",
            tags=("Avoidable", "Area Denial", "DoT", "Damage Taken Increase"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Congealed Gore (Temporary)",
            game_id=1306925,
            description="Short-lived pools left by Sanguine Storm impacts deal periodic Shadow damage and slow players.",
            url="https://www.wowhead.com/spell=1306925",
            tags=("Avoidable", "Area Denial", "DoT", "Slow", "Intermission"),
            avoidable=True,
        ),
        BossAbilityMetadata(
            name="Caustic Rain (Glob Impact)",
            game_id=1308841,
            description=(
                "Caustic globs strike during the third-Submerge hard enrage. The encounter has already reached "
                "its failure state, so these impacts are not personally scored."
            ),
            url="https://www.wowhead.com/spell=1308841",
            tags=("Ground Impact", "Enrage"),
        ),
    ),
)


__all__ = ["THE_TWIN_FANGS_HEROIC_MANIFEST"]
