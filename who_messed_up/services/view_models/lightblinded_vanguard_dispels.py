"""
View-model builder for the v2 Lightblinded Vanguard dispel report page.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..lightblinded_vanguard_dispels import (
    AVENGERS_SHIELD_DEBUFF_ID,
    DISPEL_CAST_ABILITIES,
    LightblindedVanguardDispelEvent,
    LightblindedVanguardDispelSummary,
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
from .helpers import (
    build_pull_link,
    class_color_token,
    format_duration,
    format_offset_seconds,
    merged_reports_label,
    role_tone,
)


REPORT_ID = "lightblinded-vanguard-dispels"
REPORT_TITLE = "Mythic Lightblinded Vanguard - Dispel Report"
REPORT_DESCRIPTION = "Track Avenger's Shield dispels and dispel casts during Mythic Lightblinded Vanguard pulls."
REPORT_FOOTNOTES = [
    "Shield sets are counted only when exactly four Avenger's Shield applications occur together.",
    "The default Revival filter excludes Revival and any same-player same-timestamp multi-dispel bursts.",
    "Set Dispels is the subset of successful dispels tied to counted 4-application sets and is used for Avg Dispels / Set."
]


def build_lightblinded_vanguard_dispel_report_page(
    summary: LightblindedVanguardDispelSummary,
) -> ReportPageModel:
    rows: List[TableRowModel] = []
    for entry in summary.entries:
        role = entry.role or ROLE_UNKNOWN
        role_priority = ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN])
        indicators = []
        if entry.events:
            indicators.append(
                TableCellIndicatorModel(
                    id="successful_dispels",
                    label="Successful Avenger's Shield dispels available. Click the row for details.",
                    tone="info",
                )
            )
        cells: Dict[str, TableCellModel] = {
            "player": TableCellModel(
                value=entry.player,
                colorToken=class_color_token(entry.class_name),
                indicators=indicators,
            ),
            "role": TableCellModel(
                value=role,
                sortValue=role_priority,
                tone=role_tone(role),
            ),
            "pulls": TableCellModel(value=entry.pulls),
            "sets": TableCellModel(value=entry.sets),
            "dispel_casts": TableCellModel(value=entry.dispel_casts),
            "successful_dispels": TableCellModel(value=entry.successful_dispels),
            "set_dispels": TableCellModel(value=entry.set_dispels),
            "average_dispels_per_set": TableCellModel(value=entry.average_dispels_per_set),
        }
        if summary.filtered_dispels:
            cells["filtered_dispels"] = TableCellModel(value=entry.filtered_dispels)
        rows.append(
            TableRowModel(
                id=entry.player,
                cells=cells,
                details=_build_row_details(
                    summary.report_code,
                    entry.events,
                    cast_breakdown=entry.cast_breakdown,
                    source_reports=summary.source_reports or [summary.report_code],
                ),
            )
        )

    columns = [
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
            id="sets",
            label="Sets",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="dispel_casts",
            label="Dispel Casts",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="successful_dispels",
            label="Successful Dispels",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="set_dispels",
            label="Set Dispels",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="average_dispels_per_set",
            label="Avg Dispels / Set",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.DECIMAL,
            precision=2,
        ),
    ]
    if summary.filtered_dispels:
        columns.append(
            TableColumnModel(
                id="filtered_dispels",
                label="Filtered Dispels",
                align=TextAlign.RIGHT,
                sortable=True,
                cellKind=CellKind.NUMBER,
                format=ValueFormat.INTEGER,
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
                defaultSort=SortModel(columnId="successful_dispels", direction=SortDirection.DESC),
                columns=columns,
                rows=rows,
                emptyState="No Lightblinded Vanguard dispel events matched the filters.",
            ),
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _build_summary_metrics(summary: LightblindedVanguardDispelSummary) -> List[SummaryMetricModel]:
    metrics = [
        SummaryMetricModel(
            id="pull_count",
            label="Pulls counted",
            value=summary.pull_count,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="total_sets",
            label="Shield sets counted",
            value=summary.total_sets,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="total_dispel_casts",
            label="Dispel casts",
            value=summary.total_dispel_casts,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="successful_dispels",
            label="Successful dispels",
            value=summary.successful_dispels,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="set_successful_dispels",
            label="Set dispels",
            value=summary.set_successful_dispels,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="avg_dispels_per_set",
            label="Avg dispels / Set",
            value=summary.avg_dispels_per_set,
            format=ValueFormat.DECIMAL,
            precision=2,
        ),
    ]
    if summary.filtered_dispels:
        metrics.append(
            SummaryMetricModel(
                id="filtered_dispels",
                label="Filtered dispels",
                value=summary.filtered_dispels,
                format=ValueFormat.INTEGER,
            )
        )
    if summary.non_set_dispels:
        metrics.append(
            SummaryMetricModel(
                id="non_set_dispels",
                label="Non-set successful dispels",
                value=summary.non_set_dispels,
                format=ValueFormat.INTEGER,
            )
        )
    if summary.excluded_application_groups:
        metrics.append(
            SummaryMetricModel(
                id="excluded_application_groups",
                label="Excluded application groups",
                value=summary.excluded_application_groups,
                format=ValueFormat.INTEGER,
            )
        )
    return metrics


def _build_header_tags(summary: LightblindedVanguardDispelSummary) -> List[HeaderTagModel]:
    tags: List[HeaderTagModel] = []
    if summary.fight_filter:
        tags.append(HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter))
    tags.append(
        HeaderTagModel(
            id="debuff",
            label="Debuff",
            value=f"Avenger's Shield ({AVENGERS_SHIELD_DEBUFF_ID})",
        )
    )
    tags.append(
        HeaderTagModel(
            id="casts",
            label="Casts",
            value=", ".join(ability.name for ability in DISPEL_CAST_ABILITIES),
        )
    )
    if summary.exclude_revival_dispels:
        tags.append(HeaderTagModel(id="revival_filter", label="Filter", value="Excluding Revival/multi-dispels"))
    else:
        tags.append(HeaderTagModel(id="revival_filter", label="Filter", value="Including Revival/multi-dispels"))
    if summary.exclude_dead_player_sets:
        tags.append(HeaderTagModel(id="dead_set_filter", label="Sets", value="Excluding sets after player death"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[LightblindedVanguardDispelEvent],
    *,
    cast_breakdown: Dict[str, int],
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    groups: List[RowDetailGroupModel] = []
    cast_items = _build_cast_breakdown_items(cast_breakdown)
    if cast_items:
        groups.append(
            RowDetailGroupModel(
                id="cast-breakdown",
                title="Dispel Casts",
                subtitle="Total listed dispel casts by ability",
                items=cast_items,
            )
        )
    if events:
        groups.extend(_build_event_groups(report_code, events, source_reports=source_reports))
    if not groups:
        return None
    return RowDetailsModel(variant=RowDetailsVariant.EVENT_GROUPS, groups=groups)


def _build_cast_breakdown_items(cast_breakdown: Dict[str, int]) -> List[RowDetailItemModel]:
    items: List[RowDetailItemModel] = []
    for ability_name, total in sorted(cast_breakdown.items(), key=lambda item: item[0].lower()):
        if total <= 0:
            continue
        items.append(
            RowDetailItemModel(
                id=f"cast-breakdown-{_slugify(ability_name)}",
                label=ability_name,
                description=f"{total} casts",
                badges=["Dispel Cast"],
            )
        )
    return items


def _build_event_groups(
    report_code: str,
    events: List[LightblindedVanguardDispelEvent],
    *,
    source_reports: List[str],
) -> List[RowDetailGroupModel]:
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
        items = bucket.get("items")
        if not isinstance(items, list):
            items = []
            bucket["items"] = items
        items.append(_build_event_item(event, len(items)))

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
    return groups


def _build_event_item(event: LightblindedVanguardDispelEvent, index: int) -> RowDetailItemModel:
    badges = ["Avenger's Shield"]
    if event.is_revival:
        badges.append("Revival")
    elif event.is_multi_dispel:
        badges.append("Multi-dispel")
    if event.is_non_set:
        badges.append("Non-set")
    description = f"on {event.target}" if event.target else None
    return RowDetailItemModel(
        id=f"dispel-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{index}",
        label="Dispel",
        kind="ability_event",
        abilityLabel=event.ability_label,
        abilityHref=_wowhead_spell_url(event.ability_id),
        timestampLabel=format_offset_seconds(event.offset_ms),
        description=description,
        badges=badges,
    )


def _group_sort_key(group_key: Tuple[str, int, int], source_order: dict[str, int]) -> Tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


def _wowhead_spell_url(ability_id: Optional[int]) -> Optional[str]:
    if ability_id is None:
        return None
    return f"https://www.wowhead.com/spell={int(ability_id)}"


def _slugify(value: str) -> str:
    return "-".join(str(value).strip().lower().replace("'", "").split())


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_lightblinded_vanguard_dispel_report_page",
]
