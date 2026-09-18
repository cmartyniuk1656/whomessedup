"""View-model builder for the Heroic and Mythic Vashnik death report."""
from __future__ import annotations

from dataclasses import replace

from ..boss_manifest_types import normalize_manifest_difficulty
from ..death_reports import DeathReportSummary
from ..vashnik_the_malignant_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "vashnik-the-malignant-deaths"
MYTHIC_REPORT_ID = "vashnik-the-malignant-deaths-mythic"
REPORT_TITLE = "Heroic Vashnik the Malignant - Death Report"
MYTHIC_REPORT_TITLE = "Mythic Vashnik the Malignant - Death Report"
REPORT_DESCRIPTION = "Death report for Heroic Vashnik the Malignant."
MYTHIC_REPORT_DESCRIPTION = "Death report for Mythic Vashnik the Malignant."
REPORT_FOOTNOTES: list[str] = []
REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


MYTHIC_REPORT_CONFIG = replace(
    REPORT_CONFIG,
    report_id=MYTHIC_REPORT_ID,
    title=MYTHIC_REPORT_TITLE,
)


def build_vashnik_the_malignant_deaths_report_page(
    summary: DeathReportSummary,
    *,
    difficulty: str | int | None = None,
):
    config = MYTHIC_REPORT_CONFIG if normalize_manifest_difficulty(difficulty) == "mythic" else REPORT_CONFIG
    return build_death_report_page(summary, config=config)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "MYTHIC_REPORT_ID",
    "MYTHIC_REPORT_TITLE",
    "MYTHIC_REPORT_DESCRIPTION",
    "REPORT_TITLE",
    "build_vashnik_the_malignant_deaths_report_page",
]
