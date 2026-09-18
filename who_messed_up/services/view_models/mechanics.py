"""Configurable expandable mechanics pages using the shared table contract.

Encounter modules supply columns, metrics and contribution labels; this module
owns report/pull scoping, player bars and the evidence-row presentation.
"""
from collections import Counter, defaultdict

from .common import (
    CellKind, ContentVariant, HeaderTagModel, ReportContentModel, ReportHeaderModel,
    ReportPageModel, RowDetailBarChartModel, RowDetailBarModel, RowDetailGroupModel,
    RowDetailItemModel, RowDetailsModel, RowDetailsVariant, SortDirection, SortModel,
    SummaryMetricModel, TableCellModel, TableCellPlayerModel, TableColumnModel,
    TableModel, TableRowGroupModel, TableRowModel, TableViewControlModel, TableViewOptionModel, ValueFormat,
)
from .helpers import build_pull_link, class_color_token, format_duration, format_offset_seconds


def mechanics_columns(spec):
    return [TableColumnModel(id="set", label="Set / life", sortable=True, cellKind=CellKind.TEXT),
            TableColumnModel(id="time", label="Time", sortable=True, cellKind=CellKind.TEXT),
            *[TableColumnModel(id=key, label=label, sortable=kind not in {"player_list", "outcome_bar"}, cellKind=kind,
                               format=ValueFormat.DECIMAL if key in {"duration", "average"} else ValueFormat.INTEGER if kind == "number" else None,
                               precision=2 if key in {"duration", "average"} else None)
              for key, label, kind in spec]]


def mechanics_row(summary, row, pull, view, columns, bar_spec=None):
    row_id = f"{row.source_report_code}-{row.fight_id}-{view}-{row.index}"
    order = summary.source_reports.index(row.source_report_code) if summary.source_reports else 0
    cells = dict(set=TableCellModel(value=row.label, sortValue=order * 1000000 + row.pull_index * 1000 + row.index),
                 time=TableCellModel(value=format_offset_seconds(row.start - row.fight_start), sortValue=row.start - row.fight_start))
    for key, _, kind in columns:
        if key == "dispels":
            cells[key] = TableCellModel(value=len(row.dispels), players=[
                TableCellPlayerModel(name=f"{d.dispeller} -> {d.player} ({format_offset_seconds(d.timestamp - row.fight_start)})",
                                     tooltip=f"{d.delay:.2f}s after application",
                                     colorToken=class_color_token(summary.player_classes.get(d.dispeller))) for d in row.dispels
            ], display=None if row.dispels else "See unmatched evidence" if row.values.get("unmatched") else "None observed")
        elif kind == "player_list":
            names = row.players.get(key, [])
            cells[key] = TableCellModel(value=len(names), players=[
                TableCellPlayerModel(name=n, colorToken=class_color_token(summary.player_classes.get(n))) for n in names
            ], display=None if names else "None observed")
        else:
            value = row.values.get(key)
            cells[key] = TableCellModel(value=value, display="Not observed" if value is None else None)
    groups = defaultdict(list)
    for i, detail in enumerate(row.details):
        groups[detail.section].append(RowDetailItemModel(
            id=f"{row_id}-{i}", label=detail.label, description=detail.description, badges=detail.badges, tone=detail.tone,
            timestampLabel=format_offset_seconds(detail.timestamp - row.fight_start) if detail.timestamp is not None else None))
    chart = None
    if bar_spec:
        attribute, title, unit = bar_spec
        totals = getattr(row, attribute)
        if totals:
            chart = RowDetailBarChartModel(title=title, unitLabel=unit, bars=[
                RowDetailBarModel(id=f"{row_id}-bar-{i}", label=name, value=amount, display=f"{amount:,.0f}",
                                  colorToken=class_color_token(summary.player_classes.get(name)))
                for i, (name, amount) in enumerate(sorted(totals.items(), key=lambda pair: (-pair[1], pair[0])))])
    return TableRowModel(id=row_id, cells=cells,
                        group=TableRowGroupModel(id=f"{row.source_report_code}-{row.fight_id}", label=pull.label,
                                                 subtitle=f"{format_duration(pull.duration_ms)} - Fight {pull.fight_id}",
                                                 href=build_pull_link(row.source_report_code, row.fight_id), sortValue=order * 1000 + pull.pull_index),
                        details=RowDetailsModel(variant=RowDetailsVariant.EVENT_GROUPS, barChart=chart, groups=[
                            RowDetailGroupModel(id=f"{row_id}-group-{i}", title=section, items=items,
                                                link=build_pull_link(row.source_report_code, row.fight_id))
                            for i, (section, items) in enumerate(groups.items())]))


