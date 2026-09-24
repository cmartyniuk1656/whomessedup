"""Counterfactual cooldown estimates must not inherit baseline mitigation."""
import pytest

from who_messed_up.services.defensive_attribution import reduction_rate
from who_messed_up.services.defensive_catalog import defensive_catalog
from test_defensive_usage import build, event, lane


def aura(spell, start=10, end=20, target=1):
    return [event(spell, start, "applybuff", target=target), event(spell, end, "removebuff", target=target)]


def test_thirty_percent_cooldown_removes_only_its_factor():
    pull = build(dict(casts=[event(31850, 10)], auras=aura(31850), pressure=[
        event(1, 5, "damage", target=1, amount=700, mitigated=9000),
        event(1, 11, "damage", target=1, amount=500, absorbed=200, mitigated=9000),
        event(1, 21, "damage", target=1, amount=700, mitigated=9000)]))
    use = lane(pull, 31850)["events"][0]
    assert use["attribution"]["estimatedReduction"] == 300
    assert use["protection"]["mitigated"] == 9000  # Kept solely as all-source context.
    points = pull["players"][0]["pressure"]
    assert points[2]["cooldownMitigated"] == points[10]["cooldownMitigated"] == 0
    assert points[5]["cooldownMitigated"] == 150


def test_overlapping_cooldowns_have_joint_graph_and_nonadditive_marginals():
    pull = build(dict(casts=[event(31850, 10), event(86659, 10)], auras=aura(31850) + aura(86659),
        pressure=[event(1, 11, "damage", target=1, amount=350, mitigated=1000)]))
    assert lane(pull, 31850)["events"][0]["attribution"]["estimatedReduction"] == 150
    assert lane(pull, 86659)["events"][0]["attribution"]["estimatedReduction"] == 350
    assert pull["pressure"][5]["cooldownMitigated"] == 325  # Joint prevented 650 / 2s.


def test_same_buff_from_multiple_sources_does_not_stack():
    pull = build(dict(casts=[event(102342, 10, target=2), event(102342, 11, source=2, target=2)],
        auras=aura(102342, target=2) + [event(102342, 11, "applybuff", source=2, target=2), event(102342, 20, "removebuff", source=2, target=2)],
        pressure=[event(1, 12, "damage", target=2, amount=800, mitigated=1000)]))
    assert pull["pressure"][6]["cooldownMitigated"] == 100  # 20%, not two factors of 20%.


def test_sentinel_uses_observed_stack_changes():
    pull = build(dict(casts=[event(389539, 10)], auras=aura(389539) + [event(389539, 12, "removebuffstack", target=1, stack=10)],
        pressure=[event(1, 11, "damage", target=1, amount=700, mitigated=5000),
                  event(1, 13, "damage", target=1, amount=800, mitigated=5000)]))
    assert lane(pull, 389539)["events"][0]["attribution"]["estimatedReduction"] == 500


def test_talent_rates_require_build_and_apply_selected_modifiers():
    modifier = next(m for m in defensive_catalog()[2]["talent_modifiers"] if m["spell_id"] == 377933)
    profile = next(p for p in modifier["applicability"] if p["specialization_id"] == 264)
    talent = profile["talent"]
    assert reduction_rate(108271, {"specID": 264})[0] is None
    assert reduction_rate(108271, {"specID": 264, "talentTree": [{"id": -1}]})[0] == .4
    assert reduction_rate(108271, {"specID": 264, "talentTree": [dict(id=talent["entry_id"], nodeID=talent["node_id"], rank=1)]})[0] == pytest.approx(.6)
    dynamic = next(m for m in defensive_catalog()[2]["talent_modifiers"] if m["spell_id"] == 434136)["applicability"][0]
    node = dynamic["talent"]
    assert reduction_rate(48792, {"specID": dynamic["specialization_id"], "talentTree": [
        dict(id=node["entry_id"], nodeID=node["node_id"], rank=1)]})[0] is None


def test_nominal_unknown_and_immune_only_windows_do_not_become_zero_scores():
    pull = build(dict(casts=[event(31850, 10), event(642, 20), event(86659, 30)],
        auras=aura(642, 20, 25) + aura(86659, 30, 35),
        pressure=[event(1, 11, "damage", target=1, amount=700, mitigated=9000)],
        immunities=[event(1, 31, "damage", target=1, hitType=10, amount=0)]))
    for spell in [31850, 642, 86659]:
        assert lane(pull, spell)["events"][0]["attribution"]["estimatedReduction"] is None
    assert not any(p["cooldownMitigated"] for p in pull["pressure"])


def test_recipient_target_and_logged_upper_bound():
    pull = build(dict(casts=[event(102342, 10, target=2)], auras=aura(102342, target=2),
        pressure=[event(1, 11, "damage", target=2, amount=800, mitigated=100),
                  event(1, 11, "damage", target=1, amount=5000, mitigated=5000)]))
    assert lane(pull, 102342)["events"][0]["attribution"]["estimatedReduction"] == 100
    assert pull["players"][0]["pressure"][5]["cooldownMitigated"] == 0
    assert pull["players"][1]["pressure"][5]["cooldownMitigated"] == 50
    assert pull["players"][1]["pressure"][5]["cooldownSources"] == ["Ironbark (Player)"]


def test_shield_graph_includes_depletion_hit_but_not_other_sources():
    pull = build(dict(casts=[event(235450, 10)], auras=aura(235450, 10, 12),
        pressure=[event(1, 12, "damage", target=1, amount=0, absorbed=300)],
        healing=[event(235450, 12, "absorbed", target=1, amount=200),
                 event(235450, 12, "absorbed", source=2, target=1, amount=100)]))
    assert lane(pull, 235450)["events"][0]["attribution"]["matchedAbsorbed"] == 200
    assert pull["pressure"][6]["cooldownAbsorbed"] == 100
    assert pull["pressure"][6]["cooldownSources"] == ["Prismatic Barrier (Player)"]
