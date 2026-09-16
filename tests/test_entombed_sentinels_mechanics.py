"""Regression coverage for assignment attribution, cleanup, and reused NPC IDs."""
from dataclasses import replace
from unittest.mock import patch

import pytest

from who_messed_up.api import Fight
from who_messed_up.services.entombed_sentinels_mechanics import (
    build_sentinels_mechanics_summary, fetch_sentinels_mechanics_summary,
)
from who_messed_up.services.entombed_sentinels_mechanics_analysis import (
    PullContext, build_coagulations, build_droplets, build_helical,
    build_miasma, build_protovenom,
)
from who_messed_up.services.entombed_sentinels_mechanics_events import aura_lives
from who_messed_up.services.entombed_sentinels_mechanics_resolution import build_dispels, build_intermissions
from who_messed_up.services.entombed_sentinels_mechanics_models import REPORT_ID, VIEWS
from who_messed_up.services.report_registry import build_report_job_request
from who_messed_up.services.view_models.entombed_sentinels_mechanics import build_sentinels_mechanics_report_page


def event(at, kind, aid, target=1, source=90, **extra):
    return dict(timestamp=at, type=kind, abilityGameID=aid, targetID=target, sourceID=source, **extra)


def context(**streams):
    fight = Fight(id=15, name="Entombed Sentinels", start=0, end=100000, kill=False,
                  difficulty=5, encounter_id=3445, friendly_player_ids=[1, 2, 3, 4])
    return PullContext("J3y9gP2bqmkphY7f", fight, 1, streams,
                       {1: "Alice", 2: "Bob", 3: "Claire", 4: "Dan", 10: "Pet", 90: "Vashnik",
                        91: "Venom Coagulation", 92: "Venom Coagulation"}, {10: 1})


def test_protovenom_assignments_do_not_require_damage_and_splash_does_not_assign():
    ctx = context(enemy_casts=[event(1000, "cast", 1296878)], debuffs=[
        event(1500, "applydebuff", 1296880), event(1700, "removedebuff", 1296880),
        event(2100, "applydebuff", 1296880, target=2), event(3500, "removedebuff", 1296880, target=2),
    ], damage_taken=[event(2500, "damage", 1296962, target=3, amount=100)])
    row, = build_protovenom(ctx)
    assert row.players["assigned"] == ["Alice", "Bob"]
    assert row.values["assigned"] == row.values["removed"] == 2
    assert row.values["eruption_hits"] == 1
    assert "Claire" in row.details[-1].label


def test_death_and_wipe_cleanup_are_not_aura_clears():
    ctx = context(enemy_casts=[event(1000, "cast", 1296878)], debuffs=[
        event(1500, "applydebuff", 1296880), event(3000, "removedebuff", 1296880),
        event(1500, "applydebuff", 1296880, target=2), event(99900, "removedebuff", 1296880, target=2),
        event(1500, "applydebuff", 1296880, target=3),
    ], deaths=[event(3010, "death", 0)])
    row, = build_protovenom(ctx)
    assert (row.values["removed"], row.values["deaths"], row.values["unresolved"]) == (0, 1, 2)


def test_missing_removal_is_censored_before_a_later_application_and_death():
    lives = aura_lives([event(1000, "applydebuff", 1296880),
                        event(5000, "applydebuff", 1296880)], {1296880}, {1})
    assert lives[0].status([event(9000, "death", 0)], 10000) == ("Removal not logged before reapplication", 5000)


def test_helical_deduplicates_stasis_and_does_not_invent_initial_stacks_or_partners():
    ctx = context(enemy_casts=[event(1000, "cast", 1284588), event(1002, "cast", 1284606)], debuffs=[
        event(1100, "applydebuff", 1284590), event(1200, "applydebuffstack", 1284590, stack=5),
        event(3000, "removedebuff", 1284590), event(3010, "applydebuff", 1284947),
        event(1100, "applydebuff", 1284590, target=2, stack=3),
        event(29099, "removedebuff", 1284590, target=2),
        event(1100, "applydebuff", 1284590, target=3), event(4000, "removedebuff", 1284590, target=3),
    ], damage_taken=[event(3010, "damage", 1284941, target=3, amount=100)])
    row, = build_helical(ctx)
    assert row.values["assigned"] == 3
    assert row.values["failures"] == 1
    assert row.values["removed"] == 1  # splash on Claire is not her failure aura
    assert row.values["unresolved"] == 2
    assert "Initial stacks: not logged" in row.details[0].badges
    assert any("5 stacks" in badge for badge in row.details[0].badges)
    assert "Initial stacks: 3" in row.details[1].badges


