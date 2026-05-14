"""
View-model builder for the Crown of the Cosmos Null Corona dispel report.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..crown_of_the_cosmos_null_corona_dispels import (
    CrownNullCoronaDispelEvent,
    CrownNullCoronaDispelSummary,
    REPORT_DEFAULT_FIGHT,
)
from .common import (
    CellKind,
    ContentVariant,
    HeaderTagModel,
    ReportContentModel,
    ReportHeaderModel,
    ReportPageModel,
    RowDetailGroupModel,
    RowDetailItemModel,
    RowDetailsModel,
    RowDetailsVariant,
    SortDirection,
    SortModel,
    SummaryMetricModel,
    TableCellIndicatorModel,
    TableCellModel,
    TableColumnModel,
    TableModel,
    TableRowModel,
    TextAlign,
    ValueFormat,
)
from .helpers import build_pull_link, class_color_token, format_duration, format_offset_seconds, merged_reports_label, role_tone

REPORT_ID = "crown-of-the-cosmos-null-corona-dispels"
REPORT_TITLE = "Null Corona Dispel Report"
REPORT_DESCRIPTION = (
    "Track Null Corona dispels and identify Great Dispels made inside the configured HP window or with a valid exception."
)
REPORT_FOOTNOTES = [
    "Great Dispels are Null Corona dispels where the target was inside the configured HP window, above the floor with another debuff removed or Grasp/Bursting damage nearby, or received a jumped Null Corona while already below the floor.",
    "Target HP is estimated from the most recent Warcraft Logs health snapshot at or before the dispel, using resource and damage-taken events.",
    "Null Corona appears in logs as two debuff IDs: the initial Alleria application and the jumped Environment application.",
]


def build_crown_of_the_cosmos_null_corona_dispel_report_page(
    summary: CrownNullCoronaDispelSummary,
) -> ReportPageModel:
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
                        indicators=_build_player_indicators(entry),
                    ),
                    "role": TableCellModel(value=role, sortValue=role_priority, tone=role_tone(role)),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_dispels": TableCellModel(value=entry.total_dispels),
                    "great_dispels": TableCellModel(value=entry.great_dispels),
                    "needs_review_dispels": TableCellModel(value=entry.needs_review_dispels),
                    "great_rate": TableCellModel(value=entry.great_rate, display=_format_percent(entry.great_rate)),
                    "companion_dispels": TableCellModel(value=entry.companion_dispels),
                },
                details=_build_row_details(
                    summary.report_code,
                    entry.events,
                    source_reports=summary.source_reports or [summary.report_code],
                ),
            )
        )

    return ReportPageModel(
        reportId=REPORT_ID,
        title=REPORT_TITLE,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=_build_header_tags(summary),
        ),
        summary=_build_summary_metrics(summary),
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="needs_review_dispels", direction=SortDirection.DESC),
                columns=[
                    TableColumnModel(id="player", label="Player", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.PLAYER),
                    TableColumnModel(id="role", label="Role", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.BADGE),
                    TableColumnModel(id="pulls", label="Pulls", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="total_dispels", label="Total Dispels", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="great_dispels", label="Great Dispels", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="needs_review_dispels", label="Needs Review", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="great_rate", label="Great Rate", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.DECIMAL, precision=1),
                    TableColumnModel(id="companion_dispels", label="Other Debuff", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                ],
                rows=rows,
                emptyState="No Null Corona dispels matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _build_player_indicators(entry) -> List[TableCellIndicatorModel]:
    if entry.needs_review_dispels:
        return [
            TableCellIndicatorModel(
                id="null_corona_review",
                label="At least one Null Corona dispel did not meet the Great Dispel criteria.",
                tone="danger",
            )
        ]
    if entry.great_dispels:
        return [
            TableCellIndicatorModel(
                id="null_corona_great",
                label="All tracked Null Corona dispels met Great Dispel criteria.",
                tone="success",
            )
        ]
    return []


def _build_summary_metrics(summary: CrownNullCoronaDispelSummary) -> List[SummaryMetricModel]:
    return [
        SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="total_dispels", label="Total dispels", value=summary.total_dispels, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="great_dispels", label="Great dispels", value=summary.great_dispels, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="needs_review_dispels", label="Needs review", value=summary.needs_review_dispels, format=ValueFormat.INTEGER),
        SummaryMetricModel(
            id="great_rate",
            label="Great rate",
            value=summary.great_rate,
            display=_format_percent(summary.great_rate),
            format=ValueFormat.DECIMAL,
            precision=1,
        ),
        SummaryMetricModel(
            id="hp_window",
            label="HP window",
            value=summary.hp_ceiling_percent,
            display=f"{summary.hp_floor_percent:g}-{summary.hp_ceiling_percent:g}%",
            format=ValueFormat.DECIMAL,
            precision=1,
        ),
        SummaryMetricModel(
            id="low_jump_dispels",
            label="Low jump dispels",
            value=summary.low_jump_dispels,
            format=ValueFormat.INTEGER,
        ),
    ]


def _build_header_tags(summary: CrownNullCoronaDispelSummary) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    tags.append(HeaderTagModel(id="hp_window", label="HP Window", value=f"{summary.hp_floor_percent:g}-{summary.hp_ceiling_percent:g}%"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[CrownNullCoronaDispelEvent],
    *,
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    if not events:
        return None
    source_order = {code: index for index, code in enumerate(source_reports or [report_code])}
    grouped: Dict[Tuple[str, int, int], Dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.source_report_code or "", item.pull_index, item.timestamp)):
        source_report_code = event.source_report_code or report_code
        key = (source_report_code, int(event.fight_id), int(event.pull_index))
        bucket = grouped.setdefault(
            key,
            {
                "source_report_code": source_report_code,
                "fight_id": int(event.fight_id),
                "pull_index": int(event.pull_index),
                "fight_name": event.fight_name,
                "pull_duration_ms": event.pull_duration_ms,
                "items": [],
            },
        )
        bucket["items"].append(_build_event_item(event, len(bucket["items"])))

    groups: List[RowDetailGroupModel] = []
    for key in sorted(grouped.keys(), key=lambda item: _group_sort_key(item, source_order)):
        bucket = grouped[key]
        source_report_code = str(bucket["source_report_code"])
        fight_id = int(bucket["fight_id"])
        pull_index = int(bucket["pull_index"])
        duration = format_duration(bucket["pull_duration_ms"])
        subtitle_parts: List[str] = []
        if duration:
            subtitle_parts.append(f"Duration {duration}")
        if bucket["fight_name"]:
            subtitle_parts.append(f"{bucket['fight_name']} - Fight {fight_id}")
        elif fight_id:
            subtitle_parts.append(f"Fight {fight_id}")
        if source_report_code != report_code:
            subtitle_parts.append(f"Report {source_report_code}")
        groups.append(
            RowDetailGroupModel(
                id=f"{source_report_code}-fight-{fight_id}-pull-{pull_index}",
                title=f"Pull {pull_index}",
                subtitle=" - ".join(subtitle_parts) if subtitle_parts else None,
                link=build_pull_link(source_report_code, fight_id),
                items=bucket["items"],
            )
        )
    return RowDetailsModel(variant=RowDetailsVariant.EVENT_GROUPS, groups=groups)


def _build_event_item(event: CrownNullCoronaDispelEvent, index: int) -> RowDetailItemModel:
    status = "Great Dispel" if event.is_great else "Needs Review"
    tone = "success" if event.is_great else "danger"
    details = [
        f"target {event.target}",
        f"HP {_format_hp(event)}",
        f"via {event.dispel_ability_label or 'unknown dispel'}",
        f"debuff #{event.debuff_id}",
    ]
    if event.reason_labels:
        details.append("reason: " + "; ".join(event.reason_labels))
    if event.jump_application_hp_percent is not None:
        details.append(f"HP when debuff applied {event.jump_application_hp_percent:.1f}%")
    if event.health_snapshot_age_ms is not None:
        details.append(f"HP sample age {event.health_snapshot_age_ms / 1000.0:.1f}s")
    return RowDetailItemModel(
        id=f"null-corona-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{event.target}-{index}",
        label=status,
        kind="ability_event",
        abilityLabel=event.debuff_label,
        abilityHref=f"https://www.wowhead.com/spell={event.debuff_id}/null-corona",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description="; ".join(details),
        tooltip=(
            "Great Dispels require the target to be inside the HP window, or above the floor with another debuff removed "
            "by the same dispel or Grasp/Bursting damage near the dispel timestamp. Jumped Null Corona is also great below "
            "the floor when it landed on a target that was already that low."
        ),
        tooltipBadges=["Null Corona", "Dispel"] + (["Great"] if event.is_great else ["Review"]),
        badges=[status],
        tone=tone,
    )


def _group_sort_key(group_key: Tuple[str, int, int], source_order: Dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


def _format_percent(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def _format_hp(event: CrownNullCoronaDispelEvent) -> str:
    if event.target_hp_percent is None:
        return "unknown"
    return f"{event.target_hp_percent:.1f}%"


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_crown_of_the_cosmos_null_corona_dispel_report_page",
]
