"""
View-model builder for the Heroic Nek'zali avoidable damage report page.
"""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..nek_zali_the_soulcoiler_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "nek-zali-the-soulcoiler-avoidable-damage"
REPORT_TITLE = "Heroic Nek'zali the Soulcoiler - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic Nek'zali the Soulcoiler pulls."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]

REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_nek_zali_the_soulcoiler_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_nek_zali_the_soulcoiler_avoidable_damage_report_page",
]
