"""
View-model builder for the v2 Imperator Averzian damage report page.
"""
from __future__ import annotations

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "imperator-averzian-damage"
REPORT_TITLE = "Imperator Averzian - Damage Report"
REPORT_DESCRIPTION = (
    "Track player damage into Imperator Averzian, Abyssal Voidshaper, and Voidbound Annihilator."
)
REPORT_DEFAULT_FIGHT = "Imperator Averzian"
REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude specific Imperator Averzian encounter enemies.",
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]

REPORT_CONFIG = TargetDamageReportConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    combined_total_label="Combined selected-target damage",
    combined_average_label="Avg selected-target damage / Pull",
    table_total_label="Total Selected Damage",
    table_average_label="Avg Selected Damage / Pull",
    show_pull_count_summary=False,
    show_combined_total_summary=False,
    show_combined_average_summary=False,
    show_target_total_summaries=False,
    show_target_average_summaries=False,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_imperator_averzian_damage_report_page(summary: EncounterTargetDamageSummary):
    return build_target_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_imperator_averzian_damage_report_page",
]
