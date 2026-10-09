"""Twin Fangs subreports reuse compact evidence tables and scoped player bars."""
from ..the_twin_fangs_mechanics_models import REPORT_DEFAULT_FIGHT, REPORT_FOOTNOTES, REPORT_ID, REPORT_TITLE, VIEWS
from .compact_mechanics import compact_mechanics_page
from .mechanics import build_mechanics_page

COLUMNS = {
    "adds": [("contributors", "Players", "player_list"), ("damage", "Add damage", "number")],
    "orbs": [("players", "Picked up by", "player_list")],
    "waves": [("players", "Player", "player_list")],
    "shields": [("players", "CC players", "player_list"), ("status", "Attribution", "text")],
    "interrupts": [("players", "Interrupted by", "player_list"), ("spell", "Interrupted spell", "text")],
}
METRICS = {"adds": [("damage", "Add damage")], "orbs": [("contacts", "Orb pickups")],
           "waves": [("contacts", "Wave contacts")],
           "shields": [("breaks", "Attributed shield breaks"), ("ambiguous", "Ambiguous CCs"),
                       ("unattributed", "Unattributed removals")],
           "interrupts": [("interrupts", "Successful interrupts")]}
BARS = {"adds": ("contributions", "Add damage by player", "damage"),
        "orbs": ("soak_counts", "Orb pickups by player", "pickups"),
        "waves": ("soak_counts", "Wave contacts by player", "contacts"),
        "shields": ("soak_counts", "Shield breaks by player", "shields"),
        "interrupts": ("soak_counts", "Successful interrupts by player", "interrupts")}


def build_the_twin_fangs_mechanics_report_page(summary):
    page = build_mechanics_page(summary, report_id=REPORT_ID, title=REPORT_TITLE,
                                fight_name=REPORT_DEFAULT_FIGHT, views=VIEWS, columns=COLUMNS,
                                metrics=METRICS, footnotes=REPORT_FOOTNOTES, bars=BARS)
    page.content.table.secondary_view_control.label = "Subreport"
    for view, control in page.content.table.sub_view_control_by_view.items():
        control.default_value = f"{view}-bars"
        control.options[0].label = {"adds": "By add", "shields": "By shield", "interrupts": "By interrupt"}.get(view, "By contact")
    return compact_mechanics_page(page, summary, metric_cells={}, outcome_cells={},
                                   detail_metrics={"adds": [("duration", "Observed lifetime")]})
