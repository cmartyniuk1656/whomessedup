"""
Reusable v2 table page builder for encounter target-damage reports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..target_damage import EncounterTargetDamageSummary
from .common import (
    CellKind,
    ContentVariant,
    DamageTableColumnGroupModel,
    DamageTableFilterConfigModel,
    HeaderTagModel,
    ReportContentModel,
    ReportHeaderModel,
    ReportPageModel,
    SortDirection,
    SortModel,
    SummaryMetricModel,
    TableFilterModel,
    TableFilterOptionModel,
    TableCellModel,
    TableColumnModel,
    TableModel,
    TableRowModel,
    TextAlign,
    ValueFormat,
)
from .helpers import class_color_token, role_tone


@dataclass(frozen=True)
class TargetDamageReportConfig:
    report_id: str
    title: str
    combined_total_label: str
    combined_average_label: str
    table_total_label: str
    table_average_label: str
    show_pull_count_summary: bool = True
    show_combined_total_summary: bool = True
    show_combined_average_summary: bool = True
    show_target_total_summaries: bool = True
    show_target_average_summaries: bool = True
    footnotes: tuple[str, ...] = ()
    empty_state: str = "No events matched the filters."


def build_target_damage_report_page(
    summary: EncounterTargetDamageSummary,
    *,
    config: TargetDamageReportConfig,
) -> ReportPageModel:
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
            label=config.table_total_label,
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="average_damage",
            label=config.table_average_label,
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.DECIMAL,
            precision=3,
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
                label=f"{target.label} Avg / Pull",
                align=TextAlign.RIGHT,
                sortable=True,
                cellKind=CellKind.NUMBER,
                format=ValueFormat.DECIMAL,
                precision=3,
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

    summary_metrics: List[SummaryMetricModel] = []
    if config.show_pull_count_summary:
        summary_metrics.append(
            SummaryMetricModel(
                id="pull_count",
                label="Pulls counted",
                value=summary.pull_count,
                format=ValueFormat.INTEGER,
            )
        )
    if config.show_combined_total_summary:
        summary_metrics.append(
            SummaryMetricModel(
                id="total_damage",
                label=config.combined_total_label,
                value=summary.total_damage,
                format=ValueFormat.INTEGER,
            )
        )
    if config.show_combined_average_summary:
        summary_metrics.append(
            SummaryMetricModel(
                id="avg_damage_per_pull",
                label=config.combined_average_label,
                value=summary.avg_damage_per_pull,
                format=ValueFormat.DECIMAL,
                precision=3,
            )
        )
    for target in summary.targets:
        if config.show_target_total_summaries:
            summary_metrics.append(
                SummaryMetricModel(
                    id=f"summary_total_{target.target}",
                    label=f"{target.label} Total",
                    value=target.total_damage,
                    format=ValueFormat.INTEGER,
                )
            )
        if config.show_target_average_summaries:
            summary_metrics.append(
                SummaryMetricModel(
                    id=f"summary_average_{target.target}",
                    label=f"{target.label} Avg / Pull",
                    value=target.avg_damage_per_pull,
                    format=ValueFormat.DECIMAL,
                    precision=3,
                )
            )

    return ReportPageModel(
        reportId=config.report_id,
        title=config.title,
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
                emptyState=config.empty_state,
                damageFilterConfig=DamageTableFilterConfigModel(
                    targetFilter=TableFilterModel(
                        id="targets",
                        label="Targets",
                        options=[
                            TableFilterOptionModel(
                                id=target.target,
                                label=target.label,
                                defaultSelected=True,
                            )
                            for target in summary.targets
                        ],
                    ),
                    metricFilter=TableFilterModel(
                        id="metrics",
                        label="Display",
                        options=[
                            TableFilterOptionModel(id="totals", label="Totals", defaultSelected=True),
                            TableFilterOptionModel(id="averages", label="Averages", defaultSelected=True),
                        ],
                    ),
                    selectedTotalColumnId="total_damage",
                    selectedAverageColumnId="average_damage",
                    targetColumns=[
                        DamageTableColumnGroupModel(
                            targetId=target.target,
                            label=target.label,
                            totalColumnId=f"target_total_{target.target}",
                            averageColumnId=f"target_average_{target.target}",
                        )
                        for target in summary.targets
                    ],
                ),
            ),
        ),
        footnotes=list(config.footnotes),
    )


__all__ = [
    "TargetDamageReportConfig",
    "build_target_damage_report_page",
]