def test_miasma_keeps_empty_cast_and_counts_absorbed_soaks_and_nearby_deaths():
    ctx = context(enemy_casts=[event(1000, "cast", 1288232), event(99000, "cast", 1288232)],
                  debuffs=[event(1500, "applydebuff", 1288260)],
                  damage_taken=[event(9500, "damage", 1288282, target=2, amount=0, absorbed=100),
                                event(9500, "damage", 1288282, target=3, amount=100),
                                event(9500, "damage", 1288282, target=10, amount=100)],
                  deaths=[event(9600, "death", 0, target=2), event(12500, "death", 0, target=3)])
    soaked, empty = build_miasma(ctx)
    assert soaked.players["marked"] == ["Alice"]
    assert soaked.players["soakers"] == ["Bob", "Claire"]
    assert soaked.values["soakers"] == 2
    assert soaked.values["deaths"] == 1
    assert empty.values["soakers"] == 0
    assert empty.values["impact"] == "Not observed"


def test_droplets_count_pop_hits_and_burst_clusters_separately_from_victims():
    ctx = context(enemy_casts=[event(1000, "cast", 1284434), event(50000, "cast", 1284434)],
                  damage_taken=[event(5000, "damage", 1284451, amount=0, absorbed=100),
                                event(5100, "damage", 1284451, amount=100),
                                event(15000, "damage", 1284452, amount=100),
                                event(15010, "damage", 1284452, target=2, amount=100),
                                event(15500, "damage", 1284452, target=3, amount=100)])
    row, empty = build_droplets(ctx)
    assert row.values["pops"] == 2
    assert row.soak_counts == {"Alice": 2}
    assert row.values["bursts"] == 2
    assert row.values["blast_hits"] == 3
    assert empty.values["pops"] == 0
    assert empty.soak_counts == {}


@pytest.mark.parametrize("instance_fields", [{}, {"sourceInstance": 1, "targetInstance": 1}])
def test_coagulations_separate_reused_ids_and_credit_pets_without_overkill(instance_fields):
    ctx = context(enemy_casts=[event(1000, "cast", 1284251), event(50000, "cast", 1284251)],
                  enemy_buffs=[event(5000, "applybuff", 1284257, target=91, source=91, **instance_fields),
                               event(10000, "removebuff", 1284257, target=91, source=91, **instance_fields),
                               event(55000, "applybuff", 1284257, target=91, source=91, **instance_fields)],
                  add_damage=[event(6000, "damage", 1, target=91, source=10, amount=100, **instance_fields),
                              event(10000, "damage", 1, target=91, source=2, amount=500, overkill=100, **instance_fields),
                              event(10020, "damage", 1, target=91, source=2, amount=1, **instance_fields),
                              event(56000, "damage", 1, target=91, source=2, amount=200, **instance_fields)],
                  enemy_deaths=[event(10010, "death", 0, target=91, **instance_fields)],
                  damage_taken=[event(9000, "damage", 1284258, source=91, amount=80, **instance_fields),
                                event(57000, "damage", 1284258, source=91, amount=90, **instance_fields)])
    first, second = build_coagulations(ctx)
    assert first.contributions == {"Alice": 100, "Bob": 500}  # WCL amount already excludes overkill
    assert first.values["status"] == "Killed"
    assert first.values["contaminate"] == 80
    assert first.values["duration"] == 5.01
    assert first.values["delay"] == 5
    assert second.contributions == {"Bob": 200}
    assert second.values["contaminate"] == 90
    assert second.values["status"] == "No death observed"


