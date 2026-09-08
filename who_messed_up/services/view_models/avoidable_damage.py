"""
Shared view-model builder for v2 avoidable-damage reports.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, List, Optional, Tuple

from ..avoidable_damage import AvoidableDamageEntry, AvoidableDamageEvent, AvoidableDamageSummary
from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..report_pulls import ReportPull, event_belongs_to_pull
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
    TableViewControlModel,
    TableViewOptionModel,
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
from .report_pulls import AGGREGATE_VIEW_ID, build_pull_view_control


DAMAGE_BARS_VIEW_ID = "damage_bars"
TABLE_VIEW_ID = "table"


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
    rows = _build_rows(summary.entries, summary=summary)
    bar_rows = _build_bar_rows(summary.entries, summary=summary)
    rows_by_view = {AGGREGATE_VIEW_ID: rows}
    rows_by_combined_view = {
        _combined_view_id(AGGREGATE_VIEW_ID, DAMAGE_BARS_VIEW_ID): bar_rows,
        _combined_view_id(AGGREGATE_VIEW_ID, TABLE_VIEW_ID): rows,
    }
    summary_by_view = {
        AGGREGATE_VIEW_ID: _build_summary_metrics(summary.entries, pull_count=summary.pull_count)
    }
    for pull in summary.pulls:
        pull_entries = _entries_for_pull(summary, pull)
        pull_rows = _build_rows(pull_entries, summary=summary)
        rows_by_view[pull.view_id] = pull_rows
        rows_by_combined_view[
            _combined_view_id(pull.view_id, DAMAGE_BARS_VIEW_ID)
        ] = _build_bar_rows(pull_entries, summary=summary)
        rows_by_combined_view[
            _combined_view_id(pull.view_id, TABLE_VIEW_ID)
        ] = pull_rows
        summary_by_view[pull.view_id] = _build_summary_metrics(pull_entries, pull_count=1)

    return ReportPageModel(
        reportId=config.report_id,
        title=config.title,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=_build_header_tags(summary, extra_tags),
        ),
        summary=summary_by_view[AGGREGATE_VIEW_ID],
        summaryByView=summary_by_view,
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="damage", direction=SortDirection.DESC),
                defaultSortByView={
                    DAMAGE_BARS_VIEW_ID: SortModel(
                        columnId="damage", direction=SortDirection.DESC
                    ),
                    TABLE_VIEW_ID: SortModel(
                        columnId="average_damage", direction=SortDirection.DESC
                    ),
                },
                columns=_build_bar_columns(),
                columnsByView={
                    DAMAGE_BARS_VIEW_ID: _build_bar_columns(),
                    TABLE_VIEW_ID: _build_columns(),
                },
                rows=bar_rows,
                rowsByView=rows_by_view,
                rowsByCombinedView=rows_by_combined_view,
                viewControl=build_pull_view_control(summary.pulls, control_id="avoidable_damage_pull_view"),
                secondaryViewControl=TableViewControlModel(
                    id="avoidable_damage_display_view",
                    label="View",
                    defaultValue=DAMAGE_BARS_VIEW_ID,
                    options=[
                        TableViewOptionModel(
                            value=DAMAGE_BARS_VIEW_ID, label="Damage bars"
                        ),
                        TableViewOptionModel(value=TABLE_VIEW_ID, label="Table"),
                    ],
                ),
                emptyState="No avoidable damage matched the filters.",
            ),
        ),
        footnotes=list(config.footnotes),
    )


def _build_bar_rows(
    entries: Iterable[AvoidableDamageEntry],
    *,
    summary: AvoidableDamageSummary,
) -> List[TableRowModel]:
    selected_entries = list(entries)
    maximum_damage = max(
        (float(entry.total_damage) for entry in selected_entries),
        default=0.0,
    )
    rows: List[TableRowModel] = []
    for entry in selected_entries:
        grouped_events = _group_avoidable_events(entry.events, summary=summary)
        rows.append(
            TableRowModel(
                id=entry.player,
                cells={
                    "damage": TableCellModel(
                        value=entry.total_damage,
                        label=entry.player,
                        display=f"{entry.total_damage:,.0f}",
                        maxValue=maximum_damage,
                        colorToken=class_color_token(entry.class_name),
                    ),
                    "hit_count": TableCellModel(value=len(grouped_events)),
                },
                details=_build_row_details(
                    summary.report_code,
                    grouped_events,
                    source_reports=summary.source_reports or [summary.report_code],
                ),
            )
        )

    return rows


def _group_avoidable_events(
    events: Iterable[AvoidableDamageEvent],
    *,
    summary: AvoidableDamageSummary,
) -> List[AvoidableDamageEvent]:
    """Collapse configured periodic-damage runs into display/count instances."""
    abilities_by_id = {
        int(ability.game_id): ability
        for ability in summary.abilities
        if ability.game_id is not None
    }
    abilities_by_name = {
        " ".join(ability.name.strip().lower().split()): ability
        for ability in summary.abilities
        if ability.name.strip()
    }
    active_groups: dict[Tuple[str, int, str, str], Tuple[float, int]] = {}
    grouped_events: List[AvoidableDamageEvent] = []

    for event in sorted(
        events,
        key=lambda item: (
            item.source_report_code or summary.report_code,
            item.fight_id,
            item.timestamp,
        ),
    ):
        ability = abilities_by_id.get(int(event.ability_id)) if event.ability_id is not None else None
        if ability is None and event.ability_label:
            normalized_name = " ".join(event.ability_label.strip().lower().split())
            ability = abilities_by_name.get(normalized_name)
        group_window_ms = float(
            getattr(ability, "avoidable_hit_group_window_ms", 0.0) or 0.0
        )
        if group_window_ms <= 0:
            grouped_events.append(event)
            continue

        ability_key = str(event.ability_id) if event.ability_id is not None else str(event.ability_label or "")
        group_key = (
            event.source_report_code or summary.report_code,
            int(event.fight_id),
            event.player,
            ability_key,
        )
        active_group = active_groups.get(group_key)
        if active_group is None or float(event.timestamp) - active_group[0] > group_window_ms:
            grouped_events.append(event)
            active_groups[group_key] = (float(event.timestamp), len(grouped_events) - 1)
            continue

        _, grouped_index = active_group
        existing = grouped_events[grouped_index]
        grouped_events[grouped_index] = replace(
            existing,
            damage_amount=float(existing.damage_amount) + float(event.damage_amount),
        )
        active_groups[group_key] = (float(event.timestamp), grouped_index)

    return grouped_events


def _build_rows(
    entries: Iterable[AvoidableDamageEntry],
    *,
    summary: AvoidableDamageSummary,
) -> List[TableRowModel]:
    rows: List[TableRowModel] = []
    for entry in entries:
        role = entry.role or ROLE_UNKNOWN
        role_priority = ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN])
        grouped_events = _group_avoidable_events(entry.events, summary=summary)
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
                    grouped_events,
                    source_reports=summary.source_reports or [summary.report_code],
                ),
            )
        )

    return rows


def _build_summary_metrics(
    entries: Iterable[AvoidableDamageEntry],
    *,
    pull_count: int,
) -> List[SummaryMetricModel]:
    total_damage = sum(float(entry.total_damage) for entry in entries)
    return [
        SummaryMetricModel(
            id="pull_count",
            label="Pulls counted",
            value=pull_count,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="total_damage",
            label="Total avoidable damage",
            value=total_damage,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="avg_damage_per_pull",
            label="Avg avoidable damage / Pull",
            value=total_damage / pull_count if pull_count else 0.0,
            format=ValueFormat.DECIMAL,
            precision=0,
        ),
    ]


def _build_columns() -> List[TableColumnModel]:
    return [
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
    ]


def _build_bar_columns() -> List[TableColumnModel]:
    return [
        TableColumnModel(
            id="damage",
            label="Avoidable Damage",
            align=TextAlign.LEFT,
            sortable=True,
            cellKind=CellKind.RELATIVE_BAR,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="hit_count",
            label="Hits",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
    ]


def _combined_view_id(pull_view_id: str, display_view_id: str) -> str:
    return f"{pull_view_id}::{display_view_id}"


def _entries_for_pull(summary: AvoidableDamageSummary, pull: ReportPull) -> List[AvoidableDamageEntry]:
    participants = set(pull.participants)
    scoped_entries: List[AvoidableDamageEntry] = []
    for entry in summary.entries:
        events = [
            event
            for event in entry.events
            if event_belongs_to_pull(event, pull, summary.report_code)
        ]
        if entry.player not in participants and not events:
            continue
        total_damage = sum(float(event.damage_amount) for event in events)
        scoped_entries.append(
            AvoidableDamageEntry(
                player=entry.player,
                role=pull.player_roles.get(entry.player) or entry.role,
                class_name=entry.class_name,
                pulls=1,
                total_damage=total_damage,
                average_damage=total_damage,
                events=events,
            )
        )
    return scoped_entries


__all__ = [
    "AvoidableDamagePageConfig",
    "build_avoidable_damage_report_page",
]
