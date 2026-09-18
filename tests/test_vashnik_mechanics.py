"""Mechanics regressions for uncertain credit, censored lives and merged pulls."""
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from who_messed_up.api import Fight
from who_messed_up.services.mechanics_context import PullContext
from who_messed_up.services.vashnik_mechanics import build_vashnik_mechanics_summary, fetch_vashnik_mechanics_summary
from who_messed_up.services.vashnik_mechanics_adds import build_adds
from who_messed_up.services.vashnik_mechanics_bile import build_bile
from who_messed_up.services.vashnik_mechanics_infections import build_dispels, build_stygian
from who_messed_up.services.vashnik_mechanics_models import (
    BILE, CATALYST, COATING, EXPLODING, FROTH, FROTH_DAMAGE, IMBIBE, LEAK, MALIGNANCE,
    MISSED_BILE, REPORT_ID, STYGIAN, SURGE, TOTEM_SUMMON, VIEWS,
)
from who_messed_up.services.vashnik_mechanics_waves import build_froth, build_totems, build_totem_waves
from who_messed_up.services.view_models.vashnik_mechanics import build_vashnik_mechanics_report_page
from who_messed_up.services.report_registry import build_report_job_request


def event(at, kind, aid, target=1, source=90, **extra):
    return dict(timestamp=at, type=kind, abilityGameID=aid, targetID=target, sourceID=source, **extra)


def context(**streams):
    fight = Fight(id=13, name="Vashnik the Malignant", start=0, end=100000, kill=False,
                  difficulty=5, encounter_id=3455, friendly_player_ids=[1, 2, 3, 4])
    return PullContext("Nr7yQvGqjz8atHYc", fight, 1, streams,
                       {1: "Alice", 2: "Bob", 3: "Claire", 4: "Dan", 10: "Pet", 90: "Vashnik",
                        91: "Malignant Totem", 92: "Burning Venom", 93: "Shrouded Venom"}, {10: 1})


def test_recorded_early_wave_inference_and_future_boundary_stay_distinct():
    data = json.loads((Path(__file__).parent / "fixtures/vashnik_wave_inference.json").read_text())
    ctx = context(**data["streams"])
    f = data["fight"]
    ctx.fight = replace(ctx.fight, start=f["startTime"], end=f["endTime"], friendly_player_ids=data["players"])
    ctx.names = {int(k): v for k, v in data["actors"].items()}
    rows = build_totems(ctx)
    assert sum(r.values["cleared"] for r in rows) == 4
    assert sum(r.values["inferred"] for r in rows) == 3
    assert sum(r.values["group_only"] for r in rows) == 1
    details = [d for r in rows for d in r.details if "Inferred single carrier" in d.badges]
    assert all("Lazerzpewpew" in d.description and "Early release" in d.description for d in details)
    assert all(not r.contributions for r in rows)


def test_totems_preserve_pre_spawn_wave_late_death_and_cleanup():
    ctx = context(debuffs=[event(1000, "applydebuff", FROTH), event(7000, "removedebuff", FROTH)],
                  enemy_casts=[event(10000, "cast", IMBIBE)], totems=[
                      event(11000, "summon", TOTEM_SUMMON, target=91, targetInstance=1),
                      event(12000, "death", 0, target=91, targetInstance=1),
                      event(11000, "summon", TOTEM_SUMMON, target=91, targetInstance=2),
                      event(80000, "cast", MALIGNANCE, source=91, sourceInstance=2),
                      event(81000, "death", 0, target=91, targetInstance=2),
                      event(11000, "summon", TOTEM_SUMMON, target=91, targetInstance=3),
                      event(99500, "death", 0, target=91, targetInstance=3)])
    row, = build_totems(ctx)
    assert (row.values["spawned"], row.values["cleared"], row.values["detonated"], row.values["unresolved"]) == (3, 1, 1, 1)
    assert row.values["inferred"] == row.values["late_clears"] == 1


def test_froth_exposure_uses_actual_assignment_and_includes_absorbed_hits():
    ctx = context(debuffs=[event(1000, "applydebuff", FROTH), event(7000, "removedebuff", FROTH),
                          event(1000, "applydebuff", 1281910, target=2)], damage_taken=[
        event(2000, "damage", FROTH_DAMAGE, amount=100),
        event(2000, "damage", FROTH_DAMAGE, target=2, amount=0, absorbed=100),
        event(2100, "damage", FROTH_DAMAGE, target=3, amount=0, hitType=10),
        event(7100, "damage", FROTH_DAMAGE, amount=100)])
    row, = build_froth(ctx)
    assert row.players["assigned"] == ["Alice"]
    assert row.players["splash_victims"] == ["Bob"]
    assert row.values["splash_hits"] == 1


