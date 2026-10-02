"""Mythic mechanics subreports reuse the shared Sszorak Tempest presentation."""
from ..sszorak_tempest import SszorakTempestSummary
from .common import HeaderTagModel, ReportPageModel, TableViewControlModel, TableViewOptionModel
from .sszorak_tempest import build_sszorak_tempest_report_page

REPORT_ID = "sszorak-mythic-mechanics"
REPORT_TITLE = "Mythic Sszorak - Mechanics Report"
REPORT_DESCRIPTION = "Review individual Tempest hits by player, hits per pull, and successful dispels."


def build_sszorak_mechanics_report_page(summary: SszorakTempestSummary) -> ReportPageModel:
    page = build_sszorak_tempest_report_page(summary)
    page.report_id = REPORT_ID
    page.title = REPORT_TITLE
    page.header.tags.append(HeaderTagModel(id="difficulty", label="Difficulty", value="Mythic"))
    page.content.table.view_control = TableViewControlModel(
        id="mechanic", label="Subreport", defaultValue="tempest",
        options=[TableViewOptionModel(value="tempest", label="Tempest Hits")],
    )
    page.content.table.rows_by_view = {"tempest": page.content.table.rows}
    return page
