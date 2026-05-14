"""
View-model builder for the v2 Crown of the Cosmos death report page.
"""
from __future__ import annotations

from ..crown_of_the_cosmos_deaths import REPORT_DEFAULT_FIGHT
from ..death_reports import DeathReportSummary
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "crown-of-the-cosmos-deaths"
REPORT_TITLE = "Mythic Crown of the Cosmos - Death Report"
REPORT_DESCRIPTION = "Death report for Mythic Crown of the Cosmos."
REPORT_FOOTNOTES: list[str] = []

REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_crown_of_the_cosmos_deaths_report_page(summary: DeathReportSummary):
    return build_death_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_crown_of_the_cosmos_deaths_report_page",
]
