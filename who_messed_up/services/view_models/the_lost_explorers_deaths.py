"""View-model builder for the Heroic The Lost Explorers death report."""
from __future__ import annotations

from ..death_reports import DeathReportSummary
from ..the_lost_explorers_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "the-lost-explorers-deaths"
REPORT_TITLE = "Heroic The Lost Explorers - Death Report"
REPORT_DESCRIPTION = "Death report for Heroic The Lost Explorers."
REPORT_FOOTNOTES: list[str] = []
REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_the_lost_explorers_deaths_report_page(summary: DeathReportSummary):
    return build_death_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_lost_explorers_deaths_report_page",
]
