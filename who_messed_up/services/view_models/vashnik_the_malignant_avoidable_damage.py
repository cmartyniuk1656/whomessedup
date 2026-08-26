"""View-model builder for the Heroic Vashnik avoidable damage report."""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..vashnik_the_malignant_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "vashnik-the-malignant-avoidable-damage"
REPORT_TITLE = "Heroic Vashnik the Malignant - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic Vashnik the Malignant pulls."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_vashnik_the_malignant_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_vashnik_the_malignant_avoidable_damage_report_page",
]
