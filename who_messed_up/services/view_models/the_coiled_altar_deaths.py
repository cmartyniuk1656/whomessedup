"""View-model builder for the Heroic The Coiled Altar death report."""
from __future__ import annotations

from ..death_reports import DeathReportSummary
from ..the_coiled_altar_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "the-coiled-altar-deaths"
REPORT_TITLE = "Heroic The Coiled Altar - Death Report"
REPORT_DESCRIPTION = "Death report for Heroic The Coiled Altar."
REPORT_FOOTNOTES = [
    "Volatile Venom and Gloombomb killing blows are avoidable only for collateral players, not their assigned carriers or marked targets.",
    "Expired Gravebound and Unworthy are classified as avoidable lethal mechanic failures.",
]
REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_the_coiled_altar_deaths_report_page(summary: DeathReportSummary):
    return build_death_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_coiled_altar_deaths_report_page",
]
