"""Orb attribution, Rain damage timing and report/pull isolation regressions."""
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from who_messed_up.api import Fight
from who_messed_up.services.boss_manifests import get_boss_manifest
from who_messed_up.services.mechanics_context import PullContext
from who_messed_up.services.nymrissa_mechanics import build_nymrissa_mechanics_summary, fetch_nymrissa_mechanics_summary
from who_messed_up.services.nymrissa_mechanics_models import FROST_ORB, RAIN_DAMAGE, REPORT_ID
from who_messed_up.services.nymrissa_mechanics_orbs import build_orb_sets
from who_messed_up.services.report_registry import build_report_job_request
from who_messed_up.services.view_models.nymrissa_mechanics import build_nymrissa_mechanics_report_page


def event(at, aid=FROST_ORB, target=1, **extra):
    return dict(timestamp=at, type="damage", abilityGameID=aid, targetID=target, sourceID=90, **extra)


def context(events=()):
    return PullContext("fCqgJN7QMWA2vFbT", Fight(
        id=15, name="Nymrissa Wavecaller", start=0, end=60000, kill=False,
        difficulty=5, encounter_id=3379, friendly_player_ids=[1, 2]),
        1, {"damage": list(events)}, {1: "Alice", 2: "Bob", 90: "Nymrissa", 10: "Pet"}, {10: 1})


def summary_for(ctx):
    return build_nymrissa_mechanics_summary(report_code=ctx.code, fights=[ctx.fight],
        streams={key: {ctx.fight.id: events} for key, events in ctx.streams.items()},
        actor_names=ctx.names, actor_classes={1: "Mage", 2: "Priest"}, actor_owners=ctx.owners)


def test_rain_includes_lingering_damage_and_exact_one_second_buffers():
    ctx = context([event(t, RAIN_DAMAGE, tick=True) for t in range(10000, 38001, 2000)] +
                  [event(t) for t in (8999, 9000, 9999, 10000, 30000, 38000, 38001, 39000, 39001)])
    sets = build_orb_sets(ctx)
    assert len(sets["orbs"]) == 9 and len(sets["overlaps"]) == 7
    rain, = sets["rain"]
    assert (rain.values["during"], rain.values["before"], rain.values["after"]) == (3, 2, 2)
    assert rain.values["pops"] == 7
    assert rain.soak_counts == {"Alice": 7}


def test_immune_and_simultaneous_contacts_count_but_dot_and_raid_victims_do_not():
    ctx = context([event(10000, RAIN_DAMAGE), event(11000, amount=0, hitType=0),
                   event(11002, amount=0), event(11002, target=2), event(11002, tick=True),
                   event(11002, 1313450, target=2), event(11002, 1266340), event(11002, 1313456),
                   {**event(11002), "type": "applydebuff"},
                   {**event(11002), "type": "refreshdebuff"}, event(11002, target=10)])
    rows = build_orb_sets(ctx)["orbs"]
    assert len(rows) == 3
    assert [r.players["soakers"] for r in rows] == [["Alice"], ["Alice"], ["Bob"]]
    assert len(build_orb_sets(ctx)["overlaps"]) == 1  # The other two are 2ms outside the buffer.


def test_missing_rain_is_not_invented_and_other_sources_or_pulls_are_excluded():
    ctx = context([event(12000), event(-1), event(60001),
                   {**event(12000, RAIN_DAMAGE), "sourceID": 1},
                   {**event(12000, RAIN_DAMAGE), "sourceID": 10}])
    sets = build_orb_sets(ctx)
    assert not sets["rain"] and not sets["overlaps"]
    assert len(sets["orbs"]) == 1
    assert sets["orbs"][0].values["timing"] == "Outside recorded Rain"


def test_tick_gaps_split_windows_and_pull_end_clips_display():
    ctx = context([event(10000, RAIN_DAMAGE), event(12500, RAIN_DAMAGE),
                   event(15001, RAIN_DAMAGE), event(60000, RAIN_DAMAGE), event(60000)])
    sets = build_orb_sets(ctx)
    assert len(sets["rain"]) == 3
    assert sets["rain"][0].values["duration"] == 2.5
    assert "to 1:00.00 (one-second buffer)" in sets["rain"][-1].details[0].description


