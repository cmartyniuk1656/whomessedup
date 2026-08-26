"""View-model builder for the Heroic Vashnik damage report."""
from __future__ import annotations

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "vashnik-the-malignant-damage"
REPORT_TITLE = "Heroic Vashnik the Malignant - Damage Report"
REPORT_DESCRIPTION = "Damage report for Heroic Vashnik the Malignant."
REPORT_DEFAULT_FIGHT = "Vashnik the Malignant"
REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude Vashnik and each Living Venom add type.",
    (
        "Kill-only scope restricts the report to successful pulls, and the dead-player filter removes a player's "
        "data from pulls where they died."
    ),
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
    enable_spec_analysis=True,
    spec_analysis_title="Vashnik the Malignant Spec Analysis",
    spec_analysis_subtitle="Average damage per player per counted pull across Vashnik and all Living Venom adds.",
)


def build_vashnik_the_malignant_damage_report_page(summary: EncounterTargetDamageSummary):
    return build_target_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_vashnik_the_malignant_damage_report_page",
]