def test_dispels_match_one_life_preserve_unknown_application_and_healer_credit():
    ctx = context(debuffs=[event(1000, "applydebuff", EXPLODING), event(3000, "removedebuff", EXPLODING),
                          event(9000, "applydebuff", EXPLODING)], dispels=[
        event(3010, "dispel", 123, source=2, extraAbilityGameID=EXPLODING),
        event(8000, "dispel", 123, target=3, source=2, extraAbilityGameID=EXPLODING)])
    rows = build_dispels(ctx)
    assert sum(r.values["assigned"] for r in rows) == 2
    assert sum(r.values["dispelled"] for r in rows) == 2
    assert sum(r.values["unmatched"] for r in rows) == 1
    assert sum(r.values["not_dispelled"] for r in rows) == 1
    assert sum(r.dispel_counts.get("Bob", 0) for r in rows) == 2
    assert rows[0].dispels[0].delay == 2.01


def test_stygian_uses_healer_id_and_censors_death_cleanup_and_unconfirmed_removal():
    debuffs = [event(1000, "applydebuff", STYGIAN, target=p) for p in range(1, 5)]
    debuffs += [event(t, "removedebuff", STYGIAN, target=p) for p, t in [(1, 3000), (2, 4000), (3, 99500), (4, 5000)]]
    ctx = context(debuffs=debuffs, deaths=[event(4010, "death", 0, target=2)], stygian_absorbs=[
        event(t, "healabsorbed", STYGIAN, target=p, healerID=4, amount=100) for p, t in [(1, 3000), (2, 4000), (3, 99500)]])
    row, = build_stygian(ctx)
    assert row.values["cleared"] == 1
    assert row.values["unresolved"] == 3
    assert row.values["average"] == 2
    assert row.contributions == {"Dan": 300}
    assert "Vashnik" not in row.contributions


def test_add_death_effects_shields_pet_credit_and_reused_instance():
    shield = event(1000, "applybuff", COATING, target=93, targetInstance=1, absorb=100)
    ctx = context(add_summons=[event(1000, "summon", 1, target=93, targetInstance=1),
                               event(20000, "summon", 1, target=93, targetInstance=1)],
                  enemy_buffs=[shield, dict(shield)], add_damage=[
                      event(1500, "damage", 1, source=10, target=93, targetInstance=1, amount=50, absorbed=100, overkill=25),
                      event(1600, "damage", 1, source=10, target=93, targetInstance=1, amount=0, absorbed=75),
                      event(1700, "damage", 1, source=10, target=93, targetInstance=1, amount=0, absorbed=900, hitType=10),
                      event(5000, "damage", 1, source=1, target=93, targetInstance=1, amount=999),
                      event(8000, "damage", 1, source=1, target=93, targetInstance=1, amount=999)],
                  enemy_deaths=[event(2000, "death", 0, target=93, targetInstance=1)],
                  enemy_casts=[event(2200, "cast", SURGE, source=93, sourceInstance=1),
                               event(2200, "cast", SURGE, source=92, sourceInstance=1),
                               event(25000, "cast", LEAK, source=93, sourceInstance=1)])
    rows = build_adds(ctx)
    first = rows[0]
    assert first.contributions == {"Alice": 225}
    assert (first.values["health"], first.values["shield"], first.values["kills"], first.values["surge"]) == (50, 175, 1, 1)
    assert len([d for d in first.details if d.label == "Shield applied"]) == 1
    assert sum(r.values["close"] for r in rows) == 1
    assert len(rows) == 3
    assert rows[-1].values["status"] == "Leaked"


def test_bile_keeps_cast_without_impacts_and_groups_bursts_without_counting_circles():
    ctx = context(enemy_casts=[event(1000, "cast", CATALYST), event(1001, "cast", 1282516),
                               event(20000, "cast", CATALYST)], damage_taken=[
        event(2000, "damage", BILE, amount=0, absorbed=100),
        event(2000, "damage", MISSED_BILE, amount=100),
        event(2090, "damage", MISSED_BILE, target=2, amount=100),
        event(2180, "damage", MISSED_BILE, amount=100)])
    first, second = build_bile(ctx)
    assert first.soak_counts == {"Alice": 1}
    assert first.values["bursts"] == 2
    assert first.values["damage"] == 300
    assert second.values["bursts"] == second.values["soaks"] == 0


def summary_for(ctx):
    return build_vashnik_mechanics_summary(report_code=ctx.code, fights=[ctx.fight],
                                           streams={name: {ctx.fight.id: es} for name, es in ctx.streams.items()},
                                           actor_names=ctx.names, actor_classes={1: "Mage"}, actor_owners=ctx.owners)