def build_mechanics_page(summary, *, report_id, title, fight_name, views, columns, metrics, footnotes, bars):
    rows_by_combined, summary_by_combined = {}, {}
    scopes = [("aggregate", summary.pulls)] + [(p.view_id, [p]) for p in summary.pulls]
    pull_lookup = {(p.source_report_code, p.fight_id): p for p in summary.pulls}
    for scope, pulls in scopes:
        keys = {(p.source_report_code, p.fight_id) for p in pulls}
        for view in views:
            sets = [r for r in summary.sets.get(view, []) if (r.source_report_code, r.fight_id) in keys]
            key = f"{scope}::{view}"
            rows = [mechanics_row(summary, r, pull_lookup[(r.source_report_code, r.fight_id)], view, columns[view], bars.get(view)) for r in sets]
            rows_by_combined[key] = rows
            totals = [SummaryMetricModel(id="pulls", label="Pulls", value=len(pulls)),
                      SummaryMetricModel(id="sets", label="Evidence rows", value=len(sets))]
            totals.extend(SummaryMetricModel(id=field, label=label, value=sum(r.values.get(field, 0) or 0 for r in sets), format=ValueFormat.INTEGER)
                          for field, label in metrics[view])
            durations = [duration for r in sets for duration in r.values.get("clear_seconds", [])]
            if any("clear_seconds" in row.values for row in sets):
                totals.append(SummaryMetricModel(id="average", label="Average supported clear (s)",
                                                 value=sum(durations) / len(durations) if durations else None,
                                                 display=None if durations else "Not observed", format=ValueFormat.DECIMAL, precision=2))
            summary_by_combined[key] = totals
            if view in bars:
                attribute, _, unit = bars[view]
                counts = Counter()
                for row in sets:
                    counts.update(getattr(row, attribute))
                maximum = max(counts.values(), default=0)
                rows_by_combined[key + f"::{view}-sets"] = rows
                rows_by_combined[key + f"::{view}-bars"] = [
                    TableRowModel(id=f"{scope}-{view}-{name}", cells={"contribution": TableCellModel(
                        value=amount, label=name, unitLabel=unit, maxValue=maximum,
                        colorToken=class_color_token(summary.player_classes.get(name)))})
                    for name, amount in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))]
    default = next(iter(views))
    row_scopes = {scope: rows_by_combined[f"{scope}::{default}"] for scope, _ in scopes}
    metric_scopes = {scope: summary_by_combined[f"{scope}::{default}"] for scope, _ in scopes}
    return ReportPageModel(
        reportId=report_id, title=title, reportCode=summary.report_code,
        header=ReportHeaderModel(subtitle="Reports " + ", ".join(summary.source_reports or [summary.report_code]), tags=[
            HeaderTagModel(id="fight", label="Fight", value=fight_name), HeaderTagModel(id="difficulty", label="Difficulty", value="Mythic")]),
        summary=metric_scopes["aggregate"], summaryByView=metric_scopes, summaryByCombinedView=summary_by_combined,
        content=ReportContentModel(variant=ContentVariant.TABLE, table=TableModel(
            columns=mechanics_columns(columns[default]), columnsByView={
                **{view: mechanics_columns(spec) for view, spec in columns.items()},
                **{f"{view}-sets": mechanics_columns(columns[view]) for view in bars},
                **{f"{view}-bars": [TableColumnModel(id="contribution", label=title, sortable=True, cellKind=CellKind.RELATIVE_BAR,
                                                      format=ValueFormat.INTEGER)] for view, (_, title, _) in bars.items()}},
            rows=row_scopes["aggregate"], rowsByView=row_scopes, rowsByCombinedView=rows_by_combined,
            defaultSort=SortModel(columnId="set", direction=SortDirection.ASC),
            defaultSortByView={f"{view}-bars": SortModel(columnId="contribution", direction=SortDirection.DESC) for view in bars},
            viewControl=TableViewControlModel(id="pull_scope", label="Pull", defaultValue="aggregate", options=[
                TableViewOptionModel(value="aggregate", label="Aggregate"), *[TableViewOptionModel(value=p.view_id, label=p.label) for p in summary.pulls]]),
            secondaryViewControl=TableViewControlModel(id="mechanic", label="Mechanic", defaultValue=default,
                                                       options=[TableViewOptionModel(value=k, label=v) for k, v in views.items()]),
            subViewControlByView={view: TableViewControlModel(id=f"{view}_view", label="View", defaultValue=f"{view}-sets", options=[
                TableViewOptionModel(value=f"{view}-sets", label="By set / life"),
                TableViewOptionModel(value=f"{view}-bars", label=title)]) for view, (_, title, _) in bars.items()},
            emptyState="No mechanic evidence was observed in the selected pulls.",
        )), footnotes=list(footnotes))
