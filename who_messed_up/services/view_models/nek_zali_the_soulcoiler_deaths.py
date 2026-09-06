"""
View-model builder for the Mythic Nek'zali death report page.
"""
from __future__ import annotations

from ..death_reports import DeathReportSummary
from ..nek_zali_the_soulcoiler_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "nek-zali-the-soulcoiler-deaths"
REPORT_TITLE = "Mythic Nek'zali the Soulcoiler - Death Report"
REPORT_DESCRIPTION = "Death report for Mythic Nek'zali the Soulcoiler."
REPORT_FOOTNOTES: list[str] = []

REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_nek_zali_the_soulcoiler_deaths_report_page(summary: DeathReportSummary):
    return build_death_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_nek_zali_the_soulcoiler_deaths_report_page",
]
