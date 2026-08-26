"""View model for the Heroic Sszorak Tempest report."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..sszorak_tempest import (
    TEMPEST_ABILITY_ID,
    TEMPEST_ABILITY_NAME,
    SszorakTempestEvent,
    SszorakTempestSummary,
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

REPORT_ID = "sszorak-tempest"
REPORT_DEFAULT_FIGHT = "Sszorak"
REPORT_TITLE = "Heroic Sszorak - Tempest Report"
REPORT_DESCRIPTION = "Track who contacts Tempest tornadoes and who successfully dispels the resulting debuff."
REPORT_FOOTNOTES = [
    "A Tempest contact is counted from each distinct debuff application, stack application, or max-stack refresh; duplicate records for the same player and timestamp are collapsed.",
    "Only successful dispels of Tempest are counted. Natural expirations and removals at the end of a pull are excluded.",
    "Poison Cleansing Totem dispels are credited to the shaman who placed the totem.",
]


def build_sszorak_tempest_report_page(summary: SszorakTempestSummary) -> ReportPageModel:
    rows: List[TableRowModel] = []
    for entry in summary.entries:
        role = entry.role or ROLE_UNKNOWN
        indicators: List[TableCellIndicatorModel] = []
        if entry.contacts:
            indicators.append(
                TableCellIndicatorModel(
                    id="tempest_contacts",
                    label="Tempest contacts available. Click the row for details.",
                    tone="warning",
                )
            )
        if entry.dispels:
            indicators.append(
                TableCellIndicatorModel(
                    id="tempest_dispels",
                    label="Successful Tempest dispels available. Click the row for details.",
                    tone="info",
                )
            )
        rows.append(
            TableRowModel(
                id=entry.player,
                cells={
                    "player": TableCellModel(
                        value=entry.player,
                        colorToken=class_color_token(entry.class_name),
                        indicators=indicators,
                    ),
                    "role": TableCellModel(
                        value=role,
                        sortValue=ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN]),
                        tone=role_tone(role),
                    ),
                    "pulls": TableCellModel(value=entry.pulls),
                    "contacts": TableCellModel(value=entry.contacts),
                    "contacts_per_pull": TableCellModel(value=entry.contacts_per_pull, display=f"{entry.contacts_per_pull:.2f}"),
                    "dispels": TableCellModel(value=entry.dispels),
                    "dispels_per_pull": TableCellModel(value=entry.dispels_per_pull, display=f"{entry.dispels_per_pull:.2f}"),
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
        summary=[
            SummaryMetricModel(id="pull_count", label="Pulls counted", value=summary.pull_count, format=ValueFormat.INTEGER),
            SummaryMetricModel(id="total_contacts", label="Tempest contacts", value=summary.total_contacts, format=ValueFormat.INTEGER),
            SummaryMetricModel(id="total_dispels", label="Successful dispels", value=summary.total_dispels, format=ValueFormat.INTEGER),
            SummaryMetricModel(id="pet_dispels", label="Totem dispels", value=summary.pet_dispels, format=ValueFormat.INTEGER),
        ],
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="contacts", direction=SortDirection.DESC),
                columns=[
                    _column("player", "Player", TextAlign.LEFT, CellKind.PLAYER),
                    _column("role", "Role", TextAlign.LEFT, CellKind.BADGE),
                    _column("pulls", "Pulls"),
                    _column("contacts", "Tempest Hits"),
                    _decimal_column("contacts_per_pull", "Hits / Pull"),
                    _column("dispels", "Dispels"),
                    _decimal_column("dispels_per_pull", "Dispels / Pull"),
                ],
                rows=rows,
                emptyState="No Sszorak Tempest events matched the selected pulls.",
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


def _decimal_column(column_id: str, label: str) -> TableColumnModel:
    return TableColumnModel(
        id=column_id,
        label=label,
        align=TextAlign.RIGHT,
        sortable=True,
        cellKind=CellKind.NUMBER,
        format=ValueFormat.DECIMAL,
        precision=2,
    )


def _build_header_tags(summary: SszorakTempestSummary) -> List[HeaderTagModel]:
    tags = [
        HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter or REPORT_DEFAULT_FIGHT),
        HeaderTagModel(id="debuff", label="Debuff", value=f"{TEMPEST_ABILITY_NAME} ({TEMPEST_ABILITY_ID})"),
    ]
    if summary.ignore_after_deaths:
        tags.append(HeaderTagModel(id="ignore_after_deaths", label="Filter", value=f"Stop after {summary.ignore_after_deaths} deaths"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[SszorakTempestEvent],
    *,
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    if not events:
        return None
    source_order = {code: index for index, code in enumerate(source_reports or [report_code])}
    grouped: Dict[Tuple[str, int, int], Dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.source_report_code or "", item.pull_index, item.timestamp)):
        source = event.source_report_code or report_code
        key = (source, event.fight_id, event.pull_index)
        bucket = grouped.setdefault(
            key,
            {
                "source": source,
                "fight_id": event.fight_id,
                "pull_index": event.pull_index,
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


def _build_event_item(event: SszorakTempestEvent, index: int) -> RowDetailItemModel:
    if event.event_type == "dispel":
        description = f"Removed Tempest from {event.target}."
        badges = ["Successful Dispel"]
        if event.credited_from_pet:
            description += f" Credited from {event.credited_from_pet}."
            badges.append("Pet credited to owner")
        return RowDetailItemModel(
            id=f"tempest-dispel-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{index}",
            label="Tempest Dispel",
            kind="ability_event",
            abilityLabel=event.dispel_ability_name or "Dispel",
            abilityHref=f"https://www.wowhead.com/spell={event.dispel_ability_id}" if event.dispel_ability_id else None,
            timestampLabel=format_offset_seconds(event.offset_ms),
            description=description,
            badges=badges,
            tone="success",
        )
    stack_label = f"Stack {event.stack}" if event.stack else "Tempest"
    return RowDetailItemModel(
        id=f"tempest-contact-{event.source_report_code or 'report'}-{event.fight_id}-{int(event.timestamp)}-{index}",
        label="Tempest Contact",
        kind="ability_event",
        abilityLabel=TEMPEST_ABILITY_NAME,
        abilityHref=f"https://www.wowhead.com/spell={TEMPEST_ABILITY_ID}",
        timestampLabel=format_offset_seconds(event.offset_ms),
        description="The player contacted a Tempest tornado and received or increased the debuff.",
        badges=[stack_label, "Avoidable"],
        tone="warning",
    )


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_sszorak_tempest_report_page",
]
