"""Mythic mechanics subreports reuse the shared Sszorak Tempest presentation."""
from ..sszorak_tempest import SszorakTempestSummary
from .common import (
    CellKind, HeaderTagModel, ReportPageModel, SortDirection, SortModel,
    TableCellModel, TableColumnModel, TableRowModel, TableViewControlModel,
    TableViewOptionModel, ValueFormat,
)
from .sszorak_tempest import build_sszorak_tempest_report_page

REPORT_ID = "sszorak-mythic-mechanics"
REPORT_TITLE = "Mythic Sszorak - Mechanics Report"
REPORT_DESCRIPTION = "Review individual Tempest hits by player, hits per pull, and successful dispels."


def build_sszorak_mechanics_report_page(summary: SszorakTempestSummary) -> ReportPageModel:
    page = build_sszorak_tempest_report_page(summary)
    page.report_id = REPORT_ID
    page.title = REPORT_TITLE
    page.header.tags.append(HeaderTagModel(id="difficulty", label="Difficulty", value="Mythic"))
    table = page.content.table
    detail_rows = table.rows
    detail_columns = table.columns
    detail_sort = table.default_sort
    maximum = max((entry.contacts for entry in summary.entries), default=0)
    bar_rows = [
        TableRowModel(
            id=row.id,
            cells={"contacts": TableCellModel(
                value=row.cells["contacts"].value,
                label=str(row.cells["player"].value),
                unitLabel="hits",
                maxValue=maximum,
                colorToken=row.cells["player"].color_token,
            )},
            details=row.details,
        )
        for row in detail_rows
    ]
    bar_columns = [TableColumnModel(
        id="contacts", label="Tempest hits by player", sortable=True,
        cellKind=CellKind.RELATIVE_BAR, format=ValueFormat.INTEGER,
    )]
    table.view_control = TableViewControlModel(
        id="mechanic", label="Subreport", defaultValue="tempest",
        options=[TableViewOptionModel(value="tempest", label="Tempest Hits")],
    )
    table.secondary_view_control = TableViewControlModel(
        id="tempest_view", label="View", defaultValue="bars",
        options=[TableViewOptionModel(value="bars", label="Bar view"),
                 TableViewOptionModel(value="table", label="Detailed table")],
    )
    table.rows = bar_rows
    table.columns = bar_columns
    table.default_sort = SortModel(columnId="contacts", direction=SortDirection.DESC)
    table.rows_by_view = {"tempest": bar_rows}
    table.rows_by_combined_view = {"tempest::bars": bar_rows, "tempest::table": detail_rows}
    table.columns_by_view = {"bars": bar_columns, "table": detail_columns}
    table.default_sort_by_view = {"bars": table.default_sort, "table": detail_sort}
    return page
