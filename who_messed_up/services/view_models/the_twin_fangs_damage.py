"""View-model builder for the Heroic The Twin Fangs damage report."""
from __future__ import annotations

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "the-twin-fangs-damage"
REPORT_TITLE = "Heroic The Twin Fangs - Damage Report"
REPORT_DESCRIPTION = "Damage report for Heroic The Twin Fangs."
REPORT_DEFAULT_FIGHT = "The Twin Fangs"
REPORT_FOOTNOTES = [
    (
        "Kill-only scope restricts the report to successful pulls, and the dead-player filter removes a player's "
        "data from pulls where they died."
    ),
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = TargetDamageReportConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    combined_total_label="Twin Fangs damage",
    combined_average_label="Avg Twin Fangs damage / Pull",
    table_total_label="Total Twin Fangs Damage",
    table_average_label="Avg Twin Fangs Damage / Pull",
    show_pull_count_summary=False,
    show_combined_total_summary=False,
    show_combined_average_summary=False,
    show_target_total_summaries=False,
    show_target_average_summaries=False,
    footnotes=tuple(REPORT_FOOTNOTES),
    enable_spec_analysis=True,
    spec_analysis_title="The Twin Fangs Spec Analysis",
    spec_analysis_subtitle="Average boss and priority-add damage per player per counted pull.",
)


def build_the_twin_fangs_damage_report_page(summary: EncounterTargetDamageSummary):
    return build_target_damage_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_twin_fangs_damage_report_page",
]
