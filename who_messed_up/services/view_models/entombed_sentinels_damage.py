"""View-model builder for the Heroic and Mythic Entombed Sentinels damage report."""
from __future__ import annotations

from dataclasses import replace

from ..boss_manifest_types import normalize_manifest_difficulty
from ..target_damage import EncounterTargetDamageSummary
from .target_damage import TargetDamageReportConfig, build_target_damage_report_page

REPORT_ID = "entombed-sentinels-damage"
REPORT_TITLE = "Heroic Entombed Sentinels - Damage Report"
REPORT_DESCRIPTION = "Damage report for Heroic Entombed Sentinels."
REPORT_DEFAULT_FIGHT = "Entombed Sentinels"
MYTHIC_REPORT_ID = "entombed-sentinels-damage-mythic"
MYTHIC_REPORT_TITLE = "Mythic Entombed Sentinels - Damage Report"
MYTHIC_REPORT_DESCRIPTION = "Damage Report for Mythic Entombed Sentinels."
REPORT_FOOTNOTES = [
    "Use the target toggles to include or exclude Blood of Ula'tek, Breath of Ula'tek, and Venom Coagulation damage.",
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
    spec_analysis_title="Entombed Sentinels Spec Analysis",
    spec_analysis_subtitle="Average damage per player per counted pull across both Sentinels and the priority add.",
)


MYTHIC_REPORT_CONFIG = replace(
    REPORT_CONFIG,
    report_id=MYTHIC_REPORT_ID,
    title=MYTHIC_REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_entombed_sentinels_damage_report_page(
    summary: EncounterTargetDamageSummary,
    *,
    difficulty: str | int | None = None,
):
    config = (
        MYTHIC_REPORT_CONFIG
        if normalize_manifest_difficulty(difficulty) == "mythic"
        else REPORT_CONFIG
    )
    return build_target_damage_report_page(summary, config=config)


__all__ = [
    "MYTHIC_REPORT_ID",
    "MYTHIC_REPORT_TITLE",
    "MYTHIC_REPORT_DESCRIPTION",
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_entombed_sentinels_damage_report_page",
]
