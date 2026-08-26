"""View-model builder for the Heroic The Twin Fangs avoidable damage report."""
from __future__ import annotations

from ..avoidable_damage import AvoidableDamageSummary
from ..the_twin_fangs_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "the-twin-fangs-avoidable-damage"
REPORT_TITLE = "Heroic The Twin Fangs - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic The Twin Fangs pulls."
REPORT_FOOTNOTES = [
    "Ravenous Feast is counted only when the player already had Feasted before the impact.",
    "Stone Breaker is counted only when it strikes a non-tank; assigned tank soaks are excluded.",
    (
        "Coiling Ichor ticks, Caustic Globule failures, and missed Stone Breaker raid hits are not personally "
        "scored because the logged victim is not necessarily the responsible player."
    ),
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_the_twin_fangs_avoidable_damage_report_page(summary: AvoidableDamageSummary):
    return build_avoidable_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_twin_fangs_avoidable_damage_report_page",
]
