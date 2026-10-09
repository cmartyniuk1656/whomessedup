"""Regression coverage for wave contacts without damage and pickup attribution."""
from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

from who_messed_up.api import Fight
from who_messed_up.services.mechanics_context import PullContext
from who_messed_up.services.report_registry import build_report_job_request
from who_messed_up.services.the_twin_fangs_mechanics import (
    build_the_twin_fangs_mechanics_summary, fetch_the_twin_fangs_mechanics_summary,
)
from who_messed_up.services.the_twin_fangs_mechanics_events import build_add_damage, build_contacts
from who_messed_up.services.the_twin_fangs_mechanics_models import GLOBULE, REPORT_ID, WAVE
from who_messed_up.services.view_models.the_twin_fangs_mechanics import build_the_twin_fangs_mechanics_report_page


def event(at=1000, aid=WAVE, kind="applydebuff", target=1, source=90, **extra):
    return dict(timestamp=at, abilityGameID=aid, type=kind, targetID=target, sourceID=source, **extra)


def context(**streams):
    return PullContext("abcdefghijklmnop", Fight(
        id=1, name="The Twin Fangs", start=0, end=60000, kill=False,
        difficulty=5, encounter_id=3421, friendly_player_ids=[1, 2]),
        1, streams, {1: "Alice", 2: "Bob", 10: "Pet", 90: "Vexhul", 91: "Spawn of Vexhul",
                     92: "Broodling of Ithraz"}, {10: 1})


def summary_for(ctx):
    return build_the_twin_fangs_mechanics_summary(
        report_code=ctx.code, fights=[ctx.fight],
        streams={key: {ctx.fight.id: events} for key, events in ctx.streams.items()},
        actor_names=ctx.names, actor_classes={1: "Mage", 2: "Priest"}, actor_owners=ctx.owners)


def test_brief_wave_contact_counts_without_damage_and_reentry_counts_again():
    ctx = context(debuffs=[event(), event(1500, kind="removedebuff"), event(2000),
                           event(2100, kind="refreshdebuff"), event(2200, kind="applydebuffstack"),
                           event(3000, kind="damage"), event(4000, aid=1292806),
                           event(5000, aid=1290336), event(6000, target=10),
                           event(-1), event(60001), event(7000, source=1), event(8000, source=10)])
    rows = build_contacts(ctx, waves=True)
    assert len(rows) == 2
    assert [r.start for r in rows] == [1000, 2000]
    assert all(r.soak_counts == {"Alice": 1} for r in rows)


def test_orbs_keep_distinct_absorbed_impacts_and_exclude_ruptures_and_ticks():
    ctx = context(pickups=[event(aid=GLOBULE, kind="damage", amount=0, absorbed=100),
                           event(aid=GLOBULE, kind="damage", amount=10),
                           event(aid=GLOBULE, kind="damage", target=2, amount=20),
                           event(aid=GLOBULE, kind="damage", tick=True),
                           event(aid=GLOBULE, kind="damage", hitType=10),
                           event(aid=1290338, kind="damage"), event(aid=GLOBULE),
                           event(aid=1290336), event(aid=GLOBULE, kind="damage", target=10)])
    rows = build_contacts(ctx)
    assert len(rows) == 4
    assert [r.players["players"] for r in rows] == [["Alice"], ["Alice"], ["Bob"], ["Alice"]]


def test_add_instances_pet_ownership_and_effective_damage():
    ctx = context(add_damage=[
        event(2000, kind="damage", target=91, source=1, targetInstance=1, amount=100, overkill=50),
        event(2100, kind="damage", target=91, source=10, targetInstance=1, amount=50, absorbed=20),
        event(2200, kind="damage", target=91, source=2, targetInstance=2, amount=200),
        event(2300, kind="damage", target=90, source=1, amount=9999),
        event(2400, kind="damage", target=91, source=90, amount=9999),
        event(2500, kind="damage", target=92, source=2, amount=30),
        event(3100, kind="damage", target=91, source=1, targetInstance=1, amount=9999),
    ], summons=[event(1000, kind="summon", target=91, targetInstance=1)],
        enemy_deaths=[event(3000, kind="death", target=91, targetInstance=1)])
    rows = build_add_damage(ctx)
    assert rows[0].contributions == {"Alice": 150}
    assert rows[0].values["duration"] == 2
    assert sum(r.values["damage"] for r in rows) == 380
    assert rows[1].contributions == {"Bob": 200}
    assert rows[1].values["duration"] is None


