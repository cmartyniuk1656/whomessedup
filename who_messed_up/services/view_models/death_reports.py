"""
Shared view-model builder for v2 death report pages.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..death_reports import DeathReportEvent, DeathReportSummary
from .common import (
    CellKind,
    ContentVariant,
    HeaderTagModel,
    ReportContentModel,
    ReportHeaderModel,
    ReportPageModel,
    RowDetailChildItemModel,
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
class DeathReportPageConfig:
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
    return f"{int(round(numeric)):,}"


def _format_hit_percent(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return f"{numeric:.1f}% HP"


def _detail_description(event: DeathReportEvent) -> Optional[str]:
    if event.description:
        return event.description

    parts: List[str] = []
    if event.ability_label:
        parts.append(f"via {event.ability_label}")
    damage = _format_damage_amount(event.damage_amount)
    if damage:
        parts.append(f"for {damage}")
    return " ".join(parts) if parts else None


def _hit_description(hit) -> Optional[str]:
    parts: List[str] = []
    damage = _format_damage_amount(hit.damage_amount)
    percent = _format_hit_percent(hit.hit_points_percent)
    if damage and percent:
        parts.append(f"for {damage} ({percent})")
    elif damage:
        parts.append(f"for {damage}")
    elif percent:
        parts.append(percent)
    return " ".join(parts) if parts else None


def _build_recent_hit_items(event: DeathReportEvent) -> List[RowDetailChildItemModel]:
    items: List[RowDetailChildItemModel] = []
    for index, hit in enumerate(event.recent_hits or []):
        try:
            timestamp = float(hit.timestamp)
        except (TypeError, ValueError):
            timestamp = float(event.timestamp)
        items.append(
            RowDetailChildItemModel(
                id=f"hit-{event.fight_id}-{int(timestamp)}-{index}",
                label="Killing Blow" if hit.is_killing_blow else "Hit",
                abilityLabel=hit.ability_label,
                abilityHref=hit.ability_url,
                timestampLabel=format_offset_seconds(hit.offset_ms),
                description=_hit_description(hit),
                tone="danger" if hit.is_killing_blow else None,
                tooltip=hit.ability_description,
                tooltipBadges=list(hit.ability_tags),
                badges=["Avoidable"] if hit.is_avoidable else [],
            )
        )
    return items


def _format_consumable_use_offsets(offsets_ms: Iterable[float]) -> Optional[str]:
    labels: List[str] = []
    for offset in offsets_ms:
        labels.append(format_offset_seconds(offset))
    if not labels:
        return None
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels)


def _build_consumable_status_items(event: object) -> List[RowDetailChildItemModel]:
    items: List[RowDetailChildItemModel] = []
    for index, consumable in enumerate(getattr(event, "consumables", []) or []):
        used = bool(getattr(consumable, "used", False))
        offsets = _format_consumable_use_offsets(getattr(consumable, "offsets_ms", []) or [])
        label = getattr(consumable, "label", None) or "Consumable"
        tooltip = f"Used before death at {offsets}." if used and offsets else f"No {label} use before death."
        items.append(
            RowDetailChildItemModel(
                id=f"consumable-{getattr(event, 'fight_id', 0)}-{getattr(consumable, 'consumable_id', index)}-{index}",
                label=label,
                kind="consumable",
                description="used" if used else "not used",
                tone="success" if used else "danger",
                tooltip=tooltip,
            )
        )
    return items


def build_death_detail_child_items(event: object) -> List[RowDetailChildItemModel]:
    return [
        *_build_recent_hit_items(event),
        *_build_consumable_status_items(event),
    ]


def build_death_player_indicators(events: Iterable[object]) -> List[TableCellIndicatorModel]:
    for event in events or []:
        for hit in getattr(event, "recent_hits", []) or []:
            if getattr(hit, "is_avoidable", False):
                return [
                    TableCellIndicatorModel(
                        id="avoidable_damage",
                        label="Avoidable damage reported. Click the row for details.",
                        tone="danger",
                    )
                ]
    return []


def _group_sort_key(group_key: Tuple[str, int, int], source_order: dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


def _build_row_details(
    report_code: str,
    events: List[DeathReportEvent],
    *,
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    if not events:
        return None

    source_order = {code: index for index, code in enumerate(source_reports or [report_code])}
    grouped: dict[Tuple[str, int, int], dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.pull_index, item.fight_id, item.timestamp)):
        source_report_code = event.source_report_code or report_code
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

        key = (source_report_code, fight_id, pull_index)
        bucket = grouped.setdefault(
            key,
            {
                "source_report_code": source_report_code,
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
                children=build_death_detail_child_items(event),
            )
        )

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


def _build_header_tags(summary: DeathReportSummary, extra_tags: Iterable[HeaderTagModel]) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
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


def build_death_report_page(
    summary: DeathReportSummary,
    *,
    config: DeathReportPageConfig,
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
                        indicators=build_death_player_indicators(entry.events),
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
                emptyState="No deaths matched the filters.",
            ),
        ),
        footnotes=list(config.footnotes),
    )


__all__ = [
    "DeathReportPageConfig",
    "build_death_detail_child_items",
    "build_death_player_indicators",
    "build_death_report_page",
]
