"""Mythic Tempest views expose every pull for shared refresh and live-update controls."""
from ..sszorak_tempest import SszorakTempestSummary, build_sszorak_tempest_pull_summary
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
    bar_rows = _build_bar_rows(detail_rows)
    bar_columns = [TableColumnModel(
        id="contacts", label="Tempest hits by player", sortable=True,
        cellKind=CellKind.RELATIVE_BAR, format=ValueFormat.INTEGER,
    )]
    table.view_control = TableViewControlModel(
        id="pull_scope", label="Pull", defaultValue="aggregate",
        options=[TableViewOptionModel(value="aggregate", label="Aggregate"),
                 *[TableViewOptionModel(value=pull.view_id, label=pull.label) for pull in summary.pulls]],
    )
    table.secondary_view_control = TableViewControlModel(
        id="mechanic", label="Subreport", defaultValue="tempest",
        options=[TableViewOptionModel(value="tempest", label="Tempest Hits")],
    )
    table.sub_view_control_by_view = {"tempest": TableViewControlModel(
        id="tempest_view", label="View", defaultValue="bars",
        options=[TableViewOptionModel(value="bars", label="Bar view"),
                 TableViewOptionModel(value="table", label="Detailed table")],
    )}
    table.rows = bar_rows
    table.columns = bar_columns
    table.default_sort = SortModel(columnId="contacts", direction=SortDirection.DESC)
    table.rows_by_view = {"aggregate": bar_rows}
    table.rows_by_combined_view = {
        "aggregate::tempest::bars": bar_rows, "aggregate::tempest::table": detail_rows,
    }
    table.columns_by_view = {"bars": bar_columns, "table": detail_columns}
    table.default_sort_by_view = {"bars": table.default_sort, "table": detail_sort}
    page.summary_by_view = {"aggregate": page.summary}
    for pull in summary.pulls:
        scoped_page = build_sszorak_tempest_report_page(build_sszorak_tempest_pull_summary(summary, pull))
        scoped_rows = scoped_page.content.table.rows
        scoped_bars = _build_bar_rows(scoped_rows)
        table.rows_by_view[pull.view_id] = scoped_bars
        table.rows_by_combined_view[f"{pull.view_id}::tempest::bars"] = scoped_bars
        table.rows_by_combined_view[f"{pull.view_id}::tempest::table"] = scoped_rows
        page.summary_by_view[pull.view_id] = scoped_page.summary
    return page


def _build_bar_rows(detail_rows: list[TableRowModel]) -> list[TableRowModel]:
    maximum = max((row.cells["contacts"].value for row in detail_rows), default=0)
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
    return bar_rows
