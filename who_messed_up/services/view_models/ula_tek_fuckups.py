"""View-model builder for the Heroic Ula'tek fuck-up report."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..ula_tek_fuckups import (
    CAUSTIC_WAVES_LABEL,
    REPORT_DEFAULT_FIGHT,
    UlaTekFuckupEvent,
    UlaTekFuckupSummary,
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
from .helpers import (
    build_pull_link,
    class_color_token,
    format_duration,
    format_offset_seconds,
    merged_reports_label,
    role_tone,
)

REPORT_ID = "ula-tek-fuckups"
REPORT_TITLE = "Heroic Ula'tek Fuck Ups Report"
REPORT_DESCRIPTION = "List every player hit by a dodgeable Caustic Wave."
REPORT_FOOTNOTES = [
    "Each distinct Caustic Waves contact is counted as one fuck-up for the player it hit.",
    "The periodic damage train from one contact is collapsed until the player's ticks have been quiet for more than 2.5 seconds.",
    "Absorbed or mitigated hits still count because the report measures contact with the dodgeable wave, not health damage taken.",
]


def build_ula_tek_fuckup_report_page(summary: UlaTekFuckupSummary) -> ReportPageModel:
    rows: List[TableRowModel] = []
    for entry in summary.entries:
        role = entry.role or ROLE_UNKNOWN
        rows.append(
            TableRowModel(
                id=entry.player,
                cells={
                    "player": TableCellModel(
                        value=entry.player,
                        colorToken=class_color_token(entry.class_name),
                        indicators=_build_player_indicators(entry.total_fuckups),
                    ),
                    "role": TableCellModel(
                        value=role,
                        sortValue=ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN]),
                        tone=role_tone(role),
                    ),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_fuckups": TableCellModel(value=entry.total_fuckups),
                    "caustic_waves_hits": TableCellModel(value=entry.caustic_waves_hits),
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
                    _column("player", "Player", TextAlign.LEFT, CellKind.PLAYER),
                    _column("role", "Role", TextAlign.LEFT, CellKind.BADGE),
                    _column("pulls", "Pulls"),
                    _column("total_fuckups", "Total"),
                    _column("caustic_waves_hits", "Caustic Waves"),
                    TableColumnModel(
                        id="fuckups_per_pull",
                        label="Per Pull",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.DECIMAL,
                        precision=2,
                    ),
                ],
                rows=rows,
                emptyState="No Caustic Waves hits matched the selected Ula'tek pulls.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _column(
    column_id: str,
    label: str,
    align: TextAlign = TextAlign.RIGHT,
    cell_kind: CellKind = CellKind.NUMBER,
) -> TableColumnModel:
    return TableColumnModel(
        id=column_id,
        label=label,
        align=align,
        sortable=True,
        cellKind=cell_kind,
        format=ValueFormat.INTEGER if cell_kind == CellKind.NUMBER else None,
    )


def _build_player_indicators(total_fuckups: int) -> List[TableCellIndicatorModel]:
    if not total_fuckups:
        return []
    return [
        TableCellIndicatorModel(
            id="ula_tek_wave_hit",
            label="Hit by at least one dodgeable Caustic Wave. Click the row for details.",
            tone="danger",
        )
    ]


def _build_summary_metrics(summary: UlaTekFuckupSummary) -> List[SummaryMetricModel]:
    return [
        SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="total_fuckups", label="Total wave hits", value=summary.total_fuckups, format=ValueFormat.INTEGER),
        SummaryMetricModel(
            id="affected_players",
            label="Players hit",
            value=sum(1 for entry in summary.entries if entry.total_fuckups),
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="fuckups_per_pull",
            label="Wave hits per pull",
            value=summary.fuckups_per_pull,
            display=f"{summary.fuckups_per_pull:.2f}",
            format=ValueFormat.DECIMAL,
            precision=2,
        ),
    ]


def _build_header_tags(summary: UlaTekFuckupSummary) -> List[HeaderTagModel]:
    tags = [
        HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter or REPORT_DEFAULT_FIGHT),
        HeaderTagModel(id="mechanic", label="Mechanic", value=CAUSTIC_WAVES_LABEL),
    ]
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
    return tags


def _build_row_details(
    report_code: str,
    events: List[UlaTekFuckupEvent],
    *,
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    if not events:
        return None
    source_order = {code: index for index, code in enumerate(source_reports or [report_code])}
    grouped: Dict[Tuple[str, int, int], Dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.source_report_code or "", item.pull_index, item.timestamp)):
        source = event.source_report_code or report_code
        key = (source, int(event.fight_id), int(event.pull_index))
        bucket = grouped.setdefault(
            key,
            {
                "source": source,
                "fight_id": int(event.fight_id),
                "pull_index": int(event.pull_index),
                "fight_name": event.fight_name,
                "duration": event.pull_duration_ms,
                "items": [],
            },
        )
        bucket["items"].append(_build_event_item(event, len(bucket["items"])))

    groups: List[RowDetailGroupModel] = []
    for key in sorted(grouped, key=lambda item: (source_order.get(item[0], len(source_order)), item[2], item[1])):
        bucket = grouped[key]
        source = str(bucket["source"])
        fight_id = int(bucket["fight_id"])
        subtitle = [
            part
            for part in [format_duration(bucket["duration"]), f"{bucket['fight_name']} - Fight {fight_id}"]
            if part
        ]
        if source != report_code:
            subtitle.append(f"Report {source}")
        groups.append(
            RowDetailGroupModel(
                id=f"{source}-fight-{fight_id}-pull-{bucket['pull_index']}",
                title=f"Pull {bucket['pull_index']}",
                subtitle=" - ".join(subtitle) if subtitle else None,
                link=build_pull_link(source, fight_id),
                items=bucket["items"],
            )
        )
    return RowDetailsModel(variant=RowDetailsVariant.EVENT_GROUPS, groups=groups)


def _build_event_item(event: UlaTekFuckupEvent, index: int) -> RowDetailItemModel:
    total_damage = event.amount + event.absorbed
    damage_label = f"{int(total_damage):,} incoming damage" if total_damage else "Logged wave contact"
    if event.tick_count > 1:
        damage_label = f"{damage_label}; {event.tick_count} periodic ticks collapsed"
    return RowDetailItemModel(
        id=f"ula-tek-wave-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{event.player}-{index}",
        label="Hit by Caustic Waves",
        kind="ability_event",
        abilityLabel=event.ability_label,
        abilityHref=f"https://www.wowhead.com/spell={event.ability_id}",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description=damage_label,
        tooltip="The periodic damage train from one Caustic Waves contact is counted as one failure.",
        tooltipBadges=["Avoidable", "One contact = one fuck-up", f"{event.tick_count} tick(s)"],
        badges=[CAUSTIC_WAVES_LABEL],
        tone="danger",
    )


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_ula_tek_fuckup_report_page",
]
