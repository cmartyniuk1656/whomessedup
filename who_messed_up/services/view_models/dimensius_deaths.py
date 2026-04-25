"""
View-model builder for the v2 Dimensius deaths report page.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..dimensius_deaths import (
    OBLIVION_FILTER_DEFAULT,
    OBLIVION_FILTER_EXCLUDE_ALL,
    OBLIVION_FILTER_EXCLUDE_WITHOUT_RECENT,
    OBLIVION_FILTER_INCLUDE_ALL,
    DimensiusDeathEvent,
    DimensiusDeathSummary,
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
    TableCellModel,
    TableColumnModel,
    TableModel,
    TableRowModel,
    TextAlign,
    ValueFormat,
)
from .helpers import build_pull_link, class_color_token, format_duration, format_offset_seconds, role_tone

REPORT_ID = "dimensius-deaths"
REPORT_TITLE = "Dimensius Death Counter"
REPORT_DESCRIPTION = "Count player deaths during Dimensius pulls with configurable handling for Oblivion mechanics."
REPORT_DEFAULT_FIGHT = "Dimensius, the All-Devouring"
REPORT_FOOTNOTES = [
    "Oblivion deaths can be counted as-is, ignored unless recently hit by Airborne/Fists/Devour, or removed entirely depending on this report's configuration."
]

OBLIVION_FILTER_LABELS = {
    OBLIVION_FILTER_INCLUDE_ALL: "Count all Oblivion deaths",
    OBLIVION_FILTER_EXCLUDE_WITHOUT_RECENT: "Exclude Oblivion deaths preceded by instances of Airborne, Fists of the Voidlord, or Devour",
    OBLIVION_FILTER_EXCLUDE_ALL: "Exclude all Oblivion deaths",
}


def _detail_description(event: DimensiusDeathEvent) -> Optional[str]:
    if event.description:
        return event.description
    if event.ability_label:
        return f"via {event.ability_label}"
    return None


def _group_sort_key(group_key: Tuple[int, int]) -> Tuple[int, int]:
    fight_id, pull = group_key
    return (pull, fight_id)


def _build_row_details(report_code: str, events: List[DimensiusDeathEvent]) -> Optional[RowDetailsModel]:
    if not events:
        return None

    grouped: Dict[Tuple[int, int], Dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.pull_index, item.fight_id, item.timestamp)):
        try:
            fight_id = int(event.fight_id)
        except (TypeError, ValueError):
            fight_id = 0
        try:
            pull_index = int(event.pull_index)
        except (TypeError, ValueError):
            pull_index = 0
        try:
            timestamp = float(event.timestamp)
        except (TypeError, ValueError):
            timestamp = 0.0

        key = (fight_id, pull_index)
        bucket = grouped.setdefault(
            key,
            {
                "fight_id": fight_id,
                "pull_index": pull_index,
                "fight_name": event.fight_name,
                "pull_duration_ms": event.pull_duration_ms,
                "items": [],
            },
        )
        bucket["items"].append(
            RowDetailItemModel(
                id=f"event-{fight_id}-{pull_index}-{int(timestamp)}-{len(bucket['items'])}",
                label=event.label or "Event",
                timestampLabel=f"{format_offset_seconds(event.offset_ms)} ({int(round(event.timestamp))})",
                description=_detail_description(event),
            )
        )

    groups: List[RowDetailGroupModel] = []
    for key in sorted(grouped.keys(), key=_group_sort_key):
        bucket = grouped[key]
        fight_id = int(bucket["fight_id"])
        pull_index = int(bucket["pull_index"])
        fight_name = bucket["fight_name"] or None
        duration = format_duration(bucket["pull_duration_ms"])
        subtitle_parts: List[str] = []
        if duration:
            subtitle_parts.append(f"Duration {duration}")
        if fight_name:
            subtitle_parts.append(f"{fight_name} - Fight {fight_id}")
        elif fight_id:
            subtitle_parts.append(f"Fight {fight_id}")
        groups.append(
            RowDetailGroupModel(
                id=f"fight-{fight_id}-pull-{pull_index}",
                title=f"Pull {pull_index}",
                subtitle=" - ".join(subtitle_parts) if subtitle_parts else None,
                link=build_pull_link(report_code, fight_id),
                items=bucket["items"],
            )
        )

    return RowDetailsModel(variant=RowDetailsVariant.EVENT_GROUPS, groups=groups)


def build_dimensius_deaths_report_page(summary: DimensiusDeathSummary) -> ReportPageModel:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))

    oblivion_value = OBLIVION_FILTER_LABELS.get(summary.oblivion_filter or OBLIVION_FILTER_DEFAULT)
    if oblivion_value:
        tags.append(HeaderTagModel(id="oblivion_filter", label="Oblivion", value=oblivion_value))

    if summary.ignore_after_deaths:
        tags.append(
            HeaderTagModel(
                id="ignore_after_deaths",
                label="Filter",
                value=f"Stop after {summary.ignore_after_deaths} deaths",
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
                    "deaths": TableCellModel(value=entry.deaths),
                    "death_rate": TableCellModel(value=entry.death_rate),
                },
                details=_build_row_details(summary.report_code, entry.events),
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
                id="total_deaths",
                label="Total deaths",
                value=summary.total_deaths,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="avg_deaths_per_pull",
                label="Avg deaths / Pull",
                value=(summary.total_deaths / summary.pull_count) if summary.pull_count else 0,
                format=ValueFormat.DECIMAL,
                precision=3,
            ),
        ],
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="death_rate", direction=SortDirection.DESC),
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
                        id="deaths",
                        label="Deaths",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.INTEGER,
                    ),
                    TableColumnModel(
                        id="death_rate",
                        label="Death Rate",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.DECIMAL,
                        precision=3,
                    ),
                ],
                rows=rows,
                emptyState="No events matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


__all__ = [
    "OBLIVION_FILTER_LABELS",
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_dimensius_deaths_report_page",
]
