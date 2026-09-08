"""UI view model for the Mythic Nek'zali mechanics report."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Sequence, Tuple

from ..nek_zali_the_soulcoiler_mechanics import (
    ADD_DAMAGE_VIEW_ID,
    AddDamageSet,
    CremationCarrier,
    ESSENCE_REND_DISPELS_VIEW_ID,
    EssenceRendApplication,
    EssenceRendSet,
    KILL_SQUADS_VIEW_ID,
    PYRE_SOAKS_VIEW_ID,
    KillSquadEntrant,
    KillSquadSet,
    NekZaliMechanicsSummary,
    PyreSet,
    PyreSoaker,
    REPORT_FOOTNOTES,
    REPORT_ID,
    REPORT_TITLE,
)
from .common import (
    CellKind,
    ContentVariant,
    HeaderTagModel,
    ReportContentModel,
    ReportHeaderModel,
    ReportPageModel,
    RowDetailGroupModel,
    RowDetailBarChartModel,
    RowDetailBarModel,
    RowDetailItemModel,
    RowDetailsModel,
    RowDetailsVariant,
    SortDirection,
    SortModel,
    SummaryMetricModel,
    TableCellIndicatorModel,
    TableCellModel,
    TableCellPlayerModel,
    TableCellTextSegmentModel,
    TableColumnModel,
    TableFilterModel,
    TableFilterOptionModel,
    TableModel,
    TableRowGroupModel,
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
)


AGGREGATE_VIEW_ID = "aggregate"
ESSENCE_REND_BY_SET_VIEW_ID = "essence-rend-by-set"
ESSENCE_REND_BY_HEALER_VIEW_ID = "essence-rend-by-healer"


def build_nek_zali_mechanics_report_page(
    summary: NekZaliMechanicsSummary,
) -> ReportPageModel:
    source_reports = summary.source_reports or [summary.report_code]
    source_order = {code: index for index, code in enumerate(source_reports)}
    rows_by_mechanic = {}
    for view in summary.views:
        set_counts = Counter(
            (mechanic_set.source_report_code, mechanic_set.fight_id)
            for mechanic_set in view.sets
        )
        rows_by_mechanic[view.id] = [
            _build_mechanic_row(
                summary,
                view.id,
                mechanic_set,
                source_order.get(
                    mechanic_set.source_report_code, len(source_order)
                ),
                set_counts[
                    (mechanic_set.source_report_code, mechanic_set.fight_id)
                ],
            )
            for mechanic_set in view.sets
        ]
    default_mechanic = summary.views[0].id if summary.views else "mechanics"
    essence_rend_sets = [
        mechanic_set
        for view in summary.views
        if view.id == ESSENCE_REND_DISPELS_VIEW_ID
        for mechanic_set in view.sets
        if isinstance(mechanic_set, EssenceRendSet)
    ]
    essence_rend_healer_rows = _build_essence_rend_healer_rows(
        summary,
        essence_rend_sets,
        source_order,
    )
    rows_by_combined_view = {
        _combined_view_id(AGGREGATE_VIEW_ID, view.id): rows_by_mechanic[view.id]
        for view in summary.views
    }
    for pull in summary.pulls:
        for view in summary.views:
            rows_by_combined_view[_combined_view_id(pull.view_id, view.id)] = [
                row
                for row, mechanic_set in zip(rows_by_mechanic[view.id], view.sets)
                if mechanic_set.source_report_code == pull.source_report_code
                and mechanic_set.fight_id == pull.fight_id
            ]
    if any(view.id == ESSENCE_REND_DISPELS_VIEW_ID for view in summary.views):
        set_rows = rows_by_mechanic.get(ESSENCE_REND_DISPELS_VIEW_ID, [])
        rows_by_combined_view[
            _combined_sub_view_id(
                AGGREGATE_VIEW_ID,
                ESSENCE_REND_DISPELS_VIEW_ID,
                ESSENCE_REND_BY_SET_VIEW_ID,
            )
        ] = set_rows
        rows_by_combined_view[
            _combined_sub_view_id(
                AGGREGATE_VIEW_ID,
                ESSENCE_REND_DISPELS_VIEW_ID,
                ESSENCE_REND_BY_HEALER_VIEW_ID,
            )
        ] = essence_rend_healer_rows
        for pull in summary.pulls:
            group_id = f"{pull.source_report_code}-fight-{pull.fight_id}"
            rows_by_combined_view[
                _combined_sub_view_id(
                    pull.view_id,
                    ESSENCE_REND_DISPELS_VIEW_ID,
                    ESSENCE_REND_BY_SET_VIEW_ID,
                )
            ] = [
                row
                for row in set_rows
                if row.group is not None and row.group.id == group_id
            ]
            rows_by_combined_view[
                _combined_sub_view_id(
                    pull.view_id,
                    ESSENCE_REND_DISPELS_VIEW_ID,
                    ESSENCE_REND_BY_HEALER_VIEW_ID,
                )
            ] = [
                row
                for row in essence_rend_healer_rows
                if row.group is not None and row.group.id == group_id
            ]
    rows_by_view = {
        AGGREGATE_VIEW_ID: rows_by_mechanic.get(default_mechanic, []),
        **{
            pull.view_id: rows_by_combined_view.get(
                _combined_view_id(pull.view_id, default_mechanic), []
            )
            for pull in summary.pulls
        },
    }
    default_view = next(
        (view for view in summary.views if view.id == default_mechanic), None
    )
    default_sets = list(default_view.sets) if default_view else []
    summary_by_view = {
        AGGREGATE_VIEW_ID: _summary_metrics(
            summary.pull_count, default_mechanic, default_sets
        ),
        **{
            pull.view_id: _summary_metrics(
                1,
                default_mechanic,
                [
                    mechanic_set
                    for mechanic_set in default_sets
                    if mechanic_set.source_report_code == pull.source_report_code
                    and mechanic_set.fight_id == pull.fight_id
                ],
            )
            for pull in summary.pulls
        },
    }
    summary_by_combined_view = {}
    for view in summary.views:
        summary_by_combined_view[
            _combined_view_id(AGGREGATE_VIEW_ID, view.id)
        ] = _summary_metrics(summary.pull_count, view.id, view.sets)
        for pull in summary.pulls:
            summary_by_combined_view[
                _combined_view_id(pull.view_id, view.id)
            ] = _summary_metrics(
                1,
                view.id,
                [
                    mechanic_set
                    for mechanic_set in view.sets
                    if mechanic_set.source_report_code == pull.source_report_code
                    and mechanic_set.fight_id == pull.fight_id
                ],
            )
    tags = [
        HeaderTagModel(id="fight", label="Fight", value=summary.fight_filter),
        HeaderTagModel(id="difficulty", label="Difficulty", value="Mythic"),
    ]
    merged_label = merged_reports_label(source_reports)
    if merged_label:
        tags.append(
            HeaderTagModel(id="merged_reports", label="Reports", value=merged_label)
        )

    return ReportPageModel(
        reportId=REPORT_ID,
        title=REPORT_TITLE,
        reportCode=summary.report_code,
        header=ReportHeaderModel(
            subtitle=f"Report {summary.report_code}",
            tags=tags,
        ),
        summary=summary_by_view[AGGREGATE_VIEW_ID],
        summaryByView=summary_by_view,
        summaryByCombinedView=summary_by_combined_view,
        content=ReportContentModel(
            variant=ContentVariant.TABLE,
            table=TableModel(
                defaultSort=SortModel(columnId="set", direction=SortDirection.ASC),
                defaultSortByView={
                    ESSENCE_REND_BY_HEALER_VIEW_ID: SortModel(
                        columnId="dispels", direction=SortDirection.DESC
                    )
                },
                columns=_kill_squad_columns(),
                columnsByView={
                    KILL_SQUADS_VIEW_ID: _kill_squad_columns(),
                    PYRE_SOAKS_VIEW_ID: _pyre_columns(),
                    ESSENCE_REND_DISPELS_VIEW_ID: _essence_rend_columns(),
                    ESSENCE_REND_BY_SET_VIEW_ID: _essence_rend_columns(),
                    ESSENCE_REND_BY_HEALER_VIEW_ID: (
                        _essence_rend_healer_columns()
                    ),
                    ADD_DAMAGE_VIEW_ID: _add_damage_columns(),
                },
                rows=rows_by_view.get(AGGREGATE_VIEW_ID, []),
                rowsByView=rows_by_view,
                rowsByCombinedView=rows_by_combined_view,
                viewControl=TableViewControlModel(
                    id="pull_scope",
                    label="Pull",
                    defaultValue=AGGREGATE_VIEW_ID,
                    options=[
                        TableViewOptionModel(
                            value=AGGREGATE_VIEW_ID, label="Aggregate"
                        ),
                        *[
                            TableViewOptionModel(value=pull.view_id, label=pull.label)
                            for pull in summary.pulls
                        ],
                    ],
                ),
                secondaryViewControl=TableViewControlModel(
                    id="mechanic",
                    label="Mechanic",
                    defaultValue=default_mechanic,
                    options=[
                        TableViewOptionModel(value=view.id, label=view.label)
                        for view in summary.views
                    ],
                ),
                emptyState="No Kill Squad sets were found in the selected pulls.",
                emptyStateByView={
                    KILL_SQUADS_VIEW_ID: (
                        "No Kill Squad sets were found in the selected pulls."
                    ),
                    PYRE_SOAKS_VIEW_ID: (
                        "No Hungering Pyre casts were found in the selected pulls."
                    ),
                    ESSENCE_REND_DISPELS_VIEW_ID: (
                        "No Essence Rend application waves were found in the "
                        "selected pulls."
                    ),
                    ESSENCE_REND_BY_SET_VIEW_ID: (
                        "No Essence Rend application waves were found in the "
                        "selected pulls."
                    ),
                    ESSENCE_REND_BY_HEALER_VIEW_ID: (
                        "No Essence Rend dispels were found in the selected pulls."
                    ),
                    ADD_DAMAGE_VIEW_ID: (
                        "No Restless Amani or Echo of Jawae damage was found in "
                        "the selected pulls."
                    ),
                },
                columnFilterByView={
                    ESSENCE_REND_BY_SET_VIEW_ID: TableFilterModel(
                        id="essence_rend_columns",
                        label="Optional columns",
                        options=[
                            TableFilterOptionModel(
                                id="start", label="Applied time"
                            ),
                            TableFilterOptionModel(
                                id="players",
                                label="Debuffed players",
                                defaultSelected=False,
                            ),
                            TableFilterOptionModel(
                                id="dispelled", label="Dispelled count"
                            ),
                            TableFilterOptionModel(
                                id="not_dispelled", label="Not dispelled count"
                            ),
                        ],
                    )
                },
                rowFilterByView={
                    ADD_DAMAGE_VIEW_ID: TableFilterModel(
                        id="add_type",
                        label="Add types",
                        options=[
                            TableFilterOptionModel(
                                id="Restless Amani",
                                label="Restless Amani",
                            ),
                            TableFilterOptionModel(
                                id="Echo of Jawae",
                                label="Echo of Jawae",
                            ),
                        ],
                    )
                },
                subViewControlByView={
                    ESSENCE_REND_DISPELS_VIEW_ID: TableViewControlModel(
                        id="essence_rend_breakdown",
                        label="Dispel view",
                        defaultValue=ESSENCE_REND_BY_SET_VIEW_ID,
                        options=[
                            TableViewOptionModel(
                                value=ESSENCE_REND_BY_SET_VIEW_ID,
                                label="By set",
                            ),
                            TableViewOptionModel(
                                value=ESSENCE_REND_BY_HEALER_VIEW_ID,
                                label="By healer",
                            ),
                        ],
                    )
                },
            )
        ),
        footnotes=list(REPORT_FOOTNOTES),
    )


def _combined_view_id(pull_view_id: str, mechanic_id: str) -> str:
    return f"{pull_view_id}::{mechanic_id}"


def _combined_sub_view_id(
    pull_view_id: str, mechanic_id: str, sub_view_id: str
) -> str:
    return f"{pull_view_id}::{mechanic_id}::{sub_view_id}"


def _summary_metrics(
    pull_count: int,
    mechanic_id: str,
    mechanic_sets: Sequence[
        KillSquadSet | PyreSet | EssenceRendSet | AddDamageSet
    ],
) -> List[SummaryMetricModel]:
    if mechanic_id == ADD_DAMAGE_VIEW_ID:
        add_sets = [
            mechanic_set
            for mechanic_set in mechanic_sets
            if isinstance(mechanic_set, AddDamageSet)
        ]
        return [
            SummaryMetricModel(
                id="pull_count",
                label="Pulls counted",
                value=pull_count,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="add_sets",
                label="Add sets",
                value=len(add_sets),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="amani_sets",
                label="Amani sets",
                value=sum(
                    add_set.add_name == "Restless Amani" for add_set in add_sets
                ),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="jawae_sets",
                label="Jawae sets",
                value=sum(
                    add_set.add_name == "Echo of Jawae" for add_set in add_sets
                ),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="adds_observed",
                label="Adds observed",
                value=sum(add_set.add_count for add_set in add_sets),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="total_add_damage",
                label="Total add damage",
                value=sum(add_set.total_damage for add_set in add_sets),
                format=ValueFormat.INTEGER,
            ),
        ]

    if mechanic_id == ESSENCE_REND_DISPELS_VIEW_ID:
        rend_sets = [
            mechanic_set
            for mechanic_set in mechanic_sets
            if isinstance(mechanic_set, EssenceRendSet)
        ]
        applications = [
            application
            for rend_set in rend_sets
            for application in rend_set.applications
        ]
        dispelled = [
            application for application in applications if application.was_dispelled
        ]
        average_dispel_seconds = (
            sum(application.dispel_delay_ms or 0 for application in dispelled)
            / len(dispelled)
            / 1_000.0
            if dispelled
            else 0.0
        )
        return [
            SummaryMetricModel(
                id="pull_count",
                label="Pulls counted",
                value=pull_count,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="essence_rend_sets",
                label="Essence Rend sets",
                value=len(rend_sets),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="debuffs_applied",
                label="Debuffs applied",
                value=len(applications),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="dispelled",
                label="Dispelled",
                value=len(dispelled),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="not_dispelled",
                label="Not dispelled",
                value=len(applications) - len(dispelled),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="average_dispel_time",
                label="Avg dispel time (sec)",
                value=round(average_dispel_seconds, 2),
                format=ValueFormat.DECIMAL,
                precision=2,
            ),
        ]

    if mechanic_id == PYRE_SOAKS_VIEW_ID:
        pyre_sets = [
            mechanic_set
            for mechanic_set in mechanic_sets
            if isinstance(mechanic_set, PyreSet)
        ]
        soakers = [soaker for pyre_set in pyre_sets for soaker in pyre_set.soakers]
        return [
            SummaryMetricModel(
                id="pull_count",
                label="Pulls counted",
                value=pull_count,
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="pyre_sets",
                label="Pyre casts",
                value=len(pyre_sets),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="soaks",
                label="Soak events",
                value=len(soakers),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="cremation_carriers",
                label="Cremation carriers",
                value=sum(len(pyre_set.cremation_carriers) for pyre_set in pyre_sets),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="corpse_opportunities",
                label="Corpse opportunities",
                value=sum(pyre_set.corpse_opportunity_count for pyre_set in pyre_sets),
                format=ValueFormat.INTEGER,
            ),
            SummaryMetricModel(
                id="confirmed_misses",
                label="Confirmed misses",
                value=sum(pyre_set.confirmed_miss_count for pyre_set in pyre_sets),
                format=ValueFormat.INTEGER,
            ),
        ]

    kill_sets = [
        mechanic_set
        for mechanic_set in mechanic_sets
        if isinstance(mechanic_set, KillSquadSet)
    ]
    entries = [entrant for kill_set in kill_sets for entrant in kill_set.entrants]
    return [
        SummaryMetricModel(
            id="pull_count",
            label="Pulls counted",
            value=pull_count,
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="sets",
            label="Kill Squad sets",
            value=len(kill_sets),
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="entries",
            label="Downstairs entries",
            value=len(entries),
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="exhausted_entries",
            label="Entries with exhaustion",
            value=sum(entrant.entered_exhausted for entrant in entries),
            format=ValueFormat.INTEGER,
        ),
        SummaryMetricModel(
            id="unusual_sets",
            label="Sets not exactly five",
            value=sum(len(kill_set.entrants) != 5 for kill_set in kill_sets),
            format=ValueFormat.INTEGER,
        ),
    ]


def _kill_squad_columns() -> List[TableColumnModel]:
    return [
        _column("set", "Set", CellKind.TEXT, TextAlign.LEFT),
        _column("start", "Started", CellKind.TEXT, TextAlign.LEFT),
        _column("players", "Who went down", CellKind.PLAYER_LIST, TextAlign.LEFT),
        _column("entrants", "Entrants", CellKind.NUMBER, TextAlign.RIGHT),
        _column("exhausted", "Exhausted", CellKind.NUMBER, TextAlign.RIGHT),
    ]


def _pyre_columns() -> List[TableColumnModel]:
    return [
        _column("set", "Pyre", CellKind.TEXT, TextAlign.LEFT),
        _column("start", "Impact", CellKind.TEXT, TextAlign.LEFT),
        _column("players", "Who soaked", CellKind.PLAYER_LIST, TextAlign.LEFT),
        _column(
            "cremation_carriers",
            "Cremation carriers",
            CellKind.PLAYER_LIST,
            TextAlign.LEFT,
        ),
        _column("soakers", "Soakers", CellKind.NUMBER, TextAlign.RIGHT),
        _column(
            "corpse_opportunities",
            "Corpse opportunities",
            CellKind.NUMBER,
            TextAlign.RIGHT,
        ),
        _column(
            "confirmed_misses",
            "Confirmed misses",
            CellKind.NUMBER,
            TextAlign.RIGHT,
        ),
    ]


def _essence_rend_columns() -> List[TableColumnModel]:
    return [
        _column("set", "Rend", CellKind.TEXT, TextAlign.LEFT),
        _column("start", "Applied", CellKind.TEXT, TextAlign.LEFT),
        _column("players", "Debuffed players", CellKind.PLAYER_LIST, TextAlign.LEFT),
        _column("dispels", "Who dispelled and when", CellKind.PLAYER_LIST, TextAlign.LEFT),
        _column("dispelled", "Dispelled", CellKind.NUMBER, TextAlign.RIGHT),
        _column("not_dispelled", "Not dispelled", CellKind.NUMBER, TextAlign.RIGHT),
    ]


def _essence_rend_healer_columns() -> List[TableColumnModel]:
    return [
        TableColumnModel(
            id="dispels",
            label="Dispels",
            align=TextAlign.LEFT,
            sortable=True,
            cellKind=CellKind.RELATIVE_BAR,
            format=ValueFormat.INTEGER,
        ),
    ]


def _add_damage_columns() -> List[TableColumnModel]:
    return [
        _column("set", "Set", CellKind.TEXT, TextAlign.LEFT),
        _column("start", "First damage", CellKind.TEXT, TextAlign.LEFT),
        _column("add_type", "Add type", CellKind.TEXT, TextAlign.LEFT),
        _column("players", "Who damaged", CellKind.PLAYER_LIST, TextAlign.LEFT),
        _column("adds", "Adds", CellKind.NUMBER, TextAlign.RIGHT),
        _column("total_damage", "Damage", CellKind.NUMBER, TextAlign.RIGHT),
    ]


def _column(
    column_id: str,
    label: str,
    cell_kind: CellKind,
    align: TextAlign,
) -> TableColumnModel:
    return TableColumnModel(
        id=column_id,
        label=label,
        align=align,
        sortable=cell_kind != CellKind.PLAYER_LIST,
        cellKind=cell_kind,
        format=ValueFormat.INTEGER if cell_kind == CellKind.NUMBER else None,
    )


def _build_mechanic_row(
    summary: NekZaliMechanicsSummary,
    mechanic_id: str,
    mechanic_set: KillSquadSet | PyreSet | EssenceRendSet | AddDamageSet,
    source_index: int,
    set_count: int,
) -> TableRowModel:
    if mechanic_id == PYRE_SOAKS_VIEW_ID and isinstance(mechanic_set, PyreSet):
        return _build_pyre_row(summary, mechanic_set, source_index, set_count)
    if mechanic_id == ESSENCE_REND_DISPELS_VIEW_ID and isinstance(
        mechanic_set, EssenceRendSet
    ):
        return _build_essence_rend_row(
            summary, mechanic_set, source_index, set_count
        )
    if mechanic_id == ADD_DAMAGE_VIEW_ID and isinstance(
        mechanic_set, AddDamageSet
    ):
        return _build_add_damage_row(
            summary, mechanic_set, source_index, set_count
        )
    if isinstance(mechanic_set, KillSquadSet):
        return _build_kill_squad_row(
            summary, mechanic_set, source_index, set_count
        )
    raise ValueError(f"Unsupported mechanic set for view {mechanic_id!r}")


def _build_essence_rend_healer_rows(
    summary: NekZaliMechanicsSummary,
    rend_sets: Sequence[EssenceRendSet],
    source_order: Dict[str, int],
) -> List[TableRowModel]:
    counts: Counter[Tuple[str, int, int, float, str, str | None]] = Counter()
    aggregate_counts: Counter[str] = Counter()
    healer_classes: Dict[str, str | None] = {}
    pull_dispel_counts: Counter[Tuple[str, int]] = Counter()
    pull_healers: Dict[Tuple[str, int], set[str]] = {}
    for rend_set in rend_sets:
        pull_key = (rend_set.source_report_code, rend_set.fight_id)
        for application in rend_set.applications:
            if not application.was_dispelled or not application.dispeller:
                continue
            key = (
                rend_set.source_report_code,
                rend_set.fight_id,
                rend_set.pull_index,
                rend_set.pull_duration_ms,
                application.dispeller,
                application.dispeller_class_name,
            )
            counts[key] += 1
            aggregate_counts[application.dispeller] += 1
            if (
                application.dispeller not in healer_classes
                or application.dispeller_class_name
            ):
                healer_classes[application.dispeller] = application.dispeller_class_name
            pull_dispel_counts[pull_key] += 1
            pull_healers.setdefault(pull_key, set()).add(application.dispeller)

    rows: List[TableRowModel] = []
    aggregate_maximum = max(aggregate_counts.values(), default=0)
    aggregate_total = sum(aggregate_counts.values())
    aggregate_healer_count = len(aggregate_counts)
    aggregate_pull_count = len(pull_dispel_counts)
    for healer, dispel_count in sorted(
        aggregate_counts.items(), key=lambda item: (-item[1], item[0])
    ):
        rows.append(
            TableRowModel(
                id=f"all-pulls-essence-rend-healer-{healer}",
                cells={
                    "dispels": TableCellModel(
                        value=dispel_count,
                        label=healer,
                        unitLabel="dispels",
                        maxValue=aggregate_maximum,
                        colorToken=class_color_token(healer_classes.get(healer)),
                    ),
                },
                group=TableRowGroupModel(
                    id="all-pulls",
                    label="All pulls",
                    subtitle=(
                        f"{aggregate_total} "
                        f"{'dispel' if aggregate_total == 1 else 'dispels'} by "
                        f"{aggregate_healer_count} "
                        f"{'healer' if aggregate_healer_count == 1 else 'healers'} across "
                        f"{aggregate_pull_count} "
                        f"{'pull' if aggregate_pull_count == 1 else 'pulls'}"
                    ),
                    sortValue=-1,
                ),
            )
        )

    pull_maximums: Dict[Tuple[str, int], int] = {}
    for key, dispel_count in counts.items():
        pull_key = (key[0], key[1])
        pull_maximums[pull_key] = max(
            pull_maximums.get(pull_key, 0), dispel_count
        )
    multiple_reports = len(summary.source_reports) > 1
    for key, dispel_count in sorted(
        counts.items(),
        key=lambda item: (
            source_order.get(item[0][0], len(source_order)),
            item[0][2],
            -item[1],
            item[0][4],
        ),
    ):
        (
            report_code,
            fight_id,
            pull_index,
            pull_duration_ms,
            healer,
            class_name,
        ) = key
        pull_key = (report_code, fight_id)
        pull_label = f"Pull {pull_index}"
        if multiple_reports:
            pull_label = f"{report_code} {pull_label}"
        healer_count = len(pull_healers.get(pull_key, set()))
        pull_sort = (
            source_order.get(report_code, len(source_order)) * 1_000_000
            + pull_index * 1_000
        )
        rows.append(
            TableRowModel(
                id=f"{report_code}-fight-{fight_id}-essence-rend-healer-{healer}",
                cells={
                    "dispels": TableCellModel(
                        value=dispel_count,
                        label=healer,
                        unitLabel="dispels",
                        maxValue=pull_maximums[pull_key],
                        colorToken=class_color_token(class_name),
                    ),
                },
                group=TableRowGroupModel(
                    id=f"{report_code}-fight-{fight_id}",
                    label=pull_label,
                    subtitle=(
                        f"{pull_dispel_counts[pull_key]} "
                        f"{'dispel' if pull_dispel_counts[pull_key] == 1 else 'dispels'} by "
                        f"{healer_count} "
                        f"{'healer' if healer_count == 1 else 'healers'} - "
                        f"{format_duration(pull_duration_ms)} - Fight {fight_id}"
                    ),
                    href=build_pull_link(report_code, fight_id),
                    sortValue=pull_sort,
                ),
            )
        )
    return rows


def _build_add_damage_row(
    summary: NekZaliMechanicsSummary,
    add_set: AddDamageSet,
    source_index: int,
    set_count: int,
) -> TableRowModel:
    multiple_reports = len(summary.source_reports) > 1
    pull_label = f"Pull {add_set.pull_index}"
    if multiple_reports:
        pull_label = f"{add_set.source_report_code} {pull_label}"
    pull_sort = source_index * 1_000_000 + add_set.pull_index * 1_000
    player_names = [
        contribution.player for contribution in add_set.damage_contributions
    ]
    return TableRowModel(
        id=(
            f"{add_set.source_report_code}-fight-{add_set.fight_id}-"
            f"add-damage-{add_set.set_index}"
        ),
        cells={
            "set": TableCellModel(
                value=f"Set {add_set.set_index}", sortValue=add_set.set_index
            ),
            "start": TableCellModel(
                value=add_set.start_offset_ms,
                display=format_offset_seconds(add_set.start_offset_ms),
                sortValue=add_set.start_offset_ms,
            ),
            "add_type": TableCellModel(value=add_set.add_name),
            "players": TableCellModel(
                value=", ".join(player_names),
                players=[
                    TableCellPlayerModel(
                        name=contribution.player,
                        colorToken=class_color_token(contribution.class_name),
                        tooltip=f"{contribution.damage:,.0f} damage",
                    )
                    for contribution in add_set.damage_contributions
                ],
            ),
            "adds": TableCellModel(value=add_set.add_count),
            "total_damage": TableCellModel(value=add_set.total_damage),
        },
        details=_build_add_damage_details(add_set),
        group=TableRowGroupModel(
            id=f"{add_set.source_report_code}-fight-{add_set.fight_id}",
            label=pull_label,
            subtitle=(
                f"{set_count} add {'set' if set_count == 1 else 'sets'} - "
                f"{format_duration(add_set.pull_duration_ms)} - "
                f"Fight {add_set.fight_id}"
            ),
            href=build_pull_link(add_set.source_report_code, add_set.fight_id),
            sortValue=pull_sort,
        ),
    )


def _build_add_damage_details(add_set: AddDamageSet) -> RowDetailsModel:
    return RowDetailsModel(
        variant=RowDetailsVariant.EVENT_GROUPS,
        groups=[
            RowDetailGroupModel(
                id=(
                    f"{add_set.source_report_code}-fight-{add_set.fight_id}-"
                    f"add-damage-{add_set.set_index}"
                ),
                title=f"Pull {add_set.pull_index} - Add Set {add_set.set_index}",
                subtitle=(
                    f"{add_set.add_name} - first damage "
                    f"{format_offset_seconds(add_set.start_offset_ms)} - "
                    f"window {add_set.duration_ms / 1000.0:.2f}s - "
                    f"Fight {add_set.fight_id}"
                ),
                link=build_pull_link(add_set.source_report_code, add_set.fight_id),
                items=[
                    RowDetailItemModel(
                        id=(
                            f"{add_set.source_report_code}-{add_set.fight_id}-"
                            f"{add_set.set_index}-add-summary"
                        ),
                        label=(
                            f"{add_set.add_count} "
                            f"{'add' if add_set.add_count == 1 else 'adds'} observed"
                        ),
                        description=(
                            f"Logged damage ran through "
                            f"{format_offset_seconds(add_set.end_offset_ms)} for "
                            f"{add_set.total_damage:,.0f} total damage."
                        ),
                    )
                ],
            )
        ],
        barChart=RowDetailBarChartModel(
            title=f"{add_set.add_name} damage",
            subtitle=(
                "Damage during this add set, scaled relative to the highest "
                "contributor."
            ),
            bars=[
                RowDetailBarModel(
                    id=(
                        f"{add_set.source_report_code}-{add_set.fight_id}-"
                        f"{add_set.set_index}-add-damage-{index}"
                    ),
                    label=contribution.player,
                    value=contribution.damage,
                    display=f"{contribution.damage:,.0f}",
                    colorToken=class_color_token(contribution.class_name),
                )
                for index, contribution in enumerate(
                    add_set.damage_contributions, start=1
                )
            ],
        ),
    )


def _build_kill_squad_row(
    summary: NekZaliMechanicsSummary,
    kill_set: KillSquadSet,
    source_index: int,
    set_count: int,
) -> TableRowModel:
    multiple_reports = len(summary.source_reports) > 1
    pull_label = f"Pull {kill_set.pull_index}"
    if multiple_reports:
        pull_label = f"{kill_set.source_report_code} {pull_label}"
    player_names = [entrant.player for entrant in kill_set.entrants]
    pull_sort = source_index * 1_000_000 + kill_set.pull_index * 1_000
    return TableRowModel(
        id=(
            f"{kill_set.source_report_code}-fight-{kill_set.fight_id}-"
            f"kill-squad-{kill_set.set_index}"
        ),
        cells={
            "set": TableCellModel(
                value=f"Set {kill_set.set_index}", sortValue=kill_set.set_index
            ),
            "start": TableCellModel(
                value=kill_set.start_offset_ms,
                display=format_offset_seconds(kill_set.start_offset_ms),
                sortValue=kill_set.start_offset_ms,
            ),
            "players": TableCellModel(
                value=", ".join(player_names) if player_names else "No entrants observed",
                players=[_build_player_cell(entrant) for entrant in kill_set.entrants],
            ),
            "entrants": TableCellModel(value=len(kill_set.entrants)),
            "exhausted": TableCellModel(value=kill_set.exhausted_count),
        },
        details=_build_set_details(kill_set),
        group=TableRowGroupModel(
            id=f"{kill_set.source_report_code}-fight-{kill_set.fight_id}",
            label=pull_label,
            subtitle=(
                f"{set_count} {'set' if set_count == 1 else 'sets'} - "
                f"{format_duration(kill_set.pull_duration_ms)} - Fight {kill_set.fight_id}"
            ),
            href=build_pull_link(kill_set.source_report_code, kill_set.fight_id),
            sortValue=pull_sort,
        ),
    )


def _build_pyre_row(
    summary: NekZaliMechanicsSummary,
    pyre_set: PyreSet,
    source_index: int,
    set_count: int,
) -> TableRowModel:
    multiple_reports = len(summary.source_reports) > 1
    pull_label = f"Pull {pyre_set.pull_index}"
    if multiple_reports:
        pull_label = f"{pyre_set.source_report_code} {pull_label}"
    player_names = [soaker.player for soaker in pyre_set.soakers]
    carrier_names = [carrier.player for carrier in pyre_set.cremation_carriers]
    pull_sort = source_index * 1_000_000 + pyre_set.pull_index * 1_000
    return TableRowModel(
        id=(
            f"{pyre_set.source_report_code}-fight-{pyre_set.fight_id}-"
            f"pyre-{pyre_set.set_index}"
        ),
        cells={
            "set": TableCellModel(
                value=f"Pyre {pyre_set.set_index}", sortValue=pyre_set.set_index
            ),
            "start": TableCellModel(
                value=pyre_set.impact_offset_ms,
                display=format_offset_seconds(pyre_set.impact_offset_ms),
                sortValue=pyre_set.impact_offset_ms,
            ),
            "players": TableCellModel(
                value=(
                    ", ".join(player_names)
                    if player_names
                    else "No soakers observed"
                ),
                players=[_build_pyre_player_cell(soaker) for soaker in pyre_set.soakers],
            ),
            "cremation_carriers": TableCellModel(
                value=(
                    ", ".join(carrier_names)
                    if carrier_names
                    else "No carriers observed"
                ),
                players=[
                    _build_cremation_carrier_cell(carrier)
                    for carrier in pyre_set.cremation_carriers
                ],
            ),
            "soakers": TableCellModel(value=len(pyre_set.soakers)),
            "corpse_opportunities": TableCellModel(
                value=pyre_set.corpse_opportunity_count
            ),
            "confirmed_misses": TableCellModel(
                value=pyre_set.confirmed_miss_count,
                tone="danger" if pyre_set.confirmed_miss_count else "success",
            ),
        },
        details=_build_pyre_details(pyre_set),
        group=TableRowGroupModel(
            id=f"{pyre_set.source_report_code}-fight-{pyre_set.fight_id}",
            label=pull_label,
            subtitle=(
                f"{set_count} {'Pyre' if set_count == 1 else 'Pyres'} - "
                f"{format_duration(pyre_set.pull_duration_ms)} - "
                f"Fight {pyre_set.fight_id}"
            ),
            href=build_pull_link(pyre_set.source_report_code, pyre_set.fight_id),
            sortValue=pull_sort,
        ),
    )


def _build_essence_rend_row(
    summary: NekZaliMechanicsSummary,
    rend_set: EssenceRendSet,
    source_index: int,
    set_count: int,
) -> TableRowModel:
    multiple_reports = len(summary.source_reports) > 1
    pull_label = f"Pull {rend_set.pull_index}"
    if multiple_reports:
        pull_label = f"{rend_set.source_report_code} {pull_label}"
    pull_sort = source_index * 1_000_000 + rend_set.pull_index * 1_000
    player_names = [application.player for application in rend_set.applications]
    dispel_labels = [
        (
            f"{application.dispeller} · "
            f"{format_offset_seconds(application.dispel_offset_ms)} → "
            f"{application.player}"
        )
        for application in rend_set.applications
        if application.was_dispelled
    ]
    return TableRowModel(
        id=(
            f"{rend_set.source_report_code}-fight-{rend_set.fight_id}-"
            f"essence-rend-{rend_set.set_index}"
        ),
        cells={
            "set": TableCellModel(
                value=f"Rend {rend_set.set_index}", sortValue=rend_set.set_index
            ),
            "start": TableCellModel(
                value=rend_set.application_offset_ms,
                display=format_offset_seconds(rend_set.application_offset_ms),
                sortValue=rend_set.application_offset_ms,
            ),
            "players": TableCellModel(
                value=", ".join(player_names),
                players=[
                    _build_essence_rend_target_cell(application)
                    for application in rend_set.applications
                ],
            ),
            "dispels": TableCellModel(
                value=(
                    ", ".join(dispel_labels)
                    if dispel_labels
                    else "No dispels logged"
                ),
                players=[
                    _build_essence_rend_dispel_cell(application)
                    for application in rend_set.applications
                    if application.was_dispelled
                ],
            ),
            "dispelled": TableCellModel(value=rend_set.dispelled_count),
            "not_dispelled": TableCellModel(
                value=rend_set.undispelled_count,
                tone="warning" if rend_set.undispelled_count else "success",
            ),
        },
        details=_build_essence_rend_details(rend_set),
        group=TableRowGroupModel(
            id=f"{rend_set.source_report_code}-fight-{rend_set.fight_id}",
            label=pull_label,
            subtitle=(
                f"{set_count} Essence Rend "
                f"{'set' if set_count == 1 else 'sets'} - "
                f"{format_duration(rend_set.pull_duration_ms)} - "
                f"Fight {rend_set.fight_id}"
            ),
            href=build_pull_link(rend_set.source_report_code, rend_set.fight_id),
            sortValue=pull_sort,
        ),
    )


def _build_essence_rend_target_cell(
    application: EssenceRendApplication,
) -> TableCellPlayerModel:
    status = (
        f"dispelled by {application.dispeller} at "
        f"{format_offset_seconds(application.dispel_offset_ms)}"
        if application.was_dispelled
        else "no dispel was logged"
    )
    return TableCellPlayerModel(
        name=application.player,
        colorToken=class_color_token(application.class_name),
        tone=None if application.was_dispelled else "warning",
        tooltip=(
            f"Essence Rend applied at "
            f"{format_offset_seconds(application.application_offset_ms)}; {status}"
        ),
    )


def _build_essence_rend_dispel_cell(
    application: EssenceRendApplication,
) -> TableCellPlayerModel:
    return TableCellPlayerModel(
        name=(
            f"{application.dispeller} · "
            f"{format_offset_seconds(application.dispel_offset_ms)} → "
            f"{application.player}"
        ),
        colorToken=class_color_token(application.dispeller_class_name),
        segments=[
            TableCellTextSegmentModel(
                text=str(application.dispeller),
                colorToken=class_color_token(application.dispeller_class_name),
            ),
            TableCellTextSegmentModel(
                text=(
                    f" · {format_offset_seconds(application.dispel_offset_ms)} → "
                )
            ),
            TableCellTextSegmentModel(
                text=application.player,
                colorToken=class_color_token(application.class_name),
            ),
        ],
        tooltip=(
            f"Dispelled {application.player} "
            f"{(application.dispel_delay_ms or 0) / 1000.0:.2f}s after application"
        ),
    )


def _build_essence_rend_details(rend_set: EssenceRendSet) -> RowDetailsModel:
    items = [
        _build_essence_rend_detail(rend_set, application, index)
        for index, application in enumerate(rend_set.applications, start=1)
    ]
    return RowDetailsModel(
        variant=RowDetailsVariant.EVENT_GROUPS,
        groups=[
            RowDetailGroupModel(
                id=(
                    f"{rend_set.source_report_code}-fight-{rend_set.fight_id}-"
                    f"essence-rend-{rend_set.set_index}"
                ),
                title=(
                    f"Pull {rend_set.pull_index} - Essence Rend Set "
                    f"{rend_set.set_index}"
                ),
                subtitle=(
                    f"Applied {format_offset_seconds(rend_set.application_offset_ms)} - "
                    f"{rend_set.dispelled_count}/{len(rend_set.applications)} "
                    f"dispelled - Fight {rend_set.fight_id}"
                ),
                link=build_pull_link(rend_set.source_report_code, rend_set.fight_id),
                items=items,
            )
        ],
    )


def _build_essence_rend_detail(
    rend_set: EssenceRendSet,
    application: EssenceRendApplication,
    index: int,
) -> RowDetailItemModel:
    if application.was_dispelled:
        description = (
            f"dispelled by {application.dispeller} at "
            f"{format_offset_seconds(application.dispel_offset_ms)} "
            f"({(application.dispel_delay_ms or 0) / 1000.0:.2f}s after application)"
        )
        badges = [
            f"Dispeller: {application.dispeller}",
            f"Dispel: {format_offset_seconds(application.dispel_offset_ms)}",
        ]
        tone = "success"
    elif application.removal_offset_ms is not None:
        duration_ms = max(
            (application.removal_timestamp or application.application_timestamp)
            - application.application_timestamp,
            0.0,
        )
        description = (
            "was not dispelled; the aura ended at "
            f"{format_offset_seconds(application.removal_offset_ms)} "
            f"after {duration_ms / 1000.0:.2f}s"
        )
        badges = [
            "Not dispelled",
            f"Aura removed: {format_offset_seconds(application.removal_offset_ms)}",
        ]
        tone = "warning"
    else:
        description = "had no logged dispel or aura-removal event"
        badges = ["Not dispelled", "Aura removal not logged"]
        tone = "warning"
    return RowDetailItemModel(
        id=(
            f"{rend_set.source_report_code}-{rend_set.fight_id}-"
            f"{rend_set.set_index}-essence-rend-{index}"
        ),
        label=application.player,
        kind="ability_event",
        abilityLabel="Essence Rend",
        abilityHref="https://www.wowhead.com/spell=1287434/essence-rend",
        timestampLabel=format_offset_seconds(application.application_offset_ms),
        description=description,
        badges=badges,
        tone=tone,
    )


def _build_pyre_player_cell(soaker: PyreSoaker) -> TableCellPlayerModel:
    indicators: List[TableCellIndicatorModel] = []
    if soaker.died:
        indicators.append(
            TableCellIndicatorModel(
                id="death",
                label=(
                    "Killed by Hungering Pyre at "
                    f"{format_offset_seconds(soaker.death_offset_ms)}"
                ),
                tone="danger",
                icon="skull",
            )
        )
    return TableCellPlayerModel(
        name=soaker.player,
        colorToken=class_color_token(soaker.class_name),
        tone="danger" if soaker.died else None,
        tooltip=(
            f"Soaked at {format_offset_seconds(soaker.offset_ms)} - "
            f"{soaker.damage:,.0f} damage taken"
        ),
        indicators=indicators,
    )


def _build_cremation_carrier_cell(
    carrier: CremationCarrier,
) -> TableCellPlayerModel:
    removal = (
        f"cleared at {format_offset_seconds(carrier.removal_offset_ms)}"
        if carrier.removal_offset_ms is not None
        else f"expected duration {format_duration(carrier.duration_ms)}"
    )
    return TableCellPlayerModel(
        name=carrier.player,
        colorToken=class_color_token(carrier.class_name),
        tone="warning",
        tooltip=(
            f"{carrier.ability_name} applied at "
            f"{format_offset_seconds(carrier.application_offset_ms)}; {removal}"
        ),
    )


def _build_pyre_details(pyre_set: PyreSet) -> RowDetailsModel:
    if pyre_set.soakers:
        soak_items = [
            RowDetailItemModel(
                id=(
                    f"{pyre_set.source_report_code}-{pyre_set.fight_id}-"
                    f"{pyre_set.set_index}-soaker-{index}"
                ),
                label=soaker.player,
                kind="ability_event",
                abilityLabel="Hungering Pyre soak",
                abilityHref="https://www.wowhead.com/spell=1289855/hungering-pyre",
                timestampLabel=format_offset_seconds(soaker.offset_ms),
                description=f"took {soaker.damage:,.0f} damage",
                badges=(
                    ["Killed by Hungering Pyre"] if soaker.died else []
                ),
                tone="danger" if soaker.died else "success",
            )
            for index, soaker in enumerate(pyre_set.soakers, start=1)
        ]
    else:
        soak_items = [
            RowDetailItemModel(
                id=(
                    f"{pyre_set.source_report_code}-{pyre_set.fight_id}-"
                    f"{pyre_set.set_index}-empty"
                ),
                label="No soakers observed",
                description=(
                    "The Hungering Pyre cast completed without a matching friendly "
                    "player damage event."
                ),
                tone="warning",
            )
        ]
    if pyre_set.cremation_carriers:
        carrier_items = [
            RowDetailItemModel(
                id=(
                    f"{pyre_set.source_report_code}-{pyre_set.fight_id}-"
                    f"{pyre_set.set_index}-carrier-{index}"
                ),
                label=carrier.player,
                kind="ability_event",
                abilityLabel=carrier.ability_name,
                abilityHref=(
                    "https://www.wowhead.com/spell=1294933/slithering-flame"
                    if carrier.ability_name == "Slithering Flame"
                    else "https://www.wowhead.com/spell=1289875/cremation"
                ),
                timestampLabel=format_offset_seconds(
                    carrier.application_offset_ms
                ),
                description=(
                    f"carried the corpse-burning aura for "
                    f"{format_duration(carrier.duration_ms)}"
                ),
                badges=[
                    (
                        "Removed: "
                        + format_offset_seconds(carrier.removal_offset_ms)
                        if carrier.removal_offset_ms is not None
                        else "Removal was not logged"
                    )
                ],
                tone="warning",
            )
            for index, carrier in enumerate(
                pyre_set.cremation_carriers, start=1
            )
        ]
    else:
        carrier_items = [
            RowDetailItemModel(
                id=(
                    f"{pyre_set.source_report_code}-{pyre_set.fight_id}-"
                    f"{pyre_set.set_index}-no-carriers"
                ),
                label="No Cremation carriers observed",
                description=(
                    "No Slithering Flame or Cremation aura application was "
                    "matched to this Pyre."
                ),
                tone="warning",
            )
        ]

    miss_badges = [
        (
            f"Vessel {miss.source_instance} active at "
            f"{format_offset_seconds(miss.offset_ms)}"
            if miss.source_instance is not None
            else f"Vessel active at {format_offset_seconds(miss.offset_ms)}"
        )
        for miss in pyre_set.confirmed_misses
    ]
    corpse_items = [
        RowDetailItemModel(
            id=(
                f"{pyre_set.source_report_code}-{pyre_set.fight_id}-"
                f"{pyre_set.set_index}-corpse-opportunities"
            ),
            label=f"{pyre_set.corpse_opportunity_count} corpse opportunities",
            description=(
                "Unique Restless Amani deaths assigned to this Pyre's "
                "corpse-burning window."
            ),
        ),
        RowDetailItemModel(
            id=(
                f"{pyre_set.source_report_code}-{pyre_set.fight_id}-"
                f"{pyre_set.set_index}-confirmed-misses"
            ),
            label=f"{pyre_set.confirmed_miss_count} confirmed missed",
            description=(
                "Distinct Amani instances that later produced Vessel of "
                "Awakening damage before the next Pyre."
            ),
            badges=miss_badges,
            tone="danger" if pyre_set.confirmed_miss_count else "success",
        ),
    ]
    return RowDetailsModel(
        variant=RowDetailsVariant.EVENT_GROUPS,
        groups=[
            RowDetailGroupModel(
                id=(
                    f"{pyre_set.source_report_code}-fight-{pyre_set.fight_id}-"
                    f"pyre-{pyre_set.set_index}"
                ),
                title=f"Pull {pyre_set.pull_index} - Pyre {pyre_set.set_index}",
                subtitle=(
                    f"Impact {format_offset_seconds(pyre_set.impact_offset_ms)} - "
                    f"{len(pyre_set.soakers)} "
                    f"{'soaker' if len(pyre_set.soakers) == 1 else 'soakers'} - "
                    f"Fight {pyre_set.fight_id}"
                ),
                link=build_pull_link(pyre_set.source_report_code, pyre_set.fight_id),
                items=soak_items,
            ),
            RowDetailGroupModel(
                id=(
                    f"{pyre_set.source_report_code}-fight-{pyre_set.fight_id}-"
                    f"pyre-{pyre_set.set_index}-cremation"
                ),
                title="Cremation carriers",
                subtitle=(
                    f"{len(pyre_set.cremation_carriers)} "
                    f"{'player' if len(pyre_set.cremation_carriers) == 1 else 'players'} "
                    "received a "
                    "corpse-burning aura from this Pyre."
                ),
                items=carrier_items,
            ),
            RowDetailGroupModel(
                id=(
                    f"{pyre_set.source_report_code}-fight-{pyre_set.fight_id}-"
                    f"pyre-{pyre_set.set_index}-corpse-control"
                ),
                title="Corpse control",
                subtitle=(
                    "Successful burns are not directly exposed by Warcraft Logs."
                ),
                items=corpse_items,
            ),
        ],
    )


def _build_player_cell(entrant: KillSquadEntrant) -> TableCellPlayerModel:
    indicators: List[TableCellIndicatorModel] = []
    if entrant.died:
        indicators.append(
            TableCellIndicatorModel(
                id="death",
                label=(
                    "Died at "
                    f"{format_offset_seconds(entrant.death_offset_ms)} during this set"
                ),
                tone="danger",
                icon="skull",
            )
        )
    if entrant.was_ejected:
        indicators.append(
            TableCellIndicatorModel(
                id="ejected",
                label=(
                    "Ejected by Soulcoiler's Curse; Soulcoiled applied at "
                    f"{format_offset_seconds(entrant.ejection_offset_ms)}"
                ),
                tone="ejected",
                icon="ejected",
            )
        )
    if entrant.entered_exhausted:
        tooltip = (
            "Entered with Soul Exhaustion: "
            f"{entrant.exhaustion_remaining_ms / 1000.0:.2f}s remaining"
        )
    else:
        tooltip = "No active Soul Exhaustion at entry"
    return TableCellPlayerModel(
        name=entrant.player,
        colorToken=class_color_token(entrant.class_name),
        tone=(
            "danger"
            if entrant.died
            else "ejected"
            if entrant.was_ejected
            else "warning"
            if entrant.entered_exhausted
            else None
        ),
        tooltip=tooltip,
        indicators=indicators,
    )


def _build_set_details(kill_set: KillSquadSet) -> RowDetailsModel:
    items: List[RowDetailItemModel]
    if kill_set.entrants:
        items = [
            _build_entrant_detail(kill_set, entrant, index)
            for index, entrant in enumerate(kill_set.entrants, start=1)
        ]
    else:
        items = [
            RowDetailItemModel(
                id=f"{kill_set.source_report_code}-{kill_set.fight_id}-{kill_set.set_index}-empty",
                label="No downstairs entry observed",
                description="No Immortal Coil player tick was logged for this set.",
                tone="warning",
            )
        ]
    return RowDetailsModel(
        variant=RowDetailsVariant.EVENT_GROUPS,
        groups=[
            RowDetailGroupModel(
                id=(
                    f"{kill_set.source_report_code}-fight-{kill_set.fight_id}-"
                    f"set-{kill_set.set_index}"
                ),
                title=f"Pull {kill_set.pull_index} - Set {kill_set.set_index}",
                subtitle=(
                    f"Grasp began {format_offset_seconds(kill_set.start_offset_ms)} - "
                    f"window {format_duration(kill_set.duration_ms)} - "
                    f"Fight {kill_set.fight_id}"
                ),
                link=build_pull_link(kill_set.source_report_code, kill_set.fight_id),
                items=items,
            )
        ],
        barChart=RowDetailBarChartModel(
            title="Drowned Echo damage",
            subtitle=(
                "Damage during this set, scaled relative to the highest contributor."
            ),
            bars=[
                RowDetailBarModel(
                    id=(
                        f"{kill_set.source_report_code}-{kill_set.fight_id}-"
                        f"{kill_set.set_index}-damage-{index}"
                    ),
                    label=contribution.player,
                    value=contribution.damage,
                    display=f"{contribution.damage:,.0f}",
                    colorToken=class_color_token(contribution.class_name),
                )
                for index, contribution in enumerate(
                    kill_set.damage_contributions, start=1
                )
            ],
        ),
    )


def _build_entrant_detail(
    kill_set: KillSquadSet,
    entrant: KillSquadEntrant,
    index: int,
) -> RowDetailItemModel:
    badges = [
        (
            f"Soul Exhaustion: {entrant.exhaustion_remaining_ms / 1000.0:.2f}s remaining"
            if entrant.entered_exhausted
            else "Soul Exhaustion: clear"
        )
    ]
    if entrant.was_ejected:
        badges.append(
            "Ejected - Soulcoiled: "
            + format_offset_seconds(entrant.ejection_offset_ms)
        )
    if entrant.died:
        badges.append("Died: " + format_offset_seconds(entrant.death_offset_ms))
    status_description = "first logged downstairs tick"
    if entrant.was_ejected and entrant.died:
        status_description += "; later ejected and killed"
    elif entrant.was_ejected:
        status_description += "; later ejected"
    elif entrant.died:
        status_description += "; later died"
    return RowDetailItemModel(
        id=(
            f"{kill_set.source_report_code}-{kill_set.fight_id}-{kill_set.set_index}-"
            f"entrant-{index}"
        ),
        label=entrant.player,
        kind="ability_event",
        abilityLabel="Immortal Coil entry",
        abilityHref="https://www.wowhead.com/spell=1308227/immortal-coil",
        timestampLabel=format_offset_seconds(entrant.entry_offset_ms),
        description=status_description,
        badges=badges,
        tone=(
            "danger"
            if entrant.died
            else "warning"
            if entrant.was_ejected or entrant.entered_exhausted
            else "success"
        ),
    )


__all__ = ["build_nek_zali_mechanics_report_page"]