def test_page_contract_includes_five_scoped_subreports_and_empty_pull():
    summary = summary_for(context(debuffs=[event()], pickups=[event(aid=GLOBULE, kind="damage")]))
    page = build_the_twin_fangs_mechanics_report_page(summary)
    table = page.content.table
    assert page.report_id == REPORT_ID
    assert [o.value for o in table.secondary_view_control.options] == ["adds", "orbs", "waves", "shields", "interrupts"]
    assert table.sub_view_control_by_view["adds"].default_value == "adds-bars"
    assert table.rows_by_combined_view["aggregate::waves::waves-bars"][0].cells["contribution"].value == 1
    assert table.rows_by_combined_view[f"{summary.pulls[0].view_id}::orbs::orbs-bars"][0].cells["contribution"].value == 1
    assert not table.rows_by_combined_view["aggregate::adds::adds-bars"]
    page.model_dump(mode="json", by_alias=True)
    empty = build_the_twin_fangs_mechanics_report_page(summary_for(context()))
    assert len(empty.content.table.view_control.options) == 2


def test_registry_forces_mythic_and_preserves_extra_reports():
    job, payload, fresh = build_report_job_request(REPORT_ID, {
        "report_codes": ["abcdefghijklmnop", "qrstuvwxyzABCDEF"], "difficulty": "heroic", "fresh_run": True,
    })
    assert job == "v2_report_twin_fangs_mechanics"
    assert payload["difficulty"] == "mythic" and fresh
    assert payload["extra_reports"] == ["qrstuvwxyzABCDEF"]


def test_recorded_mythic_pull_snapshot():
    data = json.loads((Path(__file__).parent / "fixtures/twin_fangs_mythic_observed.json").read_text())
    ctx = PullContext(data["report_code"], Fight(**data["fight"]), 1, data["streams"],
                      {int(k): v for k, v in data["names"].items()},
                      {int(k): v for k, v in data["owners"].items()})
    summary = summary_for(ctx)
    assert {view: len(rows) for view, rows in summary.sets.items()} == {"adds": 2, "orbs": 30, "waves": 8, "shields": 0, "interrupts": 0}
    assert [row.values["damage"] for row in summary.sets["adds"]] == [12136258, 1054732]
    assert [row.values["duration"] for row in summary.sets["adds"]] == [7.43, None]
    page = build_the_twin_fangs_mechanics_report_page(summary)
    for view, expected in (("adds", 13190990), ("orbs", 30), ("waves", 8)):
        bars = page.content.table.rows_by_combined_view[f"aggregate::{view}::{view}-bars"]
        assert sum(row.cells["contribution"].value for row in bars) == expected


def test_fetch_scopes_difficulty_encounter_and_report_local_ids():
    ctx = context(debuffs=[event()])
    fights = [ctx.fight, replace(ctx.fight, id=2, difficulty=4), replace(ctx.fight, id=3, encounter_id=1)]
    module = "who_messed_up.services.the_twin_fangs_mechanics"
    with patch(module + ".load_env"), patch(module + "._resolve_token", return_value="token"), \
            patch(module + ".fetch_fights", return_value=(fights, ctx.names, {}, ctx.owners)), \
            patch(module + "._fetch_streams", return_value={"debuffs": {1: [event()]}}) as streams:
        summary = fetch_the_twin_fangs_mechanics_summary(
            report_code=ctx.code, difficulty="heroic", extra_report_codes=["qrstuvwxyzABCDEF", ctx.code])
    assert len(summary.pulls) == 2
    assert len(summary.sets["waves"]) == 2
    assert all([f.id for f in call.args[1]] == [1] for call in streams.call_args_list)
    page = build_the_twin_fangs_mechanics_report_page(summary)
    assert len({r.id for r in page.content.table.rows_by_combined_view["aggregate::waves::waves-sets"]}) == 2
    for pull in summary.pulls:
        assert page.content.table.rows_by_combined_view[f"{pull.view_id}::waves::waves-bars"][0].cells["contribution"].value == 1
