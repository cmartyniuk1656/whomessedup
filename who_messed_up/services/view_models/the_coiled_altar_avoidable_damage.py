"""View-model builder for the Heroic The Coiled Altar avoidable damage report."""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..the_coiled_altar_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "the-coiled-altar-avoidable-damage"
REPORT_TITLE = "Heroic The Coiled Altar - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic The Coiled Altar pulls."
REPORT_FOOTNOTES = [
    "Volatile Venom excludes the assigned orb carrier and counts only nearby players clipped by that carrier's pulse.",
    "Gloombomb excludes its marked players and counts only additional players caught in an explosion.",
    "Sever, Soul Sever, their associated DoT, and Blighted Sever count only non-tank victims.",
    "Execution and Grim Execution are not personally scored because their victims do not identify who caused the failed group soak.",
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_the_coiled_altar_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_coiled_altar_avoidable_damage_report_page",
]
