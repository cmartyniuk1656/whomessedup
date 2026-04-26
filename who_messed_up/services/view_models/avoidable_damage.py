"""
Shared view-model builder for v2 avoidable-damage reports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from ..avoidable_damage import AvoidableDamageEvent, AvoidableDamageSummary
from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
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
from .helpers import (
    build_pull_link,
    class_color_token,
    format_duration,
    format_offset_seconds,
    merged_reports_label,
    role_tone,
)


@dataclass(frozen=True)
class AvoidableDamagePageConfig:
    report_id: str
    title: str
    footnotes: Tuple[str, ...] = ()


def _format_damage_amount(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    return f"for {int(round(numeric)):,}"


def _build_event_item(event: AvoidableDamageEvent, index: int) -> RowDetailItemModel:
    return RowDetailItemModel(
        id=f"avoidable-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{index}",
        label="Damage",
        kind="ability_event",
        abilityLabel=event.ability_label,
        abilityHref=event.ability_url,
        timestampLabel=format_offset_seconds(event.offset_ms),
        description=_format_damage_amount(event.damage_amount),
        tooltip=event.ability_description,
        tooltipBadges=list(event.ability_tags),
        badges=["Avoidable"],
    )


def _group_sort_key(group_key: Tuple[str, int, int], source_order: dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


def _build_row_details(
    report_code: str,
    events: List[AvoidableDamageEvent],
    *,
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    if not events:
        return None

    source_order = {code: index for index, code in enumerate(source_reports or [report_code])}
    grouped: dict[Tuple[str, int, int], dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.source_report_code or "", item.pull_index, item.fight_id, item.timestamp)):
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
        fight_name = bucket["fight_name"] or None
        duration = format_duration(bucket["pull_duration_ms"])
        subtitle_parts: List[str] = []
        if duration:
            subtitle_parts.append(f"Duration {duration}")
        if fight_name:
            subtitle_parts.append(f"{fight_name} - Fight {fight_id}")
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


def _build_header_tags(summary: AvoidableDamageSummary, extra_tags: Iterable[HeaderTagModel]) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    if summary.abilities:
        tags.append(HeaderTagModel(id="abilities", label="Sources", value=", ".join(ability.name for ability in summary.abilities)))
    if summary.ignore_after_deaths:
        tags.append(
            HeaderTagModel(
                id="ignore_after_deaths",
                label="Filter",
                value=f"Stop after {summary.ignore_after_deaths} deaths",
            )
        )
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    tags.extend(extra_tags)
    return tags


def _build_player_indicators(entry) -> List[TableCellIndicatorModel]:
    if entry.events:
        return [
            TableCellIndicatorModel(
                id="avoidable_damage",
                label="Avoidable damage reported. Click the row for details.",
                tone="danger",
            )
        ]
    return []


def build_avoidable_damage_report_page(
    summary: AvoidableDamageSummary,
    *,
    config: AvoidableDamagePageConfig,
    extra_tags: Iterable[HeaderTagModel] = (),
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
                    "role": TableCellModel(
                        value=role,
                        sortValue=role_priority,
                        tone=role_tone(role),
                    ),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_damage": TableCellModel(value=entry.total_damage),
                    "average_damage": TableCellModel(value=entry.average_damage),
                },
                details=_build_row_details(
                    summary.report_code,
                    entry.events,
                    source_reports=summary.source_reports or [summary.report_code],
                ),
            )
        )

    return ReportPageModel(
        reportId=config.report_id,
        title=config.title,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=_build_header_tags(summary, extra_tags),
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
                label="Total avoidable damage",
                value=summary.total_damage,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="avg_damage_per_pull",
                label="Avg avoidable damage / Pull",
                value=summary.avg_damage_per_pull,
                format=ValueFormat.DECIMAL,
                precision=0,
            ),
        ],
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="average_damage", direction=SortDirection.DESC),
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
                        label="Total Avoidable Damage",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.INTEGER,
                    ),
                    TableColumnModel(
                        id="average_damage",
                        label="Avg Avoidable Damage / Pull",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.DECIMAL,
                        precision=0,
                    ),
                ],
                rows=rows,
                emptyState="No avoidable damage matched the filters.",
            ),
        ),
        footnotes=list(config.footnotes),
    )


__all__ = [
    "AvoidableDamagePageConfig",
    "build_avoidable_damage_report_page",
]
