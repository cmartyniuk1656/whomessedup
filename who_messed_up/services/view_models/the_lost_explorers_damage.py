"""View-model builder for the Heroic The Lost Explorers damage report."""
from __future__ import annotations

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "the-lost-explorers-damage"
REPORT_TITLE = "Heroic The Lost Explorers - Damage Report"
REPORT_DESCRIPTION = "Damage report for Heroic The Lost Explorers."
REPORT_DEFAULT_FIGHT = "The Lost Explorers"
REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude First Mate Nama, Scrollsage Iku, and Trader Gebbo damage.",
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
    spec_analysis_title="The Lost Explorers Spec Analysis",
    spec_analysis_subtitle="Average damage per player per counted pull across all three explorers.",
)


def build_the_lost_explorers_damage_report_page(summary: EncounterTargetDamageSummary):
    return build_target_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_lost_explorers_damage_report_page",
]
