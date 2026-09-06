"""View-model builder for the Heroic Ula'tek avoidable damage report."""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..ula_tek_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "ula-tek-avoidable-damage"
REPORT_TITLE = "Heroic Ula'tek - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic Ula'tek pulls."
REPORT_FOOTNOTES = [
    "Caustic Waves include both the initial wave hit and its stacking damage-over-time effect.",
    "Desperate Thrash counts only non-tank victims caught in the Weakened Doomscale's frontal.",
    "Calcified Corpse scores only the petrified player's direct damage; its raid-wide toxin is a team failure.",
    "Volatile Purge is evaluated in the mechanics scorecard because baseline and overlap damage share log IDs.",
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_ula_tek_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_ula_tek_avoidable_damage_report_page",
]
