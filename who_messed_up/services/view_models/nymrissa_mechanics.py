"""Compact orb review using existing pull selectors, evidence rows and player bars."""
from ..nymrissa_mechanics_models import REPORT_DEFAULT_FIGHT, REPORT_FOOTNOTES, REPORT_ID, REPORT_TITLE, VIEWS
from .compact_mechanics import compact_mechanics_page
from .mechanics import build_mechanics_page

COLUMNS = {
    "overlaps": [("soakers", "Player", "player_list"), ("timing", "Timing", "heading")],
    "rain": [("soakers", "Orb soakers", "player_list"), ("pops", "Flagged pops", "number")],
    "orbs": [("soakers", "Player", "player_list"), ("timing", "Timing", "heading")],
}
METRICS = {
    "overlaps": [("pops", "Flagged pops"), ("during", "During damage"),
                 ("before", "Within 1s before"), ("after", "Within 1s after")],
    "rain": [("pops", "Flagged pops")],
    "orbs": [("pops", "All orb pops"), ("flagged", "Flagged pops")],
}
BARS = {
    "overlaps": ("soak_counts", "Flagged pops by player", "pops"),
    "rain": ("soak_counts", "Flagged pops by player", "pops"),
    "orbs": ("soak_counts", "All pops by player", "pops"),
}


def _row_context(rendered, view, source):
    if view == "rain":
        rendered.cells["set"].label += " - " + source.values["end"]
    else:
        rendered.cells["timing"].label = source.values["rain"]
        rendered.cells["timing"].tone = "danger" if source.values["flagged"] else None


def build_nymrissa_mechanics_report_page(summary):
    page = build_mechanics_page(summary, report_id=REPORT_ID, title=REPORT_TITLE,
                                fight_name=REPORT_DEFAULT_FIGHT, views=VIEWS, columns=COLUMNS,
                                metrics=METRICS, footnotes=REPORT_FOOTNOTES, bars=BARS)
    for view, control in page.content.table.sub_view_control_by_view.items():
        control.options[0].label = "By Rain window" if view == "rain" else "By orb pop"
    return compact_mechanics_page(page, summary, metric_cells={}, outcome_cells={},
                                   detail_metrics={}, decorate_row=_row_context)
