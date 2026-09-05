"""View-model builder for reusable encounter mechanics scorecards."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..mechanic_scorecard_types import (
    MechanicObservation,
    MechanicScoreEntry,
    MechanicScorecardSummary,
    OUTCOME_CONTRIBUTION,
    OUTCOME_MISTAKE,
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


def build_mechanic_scorecard_report_page(
    summary: MechanicScorecardSummary,
) -> ReportPageModel:
    report_id = f"{summary.boss_id}-mechanics-scorecard"
    rows_by_view = {
        view.mechanic.id: [
            _build_row(summary, entry) for entry in view.entries
        ]
        for view in summary.views
    }
    default_view = summary.views[0].mechanic.id if summary.views else "mechanics"
    total_successes = sum(view.successes for view in summary.views)
    total_mistakes = sum(view.mistakes for view in summary.views)
    total_contributions = sum(view.contributions for view in summary.views)
    title = f"Heroic {summary.boss_name} - Mechanics Scorecard"
    return ReportPageModel(
        reportId=report_id,
        title=title,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=_build_header_tags(summary),
        ),
        summary=[
            SummaryMetricModel(
                id="pull_count",
                label="Pulls counted",
                value=summary.pull_count,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="mechanics",
                label="Mechanics tracked",
                value=len(summary.views),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="clean_executions",
                label="Clean executions",
                value=total_successes,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="mistakes",
                label="Mistakes",
                value=total_mistakes,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="contributions",
                label="Contributions",
                value=total_contributions,
                format=ValueFormat.INTEGER,
            ),
        ],
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(
                    columnId="mistakes", direction=SortDirection.DESC
                ),
                columns=[
                    _column("player", "Player", TextAlign.LEFT, CellKind.PLAYER),
                    _column("role", "Role", TextAlign.LEFT, CellKind.BADGE),
                    _column("pulls", "Pulls"),
                    _column("opportunities", "Opportunities"),
                    _column("successes", "Clean"),
                    _column("mistakes", "Mistakes"),
                    _column("contributions", "Contributions"),
                    TableColumnModel(
                        id="success_rate",
                        label="Success Rate",
                        align=TextAlign.RIGHT,
                        sortable=True,
                        cellKind=CellKind.NUMBER,
                        format=ValueFormat.DECIMAL,
                        precision=1,
                    ),
                ],
                rows=rows_by_view.get(default_view, []),
                rowsByView=rows_by_view,
                viewControl=TableViewControlModel(
                    id="mechanic",
                    label="Mechanic",
                    defaultValue=default_view,
                    options=[
                        TableViewOptionModel(
                            value=view.mechanic.id,
                            label=view.mechanic.label,
                        )
                        for view in summary.views
                    ],
                ),
                emptyState="No matching mechanic events were found in the selected pulls.",
            ),
        ),
        footnotes=_build_footnotes(summary),
    )


def _build_row(
    summary: MechanicScorecardSummary, entry: MechanicScoreEntry
) -> TableRowModel:
    indicators: List[TableCellIndicatorModel] = []
    if entry.mistakes:
        indicators.append(
            TableCellIndicatorModel(
                id="mistakes",
                label="Mistake details available. Click the row for details.",
                tone="warning",
            )
        )
    if entry.successes or entry.contributions:
        indicators.append(
            TableCellIndicatorModel(
                id="positive_events",
                label="Successful executions or contributions available. Click the row for details.",
                tone="info",
            )
        )
    role = entry.role or ROLE_UNKNOWN
    success_rate = entry.success_rate
    return TableRowModel(
        id=entry.player,
        cells={
            "player": TableCellModel(
                value=entry.player,
                colorToken=class_color_token(entry.class_name),
                indicators=indicators,
            ),
            "role": TableCellModel(
                value=role,
                sortValue=ROLE_PRIORITY.get(role, 5),
                tone="neutral" if role == "Team" else role_tone(role),
            ),
            "pulls": TableCellModel(value=entry.pulls),
            "opportunities": TableCellModel(value=entry.opportunities),
            "successes": TableCellModel(value=entry.successes),
            "mistakes": TableCellModel(value=entry.mistakes),
            "contributions": TableCellModel(value=entry.contributions),
            "success_rate": TableCellModel(
                value=success_rate,
                display=f"{success_rate:.1f}%" if success_rate is not None else "—",
                sortValue=success_rate if success_rate is not None else -1,
            ),
        },
        details=_build_row_details(summary, entry.events),
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


def _build_header_tags(summary: MechanicScorecardSummary) -> List[HeaderTagModel]:
    scope_labels = {
        "all": "All matching pulls",
        "last": "Last matching pull",
        "specific": f"Fight {summary.fight_ids[0]}" if summary.fight_ids else "Specific fight",
    }
    tags = [
        HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter),
        HeaderTagModel(
            id="scope",
            label="Scope",
            value=scope_labels.get(summary.fight_selection, summary.fight_selection),
        ),
    ]
    if summary.ignore_after_deaths:
        tags.append(
            HeaderTagModel(
                id="ignore_after_deaths",
                label="Filter",
                value=f"Stop after {summary.ignore_after_deaths} deaths",
            )
        )
    merged_label = merged_reports_label(
        summary.source_reports or [summary.report_code]
    )
    if merged_label:
        tags.append(
            HeaderTagModel(
                id="merged_reports", label="Reports", value=merged_label
            )
        )
    return tags


def _build_row_details(
    summary: MechanicScorecardSummary,
    events: List[MechanicObservation],
) -> Optional[RowDetailsModel]:
    if not events:
        return None
    source_order = {
        code: index
        for index, code in enumerate(summary.source_reports or [summary.report_code])
    }
    grouped: Dict[Tuple[str, int, int], Dict[str, object]] = {}
    for index, event in enumerate(
        sorted(
            events,
            key=lambda item: (
                item.source_report_code or "",
                item.pull_index,
                item.timestamp,
            ),
        )
    ):
        source = event.source_report_code or summary.report_code
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
        bucket["items"].append(_build_event_item(event, index))

    groups: List[RowDetailGroupModel] = []
    for key in sorted(
        grouped,
        key=lambda item: (
            source_order.get(item[0], len(source_order)),
            item[2],
            item[1],
        ),
    ):
        bucket = grouped[key]
        source = str(bucket["source"])
        fight_id = int(bucket["fight_id"])
        subtitle = [
            part
            for part in [
                format_duration(bucket["duration"]),
                f"{bucket['fight_name']} - Fight {fight_id}",
            ]
            if part
        ]
        if source != summary.report_code:
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
    return RowDetailsModel(
        variant=RowDetailsVariant.EVENT_GROUPS,
        groups=groups,
    )


def _build_event_item(
    event: MechanicObservation, index: int
) -> RowDetailItemModel:
    outcome_labels = {
        OUTCOME_MISTAKE: "Mistake",
        OUTCOME_CONTRIBUTION: "Contribution",
        "success": "Clean execution",
    }
    badges = [outcome_labels.get(event.outcome, event.outcome.title())]
    if event.value is not None and event.value_label:
        value = (
            f"{event.value:.1f}"
            if isinstance(event.value, float)
            else str(event.value)
        )
        badges.append(f"{event.value_label}: {value}")
    if event.target:
        badges.append(f"Target: {event.target}")
    tone = (
        "warning"
        if event.outcome == OUTCOME_MISTAKE
        else "success"
        if event.outcome == "success"
        else "info"
    )
    return RowDetailItemModel(
        id=(
            f"mechanic-{event.source_report_code or 'report'}-{event.fight_id}-"
            f"{event.mechanic_id}-{int(event.timestamp)}-{index}"
        ),
        label=event.label,
        kind="ability_event",
        abilityLabel=event.ability_label,
        abilityHref=(
            f"https://www.wowhead.com/spell={event.ability_id}"
            if event.ability_id
            else None
        ),
        timestampLabel=format_offset_seconds(event.offset_ms),
        description=event.description,
        badges=badges,
        tone=tone,
    )


def _build_footnotes(summary: MechanicScorecardSummary) -> List[str]:
    notes = [
        "Opportunities are scored only when the combat log exposes a direct or defensibly correlated success/failure signal. Success rate is Clean / Opportunities.",
        "Contributions are positive participation counts and do not affect success rate. They are used when assignments or positioning cannot be judged reliably from events alone.",
        "The Raid team row represents group-level outcomes and is not blame assigned to players who merely received raid-wide damage.",
    ]
    for view in summary.views:
        if view.mechanic.optional or "Contribution" in view.mechanic.confidence:
            notes.append(
                f"{view.mechanic.label}: {view.mechanic.description} ({view.mechanic.confidence}.)"
            )
    if summary.boss_id == "the-coiled-altar":
        notes.append(
            "Coalesced Venom relocation credits Volatile Venom pickup and reports carry time; the log does not prove that the orb was dropped in the correct location or consumed by the tank frontal."
        )
    return notes


__all__ = ["build_mechanic_scorecard_report_page"]
