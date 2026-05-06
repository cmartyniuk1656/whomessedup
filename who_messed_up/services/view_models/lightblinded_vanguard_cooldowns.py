"""
View-model builder for v2 cooldown-usage reports.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from ..common import ROLE_PRIORITY, ROLE_UNKNOWN
from ..cooldown_usage import (
    COOLDOWN_STATUS_CORRECT,
    COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT,
    COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH,
    COOLDOWN_STATUS_IGNORED_AFTER_PULL_END,
    COOLDOWN_STATUS_IGNORED_DEAD,
    COOLDOWN_STATUS_IGNORED_MISSING_PHASE,
    COOLDOWN_STATUS_IGNORED_NOT_IN_PULL,
    COOLDOWN_STATUS_INCORRECT,
    COOLDOWN_STATUS_MISSED,
    CooldownUsageEntry,
    CooldownUsageEvent,
    CooldownUsageSummary,
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


REPORT_ID = "lightblinded-vanguard-cooldowns"
REPORT_DEFAULT_FIGHT = "Lightblinded Vanguard"
REPORT_TITLE = "Cooldown Usage Report"
REPORT_DESCRIPTION = "Check assigned NSRT cooldown reminders against Warcraft Logs casts."
REPORT_FOOTNOTES = [
    "Assignments are scored only for players listed in the pasted NSRT reminder.",
    "Correct means the assigned spell was cast inside the configured tolerance window.",
    "Incorrect means the assigned spell was cast in the pull, but outside the tolerance window.",
    "Missed means no same-spell cast was found for that assignment in the pull.",
    "Ignored assignments do not count against the on-time percentage.",
]


def build_cooldown_usage_report_page(
    summary: CooldownUsageSummary,
    *,
    report_id: str = REPORT_ID,
    title: str = REPORT_TITLE,
    fight_name: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> ReportPageModel:
    aggregate_rows = _build_rows(summary.entries, report_code=summary.report_code, source_reports=summary.source_reports)
    rows_by_view: Dict[str, List[TableRowModel]] = {"aggregate": aggregate_rows}
    view_options = [TableViewOptionModel(value="aggregate", label="Aggregate")]

    for pull in summary.pulls:
        scoped_entries = _entries_for_pull(summary.entries, pull.view_id)
        rows_by_view[pull.view_id] = _build_rows(scoped_entries, report_code=summary.report_code, source_reports=summary.source_reports)
        view_options.append(TableViewOptionModel(value=pull.view_id, label=pull.label))

    table = TableModel(
        defaultSort=SortModel(columnId="on_time_rate", direction=SortDirection.ASC),
        columns=_build_columns(),
        rows=aggregate_rows,
        rowsByView=rows_by_view,
        viewControl=TableViewControlModel(
            id="cooldown_pull_view",
            label="View",
            defaultValue="aggregate",
            options=view_options,
        ),
        emptyState="No cooldown assignments matched the selected view.",
    )

    return ReportPageModel(
        reportId=report_id,
        title=title,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=_build_header_tags(summary, fight_name=fight_name, difficulty=difficulty),
        ),
        summary=_build_summary_metrics(summary),
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=table,
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


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
            id="assignments",
            label="Assignments",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="correct",
            label="Correct",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="incorrect",
            label="Incorrect",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="missed",
            label="Missed",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="ignored",
            label="Ignored",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.INTEGER,
        ),
        TableColumnModel(
            id="on_time_rate",
            label="On-time %",
            align=TextAlign.RIGHT,
            sortable=True,
            cellKind=CellKind.NUMBER,
            format=ValueFormat.DECIMAL,
            precision=1,
        ),
    ]


def _build_rows(
    entries: Iterable[CooldownUsageEntry],
    *,
    report_code: str,
    source_reports: List[str],
) -> List[TableRowModel]:
    rows: List[TableRowModel] = []
    for entry in entries:
        role = entry.role or ROLE_UNKNOWN
        role_priority = ROLE_PRIORITY.get(role, ROLE_PRIORITY[ROLE_UNKNOWN])
        indicators: List[TableCellIndicatorModel] = []
        if entry.missed:
            indicators.append(
                TableCellIndicatorModel(
                    id="missed",
                    label=f"{entry.missed} missed cooldown assignments. Click the row for details.",
                    tone="danger",
                )
            )
        elif entry.incorrect:
            indicators.append(
                TableCellIndicatorModel(
                    id="incorrect",
                    label=f"{entry.incorrect} cooldown assignments were cast outside the window.",
                    tone="warning",
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
                        sortValue=role_priority,
                        tone=role_tone(role),
                    ),
                    "pulls": TableCellModel(value=entry.pulls),
                    "assignments": TableCellModel(value=entry.assignments),
                    "correct": TableCellModel(value=entry.correct),
                    "incorrect": TableCellModel(value=entry.incorrect),
                    "missed": TableCellModel(value=entry.missed),
                    "ignored": TableCellModel(value=entry.ignored),
                    "on_time_rate": TableCellModel(
                        value=entry.on_time_rate * 100.0,
                        sortValue=entry.on_time_rate,
                        display=f"{entry.on_time_rate * 100.0:.1f}%",
                    ),
                },
                details=_build_row_details(report_code, entry.events, source_reports=source_reports),
            )
        )
    return rows


def _entries_for_pull(entries: Iterable[CooldownUsageEntry], pull_view_id: str) -> List[CooldownUsageEntry]:
    scoped_entries: List[CooldownUsageEntry] = []
    for entry in entries:
        events = [event for event in entry.events if event.pull_view_id == pull_view_id]
        correct = sum(1 for event in events if event.status == COOLDOWN_STATUS_CORRECT)
        incorrect = sum(1 for event in events if event.status == COOLDOWN_STATUS_INCORRECT)
        missed = sum(1 for event in events if event.status == COOLDOWN_STATUS_MISSED)
        ignored = sum(1 for event in events if _is_ignored_status(event.status))
        checked = correct + incorrect + missed
        deltas = [abs(event.delta_seconds) for event in events if event.delta_seconds is not None]
        pulls = 1 if any(event.status != COOLDOWN_STATUS_IGNORED_NOT_IN_PULL for event in events) else 0
        scoped_entries.append(
            CooldownUsageEntry(
                player=entry.player,
                role=entry.role,
                class_name=entry.class_name,
                pulls=pulls,
                assignments=len(events),
                correct=correct,
                incorrect=incorrect,
                missed=missed,
                ignored=ignored,
                on_time_rate=correct / checked if checked else 0.0,
                average_delta_seconds=sum(deltas) / len(deltas) if deltas else None,
                events=events,
            )
        )
    scoped_entries.sort(
        key=lambda item: (
            item.on_time_rate if (item.correct + item.incorrect + item.missed) else 1.0,
            -item.missed,
            ROLE_PRIORITY.get(item.role or ROLE_UNKNOWN, ROLE_PRIORITY[ROLE_UNKNOWN]),
            item.player.lower(),
        )
    )
    return scoped_entries


def _build_summary_metrics(summary: CooldownUsageSummary) -> List[SummaryMetricModel]:
    return [
        SummaryMetricModel(
            id="pull_count",
            label="Pulls counted",
            value=summary.pull_count,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="assignments_checked",
            label="Assignments checked",
            value=summary.checked_assignments,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="on_time_casts",
            label="On-time casts",
            value=summary.total_correct,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="missed_cooldowns",
            label="Missed cooldowns",
            value=summary.total_missed,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="ignored_assignments",
            label="Ignored assignments",
            value=summary.total_ignored,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="raid_on_time_rate",
            label="Raid on-time",
            value=summary.on_time_rate * 100.0,
            display=f"{summary.on_time_rate * 100.0:.1f}%",
        ),
    ]


def build_lightblinded_vanguard_cooldown_report_page(summary: CooldownUsageSummary) -> ReportPageModel:
    return build_cooldown_usage_report_page(summary)


def _build_header_tags(
    summary: CooldownUsageSummary,
    *,
    fight_name: Optional[str],
    difficulty: Optional[str],
) -> List[HeaderTagModel]:
    fight_label = fight_name or summary.fight_filter or summary.plan.header.name or "Selected fight"
    difficulty_label = difficulty or summary.plan.header.difficulty
    tags = [
        HeaderTagModel(id="fight", label="Fight", value=fight_label),
        HeaderTagModel(id="difficulty", label="Difficulty", value=str(difficulty_label).title()),
        HeaderTagModel(id="encounter", label="Encounter", value=str(summary.plan.header.encounter_id)),
        HeaderTagModel(id="tolerance", label="Tolerance", value=f"+/- {summary.tolerance_seconds:g}s"),
    ]
    if summary.ignore_stasis:
        tags.append(HeaderTagModel(id="ignore_stasis", label="Stasis", value="Ignored"))
    if summary.ignore_after_deaths:
        tags.append(HeaderTagModel(id="ignore_after_deaths", label="Death cutoff", value=f"After {summary.ignore_after_deaths} deaths"))
    if summary.ignore_after_healer_death:
        tags.append(HeaderTagModel(id="ignore_after_healer_death", label="Healer deaths", value="Ignored after first healer death"))
    merged_label = merged_reports_label(summary.source_reports or [summary.report_code])
    if merged_label:
        tags.append(HeaderTagModel(id="merged_reports", label="Reports", value=merged_label))
    return tags


def _build_row_details(
    report_code: str,
    events: List[CooldownUsageEvent],
    *,
    source_reports: List[str],
) -> Optional[RowDetailsModel]:
    if not events:
        return None
    source_order = {code: index for index, code in enumerate(source_reports or [report_code])}
    grouped: Dict[tuple[str, int, int], dict[str, object]] = {}
    for event in sorted(events, key=lambda item: (item.source_report_code or "", item.pull_index, item.fight_id, item.scheduled_offset_ms or 0.0)):
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
        duration = format_duration(bucket["pull_duration_ms"])
        subtitle_parts: List[str] = []
        if duration:
            subtitle_parts.append(f"Duration {duration}")
        fight_name = bucket["fight_name"] or None
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


def _build_event_item(event: CooldownUsageEvent, index: int) -> RowDetailItemModel:
    status_label = _status_label(event.status)
    badges = [status_label]
    if event.boss_spell_id is not None:
        boss_label = event.boss_ability_label or str(event.boss_spell_id)
        badges.append(f"Boss {boss_label}")
    if event.intended_target:
        badges.append(f"Target {event.intended_target}")
        if event.target_was_alive is False:
            badges.append("Target dead")
    if event.target_mismatch:
        badges.append("Target mismatch")
    if event.ignore_reason:
        badges.append(_ignore_reason_label(event.ignore_reason))

    return RowDetailItemModel(
        id=f"cooldown-{event.source_report_code or 'report'}-{event.fight_id}-{event.line_number}-{index}",
        label=status_label,
        kind="cooldown_assignment",
        abilityLabel=event.ability_label or str(event.spell_id),
        abilityHref=_wowhead_spell_url(event.spell_id),
        timestampLabel=format_offset_seconds(event.scheduled_offset_ms),
        description=_event_description(event),
        tone=_event_tone(event.status),
        badges=badges,
    )


def _event_description(event: CooldownUsageEvent) -> str:
    phase_label = f"P{event.phase} + {event.phase_time_seconds:g}s"
    actual_target = f" on {event.actual_target}" if event.actual_target else ""
    target_dead_suffix = (
        f"; intended target {event.intended_target} was dead"
        if event.intended_target and event.target_was_alive is False
        else ""
    )
    if event.status == COOLDOWN_STATUS_CORRECT:
        return f"{phase_label}; cast{actual_target} at {format_offset_seconds(event.actual_offset_ms)} ({_format_signed_delta(event.delta_seconds)}){target_dead_suffix}"
    if event.status == COOLDOWN_STATUS_INCORRECT:
        if event.target_mismatch and event.intended_target:
            actual = event.actual_target or "unknown target"
            return (
                f"{phase_label}; cast on {actual} at {format_offset_seconds(event.actual_offset_ms)} "
                f"({_format_signed_delta(event.delta_seconds)}) instead of {event.intended_target}"
            )
        return f"{phase_label}; cast outside window{actual_target} at {format_offset_seconds(event.actual_offset_ms)} ({_format_signed_delta(event.delta_seconds)}){target_dead_suffix}"
    if event.status == COOLDOWN_STATUS_MISSED:
        return f"{phase_label}; no same-spell cast found"
    if event.status == COOLDOWN_STATUS_IGNORED_DEAD:
        return f"{phase_label}; player was dead"
    if event.status == COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT:
        return f"{phase_label}; after death-count cutoff"
    if event.status == COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH:
        return f"{phase_label}; after healer death"
    if event.status == COOLDOWN_STATUS_IGNORED_AFTER_PULL_END:
        return f"{phase_label}; after pull ended"
    if event.status == COOLDOWN_STATUS_IGNORED_MISSING_PHASE:
        return f"{phase_label}; phase start was not available"
    if event.status == COOLDOWN_STATUS_IGNORED_NOT_IN_PULL:
        return f"{phase_label}; player was not in this pull"
    return phase_label


def _status_label(status: str) -> str:
    labels = {
        COOLDOWN_STATUS_CORRECT: "Correct",
        COOLDOWN_STATUS_INCORRECT: "Incorrect",
        COOLDOWN_STATUS_MISSED: "Missed",
        COOLDOWN_STATUS_IGNORED_DEAD: "Ignored",
        COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT: "Ignored",
        COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH: "Ignored",
        COOLDOWN_STATUS_IGNORED_AFTER_PULL_END: "Ignored",
        COOLDOWN_STATUS_IGNORED_MISSING_PHASE: "Ignored",
        COOLDOWN_STATUS_IGNORED_NOT_IN_PULL: "Ignored",
    }
    return labels.get(status, status.replace("_", " ").title())


def _ignore_reason_label(reason: str) -> str:
    labels = {
        "dead": "Dead",
        "death_count_cutoff": "Death cutoff",
        "healer_death_cutoff": "Healer death",
        "after_pull_end": "After pull end",
        "missing_phase": "Missing phase",
        "not_in_pull": "Not in pull",
    }
    return labels.get(reason, reason.replace("_", " ").title())


def _is_ignored_status(status: str) -> bool:
    return status in {
        COOLDOWN_STATUS_IGNORED_DEAD,
        COOLDOWN_STATUS_IGNORED_AFTER_DEATH_COUNT,
        COOLDOWN_STATUS_IGNORED_AFTER_HEALER_DEATH,
        COOLDOWN_STATUS_IGNORED_AFTER_PULL_END,
        COOLDOWN_STATUS_IGNORED_MISSING_PHASE,
        COOLDOWN_STATUS_IGNORED_NOT_IN_PULL,
    }


def _event_tone(status: str) -> Optional[str]:
    if _is_ignored_status(status):
        return "muted"
    if status == COOLDOWN_STATUS_CORRECT:
        return "success"
    if status in {COOLDOWN_STATUS_INCORRECT, COOLDOWN_STATUS_MISSED}:
        return "danger"
    return None


def _format_signed_delta(value: Optional[float]) -> str:
    if value is None:
        return "no delta"
    return f"{value:+.1f}s"


def _group_sort_key(group_key: tuple[str, int, int], source_order: dict[str, int]) -> tuple[int, int, int]:
    source_report, fight_id, pull = group_key
    return (source_order.get(source_report, len(source_order)), pull, fight_id)


def _wowhead_spell_url(ability_id: Optional[int]) -> Optional[str]:
    if ability_id is None:
        return None
    return f"https://www.wowhead.com/spell={int(ability_id)}"


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_cooldown_usage_report_page",
    "build_lightblinded_vanguard_cooldown_report_page",
]
