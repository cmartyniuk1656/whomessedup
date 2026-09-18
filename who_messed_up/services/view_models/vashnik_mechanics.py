"""Vashnik column vocabulary; shared mechanics presentation handles the UI."""
from ..vashnik_mechanics_models import REPORT_DEFAULT_FIGHT, REPORT_FOOTNOTES, REPORT_ID, REPORT_TITLE, VIEWS
from .mechanics import build_mechanics_page
from .vashnik_totems import add_totem_views
from .compact_mechanics import compact_mechanics_page

COLUMNS = {
    "totems": [("outcomes", "Totem outcomes", "outcome_bar")],
    "froth": [("assigned", "Carriers", "player_list"), ("exposure", "Exposure", "metric_list")],
    "dispels": [("assigned", "Infected players", "player_list"), ("outcomes", "Dispels", "outcome_bar")],
    "stygian": [("assigned", "Infected players", "player_list"), ("outcomes", "Absorb resolution", "outcome_bar")],
    "adds": [("status", "Outcome", "heading"), ("damage_split", "Damage", "metric_list")],
    "bile": [("soakers", "Soakers", "player_list"), ("handling", "Soak handling", "metric_list")],
}
OUTCOME_CELLS = {
    "totems": [("cleared", "Cleared", "success"), ("detonated", "Detonated", "danger"), ("unresolved", "Unresolved", "neutral")],
    "dispels": [("dispelled", "Dispelled", "success"), ("not_dispelled", "No dispel logged", "neutral")],
    "stygian": [("cleared", "Cleared", "success"), ("unresolved", "Other outcomes", "neutral")],
}
METRIC_CELLS = {
    "froth": {"exposure": [("splash_hits", "Unmarked splash hits"), ("wave_hits", "Wave hits")]},
    "adds": {"damage_split": [("health", "Health"), ("shield", "Shield")]},
    "bile": {"handling": [("soaks", "Soak hits"), ("bursts", "Missed bursts")]},
    "totem_waves": {"clears": [("cleared", "Associated clears"), ("late_clears", "After detonation")]},
}
DETAIL_METRICS = {
    "totems": [("spawned", "Spawned"), ("cleared", "Cleared"), ("detonated", "Detonated"),
               ("unresolved", "Unresolved"), ("inferred", "Single-carrier inferences")],
    "totem_waves": [("assigned", "Carriers"), ("released", "Observed releases"), ("release", "First release")],
    "froth": [("splash_hits", "Unmarked splash hits"), ("wave_hits", "Wave hits"), ("early", "Early releases")],
    "dispels": [("dispelled", "Explicit dispels"), ("not_dispelled", "No dispel logged"),
                ("unmatched", "Unknown applications"), ("explosion_hits", "Explosion hits")],
    "stygian": [("average", "Average supported clear"), ("healing", "Absorb healing"), ("burst_hits", "Burst hits")],
    "adds": [("duration", "Observed lifetime"), ("health", "Health damage"), ("shield", "Shield damage"),
             ("pressure", "Raid damage"), ("surge", "Burning Surges"), ("close", "Close explosions")],
    "bile": [("soaks", "Soak hits"), ("bursts", "Missed bursts"), ("damage", "Missed-soak damage")],
}
METRICS = {
    "totems": [("spawned", "Spawned"), ("cleared", "Removed before detonation"), ("detonated", "Detonated"), ("unresolved", "Unresolved")],
    "froth": [("assigned", "Assignments"), ("splash_hits", "Unmarked splash hits"), ("wave_hits", "Wave hits")],
    "dispels": [("assigned", "Applications"), ("dispelled", "Explicit dispels"), ("unmatched", "Unmatched dispels")],
    "stygian": [("assigned", "Applications"), ("cleared", "Supported clears"), ("healing", "Absorb healing")],
    "adds": [("kills", "Confirmed deaths without leak"), ("leaks", "Leaks"), ("unresolved", "Unresolved"), ("damage", "Health + shield damage")],
    "bile": [("soaks", "Soak hits"), ("bursts", "Missed-soak bursts"), ("damage", "Missed-soak damage")],
}
BARS = {
    "froth": ("contributions", "Unmarked splash received", "hits"),
    "dispels": ("dispel_counts", "Dispels by healer", "dispels"),
    "stygian": ("contributions", "Absorb healing by healer", "absorb healing"),
    "adds": ("contributions", "Add damage by player", "health + shield damage"),
    "bile": ("soak_counts", "Soak hits by player", "soak hits"),
}


def _row_context(rendered, view, source):
    values = source.values
    if view == "totems" and values.get("fountains"):
        rendered.cells["set"].label += " · " + values["fountains"]
    if view == "adds" and "status" in rendered.cells:
        rendered.cells["status"].tone = "danger" if values.get("leaks") else "success" if values.get("kills") else None
        if values.get("close"):
            rendered.cells["status"].label = f"{values['close']} close explosion(s) — review"


def build_vashnik_mechanics_report_page(summary):
    page = build_mechanics_page(summary, report_id=REPORT_ID, title=REPORT_TITLE,
                                fight_name=REPORT_DEFAULT_FIGHT, views=VIEWS, columns=COLUMNS,
                                metrics=METRICS, footnotes=REPORT_FOOTNOTES, bars=BARS)
    page = add_totem_views(page, summary)
    return compact_mechanics_page(page, summary, metric_cells=METRIC_CELLS, outcome_cells=OUTCOME_CELLS,
                                   detail_metrics=DETAIL_METRICS, aliases={"totems-bars": "totems", "totems-waves": "totem_waves"},
                                   decorate_row=_row_context)