def test_page_scopes_reused_fight_ids_and_player_bars_by_report():
    ctx = context(enemy_casts=[event(1000, "cast", CATALYST)], damage_taken=[event(2000, "damage", BILE)])
    summary = summary_for(ctx)
    ctx.code = "AZfwY8vr1DanQbch"
    ctx.streams["damage_taken"] = [event(2000, "damage", BILE, target=2)]
    other = summary_for(ctx)
    from who_messed_up.services.report_pulls import merge_report_pulls
    summary.pulls = merge_report_pulls([summary.pulls, other.pulls])
    summary.source_reports += other.source_reports
    for view in summary.sets:
        summary.sets[view] += other.sets[view]
    page = build_vashnik_mechanics_report_page(summary).model_dump(by_alias=True)
    table = page["content"]["table"]
    assert len(table["secondaryViewControl"]["options"]) == 6
    assert table["subViewControlByView"]["totems"]["defaultValue"] == "totems-bars"
    for pull, expected in zip(summary.pulls, ["Alice", "Bob"]):
        rows = table["rowsByCombinedView"][f"{pull.view_id}::bile::bile-bars"]
        assert [r["cells"]["contribution"]["label"] for r in rows] == [expected]
    assert len({r["id"] for r in table["rowsByCombinedView"]["aggregate::bile"]}) == 2


def test_fetch_forces_mythic_encounter_and_deduplicates_reports():
    ctx = context()
    fights = [ctx.fight, replace(ctx.fight, id=14, difficulty=4), replace(ctx.fight, id=15, encounter_id=3445)]
    with patch("who_messed_up.services.vashnik_mechanics.load_env"), \
         patch("who_messed_up.services.vashnik_mechanics._resolve_token", return_value="token"), \
         patch("who_messed_up.services.vashnik_mechanics.fetch_fights", return_value=(fights, ctx.names, {}, ctx.owners)), \
         patch("who_messed_up.services.vashnik_mechanics._fetch_streams", return_value={}) as fetch:
        summary = fetch_vashnik_mechanics_summary(report_code=ctx.code, extra_report_codes=[ctx.code], difficulty="heroic")
    assert summary.pull_count == 1
    assert fetch.call_count == 1
    assert [f.id for f in fetch.call_args.args[1]] == [13]


def test_mechanics_job_and_empty_page():
    job, payload, fresh = build_report_job_request(REPORT_ID, {"report_codes": ["Nr7yQvGqjz8atHYc"], "fresh_run": True})
    assert job == "v2_report_vashnik_mechanics" and fresh and payload["difficulty"] == "mythic"
    page = build_vashnik_mechanics_report_page(summary_for(context()))
    assert page.report_id == REPORT_ID


def test_wave_roster_keeps_zero_clears_and_missing_releases():
    ctx = context(debuffs=[event(1000, "applydebuff", FROTH), event(7000, "removedebuff", FROTH),
                          event(1000, "applydebuff", FROTH, target=2),
                          event(40000, "applydebuff", FROTH, target=3)],
                  totems=[event(10000, "summon", TOTEM_SUMMON, target=91),
                          event(12000, "death", 0, target=91)])
    first, second = build_totem_waves(ctx)
    assert first.players["carriers"] == ["Alice", "Bob"]
    assert first.values["released"] == 1 and first.values["cleared"] == 1
    assert "no release observed" in first.details[1].description
    assert second.players["carriers"] == ["Claire"]
    assert second.values["cleared"] == 0 and second.values["release"] == "Not observed"
    assert second.values["result"] == "No associated clears observed"


def test_wave_late_removals_are_separate_from_successful_clears():
    ctx = context(debuffs=[event(1000, "applydebuff", FROTH), event(7000, "removedebuff", FROTH)],
                  totems=[event(2000, "summon", TOTEM_SUMMON, target=91),
                          event(6000, "cast", MALIGNANCE, source=91), event(8000, "death", 0, target=91)])
    row, = build_totem_waves(ctx)
    assert row.values["late_clears"] == 1 and row.values["cleared"] == 0


