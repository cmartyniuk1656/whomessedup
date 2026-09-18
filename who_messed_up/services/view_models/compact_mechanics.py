"""Opt-in compact mechanics presentation, independent of encounter calculations.

Keep primary cells small, put time beneath the row label, and retain secondary
metrics plus complete event evidence in progressively disclosed details.
"""
from .common import (
    CellKind, CompactRowDetailsModel, CompactTableModel, MetricListCellModel,
    OutcomeBarCellModel, OutcomeSegmentModel, SummaryMetricModel, ValueFormat,
)


def metric(field, label, values):
    value = values.get(field)
    display = "Not observed" if value is None else None
    if value is not None and field in {"average", "duration"}:
        display = f"{value:.2f}s"
    elif isinstance(value, (int, float)) and abs(value) >= 10000:
        display = f"{value / 1_000_000:.2f}m" if abs(value) >= 1_000_000 else f"{value / 1000:.1f}k"
    return SummaryMetricModel(id=field, label=label, value=value, display=display,
                              format=ValueFormat.INTEGER if isinstance(value, (int, float)) else ValueFormat.TEXT)


def compact_mechanics_page(page, summary, *, metric_cells, outcome_cells, detail_metrics, aliases=None, decorate_row=None):
    table = page.content.table
    sources = {}
    for view, sets in summary.sets.items():
        variants = [view] + [alias for alias, source in (aliases or {}).items() if source == view]
        for row in sets:
            for variant in variants:
                sources[f"{row.source_report_code}-{row.fight_id}-{variant}-{row.index}"] = (view, row)
    for columns in [table.columns, *table.columns_by_view.values()]:
        columns[:] = [column for column in columns if column.id != "time"]
        for column in columns:
            if column.id == "set":
                column.cell_kind = CellKind.HEADING
                if column.label == "Set / life":
                    column.label = "Set"
    visited = set()
    for rows in [table.rows, *table.rows_by_view.values(), *table.rows_by_combined_view.values()]:
        for rendered in rows:
            if id(rendered) in visited or rendered.id not in sources:
                continue
            visited.add(id(rendered))
            view, source = sources[rendered.id]
            values = source.values
            rendered.cells["set"].label = str(rendered.cells["time"].value)
            for cell_id, spec in metric_cells.get(view, {}).items():
                items = [metric(field, label, values) for field, label in spec]
                rendered.cells[cell_id] = MetricListCellModel(value=items[0].value, metrics=items,
                    display="; ".join(f"{item.label}: {item.display if item.display is not None else item.value}" for item in items))
            if view in outcome_cells:
                segments = [OutcomeSegmentModel(id=field, label=label, value=int(values.get(field, 0)), tone=tone)
                            for field, label, tone in outcome_cells[view]]
                rendered.cells["outcomes"] = OutcomeBarCellModel(
                    value=sum(s.value for s in segments), label="Observed outcomes", outcomes=segments,
                    display="; ".join(f"{s.label}: {s.value}" for s in segments))
            if decorate_row:
                decorate_row(rendered, view, source)
            if rendered.details:
                original = rendered.details.model_dump(by_alias=True)
                rendered.details = CompactRowDetailsModel(**{**original, "layout": "compact", "barChartPosition": "before"},
                    metrics=[metric(field, label, values) for field, label in detail_metrics.get(view, [])])
    page.content.table = CompactTableModel(**table.model_dump(by_alias=True), layout="compact")
    return page
