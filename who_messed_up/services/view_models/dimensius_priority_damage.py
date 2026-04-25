"""
View-model builder for the v2 Dimensius priority-damage report page.
"""
from __future__ import annotations

from typing import List

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..dimensius_priority_damage import (
    AVERAGING_MODE_DAMAGE_PULLS,
    DimensiusPriorityDamageSummary,
)
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
from .helpers import class_color_token, role_tone

REPORT_ID = "dimensius-priority-damage"
REPORT_TITLE = "Dimensius - Phase 2 Priority Damage"
REPORT_DESCRIPTION = (
    "Track player damage into Dimensius phase-two priority targets (Artoshion, Pargoth, Nullbinder, "
    "Voidwarden). Only players alive when Phase 2 begins are counted."
)
REPORT_DEFAULT_FIGHT = "Dimensius, the All-Devouring"
REPORT_FOOTNOTES = [
    "Includes only pulls that reached Phase 2 and players who were alive at the start of that phase.",
    "Damage credited to Shooting Star is ignored.",
    "Pargoth averages only include pulls where the player dealt damage to Pargoth.",
]


def _target_average_label(target) -> str:
    if target.averaging_mode == AVERAGING_MODE_DAMAGE_PULLS:
        return f"{target.label} Avg / Pull (damage pulls)"
    return f"{target.label} Avg / Pull"


def build_dimensius_priority_damage_report_page(summary: DimensiusPriorityDamageSummary) -> ReportPageModel:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    if summary.targets:
        tags.append(
            HeaderTagModel(
                id="targets",
                label="Targets",
                value=", ".join(target.label for target in summary.targets),
            )
        )
    if summary.ignored_source:
        tags.append(HeaderTagModel(id="ignored_source", label="Ignored source", value=summary.ignored_source))

    columns: List[TableColumnModel] = [
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
            label="Total Priority Damage",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="average_damage",
            label="Avg Priority Damage / Pull",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.DECIMAL,
            precision=0,
        ),
    ]

    for target in summary.targets:
        columns.append(
            TableColumnModel(
                id=f"target_total_{target.target}",
                label=f"{target.label} Total",
                align=TextAlign.RIGHT,
                sortable=True,
                cellKind=CellKind.NUMBER,
                format=ValueFormat.INTEGER,
            )
        )
        columns.append(
            TableColumnModel(
                id=f"target_average_{target.target}",
                label=_target_average_label(target),
                align=TextAlign.RIGHT,
                sortable=True,
                cellKind=CellKind.NUMBER,
                format=ValueFormat.DECIMAL,
                precision=0,
            )
        )

    rows: List[TableRowModel] = []
    for entry in summary.entries:
        role = entry.role or ROLE_UNKNOWN
        role_priority = ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN])
        cells = {
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
        }
        for target in summary.targets:
            breakdown = entry.target_totals.get(target.target)
            cells[f"target_total_{target.target}"] = TableCellModel(value=breakdown.total_damage if breakdown else 0)
            cells[f"target_average_{target.target}"] = TableCellModel(
                value=breakdown.average_damage if breakdown else 0
            )
        rows.append(TableRowModel(id=entry.player, cells=cells, details=None))

    summary_metrics = [
        SummaryMetricModel(
            id="pull_count",
            label="Pulls counted",
            value=summary.pull_count,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="total_damage",
            label="Total priority damage",
            value=summary.total_damage,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="avg_damage_per_pull",
            label="Avg priority damage / Pull",
            value=summary.avg_damage_per_pull,
            format=ValueFormat.DECIMAL,
            precision=0,
        ),
    ]
    for target in summary.targets:
        summary_metrics.append(
            SummaryMetricModel(
                id=f"summary_total_{target.target}",
                label=f"{target.label} Total",
                value=target.total_damage,
                format=ValueFormat.INTEGER,
            )
        )
        summary_metrics.append(
            SummaryMetricModel(
                id=f"summary_average_{target.target}",
                label=_target_average_label(target),
                value=target.avg_damage_per_pull,
                format=ValueFormat.DECIMAL,
                precision=0,
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
        summary=summary_metrics,
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="average_damage", direction=SortDirection.DESC),
                columns=columns,
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
    "build_dimensius_priority_damage_report_page",
]
