"""Compact totem outcomes and complete wave rosters, using shared table cells.

Outcome bars describe totem sets. Wave clears are group associations, so the
wave view never derives per-player missed counts from uncredited NPC deaths.
"""
from dataclasses import replace

from .common import (
    CellKind, OutcomeBarCellModel, OutcomeSegmentModel, SummaryMetricModel,
    TableViewControlModel, TableViewOptionModel,
)
from .mechanics import mechanics_columns, mechanics_row

OUTCOME_COLUMNS = [("outcomes", "Totem outcomes", "text")]
WAVE_COLUMNS = [("carriers", "Wave carriers", "player_list"), ("clears", "Totem clears", "metric_list")]
OUTCOMES = [("cleared", "Cleared", "success"), ("detonated", "Missed / detonated", "danger"),
            ("unresolved", "Unresolved", "neutral")]


def add_totem_views(page, summary):
    table = page.content.table
    table.sub_view_control_by_view["totems"] = TableViewControlModel(
        id="totem_view", label="View", defaultValue="totems-bars", options=[
            TableViewOptionModel(value="totems-bars", label="Totem outcomes"),
            TableViewOptionModel(value="totems-waves", label="Wave carriers"),
            TableViewOptionModel(value="totems-details", label="Totem details"),
        ])
    outcome_columns = mechanics_columns(OUTCOME_COLUMNS)
    outcome_columns[2].cell_kind = CellKind.OUTCOME_BAR
    outcome_columns[2].sortable = False
    table.columns_by_view["totems-bars"] = outcome_columns
    table.columns_by_view["totems-details"] = table.columns_by_view["totems"]
    wave_columns = mechanics_columns(WAVE_COLUMNS)
    wave_columns[0].label = "Wave"
    wave_columns[1].label = "Assigned"
    table.columns_by_view["totems-waves"] = wave_columns
    lookup = {(p.source_report_code, p.fight_id): p for p in summary.pulls}
    for scope, pulls in [("aggregate", summary.pulls)] + [(p.view_id, [p]) for p in summary.pulls]:
        keys = {(p.source_report_code, p.fight_id) for p in pulls}
        sets = [r for r in summary.sets["totems"] if (r.source_report_code, r.fight_id) in keys]
        waves = [r for r in summary.sets.get("totem_waves", []) if (r.source_report_code, r.fight_id) in keys]
        prefix = f"{scope}::totems"
        bar_rows = []
        for row in sets:
            compact = replace(row, details=[d for d in row.details if d.section in {"Plague waves", "Fountain context"}])
            rendered = mechanics_row(summary, compact, lookup[(row.source_report_code, row.fight_id)], "totems-bars", OUTCOME_COLUMNS)
            total = sum(row.values[key] for key, _, _ in OUTCOMES)
            rendered.cells["outcomes"] = OutcomeBarCellModel(
                value=total, label=f"{row.label} outcomes", display=f"{row.values['cleared']} cleared / {row.values['detonated']} missed / {row.values['unresolved']} unresolved",
                outcomes=[OutcomeSegmentModel(id=key, label=label, value=row.values[key], tone=tone) for key, label, tone in OUTCOMES])
            bar_rows.append(rendered)
        table.rows_by_combined_view[prefix + "::totems-bars"] = bar_rows
        table.rows_by_combined_view[prefix + "::totems-details"] = table.rows_by_combined_view[prefix]
        table.rows_by_combined_view[prefix + "::totems-waves"] = [
            mechanics_row(summary, row, lookup[(row.source_report_code, row.fight_id)], "totems-waves", WAVE_COLUMNS) for row in waves]
        page.summary_by_combined_view[prefix + "::totems-waves"] = [
            SummaryMetricModel(id="pulls", label="Pulls", value=len(pulls)),
            SummaryMetricModel(id="waves", label="Waves", value=len(waves)),
            SummaryMetricModel(id="assignments", label="Carrier assignments", value=sum(r.values["assigned"] for r in waves)),
            SummaryMetricModel(id="cleared", label="Group-associated clears", value=sum(r.values["cleared"] for r in waves)),
        ]
    table.empty_state_by_view["totems-waves"] = "No wave assignments were observed in the selected pulls."
    page.footnotes.insert(0, "Totem bars: cleared before detonation, missed (Malignance completed), or unresolved. Unresolved totems are not counted as misses. Wave carriers includes every Froth assignment group, even with no associated clears; those zeros do not establish a missed assignment or individual responsibility.")
    return page
