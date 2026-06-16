"""
View-model builder for the Midnight Falls fuck-up report.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..midnight_falls_fuckups import (
    DARK_PULSAR_LABEL,
    HEAVENS_GLAIVES_LABEL,
    MidnightFallsFuckupEvent,
    MidnightFallsFuckupSummary,
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

REPORT_ID = "midnight-falls-fuckups"
REPORT_TITLE = "Midnight Falls Fuck Ups Report"
REPORT_DESCRIPTION = "Count discrete Mythic Midnight Falls player mistakes, including Heaven's Glaives and Dark Pulsar hits."
REPORT_FOOTNOTES = [
    "Heaven's Glaives counts one event when a player takes positive health damage from Heaven's Glaives.",
    "Additional Heaven's Glaives ticks on the same player inside the next 2 seconds are deduped into the original event.",
    "Dark Pulsar uses Dark Quasar combat-log events. Beam sets start from the first Dark Quasar cast marker, reset after 50 seconds, and only count players hit inside the first 2 seconds of each set.",
    "Dark Pulsar hits are ignored when that player has a Tears of L'ura damage event within 3 seconds of the beam hit.",
    "Fully absorbed, immuned, or otherwise zero-health-damage events are ignored.",
]


def build_midnight_falls_fuckup_report_page(summary: MidnightFallsFuckupSummary) -> ReportPageModel:
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
                        indicators=_build_player_indicators(entry.total_fuckups),
                    ),
                    "role": TableCellModel(value=role, sortValue=role_priority, tone=role_tone(role)),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_fuckups": TableCellModel(value=entry.total_fuckups),
                    "heavens_glaives_hits": TableCellModel(value=entry.heavens_glaives_hits),
                    "dark_pulsar_hits": TableCellModel(value=entry.dark_pulsar_hits),
                    "fuckups_per_pull": TableCellModel(
                        value=entry.fuckups_per_pull,
                        display=f"{entry.fuckups_per_pull:.2f}",
                    ),
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
                defaultSort=SortModel(columnId="total_fuckups", direction=SortDirection.DESC),
                columns=[
                    TableColumnModel(id="player", label="Player", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.PLAYER),
                    TableColumnModel(id="role", label="Role", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.BADGE),
                    TableColumnModel(id="pulls", label="Pulls", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="total_fuckups", label="Total", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="heavens_glaives_hits", label="Heaven's Glaives", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="dark_pulsar_hits", label="Dark Pulsar", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="fuckups_per_pull", label="Per Pull", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.DECIMAL, precision=2),
                ],
                rows=rows,
                emptyState="No Midnight Falls fuck-up events matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _build_player_indicators(total_fuckups: int) -> List[TableCellIndicatorModel]:
    if not total_fuckups:
        return []
    return [
        TableCellIndicatorModel(
            id="midnight_falls_fuckup",
            label="At least one counted Midnight Falls fuck-up event. Click the row for details.",
            tone="danger",
        )
    ]


def _build_summary_metrics(summary: MidnightFallsFuckupSummary) -> List[SummaryMetricModel]:
    return [
        SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="total_fuckups", label="Total fuck-ups", value=summary.total_fuckups, format=ValueFormat.INTEGER),
        SummaryMetricModel(
            id="heavens_glaives_hits",
            label="Heaven's Glaives",
            value=summary.heavens_glaives_hits,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="dark_pulsar_hits",
            label="Dark Pulsar",
            value=summary.dark_pulsar_hits,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="affected_players",
            label="Players hit",
            value=len(summary.entries),
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="fuckups_per_pull",
            label="Fuck-ups per pull",
            value=summary.fuckups_per_pull,
            display=f"{summary.fuckups_per_pull:.2f}",
            format=ValueFormat.DECIMAL,
            precision=2,
        ),
    ]


def _build_header_tags(summary: MidnightFallsFuckupSummary) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    tags.append(HeaderTagModel(id="dedupe_window", label="Dedupe", value=f"{summary.dedupe_window_ms / 1000.0:g}s"))
    if summary.ignore_after_deaths:
        tags.append(HeaderTagModel(id="ignore_after_deaths", label="Filter", value=f"Stop after {summary.ignore_after_deaths} deaths"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[MidnightFallsFuckupEvent],
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


def _build_event_item(event: MidnightFallsFuckupEvent, index: int) -> RowDetailItemModel:
    details = ["counted as 1 hit"]
    tooltip_badges = ["Avoidable"]
    if event.mechanic_type == "heavens_glaives" and event.deduped_tick_count > 1:
        details.append(f"{event.deduped_tick_count - 1} extra tick(s) deduped")
    if event.mechanic_type == "dark_pulsar":
        if event.set_index is not None:
            details.append(f"beam set {event.set_index}")
        if event.set_start_offset_ms is not None:
            details.append(f"set start {format_offset_seconds(event.set_start_offset_ms)}")
        tooltip = (
            "Dark Pulsar is counted from Dark Quasar damage only when the player is hit inside the first 2 seconds "
            "of a beam set. Hits near Tears of L'ura are ignored as intentional soak movement."
        )
        tooltip_badges.extend([DARK_PULSAR_LABEL, "2s Opening", "Tears Excluded"])
        badge = DARK_PULSAR_LABEL
    else:
        tooltip = "Heaven's Glaives damage events are clustered per player with a 2-second lockout after the first positive-damage tick."
        tooltip_badges.extend([HEAVENS_GLAIVES_LABEL, "2s Dedupe"])
        badge = HEAVENS_GLAIVES_LABEL
    return RowDetailItemModel(
        id=f"midnight-falls-fuckup-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{event.player}-{index}",
        label=event.mechanic_label,
        kind="ability_event",
        abilityLabel=event.ability_label,
        abilityHref=f"https://www.wowhead.com/spell={event.ability_id}",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description="; ".join(details),
        tooltip=tooltip,
        tooltipBadges=tooltip_badges,
        badges=[badge],
        tone="danger",
    )


def _group_sort_key(group_key: Tuple[str, int, int], source_order: Dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_midnight_falls_fuckup_report_page",
]