def test_coagulation_killing_blow_fallback_and_empty_summon():
    ctx = context(enemy_casts=[event(1000, "cast", 1284251), event(99000, "cast", 1284251)],
                  add_damage=[event(5000, "damage", 1, target=91, source=1, amount=100),
                              event(8000, "damage", 1, target=91, source=1, amount=300, overkill=50)])
    first, last = build_coagulations(ctx)
    assert first.values["status"] == "Killed"
    assert first.values["duration"] == 3
    assert last.values["status"] == "No add instance observed"


def test_buff_only_actor_discrepancy_is_not_a_confirmed_add():
    ctx = context(enemy_buffs=[event(5000, "applybuff", 1284257, target=92, source=92)],
                  enemy_casts=[event(5000, "cast", 1284257, source=91)])
    rows = build_coagulations(ctx)
    assert len(rows) == 2
    assert {r.values["status"] for r in rows} == {"Unmatched buff signal", "No death observed"}


def _summary(ctx):
    return build_sentinels_mechanics_summary(
        report_code=ctx.code, fights=[ctx.fight], streams={k: {ctx.fight.id: v} for k, v in ctx.streams.items()},
        actor_names=ctx.names, actor_classes={1: "Mage"}, actor_owners=ctx.owners,
    )


def test_page_selectors_and_metrics_scope_by_report_and_fight():
    ctx = context(enemy_casts=[event(1000, "cast", 1288232)])
    first = _summary(ctx)
    second = _summary(replace(ctx, code="ZARtb8Dxjhg9H4BF", streams={}))
    merged = replace(first, sets={key: first.sets[key] + second.sets[key] for key in VIEWS},
                     pulls=first.pulls + second.pulls, source_reports=[ctx.code, second.report_code])
    page = build_sentinels_mechanics_report_page(merged).model_dump(by_alias=True)
    table = page["content"]["table"]
    assert {option["value"] for option in table["secondaryViewControl"]["options"]} == {
        "protovenom", "helical-toxins", "miasma", "droplets", "coagulations", "dispels", "intermission",
    }
    assert "side-swaps" not in table["columnsByView"]
    assert all("side-swaps" not in key for key in table["rowsByCombinedView"])
    assert len(table["viewControl"]["options"]) == 3
    key1, key2 = [p.view_id + "::miasma" for p in merged.pulls]
    assert len(table["rowsByCombinedView"][key1]) == 1
    assert table["rowsByCombinedView"][key2] == []
    assert next(m["value"] for m in page["summaryByCombinedView"][key2] if m["id"] == "sets") == 0
    all_rows = [r for view in VIEWS for r in table["rowsByCombinedView"]["aggregate::" + view]]
    assert len({r["id"] for r in all_rows}) == len(all_rows)


def test_live_fetch_filters_mythic_encounter_and_merges_reports_without_id_collisions():
    ctx = context()
    wrong = replace(ctx.fight, id=99, difficulty=4)
    fragment = replace(ctx.fight, id=20, encounter_id=0)
    module = "who_messed_up.services.entombed_sentinels_mechanics"
    with patch(module + ".load_env"), patch(module + "._resolve_token", return_value="token"), \
            patch(module + ".fetch_fights", return_value=([ctx.fight, wrong, fragment], ctx.names, {}, ctx.owners)), \
            patch(module + "._fetch_streams", return_value={}) as fetch:
        summary = fetch_sentinels_mechanics_summary(report_code=ctx.code, difficulty=None,
                                                    extra_report_codes=[ctx.code, "ZARtb8Dxjhg9H4BF"])
    assert summary.pull_count == 2
    assert "side-swaps" not in summary.sets
    assert all([f.id for f in call.args[1]] == [15] for call in fetch.call_args_list)
    assert len({p.view_id for p in summary.pulls}) == 2


def test_job_registration_executes_real_page_builder():
    import app
    job, payload, fresh = build_report_job_request(REPORT_ID, {"report_codes": ["J3y9gP2bqmkphY7f"], "fresh_run": True})
    assert job == "v2_report_entombed_sentinels_mechanics"
    assert fresh and payload["difficulty"] == "mythic"
    with patch.object(app, "fetch_sentinels_mechanics_summary", return_value=_summary(context())):
        page = app._execute_v2_sentinels_mechanics_job(payload)
    assert page["reportId"] == REPORT_ID
    assert set(VIEWS).issubset(page["content"]["table"]["columnsByView"])


