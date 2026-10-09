"""Successful kicks and shield-break attribution, including ambiguous CC races."""
import json
from pathlib import Path

from who_messed_up.api import Fight
from who_messed_up.services.mechanics_context import PullContext
from who_messed_up.services.the_twin_fangs_mechanics import build_the_twin_fangs_mechanics_summary
from who_messed_up.services.the_twin_fangs_mechanics_control import build_interrupts, build_shield_ccs
from who_messed_up.services.view_models.the_twin_fangs_mechanics import build_the_twin_fangs_mechanics_report_page


def event(at, kind, aid=1303378, target=90, source=90, number=1, **extra):
    return dict(timestamp=at, type=kind, abilityGameID=aid, targetID=target,
                sourceID=source, targetInstance=number, **extra)


def context(shields=(), kicks=()):
    return PullContext("XAYPC7qxRHkQVjT4", Fight(
        id=28, name="The Twin Fangs", start=1000, end=60000, kill=False,
        difficulty=5, encounter_id=3421, friendly_player_ids=[1, 2]), 1,
        {"shield_control": list(shields), "interrupts": list(kicks)},
        {1: "Alice", 2: "Bob", 10: "Totem", 90: "Barbed Bulwark", 91: "Broodling of Ithraz",
         92: "Spawn of Vexhul", 93: "Ithraz"}, {10: 1})


def shield(at=2000, number=1):
    return event(at, "applybuff", number=number, absorb=1000)


def cc(at=3000, number=1, source=1, aid=8122):
    return event(at, "applydebuff", aid, number=number, source=source)


def removal(at=3025, number=1, absorb=900):
    return event(at, "removebuff", number=number, absorb=absorb)


def test_area_cc_credits_each_shield_once_and_resolves_totem_owner():
    ctx = context([shield(), shield(), shield(number=2), cc(source=10, aid=118905),
                   cc(number=2, source=10, aid=118905), removal(), removal(), removal(number=2)])
    rows = build_shield_ccs(ctx)
    assert len(rows) == 2
    assert all(r.soak_counts == {"Alice": 1} for r in rows)
    assert [r.label for r in rows] == ["Barbed Bulwark #1", "Barbed Bulwark #2"]
    assert "Capacitor Totem" in rows[0].details[1].description


def test_competing_players_are_visible_without_double_credit():
    rows = build_shield_ccs(context([shield(), cc(), cc(at=3001, source=2), removal()]))
    row, = rows
    assert row.values == dict(breaks=0, ambiguous=1, unattributed=0, status="Ambiguous CCs")
    assert row.players["players"] == ["Alice", "Bob"]
    assert not row.soak_counts


def test_same_player_multiple_control_auras_only_credit_one_shield():
    row, = build_shield_ccs(context([shield(), cc(), cc(at=3001, aid=853), removal()]))
    assert row.soak_counts == {"Alice": 1}


def test_no_credit_for_wrong_instance_expired_cc_non_control_or_unknown_player():
    for control in [cc(number=2), cc(at=2924), cc(at=3026), cc(aid=113746),
                    event(3000, "cast", 8122, source=1), cc(source=999)]:
        row, = build_shield_ccs(context([shield(), control, removal()]))
        assert row.values["unattributed"] == 1 and not row.soak_counts


def test_missing_application_instance_or_remaining_absorb_stays_unattributed():
    for events in ([cc(), removal()], [shield(number=0), cc(number=0), removal(number=0)],
                   [shield(), cc(), removal(absorb=0)], [shield(), cc(), removal(absorb=None)]):
        row, = build_shield_ccs(context(events))
        assert row.values["unattributed"] == 1 and not row.soak_counts


def test_refresh_out_of_pull_and_cc_without_removal_do_not_count():
    assert not build_shield_ccs(context([shield(), cc()]))
    row, = build_shield_ccs(context([shield(), {**cc(), "type": "refreshdebuff"}, removal()]))
    assert not row.soak_counts
    assert not build_shield_ccs(context([shield(500), removal(999)]))


def test_interrupts_keep_same_name_instances_and_exclude_failed_casts():
    kick = event(3000, "interrupt", 19647, target=91, source=10, extraAbilityGameID=1308385)
    ctx = context(kicks=[kick, kick, {**kick, "targetInstance": 2},
                         {**kick, "type": "cast"}, {**kick, "sourceID": 93},
                         {**kick, "targetID": 93}, {**kick, "timestamp": 999},
                         {**kick, "timestamp": 60001}, {**kick, "timestamp": 4000, "targetInstance": 0}])
    rows = build_interrupts(ctx)
    assert len(rows) == 3
    assert [r.label for r in rows] == ["Broodling of Ithraz #1", "Broodling of Ithraz #2",
                                     "Broodling of Ithraz (instance unavailable)"]
    assert all(r.soak_counts == {"Alice": 1} and r.values["spell"] == "Visceral Burst" for r in rows)
    assert "Spell Lock" in rows[0].details[0].description


def test_recorded_control_snapshot_and_player_bars():
    data = json.loads((Path(__file__).parent / "fixtures/twin_fangs_mythic_control.json").read_text())
    summary = build_the_twin_fangs_mechanics_summary(
        report_code=data["code"], fights=[Fight(**f) for f in data["fights"]],
        streams={k: {int(fid): es for fid, es in group.items()} for k, group in data["streams"].items()},
        actor_names={int(k): v for k, v in data["names"].items()}, actor_classes={},
        actor_owners={int(k): v for k, v in data["owners"].items()})
    shields = summary.sets["shields"]
    assert len(shields) == 356
    assert sum(r.values["breaks"] for r in shields) == 353
    assert sum(r.values["ambiguous"] for r in shields) == 3
    assert sum(r.values["unattributed"] for r in shields) == 0
    assert len(summary.sets["interrupts"]) == 218
    assert all("#" in r.label for r in summary.sets["interrupts"])
    page = build_the_twin_fangs_mechanics_report_page(summary)
    for view, count in (("shields", 353), ("interrupts", 218)):
        bars = page.content.table.rows_by_combined_view[f"aggregate::{view}::{view}-bars"]
        assert sum(r.cells["contribution"].value for r in bars) == count
    assert len(page.content.table.rows_by_combined_view[f"{summary.pulls[0].view_id}::interrupts::interrupts-sets"]) == 18
