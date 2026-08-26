"""View-model builder for The Twin Fangs Eternal Venom fuck-up report."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..the_twin_fangs_fuckups import TwinFangsFuckupEvent, TwinFangsFuckupSummary
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

REPORT_ID = "the-twin-fangs-fuckups"
REPORT_DEFAULT_FIGHT = "The Twin Fangs"
REPORT_TITLE = "The Twin Fangs Eternal Venom Fuck Ups Report"
REPORT_DESCRIPTION = "Show player-owned avoidable Eternal Venom applications and the resulting stack count."
REPORT_FOOTNOTES = [
    "Stir the Depths waves, Vile Flood, Caustic Deluge splash, and collateral Corrosive Spit hits are scored as avoidable stack applications.",
    "The intended target of Corrosive Spit is not scored; only additional players caught in that targeted line are counted.",
    "A successful Caustic Globule soak is positive venom management and is not scored unless it raises the player to the lethal 10-stack threshold.",
    "Unavoidable Venomous Emergence applications and raid victims of an unsoaked Caustic Globule are not personally scored.",
    "Applications without a defensible cause match in the combat log are left unscored.",
]


def build_the_twin_fangs_fuckup_report_page(summary: TwinFangsFuckupSummary) -> ReportPageModel:
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
                        indicators=_build_player_indicators(entry.total_fuckups, entry.fatal_stack_events),
                    ),
                    "role": TableCellModel(
                        value=role,
                        sortValue=ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN]),
                        tone=role_tone(role),
                    ),
                    "pulls": TableCellModel(value=entry.pulls),
                    "total_fuckups": TableCellModel(value=entry.total_fuckups),
                    "corrosive_spit_collateral": TableCellModel(value=entry.corrosive_spit_collateral),
                    "caustic_deluge_splashes": TableCellModel(value=entry.caustic_deluge_splashes),
                    "stir_the_depths_hits": TableCellModel(value=entry.stir_the_depths_hits),
                    "vile_flood_hits": TableCellModel(value=entry.vile_flood_hits),
                    "fatal_globules": TableCellModel(value=entry.fatal_globules),
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
        header=ReportHeaderModel(subtitle=f"Report {summary.report_code}", tags=_build_header_tags(summary)),
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
                    _column("corrosive_spit_collateral", "Spit"),
                    _column("caustic_deluge_splashes", "Deluge"),
                    _column("stir_the_depths_hits", "Waves"),
                    _column("vile_flood_hits", "Flood"),
                    _column("fatal_globules", "Globule"),
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
                emptyState="No Twin Fangs Eternal Venom applications matched the selected pulls.",
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


def _build_player_indicators(total: int, fatal: int) -> List[TableCellIndicatorModel]:
    if fatal:
        return [TableCellIndicatorModel(id="lethal_venom", label="Reached lethal Eternal Venom stacks.", tone="danger")]
    if total:
        return [TableCellIndicatorModel(id="avoidable_venom", label="Took an avoidable Eternal Venom stack.", tone="warning")]
    return []


def _build_summary_metrics(summary: TwinFangsFuckupSummary) -> List[SummaryMetricModel]:
    return [
        SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="total_fuckups", label="Avoidable stacks", value=summary.total_fuckups, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="fatal_stack_events", label="Lethal applications", value=summary.fatal_stack_events, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="corrosive_spit_collateral", label="Spit collateral", value=summary.corrosive_spit_collateral, format=ValueFormat.INTEGER),
        SummaryMetricModel(id="stir_the_depths_hits", label="Wave stacks", value=summary.stir_the_depths_hits, format=ValueFormat.INTEGER),
        SummaryMetricModel(
            id="fuckups_per_pull",
            label="Fuck-ups per pull",
            value=summary.fuckups_per_pull,
            display=f"{summary.fuckups_per_pull:.2f}",
            format=ValueFormat.DECIMAL,
            precision=2,
        ),
    ]


def _build_header_tags(summary: TwinFangsFuckupSummary) -> List[HeaderTagModel]:
    tags = [
        HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter or REPORT_DEFAULT_FIGHT),
        HeaderTagModel(id="threshold", label="Lethal", value=f"{summary.lethal_stack_threshold} stacks"),
    ]
    if summary.ignore_after_deaths:
        tags.append(HeaderTagModel(id="ignore_after_deaths", label="Filter", value=f"Stop after {summary.ignore_after_deaths} deaths"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[TwinFangsFuckupEvent],
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
        subtitle = [part for part in [format_duration(bucket["duration"]), f"{bucket['fight_name']} - Fight {fight_id}"] if part]
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


def _build_event_item(event: TwinFangsFuckupEvent, index: int) -> RowDetailItemModel:
    badges = [f"Stack {event.resulting_stack}", event.cause_ability_label]
    if event.fatal_stack:
        badges.insert(0, "Lethal")
    return RowDetailItemModel(
        id=f"twin-fangs-venom-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{event.player}-{index}",
        label=event.mechanic_label,
        kind="ability_event",
        abilityLabel=event.cause_ability_label,
        abilityHref=f"https://www.wowhead.com/spell={event.cause_ability_id}",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description=f"Eternal Venom reached {event.resulting_stack} stack(s). {event.reason}",
        tooltip=event.reason,
        tooltipBadges=["Avoidable Stack", f"Result: {event.resulting_stack}"],
        badges=badges,
        tone="danger" if event.fatal_stack else "warning",
    )


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_the_twin_fangs_fuckup_report_page",
]
