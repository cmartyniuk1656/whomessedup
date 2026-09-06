"""
View-model builder for the Mythic Nek'zali damage report page.
"""
from __future__ import annotations

from dataclasses import replace

from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "nek-zali-the-soulcoiler-damage"
REPORT_TITLE = "Heroic Nek'zali the Soulcoiler - Damage Report"
REPORT_DESCRIPTION = "Damage report for Heroic Nek'zali the Soulcoiler."
MYTHIC_REPORT_ID = "nek-zali-the-soulcoiler-damage-mythic"
MYTHIC_REPORT_TITLE = "Mythic Nek'zali the Soulcoiler - Damage Report"
MYTHIC_REPORT_DESCRIPTION = "Damage report for Mythic Nek'zali the Soulcoiler."
REPORT_DEFAULT_FIGHT = "Nek'zali the Soulcoiler"
REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude Nek'zali, Restless Amani, and Echo of Jawae damage.",
    (
        "Kill-only scope restricts the report to successful pulls, and the dead-player filter removes a player's "
        "data from pulls where they died."
    ),
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
MYTHIC_REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude Nek'zali, Restless Amani, Echo of Jawae, and Drowned Echo damage.",
    *REPORT_FOOTNOTES[1:],
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
    spec_analysis_title="Nek'zali Spec Analysis",
    spec_analysis_subtitle="Average damage per player per counted pull across Nek'zali and priority adds.",
)

MYTHIC_REPORT_CONFIG = replace(
    REPORT_CONFIG,
    report_id=MYTHIC_REPORT_ID,
    title=MYTHIC_REPORT_TITLE,
    footnotes=tuple(MYTHIC_REPORT_FOOTNOTES),
)


def build_nek_zali_the_soulcoiler_damage_report_page(
    summary: EncounterTargetDamageSummary,
    *,
    difficulty: str | int | None = None,
):
    config = MYTHIC_REPORT_CONFIG if str(difficulty or "").lower() in {"mythic", "5"} else REPORT_CONFIG
    return build_target_damage_report_page(summary, config=config)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "MYTHIC_REPORT_DESCRIPTION",
    "MYTHIC_REPORT_ID",
    "MYTHIC_REPORT_FOOTNOTES",
    "MYTHIC_REPORT_TITLE",
    "build_nek_zali_the_soulcoiler_damage_report_page",
]
