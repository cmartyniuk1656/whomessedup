"""View-model builder for the Heroic The Lost Explorers avoidable damage report."""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..the_lost_explorers_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "the-lost-explorers-avoidable-damage"
REPORT_TITLE = "Heroic The Lost Explorers - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic The Lost Explorers pulls."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_the_lost_explorers_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_lost_explorers_avoidable_damage_report_page",
]