def test_droplet_bars_sum_all_waves_and_isolate_pulls_and_report_ids():
    ctx = context(enemy_casts=[event(1000, "cast", 1284434), event(50000, "cast", 1284434)],
                  damage_taken=[event(2000, "damage", 1284451, amount=0, absorbed=100),
                                event(3000, "damage", 1284451, amount=100),
                                event(4000, "damage", 1284451, target=2, amount=100),
                                event(51000, "damage", 1284451, amount=100),
                                event(51000, "damage", 1284451, target=10, amount=100),
                                event(55000, "damage", 1284452, target=3, amount=100)])
    first = _summary(ctx)
    other_pull = _summary(replace(ctx, fight=replace(ctx.fight, id=16), streams={
        "enemy_casts": [event(1000, "cast", 1284434)],
        "damage_taken": [event(2000, "damage", 1284451, target=3, amount=100)],
    }))
    other_report = _summary(replace(ctx, code="ZARtb8Dxjhg9H4BF", streams={
        "enemy_casts": [event(1000, "cast", 1284434)],
        "damage_taken": [event(2000, "damage", 1284451, target=2, amount=100)],
    }))
    empty = _summary(replace(ctx, fight=replace(ctx.fight, id=17), streams={}))
    summaries = [first, other_pull, other_report, empty]
    merged = replace(first,
                     sets={key: [row for s in summaries for row in s.sets[key]] for key in VIEWS},
                     pulls=[pull for s in summaries for pull in s.pulls],
                     source_reports=[ctx.code, other_report.report_code])
    page = build_sentinels_mechanics_report_page(merged).model_dump(by_alias=True)
    table = page["content"]["table"]
    assert table["subViewControlByView"]["droplets"]["defaultValue"] == "droplets-by-player"
    assert table["columnsByView"]["droplets-by-player"][0]["cellKind"] == "relative_bar"
    assert table["defaultSortByView"]["droplets-by-player"] == {"columnId": "soaks", "direction": "desc"}

    def bars(scope):
        return [r["cells"]["soaks"] for r in table["rowsByCombinedView"][f"{scope}::droplets::droplets-by-player"]]

    for scope, expected in [("aggregate", {"Alice": 3, "Bob": 2, "Claire": 1}),
                            (first.pulls[0].view_id, {"Alice": 3, "Bob": 1}),
                            (other_pull.pulls[0].view_id, {"Claire": 1}),
                            (other_report.pulls[0].view_id, {"Bob": 1}),
                            (empty.pulls[0].view_id, {})]:
        cells = bars(scope)
        assert {cell["label"]: cell["value"] for cell in cells} == expected
        assert all(cell["maxValue"] == max(expected.values()) for cell in cells)
        assert all(cell["unitLabel"] == "droplet soaks" for cell in cells)
        metrics = {m["id"]: m["value"] for m in page["summaryByCombinedView"][f"{scope}::droplets"]}
        assert sum(expected.values()) == metrics["pops"]
        assert table["rowsByCombinedView"][f"{scope}::droplets::droplets-by-wave"] == table["rowsByCombinedView"][f"{scope}::droplets"]
    assert next(cell for cell in bars("aggregate") if cell["label"] == "Alice")["colorToken"] == "mage"
    waves = table["rowsByCombinedView"][f"{first.pulls[0].view_id}::droplets::droplets-by-wave"]
    assert [{bar["label"]: bar["value"] for bar in wave["details"]["barChart"]["bars"]}
            for wave in waves] == [{"Alice": 2, "Bob": 1}, {"Alice": 1}]
    assert waves[0]["details"]["barChart"]["bars"][0]["colorToken"] == "mage"
    assert waves[0]["details"]["barChart"]["unitLabel"] == "droplet soaks"
    assert all(group["title"] != "Observed pops" for wave in waves for group in wave["details"]["groups"])
    assert waves[1]["details"]["groups"][0]["title"].startswith("Noxious Blast bursts")


