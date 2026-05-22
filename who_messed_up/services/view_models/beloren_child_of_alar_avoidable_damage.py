"""
View-model builder for the v2 Belo'ren, Child of Al'ar avoidable damage report page.
"""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..beloren_child_of_alar_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "beloren-child-of-alar-avoidable-damage"
REPORT_TITLE = "Mythic Belo'ren, Child of Al'ar - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Mythic Belo'ren, Child of Al'ar pulls."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
    "Wrong-Feather Flames and Voidlight Rupture DoT ticks are aggregated into the triggering mistake event.",
]

REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_beloren_child_of_alar_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_beloren_child_of_alar_avoidable_damage_report_page",
]
