"""
View-model builder for the v2 Dimensius add-damage report page.
"""
from __future__ import annotations

from typing import List, Optional

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..dimensius import AddDamageSummary
from .common import (
    CellKind,
    ContentVariant,
    HeaderTagModel,
    ReportContentModel,
    ReportHeaderModel,
    ReportPageModel,
    SortDirection,
    SortModel,
    SummaryMetricModel,
    TableCellModel,
    TableColumnModel,
    TableModel,
    TableRowModel,
    TextAlign,
    ValueFormat,
)
from .helpers import class_color_token, merged_reports_label, role_tone

REPORT_ID = "dimensius-add-damage"
REPORT_TITLE = "Dimensius - Phase 1 Add Damage"
REPORT_DESCRIPTION = (
    "Average player damage into Living Mass adds during Stage One: Critical Mass for Dimensius, "
    "the All-Devouring."
)
REPORT_DEFAULT_FIGHT = "Dimensius, the All-Devouring"
REPORT_FOOTNOTES = ["Optional ignore first 6 adds that spawn instantly on pull."]


def build_dimensius_add_damage_report_page(summary: AddDamageSummary) -> ReportPageModel:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))

    merged_label = merged_reports_label(summary.source_reports)
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))

    if summary.ignore_first_add_set:
        tags.append(
            HeaderTagModel(
                id="ignore_first_add_set",
                label="Filter",
                value="Ignoring first Living Mass set",
            )
        )

    rows: List[TableRowModel] = []
    for entry in summary.entries:
        role = entry.role or ROLE_UNKNOWN
        role_priority = ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN])
        rows.append(
            TableRowModel(
                id=entry.player,
                cells={
                    "player": TableCellModel(
                        value=entry.player,
                        colorToken=class_color_token(entry.class_name),
                    ),
                    "role": TableCellModel(
                        value=role,
                        sortValue=role_priority,
                        tone=role_tone(role),
                    ),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_damage": TableCellModel(value=entry.total_damage),
                    "average_damage": TableCellModel(value=entry.average_damage),
                },
                details=None,
            )
        )

    return ReportPageModel(
        reportId=REPORT_ID,
        title=REPORT_TITLE,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=tags,
        ),
        summary=[
            SummaryMetricModel(
                id="pull_count",
                label="Pulls counted",
                value=summary.pull_count,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="total_damage",
                label="Combined add damage",
                value=summary.total_damage,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="avg_damage_per_pull",
                label="Avg add damage / Pull",
                value=summary.avg_damage_per_pull,
                format=ValueFormat.DECIMAL,
                precision=0,
            ),
        ],
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="role", direction=SortDirection.ASC),
                columns=[
                    TableColumnModel(
                        id="player",
                        label="Player",
                        align=TextAlign.LEFT,
                        sortable=True,
                        cellKind=CellKind.PLAYER,
                    ),
                    TableColumnModel(
                        id="role",
                        label="Role",
                        align=TextAlign.LEFT,
                        sortable=True,
                        cellKind=CellKind.BADGE,
                    ),
                    TableColumnModel(
                        id="pulls",
                        label="Pulls",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.INTEGER,
                    ),
                    TableColumnModel(
                        id="total_damage",
                        label="Total Add Damage",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.INTEGER,
                    ),
                    TableColumnModel(
                        id="average_damage",
                        label="Avg Add Damage / Pull",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.DECIMAL,
                        precision=0,
                    ),
                ],
                rows=rows,
                emptyState="No events matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_dimensius_add_damage_report_page",
]
