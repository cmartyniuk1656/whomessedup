"""
Reusable v2 table page builder for encounter target-damage reports.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..target_damage import EncounterTargetBucket, EncounterTargetDamageSummary
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
    SpecAnalysisMetricModel,
    SpecAnalysisModel,
    SpecAnalysisSeriesModel,
    SpecAnalysisSortOptionModel,
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


SPEC_ANALYSIS_METRICS: Tuple[Tuple[str, str, EncounterTargetBucket], ...] = (
    ("boss", "Boss Damage", EncounterTargetBucket.BOSS),
    ("priority", "Priority Damage", EncounterTargetBucket.PRIORITY_ADD),
    ("pad", "Pad Damage", EncounterTargetBucket.PAD_ADD),
)


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
    enable_spec_analysis: bool = False
    spec_analysis_button_label: str = "Spec Analysis"
    spec_analysis_title: str = "Spec Analysis"
    spec_analysis_subtitle: str = "Compare specialization output across boss, priority, and pad targets."
    spec_analysis_basis_label: str = "Average damage per player per counted pull"
    spec_analysis_default_sort: str = "overall"
    spec_analysis_sort_labels: Dict[str, str] = field(
        default_factory=lambda: {
            "overall": "Overall",
            "boss_priority": "Boss + Priority Damage",
            "boss": "Boss Damage",
            "priority": "Priority Damage",
            "pad": "Pad Damage",
        }
    )


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
    if summary.kill_only:
        tags.append(HeaderTagModel(id="pull_scope", label="Pulls", value="Kills only"))
    if summary.omit_dead_players:
        tags.append(HeaderTagModel(id="dead_player_filter", label="Deaths", value="Dead-player pulls omitted"))

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
                label=f"{target.label} Avg / Pull",
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
                precision=0,
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
                    precision=0,
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
        specAnalysis=build_target_damage_spec_analysis(summary, config=config),
    )


def build_target_damage_spec_analysis(
    summary: EncounterTargetDamageSummary,
    *,
    config: TargetDamageReportConfig,
) -> Optional[SpecAnalysisModel]:
    if not config.enable_spec_analysis:
        return None

    target_bucket_map = {
        target.target: target.bucket
        for target in summary.targets
        if target.bucket in {EncounterTargetBucket.BOSS, EncounterTargetBucket.PRIORITY_ADD, EncounterTargetBucket.PAD_ADD}
    }
    if not target_bucket_map:
        return None

    grouped_totals: Dict[Tuple[Optional[str], str], DefaultDict[str, float]] = {}
    grouped_players: Dict[Tuple[Optional[str], str], set[str]] = {}
    grouped_pulls: DefaultDict[Tuple[Optional[str], str], int] = defaultdict(int)

    for entry in summary.entries:
        class_name = summary.player_classes.get(entry.player) or entry.class_name
        spec_name = summary.player_specs.get(entry.player) or "Unknown"
        key = (class_name, spec_name)
        if key not in grouped_totals:
            grouped_totals[key] = defaultdict(float)
            grouped_players[key] = set()
        grouped_players[key].add(entry.player)
        grouped_pulls[key] += max(int(entry.pulls or 0), 0)

        for target_slug, breakdown in entry.target_totals.items():
            bucket = target_bucket_map.get(target_slug)
            if bucket is None:
                continue
            grouped_totals[key][bucket.value] += float(breakdown.total_damage or 0.0)

    if not grouped_totals:
        return None

    series: List[SpecAnalysisSeriesModel] = []
    for class_name, spec_name in sorted(
        grouped_totals.keys(),
        key=lambda item: (
            (item[0] or "").lower(),
            item[1].lower(),
        ),
    ):
        key = (class_name, spec_name)
        pull_count = grouped_pulls.get(key, 0)
        values = {}
        for metric_id, _label, bucket in SPEC_ANALYSIS_METRICS:
            total_value = grouped_totals[key].get(bucket.value, 0.0)
            values[metric_id] = total_value / pull_count if pull_count else 0.0
        class_slug = (class_name or "unknown").replace(" ", "-").lower()
        spec_slug = spec_name.replace(" ", "-").lower()
        series.append(
            SpecAnalysisSeriesModel(
                id=f"{class_slug}-{spec_slug}",
                className=class_name,
                specName=spec_name,
                colorToken=class_color_token(class_name),
                playerCount=len(grouped_players.get(key, set())),
                values=values,
            )
        )

    default_sort = config.spec_analysis_default_sort
    sort_options = [
        SpecAnalysisSortOptionModel(id=option_id, label=label)
        for option_id, label in config.spec_analysis_sort_labels.items()
    ]
    if not any(option.id == default_sort for option in sort_options):
        sort_options.insert(0, SpecAnalysisSortOptionModel(id="overall", label="Overall"))
        default_sort = "overall"

    return SpecAnalysisModel(
        buttonLabel=config.spec_analysis_button_label,
        title=config.spec_analysis_title,
        subtitle=config.spec_analysis_subtitle,
        basisLabel=config.spec_analysis_basis_label,
        defaultSort=default_sort,
        sortOptions=sort_options,
        metrics=[
            SpecAnalysisMetricModel(id=metric_id, label=label)
            for metric_id, label, _bucket in SPEC_ANALYSIS_METRICS
        ],
        series=series,
    )


__all__ = [
    "TargetDamageReportConfig",
    "build_target_damage_spec_analysis",
    "build_target_damage_report_page",
]
