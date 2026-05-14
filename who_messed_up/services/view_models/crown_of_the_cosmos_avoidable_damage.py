"""
View-model builder for the v2 Crown of the Cosmos avoidable damage report page.
"""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..crown_of_the_cosmos_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "crown-of-the-cosmos-avoidable-damage"
REPORT_TITLE = "Mythic Crown of the Cosmos - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Mythic Crown of the Cosmos pulls."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
    "Bursting Emptiness only counts players clipped by the outgoing lines; assigned-player expiration hits are excluded.",
    "Corrupting Essence immunity hits with no effective damage and no damage-taken debuff application are excluded.",
]

REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_crown_of_the_cosmos_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_crown_of_the_cosmos_avoidable_damage_report_page",
]
