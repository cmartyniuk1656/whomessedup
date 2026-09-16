"""Source charts must use the same filtered player events in both layouts."""
from dataclasses import replace

from who_messed_up.services.avoidable_damage import AvoidableDamageEntry, AvoidableDamageEvent, AvoidableDamageSummary
from who_messed_up.services.report_pulls import ReportPull
from who_messed_up.services.view_models.avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page


def test_source_charts_sum_damage_by_spell_and_scope_merged_reports_and_pulls():
    base = AvoidableDamageEvent("report", "Alice", 1, "Boss", 1, 1000, 1000, 10, "Ground", 100)
    events = [base, replace(base, timestamp=2000, damage_amount=150),
              replace(base, ability_id=20, ability_label="Explosion", damage_amount=500),
              replace(base, fight_id=2, pull_index=2, damage_amount=1000),
              replace(base, source_report_code="extra", damage_amount=2000)]
    pulls = [ReportPull(code, fid, "Boss", fid, f"pull:{code}:{fid}", f"Pull {fid}", 60000, ("Alice",))
             for code, fid in [("report", 1), ("report", 2), ("report", 3), ("extra", 1)]]
    summary = AvoidableDamageSummary(
        report_code="report", fight_filter="Boss", fight_ids=None, pull_count=4, ignore_after_deaths=None,
        total_damage=3750, avg_damage_per_pull=937.5,
        entries=[AvoidableDamageEntry("Alice", "DPS", "Mage", 4, 3750, 937.5, events)],
        player_classes={"Alice": "Mage"}, player_roles={}, player_specs={}, player_events={"Alice": events},
        abilities=[], pulls=pulls, source_reports=["report", "extra"],
    )
    page = build_avoidable_damage_report_page(summary, config=AvoidableDamagePageConfig("test", "Test"))
    table = page.content.table
    for scope, expected in [("aggregate", [("Ground", 3250), ("Explosion", 500)]),
                            ("pull:report:1", [("Explosion", 500), ("Ground", 250)]),
                            ("pull:report:2", [("Ground", 1000)]),
                            ("pull:extra:1", [("Ground", 2000)])]:
        for mode in ("damage_bars", "table"):
            row, = table.rows_by_combined_view[f"{scope}::{mode}"]
            assert [(b.label, b.value) for b in row.details.bar_chart.bars] == expected
            assert row.details.bar_chart_position == "before"
            assert row.details.bar_chart.unit_label == "damage"
            assert len({b.id for b in row.details.bar_chart.bars}) == len(expected)
            assert sum(b.value for b in row.details.bar_chart.bars) == row.cells["damage" if mode == "damage_bars" else "total_damage"].value
            assert row.details.groups  # timeline remains available after the chart
    for mode in ("damage_bars", "table"):
        row, = table.rows_by_combined_view[f"pull:report:3::{mode}"]
        assert row.details is None


def test_source_chart_handles_missing_labels_and_keeps_distinct_spell_ids():
    from who_messed_up.services.view_models.avoidable_damage import _build_row_details

    base = AvoidableDamageEvent("report", "Alice", 1, "Boss", 1, 1000, 1000, 10, "Hazard", 100)
    events = [base, replace(base, ability_id=20, damage_amount=200),
              replace(base, ability_id=30, ability_label=None, damage_amount=50),
              replace(base, ability_id=None, ability_label="Legacy hazard", damage_amount=60),
              replace(base, ability_id=None, ability_label="Legacy hazard", damage_amount=40),
              replace(base, ability_id=None, ability_label=None, damage_amount=10),
              replace(base, ability_id=40, ability_label="Absorbed", damage_amount=0)]
    details = _build_row_details("report", events, source_reports=["report"])
    bars = details.bar_chart.bars
    assert len(bars) == 5
    assert {b.id: b.value for b in bars} == {"spell:10": 100, "spell:20": 200, "spell:30": 50,
                                           "name:legacy hazard": 100, "name:unknown source": 10}
    assert next(b.label for b in bars if b.id == "spell:30") == "Spell 30"
    assert bars[0].display == "200"
    assert _build_row_details("report", [events[-1]], source_reports=["report"]).bar_chart is None
