"""View-model builder for the Heroic Ula'tek damage report."""
from __future__ import annotations

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "ula-tek-damage"
REPORT_TITLE = "Heroic Ula'tek - Damage Report"
REPORT_DESCRIPTION = "Damage report for Heroic Ula'tek."
REPORT_DEFAULT_FIGHT = "Ula'tek"
REPORT_FOOTNOTES = [
    "Damage includes Ula'tek, her shared-health body parts, and every priority add; Blightscale Rawlings are optional pad targets.",
    (
        "Kill-only scope restricts the report to successful pulls, and the dead-player filter removes a player's "
        "data from pulls where they died."
    ),
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = TargetDamageReportConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    combined_total_label="Ula'tek damage",
    combined_average_label="Avg Ula'tek damage / Pull",
    table_total_label="Total Ula'tek Damage",
    table_average_label="Avg Ula'tek Damage / Pull",
    show_pull_count_summary=False,
    show_combined_total_summary=False,
    show_combined_average_summary=False,
    show_target_total_summaries=False,
    show_target_average_summaries=False,
    footnotes=tuple(REPORT_FOOTNOTES),
    enable_spec_analysis=True,
    spec_analysis_title="Ula'tek Spec Analysis",
    spec_analysis_subtitle="Average boss, body-part, and priority-add damage per player per counted pull.",
)


def build_ula_tek_damage_report_page(summary: EncounterTargetDamageSummary):
    return build_target_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_ula_tek_damage_report_page",
]