def test_dispels_keep_staggered_targets_in_cast_sets_and_require_dispel_evidence():
    ctx = context(enemy_casts=[event(1000, "cast", 1284483), event(50000, "cast", 1284483)],
                  debuffs=[event(1400, "applydebuff", 1284471), event(1800, "removedebuff", 1284471),
                           event(3900, "applydebuff", 1284471, target=2),
                           event(5000, "removedebuff", 1284471, target=2),
                           event(51000, "applydebuff", 1284471)],
                  dispels=[event(1801, "dispel", 527, source=3, extraAbilityGameID=1284471),
                           event(4900, "dispel", 527, target=2, source=3, extraAbilityGameID=999),
                           event(53000, "dispel", 527, source=4, extraAbilityGameID=1284471)])
    first, second = build_dispels(ctx)
    assert first.values == {"assigned": 2, "dispelled": 1, "not_dispelled": 1}
    assert first.dispel_counts == {"Claire": 1}
    assert first.dispels[0].delay == pytest.approx(.401)
    assert second.dispel_counts == {"Dan": 1}
    assert any("No dispel event" in detail.description for detail in first.details)


def test_dispels_without_casts_and_reapplications_do_not_double_credit():
    ctx = context(debuffs=[event(1000, "applydebuff", 1284471),
                           event(3000, "applydebuff", 1284471, target=2),
                           event(50000, "applydebuff", 1284471)],
                  dispels=[event(51000, "dispel", 527, source=3, extraAbilityGameID=1284471)])
    first, second = build_dispels(ctx)
    assert first.values["assigned"] == 2
    assert first.values["dispelled"] == 0
    assert second.values["dispelled"] == 1


def test_mass_dispel_credits_each_removed_target_once_and_keeps_empty_cast():
    ctx = context(enemy_casts=[event(1000, "cast", 1284483), event(99000, "cast", 1284483)],
                  debuffs=[event(1500, "applydebuff", 1284471, target=target) for target in [1, 2]],
                  dispels=[event(3000, "dispel", 32375, source=3, target=target, extraAbilityGameID=1284471)
                           for target in [1, 2, 10]])
    row, empty = build_dispels(ctx)
    assert row.dispel_counts == {"Claire": 2}
    assert empty.values["assigned"] == 0
    table = build_sentinels_mechanics_report_page(_summary(ctx)).content.table
    players = table.rows_by_combined_view["aggregate::dispels"][0].cells["dispels"].players
    assert len({player.name for player in players}) == 2  # Stable React keys for simultaneous dispels.


def intermission_context():
    ctx = context(enemy_casts=[event(1000, "cast", 1284588), event(1002, "cast", 1284606)],
                  debuffs=[event(1100, "applydebuff", 1284590),
                           event(2500, "applydebuff", 1284590, target=2),
                           event(2000, "removedebuff", 1284590),
                           event(5000, "removedebuff", 1284590, target=2)],
                  enemy_buffs=[event(1000, "applybuff", 1284588, target=90),
                               event(6000, "removebuff", 1284588, target=90),
                               event(1002, "applybuff", 1284606, target=93),
                               event(6002, "removebuff", 1284606, target=93)],
                  boss_healing=[event(3000, "heal", 1284635, target=90, amount=100),
                                event(6001, "heal", 1284635, target=90, amount=500),
                                event(6002, "heal", 1284635, target=93, amount=200),
                                event(9000, "heal", 1284635, target=90, amount=999),
                                event(3000, "heal", 999, target=90, amount=999),
                                event(3000, "heal", 1284635, target=1, amount=999)])
    ctx.names.update({90: "Blood of Ula'tek", 93: "Breath of Ula'tek"})
    return ctx


def test_intermission_timer_starts_at_toxins_and_healing_includes_stasis_exit():
    row, = build_intermissions(intermission_context())
    assert row.start == 1100  # Not either boss's Stasis cast.
    assert row.values["status"] == "Cleared"
    assert row.values["duration"] == 3.9  # Includes the later application.
    assert row.values["resolution"] == "2 / 2"
    assert row.values["healing"] == 800
    assert row.boss_healing == {"Blood of Ula'tek": 600, "Breath of Ula'tek": 200}


