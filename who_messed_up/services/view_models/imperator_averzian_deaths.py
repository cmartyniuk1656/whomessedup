"""
View-model builder for the v2 Imperator Averzian death report page.
"""
from __future__ import annotations

from ..death_reports import DeathReportSummary
from ..imperator_averzian_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "imperator-averzian-deaths"
REPORT_TITLE = "Mythic Imperator Averzian - Death Report"
REPORT_DESCRIPTION = "Death report for Mythic Imperator Averzian."
REPORT_FOOTNOTES: list[str] = []

REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_imperator_averzian_deaths_report_page(summary: DeathReportSummary):
    return build_death_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_imperator_averzian_deaths_report_page",
]
