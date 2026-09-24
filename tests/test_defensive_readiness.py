"""Readiness is talent-aware, conservative about recovery, and subordinate to casts."""
from copy import deepcopy

import pytest

from who_messed_up.services.defensive_catalog import defensive_catalog
from who_messed_up.services.defensive_readiness import resolve_defensive_readiness, add_defensive_readiness


def build_info(spec, spell, talents=()):
    abilities, _, research = defensive_catalog()
    profile = next(p for p in abilities[spell]["specialization_profiles"] if p["specialization_id"] == spec)
    nodes = [c["talent"] for c in profile["access"]["all_of"] if c["kind"] == "selected_talent"]
    for talent_id, rank in talents:
        modifier = next(m for m in research["talent_modifiers"] if m["spell_id"] == talent_id and spell in m["affected_ability_spell_ids"])
        node = next(a["talent"] for a in modifier["applicability"] if a["specialization_id"] == spec)
        nodes.append({**node, "rank": rank})
    return dict(specID=spec, talentTree=[dict(id=n["entry_id"], nodeID=n["node_id"], rank=n.get("rank", 1)) for n in nodes]
                or [dict(id=-1, nodeID=-1, rank=1)])


def resolve(spec, spell, talents=()):
    return resolve_defensive_readiness(defensive_catalog()[0][spell], build_info(spec, spell, talents))


def test_static_spec_and_talent_timers():
    assert resolve(262, 108271)["cooldown"] == 120
    assert resolve(262, 108271, [(381647, 1)])["cooldown"] == 90
    assert resolve(251, 48707, [(205727, 1)])["cooldown"] == 40
    assert resolve(104, 22812)["cooldown"] == 45
    assert resolve(269, 115203)["cooldown"] == 120
    assert resolve(70, 403876)["cooldown"] == 90
    assert resolve(70, 403876, [(114154, 1)])["cooldown"] == pytest.approx(63)
    assert resolve(62, 45438, [(382424, 2)])["cooldown"] == 180


def test_missing_build_and_wrong_node_do_not_apply_talents():
    ability = defensive_catalog()[0][108271]
    assert resolve_defensive_readiness(ability, {"specID": 262})["status"] == "unavailable"
    info = build_info(262, 108271, [(381647, 1)])
    info["talentTree"][-1]["nodeID"] = -1
    assert resolve_defensive_readiness(ability, info)["cooldown"] == 120
    info["talentTree"][0]["nodeID"] = -1
    assert resolve_defensive_readiness(ability, info)["status"] == "unavailable"


def test_real_wcl_entry_ids_resolve_research_definitions_without_guessing_choices():
    ability = defensive_catalog()[0][108271]
    info = dict(specID=262, talentTree=[dict(id=127893, nodeID=103616, rank=1),
                                     dict(id=127888, nodeID=103611, rank=1)])
    result = resolve_defensive_readiness(ability, info)
    assert result["cooldown"] == 90
    assert "Planes Traveler" in result["note"]
    info["talentTree"][-1]["id"] = -1
    assert resolve_defensive_readiness(ability, info)["cooldown"] == 120
    info["talentTree"][-1] = dict(id=127888, nodeID=-1, rank=1)
    assert resolve_defensive_readiness(ability, info)["cooldown"] == 120


def test_dynamic_recovery_free_activations_and_stacking_remain_unknown():
    assert resolve(268, 115203)["status"] == "unavailable"  # baseline brew recovery
    assert resolve(62, 235450, [(455428, 1)])["status"] == "unavailable"
    assert resolve(73, 871, [(152278, 1)])["status"] == "unavailable"  # Anger Management
    assert resolve(73, 871, [(391271, 1), (397103, 1)])["status"] == "unavailable"
    assert resolve(251, 48707, [(444074, 1)])["status"] == "unavailable"
    assert resolve(62, 342245)["status"] == "unavailable"
    assert resolve_defensive_readiness(defensive_catalog()[0][6262], {})["status"] == "unavailable"


def test_charge_recharge_is_sequential_and_not_a_ready_button_claim():
    info = build_info(62, 235450, [(321745, 1)])
    player = dict(actorId=1, lanes=[dict(spellId=235450, events=[dict(time=t) for t in [10, 15, 80]])])
    add_defensive_readiness([player], {1: info})
    lane = player["lanes"][0]
    assert lane["readiness"]["charges"] == 2
    assert [e["ready"] for e in lane["events"]] == [40, 70, 110]
    assert all(e["readyBasis"] == "Estimated charge replenished" for e in lane["events"])
    assert "full charges at pull start" in lane["readiness"]["note"]


def test_observed_early_reuse_invalidates_prediction_and_restarts_estimate():
    info = build_info(262, 108271, [(381647, 1)])
    player = dict(actorId=1, lanes=[dict(spellId=108271, events=[dict(time=t) for t in [10, 80, 190]])])
    add_defensive_readiness([player], {1: info})
    events = player["lanes"][0]["events"]
    assert [e["ready"] for e in events] == [None, 170, 280]
    assert "withdrawn" in events[0]["readyNote"]
    other = deepcopy(player)
    add_defensive_readiness([other], {})
    assert all(e["ready"] is None for e in other["lanes"][0]["events"])
