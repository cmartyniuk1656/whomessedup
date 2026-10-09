"""Wave-contact gains are scoped, one-to-one, and independent of damage ticks."""
import json
from pathlib import Path

from who_messed_up.api import Fight
from who_messed_up.services.mechanics_context import PullContext
from who_messed_up.services.the_twin_fangs_mechanics import build_the_twin_fangs_mechanics_summary
from who_messed_up.services.the_twin_fangs_mechanics_stacks import build_wave_contact_stacks
from who_messed_up.services.view_models.the_twin_fangs_mechanics import build_the_twin_fangs_mechanics_report_page


def event(at, aid=1290336, kind="applydebuffstack", player=1, **extra):
    return dict(timestamp=at, type=kind, abilityGameID=aid, targetID=player, sourceID=90, **extra)


def context(contacts, venom):
    return PullContext("XAYPC7qxRHkQVjT4", Fight(id=28, name="The Twin Fangs", start=0,
        end=10000, kill=False, difficulty=5, encounter_id=3421, friendly_player_ids=[1, 2]),
        1, {"debuffs": [event(t, 1292807, "applydebuff") for t in contacts], "venom": venom},
        {1: "Alice", 2: "Bob"}, {})


def test_initial_and_increased_stacks_count_once_not_the_resulting_stack_level():
    rows = build_wave_contact_stacks(context([1000, 2000], [
        event(1020, kind="applydebuff"), event(2010, stack=8)]))
    assert len(rows) == 2 and sum(r.values["stacks"] for r in rows) == 2
    assert all(r.soak_counts == {"Alice": 1} for r in rows)


def test_removals_refresh_damage_wrong_player_and_unmatched_contacts_do_not_count():
    for gain in [event(1020, kind="removedebuffstack", stack=7), event(1020, kind="removedebuff"),
                 event(1020, kind="refreshdebuff"), event(1020, kind="damage"),
                 event(1020, player=2), event(1020, aid=1290480)]:
        assert not build_wave_contact_stacks(context([1000], [gain]))
    assert not build_wave_contact_stacks(context([1000], []))


def test_jitter_window_includes_either_boundary_but_not_outside_or_other_pull():
    assert len(build_wave_contact_stacks(context([1000, 2000], [event(900), event(2100)]))) == 2
    assert not build_wave_contact_stacks(context([1000], [event(899), event(1101)]))
    assert not build_wave_contact_stacks(context([0, 10000], [event(-1), event(10001)]))


def test_nearest_one_to_one_matching_and_duplicate_gain_packets():
    gain = event(1020, stack=4)
    rows = build_wave_contact_stacks(context([1000, 1010], [gain, gain]))
    assert len(rows) == 1 and rows[0].start == 1010
    assert len(build_wave_contact_stacks(context([1000], [event(1000), event(1020)]))) == 1


def test_recorded_wave_contacts_and_stack_contacts_remain_separate():
    data = json.loads((Path(__file__).parent / "fixtures/twin_fangs_wave_stacks.json").read_text())
    summary = build_the_twin_fangs_mechanics_summary(
        report_code=data["code"], fights=[Fight(**f) for f in data["fights"]],
        streams={k: {int(fid): es for fid, es in g.items()} for k, g in data["streams"].items()},
        actor_names={int(k): n for k, n in data["names"].items()}, actor_classes={}, actor_owners={})
    assert len(summary.sets["waves"]) == 62
    assert len(summary.sets["wave_stacks"]) == 59
    page = build_the_twin_fangs_mechanics_report_page(summary)
    assert [o.label for o in page.content.table.secondary_view_control.options][2:4] == ["Wave Contacts", "Wave Contact Stacks"]
    for view, expected in (("waves", 62), ("wave_stacks", 59)):
        bars = page.content.table.rows_by_combined_view[f"aggregate::{view}::{view}-bars"]
        assert sum(row.cells["contribution"].value for row in bars) == expected
