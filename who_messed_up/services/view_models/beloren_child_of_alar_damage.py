"""
View-model builder for the v2 Belo'ren, Child of Al'ar damage report page.
"""
from __future__ import annotations

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "beloren-child-of-alar-damage"
REPORT_TITLE = "Mythic Belo'ren, Child of Al'ar - Damage Report"
REPORT_DESCRIPTION = "Damage report for Mythic Belo'ren, Child of Al'ar."
REPORT_DEFAULT_FIGHT = "Belo'ren, Child of Al'ar"
REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude specific Belo'ren encounter enemies.",
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
    spec_analysis_title="Belo'ren Spec Analysis",
    spec_analysis_subtitle="Average damage per player per counted pull across boss, ember, and egg targets.",
    spec_analysis_target_metrics=(
        ("boss_egg", "Boss Egg Damage", "boss_egg"),
        ("add_egg", "Add Egg Damage", "add_egg"),
    ),
    spec_analysis_sort_labels={
        "overall": "Overall",
        "boss_priority": "Boss + Priority Damage",
        "boss": "Boss Damage",
        "priority": "Priority Damage",
        "boss_egg": "Boss Egg Damage",
        "add_egg": "Add Egg Damage",
        "pad": "Pad Damage",
    },
)


def build_beloren_child_of_alar_damage_report_page(summary: EncounterTargetDamageSummary):
    return build_target_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_beloren_child_of_alar_damage_report_page",
]
