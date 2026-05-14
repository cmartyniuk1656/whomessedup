"""
View-model builder for inferred Crown of the Cosmos Silver entity hits.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..crown_of_the_cosmos_silver_hits import CrownSilverHitEvent, CrownSilverHitSummary, REPORT_DEFAULT_FIGHT
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

REPORT_ID = "crown-of-the-cosmos-silver-hits"
REPORT_TITLE = "Obelisk Silver Entity Hits Report"
REPORT_DESCRIPTION = (
    "Infer which Bursting Emptiness assignments destroyed their Silver entity during Mythic Crown of the Cosmos."
)
REPORT_FOOTNOTES = [
    "Warcraft Logs does not expose direct Bursting Emptiness hits to Silver entities. This report infers success from Silver Simulacrum instance activity.",
    "Each Silver Simulacrum is paired to one later Grasp of Emptiness release. A player is credited when that instance's Simulacrum Backlash stream stops near that player's release timestamp.",
    "The two-player assignment is reported separately when the releases are distinct in the combat log. Overlapping releases are marked ambiguous instead of being counted as confident individual hits or misses.",
    "Player clip counts are clustered by Grasp release timestamp. Warcraft Logs does not expose the assigned player or line as the clip source, so these are inferred release-window clips rather than direct source attribution.",
]


def build_crown_of_the_cosmos_silver_hit_report_page(summary: CrownSilverHitSummary) -> ReportPageModel:
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
                        indicators=_build_player_indicators(entry.missed_hits, entry.assignments, entry.ambiguous_assignments),
                    ),
                    "role": TableCellModel(value=role, sortValue=role_priority, tone=role_tone(role)),
                    "pulls": TableCellModel(value=entry.pulls),
                    "assignments": TableCellModel(value=entry.assignments),
                    "successful_hits": TableCellModel(value=entry.successful_hits),
                    "missed_hits": TableCellModel(value=entry.missed_hits),
                    "ambiguous_assignments": TableCellModel(value=entry.ambiguous_assignments),
                    "success_rate": TableCellModel(value=entry.success_rate, display=_format_percent(entry.success_rate)),
                    "player_clips": TableCellModel(value=entry.player_clips),
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
        summary=[
            SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
            SummaryMetricModel(
                id="assignments",
                label="Assignments paired",
                value=summary.total_assignments,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="successful_hits",
                label="Silver entities hit",
                value=summary.total_successful_hits,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="missed_hits",
                label="Silver entities missed",
                value=summary.total_missed_hits,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="ambiguous_assignments",
                label="Ambiguous assignments",
                value=summary.total_ambiguous_assignments,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="success_rate",
                label="Hit rate",
                value=summary.success_rate,
                display=_format_percent(summary.success_rate),
                format=ValueFormat.DECIMAL,
                precision=1,
            ),
            SummaryMetricModel(
                id="player_clips",
                label="Release-window player clips",
                value=summary.total_player_clips,
                format=ValueFormat.INTEGER,
            ),
        ],
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="missed_hits", direction=SortDirection.DESC),
                columns=[
                    TableColumnModel(id="player", label="Player", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.PLAYER),
                    TableColumnModel(id="role", label="Role", align=TextAlign.LEFT, sortable=True, cellKind=CellKind.BADGE),
                    TableColumnModel(id="pulls", label="Pulls", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="assignments", label="Assignments", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="successful_hits", label="Hits", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="missed_hits", label="Misses", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="ambiguous_assignments", label="Ambiguous", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                    TableColumnModel(id="success_rate", label="Hit Rate", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.DECIMAL, precision=1),
                    TableColumnModel(id="player_clips", label="Release Clips", align=TextAlign.RIGHT, sortable=True, cellKind=CellKind.NUMBER, format=ValueFormat.INTEGER),
                ],
                rows=rows,
                emptyState="No Silver entity assignments matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _build_player_indicators(missed_hits: int, assignments: int, ambiguous_assignments: int) -> List[TableCellIndicatorModel]:
    if missed_hits:
        return [
            TableCellIndicatorModel(
                id="silver_miss",
                label="At least one inferred Silver entity miss. Click the row for details.",
                tone="danger",
            )
        ]
    if ambiguous_assignments:
        return [
            TableCellIndicatorModel(
                id="silver_ambiguous",
                label="At least one Silver entity assignment had overlapping release timing and could not be confidently attributed.",
                tone="warning",
            )
        ]
    if assignments:
        return [
            TableCellIndicatorModel(
                id="silver_hit",
                label="All paired Silver entity assignments were inferred as hits.",
                tone="success",
            )
        ]
    return []


def _build_header_tags(summary: CrownSilverHitSummary) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    tags.append(HeaderTagModel(id="match_window", label="Match Window", value=f"{summary.match_window_ms / 1000.0:g}s"))
    if summary.ignore_after_deaths:
        tags.append(HeaderTagModel(id="ignore_after_deaths", label="Filter", value=f"Stop after {summary.ignore_after_deaths} deaths"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[CrownSilverHitEvent],
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


def _build_event_item(event: CrownSilverHitEvent, index: int) -> RowDetailItemModel:
    if event.ambiguous:
        status = "Ambiguous"
        tone = "warning"
    else:
        status = "Hit" if event.success else "Miss"
        tone = "success" if event.success else "danger"
    details = [
        f"Set {event.set_index}" if event.set_index is not None else "Set n/a",
        f"Silver #{event.silver_instance}",
    ]
    if event.paired_player:
        paired_status = "ambiguous" if event.ambiguous else ("hit" if event.paired_player_success else "missed")
        details.append(f"paired with {event.paired_player} ({paired_status})")
    if event.set_release_gap_ms is not None:
        details.append(f"release gap {event.set_release_gap_ms / 1000.0:.3f}s")
    if event.player_clip_count:
        details.append(f"{event.player_clip_count} release-window player clip(s)")
    if event.silver_cast_offset_ms is not None:
        details.append(f"spawn {format_offset_seconds(event.silver_cast_offset_ms)}")
    return RowDetailItemModel(
        id=f"silver-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{event.silver_instance}-{index}",
        label=status,
        kind="ability_event",
        abilityLabel="Bursting Emptiness",
        abilityHref="https://www.wowhead.com/spell=1255378/bursting-emptiness",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description="; ".join(details),
        tooltip=(
            "Inferred from paired Silver Simulacrum activity, not from a direct Bursting hit event on the Silver entity or an explicit assigned-player source. "
            "Overlapping release timestamps are left ambiguous because ordering no longer proves which player destroyed which Silver entity."
        ),
        tooltipBadges=["Inferred", "Silver Entity", "Two-Player Set"] + (["Ambiguous"] if event.ambiguous else []),
        badges=[status],
        tone=tone,
    )


def _group_sort_key(group_key: Tuple[str, int, int], source_order: Dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


def _format_percent(value: float) -> str:
    return f"{value * 100.0:.1f}%"


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_crown_of_the_cosmos_silver_hit_report_page",
]