@pytest.mark.parametrize("case", ["death", "burst", "expiry", "wipe", "missing"])
def test_intermission_failures_and_cleanup_are_not_fast_completions(case):
    ctx = intermission_context()
    if case == "death":
        ctx.streams["deaths"] = [event(5001, "death", 0, target=2)]
    elif case == "burst":
        ctx.streams["debuffs"].append(event(5001, "applydebuff", 1284947, target=2))
    elif case in {"expiry", "wipe"}:
        ctx.streams["debuffs"][-1]["timestamp"] = 30500 if case == "expiry" else 99999
    else:
        ctx.streams["debuffs"].pop()
    row, = build_intermissions(ctx)
    assert row.values["duration"] is None
    assert row.values["completed"] == 0
    assert row.values["status"] == ("Incomplete" if case in {"wipe", "missing"} else "Failed")
    assert row.values["healing"] == 800  # Failures still incur real healing.


def test_intermission_missing_removal_does_not_leak_into_next_window():
    ctx = intermission_context()
    ctx.streams["debuffs"].pop()
    ctx.streams["enemy_casts"].append(event(50000, "cast", 1284588))
    ctx.streams["debuffs"].extend([event(50100, "applydebuff", 1284590, target=2),
                                  event(52000, "removedebuff", 1284590, target=2)])
    first, second = build_intermissions(ctx)
    assert first.values["status"] == "Incomplete"
    assert second.values["duration"] == 1.9
    assert second.values["healing"] == 0
    assert build_intermissions(context(enemy_casts=[event(1000, "cast", 1284588)])) == []


def test_intermission_without_cast_or_stasis_end_keeps_observed_healing():
    ctx = intermission_context()
    ctx.streams["enemy_casts"] = []
    ctx.streams["enemy_buffs"] = []
    row, = build_intermissions(ctx)
    assert row.start == 1100 and row.values["duration"] == 3.9
    assert row.values["healing"] == 1799
    assert any("Stasis end not logged" in detail.badges for detail in row.details)


def test_dispel_bars_and_intermission_averages_isolate_report_and_pull_scopes():
    ctx = intermission_context()
    ctx.streams["debuffs"].append(event(10000, "applydebuff", 1284471))
    ctx.streams["dispels"] = [event(12000, "dispel", 527, source=3, extraAbilityGameID=1284471)]
    first = _summary(ctx)
    other = replace(ctx, code="ZARtb8Dxjhg9H4BF", streams={
        "debuffs": [event(1000, "applydebuff", 1284471), event(5000, "applydebuff", 1284590)],
        "dispels": [event(2000, "dispel", 527, source=4, extraAbilityGameID=1284471)],
    })
    second = _summary(other)
    merged = replace(first, sets={key: first.sets[key] + second.sets[key] for key in VIEWS},
                     pulls=first.pulls + second.pulls, source_reports=[ctx.code, other.code])
    page = build_sentinels_mechanics_report_page(merged).model_dump(by_alias=True)
    table = page["content"]["table"]
    for scope, expected in [("aggregate", {"Claire": 1, "Dan": 1}),
                            (first.pulls[0].view_id, {"Claire": 1}),
                            (second.pulls[0].view_id, {"Dan": 1})]:
        rows = table["rowsByCombinedView"][f"{scope}::dispels::dispels-by-healer"]
        assert {r["cells"]["dispels"]["label"]: r["cells"]["dispels"]["value"] for r in rows} == expected
    metrics = {m["id"]: m["value"] for m in page["summaryByCombinedView"]["aggregate::intermission"]}
    assert metrics["sets"] == 2 and metrics["completed"] == 1
    assert metrics["average"] == 3.9 and metrics["fastest"] == 3.9
    empty_metrics = {m["id"]: m["value"] for m in page["summaryByCombinedView"][f"{second.pulls[0].view_id}::intermission"]}
    assert empty_metrics["average"] is None
    assert next(m["display"] for m in page["summaryByCombinedView"][f"{second.pulls[0].view_id}::intermission"]
                if m["id"] == "average") == "—"
    rows = table["rowsByCombinedView"]["aggregate::intermission"]
    assert rows[0]["details"]["barChart"]["unitLabel"] == "healing"
    assert rows[0]["details"]["barChartPosition"] == "before"
    assert rows[1]["cells"]["duration"]["display"] == "Not completed"