def test_recorded_pull_preserves_immune_contacts_and_close_double_soaks():
    data = json.loads((Path(__file__).parent / "fixtures/nymrissa_orb_rain.json").read_text())
    ctx = context(data["damage"])
    ctx.fight = Fight(**data["fight"])
    ctx.names = {int(k): v for k, v in data["names"].items()}
    sets = build_orb_sets(ctx)
    assert {k: len(v) for k, v in sets.items()} == {"overlaps": 16, "rain": 3, "orbs": 17}
    assert [r.values["pops"] for r in sets["rain"]] == [0, 9, 7]
    assert all(r.values["during"] == 1 for r in sets["overlaps"])
    assert len([e for e in data["damage"] if e["abilityGameID"] == FROST_ORB and not e.get("tick") and e.get("hitType") == 0]) > 0


def test_fetch_filters_mythic_encounter_and_isolates_reused_fight_ids_across_reports():
    ctx = context([event(10000, RAIN_DAMAGE), event(10000)])
    report2 = "AZfwY8vr1DanQbch"
    fights = [ctx.fight, replace(ctx.fight, id=16, difficulty=4), replace(ctx.fight, id=17, encounter_id=3455)]
    with patch("who_messed_up.services.nymrissa_mechanics.load_env"), \
         patch("who_messed_up.services.nymrissa_mechanics._resolve_token", return_value="token"), \
         patch("who_messed_up.services.nymrissa_mechanics.fetch_fights", return_value=(fights, ctx.names, {1: "Mage"}, {})), \
         patch("who_messed_up.services.nymrissa_mechanics._fetch_streams", return_value={"damage": {15: ctx.streams["damage"]}}) as fetch:
        summary = fetch_nymrissa_mechanics_summary(report_code=ctx.code, extra_report_codes=[report2, ctx.code])
    assert fetch.call_count == 2 and all(call.args[1] == [ctx.fight] for call in fetch.call_args_list)
    assert summary.pull_count == 2
    page = build_nymrissa_mechanics_report_page(summary).model_dump(by_alias=True)
    table = page["content"]["table"]
    assert table["layout"] == "compact"
    assert len(table["rowsByCombinedView"]["aggregate::overlaps"]) == 2
    assert len({row["id"] for row in table["rowsByCombinedView"]["aggregate::overlaps"]}) == 2
    for pull in summary.pulls:
        assert len(table["rowsByCombinedView"][f"{pull.view_id}::overlaps"]) == 1
        bar, = table["rowsByCombinedView"][f"{pull.view_id}::overlaps::overlaps-bars"]
        assert bar["cells"]["contribution"]["value"] == 1
        assert bar["cells"]["contribution"]["colorToken"] == "mage"


def test_empty_report_and_zero_overlap_windows_remain_reviewable():
    page = build_nymrissa_mechanics_report_page(summary_for(context()))
    assert page.content.table.rows == []
    summary = summary_for(context([event(10000, RAIN_DAMAGE)]))
    page = build_nymrissa_mechanics_report_page(summary)
    row, = page.content.table.rows_by_combined_view["aggregate::rain"]
    assert row.cells["pops"].value == 0
    assert row.details.groups[0].items[0].description


def test_registry_and_manifest_cover_observed_damage_without_blaming_raid_victims():
    job, payload, fresh = build_report_job_request(REPORT_ID, {"report_codes": ["fCqgJN7QMWA2vFbT"], "fresh_run": True})
    assert job == "v2_report_nymrissa_mechanics" and fresh
    assert payload["difficulty"] == "mythic"
    manifest = get_boss_manifest("nymrissa-wavecaller", "mythic")
    assert len(manifest.targets) == 4
    assert {a.game_id for a in manifest.abilities} == {
        1260843, 1313450, 1313448, 1257654, 1313456, 1271458, 1313393,
        1266340, 1271380, 1265425, 1258677, 1258154,
    }
    assert {a.game_id for a in manifest.abilities if a.avoidable} == {1257654, 1258677, 1265425}
