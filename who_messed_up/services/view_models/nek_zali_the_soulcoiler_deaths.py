"""
View-model builder for the Mythic Nek'zali death report page.
"""
from __future__ import annotations

from ..death_reports import DeathReportSummary
from ..nek_zali_the_soulcoiler_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "nek-zali-the-soulcoiler-deaths"
REPORT_TITLE = "Heroic Nek'zali the Soulcoiler - Death Report"
REPORT_DESCRIPTION = "Death report for Heroic Nek'zali the Soulcoiler."
MYTHIC_REPORT_ID = "nek-zali-the-soulcoiler-deaths-mythic"
MYTHIC_REPORT_TITLE = "Mythic Nek'zali the Soulcoiler - Death Report"
MYTHIC_REPORT_DESCRIPTION = "Death report for Mythic Nek'zali the Soulcoiler."
REPORT_FOOTNOTES: list[str] = []

REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)

MYTHIC_REPORT_CONFIG = DeathReportPageConfig(
    report_id=MYTHIC_REPORT_ID,
    title=MYTHIC_REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_nek_zali_the_soulcoiler_deaths_report_page(
    summary: DeathReportSummary,
    *,
    difficulty: str | int | None = None,
):
    config = MYTHIC_REPORT_CONFIG if str(difficulty or "").lower() in {"mythic", "5"} else REPORT_CONFIG
    return build_death_report_page(summary, config=config)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "MYTHIC_REPORT_DESCRIPTION",
    "MYTHIC_REPORT_ID",
    "MYTHIC_REPORT_TITLE",
    "build_nek_zali_the_soulcoiler_deaths_report_page",
]
