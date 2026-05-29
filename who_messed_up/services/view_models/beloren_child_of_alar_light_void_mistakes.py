"""
View-model builder for the Belo'ren Light/Void wrong-Feather report.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..beloren_child_of_alar_light_void_mistakes import (
    BelorenLightVoidMistakeEvent,
    BelorenLightVoidMistakeSummary,
    MECHANIC_ERUPTION,
    MECHANIC_FLAMES,
    MECHANIC_QUILL,
    MECHANIC_RUPTURE,
    REPORT_DEFAULT_FIGHT,
)
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
from .helpers import build_pull_link, class_color_token, format_duration, format_offset_seconds, merged_reports_label, role_tone

REPORT_ID = "beloren-child-of-alar-light-void-fuckups"
REPORT_TITLE = "Light/Void Fuck Ups Report"
REPORT_DESCRIPTION = (
    "Count Belo'ren wrong-Feather mistakes: Flames pulses, Quill soaks, Voidlight Rupture wrong-orb soaks, and wrong-color Eruption kicks."
)
REPORT_FOOTNOTES = [
    "Flames mistakes count players who receive the Light/Void Flames penalty debuff or stack while carrying the opposite Feather; matching-color pulse damage is ignored.",
    "Quill mistakes only count non-target players hit while carrying the wrong Feather; correct-color Quill hits are ignored.",
    "Voidlight Rupture mistakes count each debuff application or stack once; damage shown is aggregated across the burst and following DoT ticks.",
    "Eruption kick mistakes count successful wrong-Feather interrupts when logged, plus failed wrong-color kick casts that trigger Eruption raid damage.",
    "Events are counted only when the player's active Feather can be resolved from the combat log at the event timestamp.",
]


def build_beloren_child_of_alar_light_void_mistake_report_page(
    summary: BelorenLightVoidMistakeSummary,
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
                        indicators=_build_player_indicators(entry.total_mistakes),
                    ),
                    "role": TableCellModel(value=role, sortValue=role_priority, tone=role_tone(role)),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_mistakes": TableCellModel(value=entry.total_mistakes),
                    "flame_mistakes": TableCellModel(value=entry.flame_mistakes),
                    "quill_mistakes": TableCellModel(value=entry.quill_mistakes),
                    "rupture_mistakes": TableCellModel(value=entry.rupture_mistakes),
                    "eruption_mistakes": TableCellModel(value=entry.eruption_mistakes),
                    "mistakes_per_pull": TableCellModel(
                        value=entry.mistakes_per_pull,
                        display=f"{entry.mistakes_per_pull:.2f}",
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
                defaultSort=SortModel(columnId="total_mistakes", direction=SortDirection.DESC),
                columns=[
                    TableColumnModel(id="player", label="Player", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.PLAYER),
                    TableColumnModel(id="role", label="Role", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.BADGE),
                    TableColumnModel(id="pulls", label="Pulls", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="total_mistakes", label="Total", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="flame_mistakes", label="Flames", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="quill_mistakes", label="Quill", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="rupture_mistakes", label="Rupture", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="eruption_mistakes", label="Eruption", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="mistakes_per_pull", label="Per Pull", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.DECIMAL, precision=2),
                ],
                rows=rows,
                emptyState="No wrong-Feather Light/Void mistakes matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _build_player_indicators(total_mistakes: int) -> List[TableCellIndicatorModel]:
    if not total_mistakes:
        return []
    return [
        TableCellIndicatorModel(
            id="light_void_mistake",
            label="At least one wrong-Feather Light/Void event. Click the row for details.",
            tone="danger",
        )
    ]


def _build_summary_metrics(summary: BelorenLightVoidMistakeSummary) -> List[SummaryMetricModel]:
    return [
        SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="total_mistakes", label="Total mistakes", value=summary.total_mistakes, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="flame_mistakes", label="Flames mistakes", value=summary.flame_mistakes, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="quill_mistakes", label="Quill mistakes", value=summary.quill_mistakes, format=ValueFormat.INTEGER),
        SummaryMetricModel(
            id="rupture_mistakes",
            label="Rupture mistakes",
            value=summary.rupture_mistakes,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="eruption_mistakes",
            label="Eruption interrupts",
            value=summary.eruption_mistakes,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="mistakes_per_pull",
            label="Mistakes per pull",
            value=summary.mistakes_per_pull,
            display=f"{summary.mistakes_per_pull:.2f}",
            format=ValueFormat.DECIMAL,
            precision=2,
        ),
    ]


def _build_header_tags(summary: BelorenLightVoidMistakeSummary) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    if summary.ignore_after_deaths:
        tags.append(HeaderTagModel(id="ignore_after_deaths", label="Filter", value=f"Stop after {summary.ignore_after_deaths} deaths"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[BelorenLightVoidMistakeEvent],
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


def _build_event_item(event: BelorenLightVoidMistakeEvent, index: int) -> RowDetailItemModel:
    details = [
        f"expected {event.expected_feather_label}",
        f"had {event.actual_feather_label}",
    ]
    if event.mechanic_type == MECHANIC_QUILL and event.assigned_target:
        details.append(f"marked target {event.assigned_target}")
    if event.target and event.target != event.player:
        details.append(f"target {event.target}")
    if event.damage_amount is not None:
        details.append(f"damage {event.damage_amount:,.0f}")
    if event.mechanic_type == MECHANIC_ERUPTION and event.interrupt_ability_label:
        details.append(f"via {event.interrupt_ability_label}")

    return RowDetailItemModel(
        id=f"beloren-light-void-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{event.player}-{index}",
        label=event.mechanic_label,
        kind="ability_event",
        abilityLabel=event.ability_label,
        abilityHref=f"https://www.wowhead.com/spell={event.ability_id}",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description="; ".join(details),
        tooltip=_event_tooltip(event),
        tooltipBadges=["Wrong Feather", _mechanic_badge(event), event.actual_feather_label],
        badges=[_mechanic_badge(event)],
        tone="danger",
    )


def _event_tooltip(event: BelorenLightVoidMistakeEvent) -> str:
    if event.mechanic_type == MECHANIC_FLAMES:
        return "Flames mistakes count the wrong-color penalty debuff or stack from standing in the opposite Light/Void floor pulse."
    if event.mechanic_type == MECHANIC_QUILL:
        return (
            "The Quill target is exempt because they are forced to carry the line. Correct-color Quill hits are ignored; this event means "
            "the player was hit while carrying the wrong Feather."
        )
    if event.mechanic_type == MECHANIC_RUPTURE:
        return "Voidlight Rupture is counted once per debuff application or stack when the player's active Feather can be resolved. The displayed damage is the burst plus following DoT ticks."
    if event.mechanic_type == MECHANIC_ERUPTION:
        return "Eruption damage is not player-attributed here. This event counts the kick source when their Feather is opposite the Light or Void Ember they attempted to stop."
    return "Wrong-Feather Light/Void event."


def _mechanic_badge(event: BelorenLightVoidMistakeEvent) -> str:
    if event.mechanic_type == MECHANIC_FLAMES:
        return "Flames"
    if event.mechanic_type == MECHANIC_QUILL:
        return "Quill"
    if event.mechanic_type == MECHANIC_RUPTURE:
        return "Rupture"
    if event.mechanic_type == MECHANIC_ERUPTION:
        return "Eruption"
    return "Event"


def _group_sort_key(group_key: Tuple[str, int, int], source_order: Dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_beloren_child_of_alar_light_void_mistake_report_page",
]