def test_totem_bars_preserve_unknowns_and_wave_scopes_in_merged_reports():
    ctx = context(enemy_casts=[event(1000, "cast", IMBIBE)],
                  debuffs=[event(2000, "applydebuff", FROTH), event(8000, "removedebuff", FROTH)],
                  totems=[event(1500, "summon", TOTEM_SUMMON, target=91, targetInstance=i) for i in range(3)] + [
                      event(9000, "death", 0, target=91, targetInstance=0),
                      event(50000, "cast", MALIGNANCE, source=91, sourceInstance=1)])
    summary = summary_for(ctx)
    other_ctx = context(debuffs=[event(2000, "applydebuff", FROTH, target=2)])
    other_ctx.code = "AZfwY8vr1DanQbch"
    other = summary_for(other_ctx)
    from who_messed_up.services.report_pulls import merge_report_pulls
    summary.pulls = merge_report_pulls([summary.pulls, other.pulls])
    summary.source_reports += other.source_reports
    for view in summary.sets:
        summary.sets[view] += other.sets[view]
    page = build_vashnik_mechanics_report_page(summary).model_dump(by_alias=True)
    table = page["content"]["table"]
    bar, = table["rowsByCombinedView"]["aggregate::totems::totems-bars"]
    cell = bar["cells"]["outcomes"]
    assert cell["value"] == 3
    assert {part["id"]: part["value"] for part in cell["outcomes"]} == {"cleared": 1, "detonated": 1, "unresolved": 1}
    assert all(g["title"] != "Totem outcomes" for g in bar["details"]["groups"])
    assert "outcomes" not in bar["cells"]["set"]  # Existing cells retain their serialization contract.
    for pull, expected in zip(summary.pulls, ["Alice", "Bob"]):
        row, = table["rowsByCombinedView"][f"{pull.view_id}::totems::totems-waves"]
        assert [p["name"] for p in row["cells"]["carriers"]["players"]] == [expected]
        metrics = page["summaryByCombinedView"][f"{pull.view_id}::totems::totems-waves"]
        assert next(m["value"] for m in metrics if m["id"] == "assignments") == 1
    wave, = table["rowsByCombinedView"][f"{summary.pulls[0].view_id}::totems::totems-waves"]
    assert wave["cells"]["carriers"]["players"][0]["colorToken"] == "mage"


def test_compact_tables_have_three_columns_and_preserve_evidence():
    ctx = context(debuffs=[event(1000, "applydebuff", FROTH), event(7000, "removedebuff", FROTH)],
                  damage_taken=[event(2000, "damage", FROTH_DAMAGE, target=2, amount=100)])
    summary = summary_for(ctx)
    source = summary.sets["froth"][0]
    page = build_vashnik_mechanics_report_page(summary).model_dump(by_alias=True)
    table = page["content"]["table"]
    assert table["layout"] == "compact"
    for columns in table["columnsByView"].values():
        assert len(columns) <= 3
        assert all(column["id"] != "time" for column in columns)
    row, = table["rowsByCombinedView"]["aggregate::froth"]
    assert row["cells"]["set"]["label"] == "0:01.00"
    assert row["cells"]["exposure"]["metrics"][0]["value"] == 1
    assert row["details"]["layout"] == "compact"
    assert sum(len(g["items"]) for g in row["details"]["groups"]) == len(source.details)
    assert row["details"]["barChart"]["bars"][0]["label"] == "Bob"
    assert row["details"]["barChart"]["bars"][0]["value"] == 1
    assert source.players["assigned"] == ["Alice"]  # Victim bars do not change carrier assignment.


def test_compact_stygian_keeps_supported_clear_timing_and_unknown_outcomes():
    ctx = context(debuffs=[event(1000, "applydebuff", STYGIAN), event(3000, "removedebuff", STYGIAN),
                          event(1000, "applydebuff", STYGIAN, target=2)],
                  stygian_absorbs=[event(3000, "healabsorbed", STYGIAN, amount=1200000, healerID=3)])
    page = build_vashnik_mechanics_report_page(summary_for(ctx)).model_dump(by_alias=True)
    row, = page["content"]["table"]["rowsByCombinedView"]["aggregate::stygian"]
    assert {x["id"]: x["value"] for x in row["cells"]["outcomes"]["outcomes"]} == {"cleared": 1, "unresolved": 1}
    metrics = {m["id"]: m for m in row["details"]["metrics"]}
    assert metrics["average"]["display"] == "2.00s"
    assert metrics["healing"]["value"] == 1200000 and metrics["healing"]["display"] == "1.20m"
    assert next(m["value"] for m in page["summaryByCombinedView"]["aggregate::stygian"] if m["id"] == "average") == 2


def test_compact_metrics_keep_text_times_and_unmatched_dispel_evidence():
    from who_messed_up.services.view_models.compact_mechanics import metric
    assert metric("release", "First release", {"release": "0:08.00"}).format == "text"
    ctx = context(dispels=[event(8000, "dispel", 123, target=3, source=2, extraAbilityGameID=EXPLODING)])
    row, = build_vashnik_mechanics_report_page(summary_for(ctx)).content.table.rows_by_combined_view["aggregate::dispels"]
    assert row.cells["outcomes"].outcomes[0].value == 1
    assert next(m.value for m in row.details.metrics if m.id == "unmatched") == 1
    assert "application and delay unknown" in row.details.groups[0].items[0].description
