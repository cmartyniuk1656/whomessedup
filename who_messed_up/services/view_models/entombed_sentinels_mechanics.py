"""Render Sentinels analyses with the shared expandable mechanics table.

Both selectors scope rows and summary metrics by report AND fight; merged
reports may reuse fight IDs. No boss-specific frontend renderer is required.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from ..entombed_sentinels_mechanics_models import (
    REPORT_DEFAULT_FIGHT, REPORT_FOOTNOTES, REPORT_ID, REPORT_TITLE, VIEWS,
    SentinelsMechanicsSummary,
)
from .common import (
    CellKind, ContentVariant, HeaderTagModel, ReportContentModel, ReportHeaderModel,
    ReportPageModel, RowDetailBarChartModel, RowDetailBarModel, RowDetailGroupModel,
    RowDetailItemModel, RowDetailsModel, RowDetailsVariant, SortDirection, SortModel,
    SummaryMetricModel, TableCellModel, TableCellPlayerModel, TableCellTextSegmentModel, TableColumnModel,
    TableModel, TableRowGroupModel, TableRowModel, TableViewControlModel,
    TableViewOptionModel, ValueFormat,
)
from .helpers import build_pull_link, class_color_token, format_duration, format_offset_seconds


DROPLET_BARS_VIEW = "droplets-by-player"
DROPLET_WAVES_VIEW = "droplets-by-wave"
DISPEL_BARS_VIEW = "dispels-by-healer"
DISPEL_SETS_VIEW = "dispels-by-set"
COUNT_VIEWS = {
    "droplets": ("soak_counts", "soaks", "droplet soaks", DROPLET_BARS_VIEW, DROPLET_WAVES_VIEW),
    "dispels": ("dispel_counts", "dispels", "dispels", DISPEL_BARS_VIEW, DISPEL_SETS_VIEW),
}


# (field, label, kind). Counts use separate fields from player-list columns.
COLUMNS = {
    "protovenom": [("assigned", "Assigned players", "player_list"),
                   ("removed", "Removed alive", "number"), ("deaths", "Died unresolved", "number"),
                   ("unresolved", "Other unresolved", "number"), ("eruption_hits", "Eruption hits", "number")],
    "helical-toxins": [("assigned", "Assigned players", "player_list"),
                      ("removed", "Removed alive", "number"), ("deaths", "Died unresolved", "number"),
                      ("unresolved", "Other unresolved", "number"), ("failures", "Burst applications", "number")],
    "miasma": [("marked", "Marked target", "player_list"), ("impact", "Impact", "text"),
               ("soakers", "Who soaked", "player_list"), ("soaker_count", "Soakers", "number"),
               ("damage", "Damage taken", "number"), ("deaths", "Deaths within 2s", "number")],
    "droplets": [("poppers", "Who popped", "player_list"), ("pops", "Pop hits", "number"),
                 ("bursts", "Blast bursts", "number"), ("blast_hits", "Blast hits", "number"),
                 ("damage", "Blast damage", "number")],
    "coagulations": [("duration", "Observed lifetime (s)", "number"),
                     ("contributors", "Damage contributors", "player_list"),
                     ("contaminate", "Contaminate damage", "number")],
    "dispels": [("assigned", "Debuffed players", "player_list"),
                ("dispels", "Who dispelled and when", "player_list"),
                ("dispelled", "Dispelled", "number"), ("not_dispelled", "Not dispelled", "number")],
    "intermission": [("status", "Outcome", "text"), ("duration", "Clear time (s)", "number"),
                     ("end", "Finished", "text"), ("resolution", "Toxins cleared", "text"),
                     ("healing", "Boss healing", "number")],
}
METRICS = {
    "protovenom": [("assigned", "Assignments"), ("removed", "Removed alive"), ("eruption_hits", "Eruption hits")],
    "helical-toxins": [("assigned", "Assignments"), ("removed", "Removed alive"), ("failures", "Burst applications")],
    "miasma": [("soakers", "Soak participations"), ("deaths", "Deaths within 2s")],
    "droplets": [("pops", "Pop hits"), ("bursts", "Blast bursts"), ("blast_hits", "Blast hits")],
    "coagulations": [("kills", "Confirmed kills"), ("damage", "Add damage"), ("contaminate", "Contaminate damage")],
    "dispels": [("assigned", "Applications"), ("dispelled", "Dispelled"), ("not_dispelled", "Not dispelled")],
    "intermission": [("completed", "Completed"), ("healing", "Boss healing")],
}


def _columns(view):
    return [TableColumnModel(id="set", label="Set", sortable=True, cellKind=CellKind.TEXT),
            TableColumnModel(id="time", label="Time", sortable=True, cellKind=CellKind.TEXT),
            *[TableColumnModel(id=key, label=label, sortable=kind != "player_list", cellKind=kind,
                               format=(ValueFormat.DECIMAL if key in ("duration", "delay")
                                       else ValueFormat.INTEGER) if kind == "number" else None,
                               precision=2 if key in ("duration", "delay") else None)
              for key, label, kind in COLUMNS[view]]]


def _metrics(view, sets, pull_count):
    metrics = [SummaryMetricModel(id="pulls", label="Pulls", value=pull_count),
            SummaryMetricModel(id="sets", label="Evidence rows" if view == "coagulations" else "Intermissions" if view == "intermission" else "Sets", value=len(sets)),
            *[SummaryMetricModel(id=key, label=label,
                                 value=sum(row.values.get(key, 0) or 0 for row in sets),
                                 format=ValueFormat.INTEGER)
              for key, label in METRICS[view]]]
    if view == "intermission":
        durations = [row.values["duration"] for row in sets if row.values.get("completed")]
        metrics.extend([
            SummaryMetricModel(id="average", label="Average clear (s)",
                               value=sum(durations) / len(durations) if durations else None,
                               format=ValueFormat.DECIMAL, precision=2, display=None if durations else "—"),
            SummaryMetricModel(id="fastest", label="Fastest clear (s)", value=min(durations) if durations else None,
                               format=ValueFormat.DECIMAL, precision=2, display=None if durations else "—"),
        ])
    return metrics


def _count_bar_rows(summary, sets, scope, view):
    """Aggregate player counts only after selecting the report and pull scope."""
    attribute, column, unit, _, _ = COUNT_VIEWS[view]
    totals = Counter()
    for mechanic_set in sets:
        totals.update(getattr(mechanic_set, attribute))
    maximum = max(totals.values(), default=0)
    return [
        TableRowModel(
            id=f"{scope}-{view}-{player}",
            cells={column: TableCellModel(
                value=count, label=player, unitLabel=unit, maxValue=maximum,
                colorToken=class_color_token(summary.player_classes.get(player)),
            )},
        )
        for player, count in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    ]


def _add_count_views(summary, scope, sets, set_rows, rows_by_combined, view):
    _, _, _, bars_view, sets_view = COUNT_VIEWS[view]
    rows_by_combined[f"{scope}::{view}::{bars_view}"] = _count_bar_rows(summary, sets, scope, view)
    rows_by_combined[f"{scope}::{view}::{sets_view}"] = set_rows


def _row(summary, view, row, pull, report_order):
    row_id = f"{row.source_report_code}-{row.fight_id}-{view}-{row.index}"
    cells = {
        "set": TableCellModel(value=row.label, sortValue=report_order * 1000000 + row.pull_index * 1000 + row.index),
        "time": TableCellModel(value=format_offset_seconds(row.start - row.fight_start),
                               sortValue=row.start - row.fight_start),
    }
    for key, _, kind in COLUMNS[view]:
        if view == "dispels" and key == "dispels":
            cells[key] = TableCellModel(value=len(row.dispels), players=[
                TableCellPlayerModel(
                    name=f"{record.dispeller} · {format_offset_seconds(record.timestamp - row.fight_start)} → {record.player}",
                    tooltip=f"{record.delay:.2f}s after application",
                    segments=[
                        TableCellTextSegmentModel(text=record.dispeller,
                                                  colorToken=class_color_token(summary.player_classes.get(record.dispeller))),
                        TableCellTextSegmentModel(text=f" · {format_offset_seconds(record.timestamp - row.fight_start)} → "),
                        TableCellTextSegmentModel(text=record.player,
                                                  colorToken=class_color_token(summary.player_classes.get(record.player))),
                    ],
                ) for record in row.dispels
            ], display="None observed" if not row.dispels else None)
        elif kind == "player_list":
            players = row.players.get(key, [])
            cells[key] = TableCellModel(value=len(players), players=[
                TableCellPlayerModel(name=name, colorToken=class_color_token(summary.player_classes.get(name)),
                                     tone="warning" if view == "dispels" and not any(record.player == name for record in row.dispels) else None)
                for name in players
            ], display="None observed" if not players else None)
        else:
            value = row.values.get("soakers" if key == "soaker_count" else key)
            cells[key] = TableCellModel(value=value, display=("Not completed" if view == "intermission" and key in {"duration", "end"}
                                                            else "Not observed") if value is None else None)
    sections = defaultdict(list)
    for index, detail in enumerate(row.details):
        if view == "coagulations" and detail.section in {"Lifetime", "Player damage"}:
            continue
        sections[detail.section].append(RowDetailItemModel(
            id=f"{row_id}-detail-{index}", label=detail.label,
            timestampLabel=format_offset_seconds(detail.timestamp - row.fight_start) if detail.timestamp is not None else None,
            description=detail.description, badges=detail.badges, tone=detail.tone,
        ))
    chart = None
    if view == "droplets" and row.soak_counts:
        chart = RowDetailBarChartModel(title="Droplet soaks", subtitle="Player soaks in this wave.", unitLabel="droplet soaks", bars=[
            RowDetailBarModel(id=f"{row_id}-soaks-{index}", label=name, value=count, display=str(count),
                              colorToken=class_color_token(summary.player_classes.get(name)))
            for index, (name, count) in enumerate(sorted(row.soak_counts.items(), key=lambda item: (-item[1], item[0])))
        ])
    elif view == "intermission" and row.boss_healing:
        chart = RowDetailBarChartModel(title="Boss healing", unitLabel="healing", bars=[
            RowDetailBarModel(id=f"{row_id}-healing-{index}", label=name, value=amount, display=f"{amount:,.0f}")
            for index, (name, amount) in enumerate(sorted(row.boss_healing.items(), key=lambda item: -item[1]))
        ])
    elif row.contributions:
        chart = RowDetailBarChartModel(title="Coagulation damage", subtitle="Includes owned pets; excludes overkill.", bars=[
            RowDetailBarModel(id=f"{row_id}-damage-{index}", label=name, value=amount, display=f"{amount:,.0f}",
                              colorToken=class_color_token(summary.player_classes.get(name)))
            for index, (name, amount) in enumerate(sorted(row.contributions.items(), key=lambda item: -item[1]))
        ])
    return TableRowModel(
        id=row_id, cells=cells,
        group=TableRowGroupModel(id=f"{row.source_report_code}-fight-{row.fight_id}", label=pull.label,
                                 subtitle=f"{format_duration(pull.duration_ms)} - Fight {row.fight_id}",
                                 href=build_pull_link(row.source_report_code, row.fight_id),
                                 sortValue=report_order * 1000 + pull.pull_index),
        details=RowDetailsModel(variant=RowDetailsVariant.EVENT_GROUPS, barChart=chart,
                                barChartPosition="before" if view == "intermission" else "after", groups=[
            RowDetailGroupModel(id=f"{row_id}-group-{index}", title=section, items=items,
                                link=build_pull_link(row.source_report_code, row.fight_id))
            for index, (section, items) in enumerate(sections.items())
        ]),
    )


def build_sentinels_mechanics_report_page(summary: SentinelsMechanicsSummary) -> ReportPageModel:
    codes = summary.source_reports or [summary.report_code]
    pulls = {(p.source_report_code, p.fight_id): p for p in summary.pulls}
    rows_by_combined = {}
    metrics_by_combined = {}
    for view in VIEWS:
        sets = summary.sets.get(view, [])
        rows = [_row(summary, view, row, pulls[(row.source_report_code, row.fight_id)],
                     codes.index(row.source_report_code)) for row in sets]
        rows_by_combined[f"aggregate::{view}"] = rows
        metrics_by_combined[f"aggregate::{view}"] = _metrics(view, sets, summary.pull_count)
        if view in COUNT_VIEWS:
            _add_count_views(summary, "aggregate", sets, rows, rows_by_combined, view)
        for pull in summary.pulls:
            selected = [(row, item) for row, item in zip(rows, sets)
                        if (item.source_report_code, item.fight_id) == (pull.source_report_code, pull.fight_id)]
            rows_by_combined[f"{pull.view_id}::{view}"] = [row for row, _ in selected]
            metrics_by_combined[f"{pull.view_id}::{view}"] = _metrics(view, [item for _, item in selected], 1)
            if view in COUNT_VIEWS:
                _add_count_views(summary, pull.view_id, [item for _, item in selected],
                                 [row for row, _ in selected], rows_by_combined, view)
    default = next(iter(VIEWS))
    scopes = ["aggregate"] + [p.view_id for p in summary.pulls]
    rows_by_view = {scope: rows_by_combined[f"{scope}::{default}"] for scope in scopes}
    summary_by_view = {scope: metrics_by_combined[f"{scope}::{default}"] for scope in scopes}
    return ReportPageModel(
        reportId=REPORT_ID, title=REPORT_TITLE, reportCode=summary.report_code,
        header=ReportHeaderModel(subtitle="Reports " + ", ".join(codes), tags=[
            HeaderTagModel(id="fight", label="Fight", value=REPORT_DEFAULT_FIGHT),
            HeaderTagModel(id="difficulty", label="Difficulty", value="Mythic"),
        ]),
        summary=summary_by_view["aggregate"], summaryByView=summary_by_view,
        summaryByCombinedView=metrics_by_combined,
        content=ReportContentModel(variant=ContentVariant.TABLE, table=TableModel(
            defaultSort=SortModel(columnId="set", direction=SortDirection.ASC),
            defaultSortByView={bars: SortModel(columnId=column, direction=SortDirection.DESC)
                               for _, column, _, bars, _ in COUNT_VIEWS.values()},
            columns=_columns(default), columnsByView={
                **{view: _columns(view) for view in VIEWS},
                **{sets_view: _columns(view) for view, (_, _, _, _, sets_view) in COUNT_VIEWS.items()},
                **{bars: [TableColumnModel(id=column, label=unit.capitalize(), sortable=True,
                                           cellKind=CellKind.RELATIVE_BAR, format=ValueFormat.INTEGER)]
                   for _, column, unit, bars, _ in COUNT_VIEWS.values()},
            },
            rows=rows_by_view["aggregate"], rowsByView=rows_by_view, rowsByCombinedView=rows_by_combined,
            viewControl=TableViewControlModel(id="pull_scope", label="Pull", defaultValue="aggregate", options=[
                TableViewOptionModel(value="aggregate", label="Aggregate"),
                *[TableViewOptionModel(value=p.view_id, label=p.label) for p in summary.pulls],
            ]),
            secondaryViewControl=TableViewControlModel(id="mechanic", label="Mechanic", defaultValue=default,
                                                       options=[TableViewOptionModel(value=key, label=label)
                                                                for key, label in VIEWS.items()]),
            subViewControlByView={"droplets": TableViewControlModel(
                id="droplet_view", label="Droplet view", defaultValue=DROPLET_BARS_VIEW,
                options=[TableViewOptionModel(value=DROPLET_BARS_VIEW, label="Bars"),
                         TableViewOptionModel(value=DROPLET_WAVES_VIEW, label="Waves")],
            ), "dispels": TableViewControlModel(
                id="dispel_view", label="Dispel view", defaultValue=DISPEL_SETS_VIEW,
                options=[TableViewOptionModel(value=DISPEL_SETS_VIEW, label="By set"),
                         TableViewOptionModel(value=DISPEL_BARS_VIEW, label="By healer")],
            )},
            emptyState="No mechanic events were observed in the selected pulls.",
            emptyStateByView={
                **{key: f"No {label.lower()} events were observed in the selected pulls."
                   for key, label in VIEWS.items()},
                DROPLET_BARS_VIEW: "No droplet soaks were observed in the selected pulls.",
                DROPLET_WAVES_VIEW: "No droplet waves were observed in the selected pulls.",
                DISPEL_SETS_VIEW: "No Blighted Blood sets were observed in the selected pulls.",
                DISPEL_BARS_VIEW: "No Blighted Blood dispels were observed in the selected pulls.",
            },
        )), footnotes=list(REPORT_FOOTNOTES),
    )


__all__ = ["build_sentinels_mechanics_report_page"]
