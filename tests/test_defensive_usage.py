"""Defensive usage must retain recipients and distinguish unknown availability."""
from unittest.mock import patch

import pytest
import requests

from who_messed_up.api import Fight
from who_messed_up.services.cooldown_catalog import coverage_catalog
from who_messed_up.services.defensive_catalog import defensive_catalog, ability_access
from who_messed_up.services.defensive_reference import normalize_reference, fetch_defensive_references
from who_messed_up.services.defensive_usage import build_defensive_pull, fetch_defensive_usage
from who_messed_up.services.report_registry import build_report_job_request, list_report_definitions
from who_messed_up.services.view_models.defensive_usage import build_defensive_usage_page


def event(spell, time, kind="cast", source=1, target=-1, **kwargs):
    return dict(timestamp=100000 + time * 1000, type=kind, abilityGameID=spell,
                sourceID=source, targetID=target, **kwargs)


def build(streams, code="abcdefghijklmnop"):
    fight = Fight(1, "Entombed Sentinels", 100000, 160000, False, 5, 3445, (1, 2))
    return build_defensive_pull(code=code, fight=fight, boss=coverage_catalog()[1][3445],
        streams=streams, actor_names={1: "Player", 2: "Recipient", 99: "Pet"}, player_ids={1, 2})


def lane(pull, spell, actor=1):
    return next(l for p in pull["players"] if p["actorId"] == actor for l in p["lanes"] if l["spellId"] == spell)


def test_self_item_target_minus_one_and_effective_healing():
    pull = build(dict(casts=[event(1234768, 10), event(1234768, 10), event(6262, 20), event(6262, 30, source=99)],
        healing=[event(1234768, 10, "heal", target=1, amount=800, overheal=200),
                 event(1234768, 10, "heal", source=2, target=1, amount=500),
                 event(1234768, 9, "heal", target=1, amount=100)],
        pressure=[event(123, 10, "damage", target=1, amount=200, overkill=100)]))
    potion = lane(pull, 1234768)["events"]
    assert len(potion) == 1
    assert potion[0]["targetId"] == 1 and potion[0]["selfUse"]
    assert potion[0]["effectiveHealing"] == 800 and potion[0]["overhealing"] == 200
    assert potion[0]["damageTaken"] == 200
    assert pull["players"][0]["pressure"][5]["damage"] == 100  # 200 damage / 2s, no double overkill subtraction
    assert sum(len(l["events"]) for p in pull["players"] for l in p["lanes"]) == 2
    assert lane(pull, 1262857)["category"] == "consumable"


def test_observed_aura_requires_same_source_recipient_and_clips_at_death():
    pull = build(dict(casts=[event(48792, 10)],
        auras=[event(48792, 10, "applybuff", source=99, target=1), event(48792, 12, "removebuff", source=99, target=1),
               event(48792, 10, "applybuff", target=1), event(48792, 17, "removebuff", target=1)],
        deaths=[event(0, 15, "death", target=1)]))
    use = lane(pull, 48792)["events"][0]
    assert use["end"] == 15 and use["durationBasis"] == "observed aura"
    assert pull["players"][0]["deaths"][0]["time"] == 15


def test_external_recipient_is_not_credited_as_self_protection():
    pull = build(dict(casts=[event(33206, 10, target=2), event(33206, 30)],
        auras=[event(33206, 10, "applybuff", target=2), event(33206, 16, "removebuff", target=2)]))
    uses = lane(pull, 33206)["events"]
    assert uses[0]["target"] == "Recipient" and not uses[0]["selfUse"] and uses[0]["end"] == 16
    assert uses[1]["targetId"] is None and not uses[1]["selfUse"]
    assert not any(l["events"] for p in pull["players"] if p["actorId"] == 2 for l in p["lanes"])


def test_access_requires_matching_entry_node_rank_and_known_spec():
    ability = defensive_catalog()[0][97462]
    assert ability_access(ability, {"specID": 71}) == "unknown"
    talent = ability["specialization_profiles"][0]["access"]["all_of"][0]["talent"]
    node = dict(id=talent["entry_id"], nodeID=talent["node_id"], rank=1)
    assert ability_access(ability, {"specID": 71, "talentTree": [node]}) == "available"
    assert ability_access(ability, {"specID": 71, "talentTree": [{**node, "nodeID": -1}]}) == "unavailable"
    assert ability_access(ability, {"specID": 62, "talentTree": [node]}) == "unavailable"
    assert ability_access(defensive_catalog()[0][6262], {"specID": 71, "talentTree": [node]}) == "unknown"


def test_unknown_build_retains_observed_casts_and_does_not_invent_all_talents():
    pull = build(dict(casts=[event(97462, 10)], combatants=[dict(sourceID=1, specID=71)]))
    assert lane(pull, 97462)["access"] == "observed"
    assert not any(l["spellId"] == 118038 for l in pull["players"][0]["lanes"])
    assert not pull["players"][0]["buildKnown"]


def test_timestamps_and_identity_stay_pull_and_report_specific():
    spell = coverage_catalog()[1][3445]["abilities"][0]["spell_id"]
    one = build(dict(bossCasts=[event(spell, 12, source=88), event(spell, 12, source=88)],
                     casts=[event(6262, -1), event(6262, 61)]))
    two = build(dict(bossCasts=[event(spell, 18, source=88)]), code="otherreport")
    assert len(one["bossLanes"][0]["events"]) == 1
    assert one["bossLanes"][0]["events"][0]["time"] == 12
    assert two["bossLanes"][0]["events"][0]["time"] == 18
    assert one["players"][0]["id"] != two["players"][0]["id"]
    assert not lane(one, 6262)["events"]


def test_reference_only_matching_spec_difficulty_and_tracked_personals():
    ranking = dict(spec_slug="mage-arcane", boss_slug="boss", difficulty="mythic", metric="dps", reports=[dict(
        report_id="report", fights=[dict(fight_id=1, duration=60000, boss={"casts": [dict(id=999, ts=22000)]}, players=[
            dict(source_id=1, spec_slug="mage-arcane", casts=[dict(id=235450, ts=21000), dict(id=6940, ts=21000), dict(id=6262, ts=-1000)]),
            dict(source_id=2, spec_slug="mage-fire", casts=[dict(id=235450, ts=21000)])])])])
    kwargs = dict(spec_id=62, spec_slug="mage-arcane", boss_slug="boss", difficulty="mythic")
    reference = normalize_reference(ranking, {"235450": {"event_type": "applybuff"}, "6940": {}, "6262": {}}, **kwargs)
    assert len(reference["samples"]) == 1
    assert reference["samples"][0]["events"] == [dict(spellId=235450, time=21, observation="applybuff")]
    assert reference["samples"][0]["bossEvents"][0]["time"] == 22
    disabled = normalize_reference(ranking, {"235450": {"query": False}}, **kwargs)
    assert disabled["trackedSpellIds"] == [] and disabled["samples"][0]["events"] == []
    with pytest.raises(ValueError): normalize_reference(ranking, {}, **{**kwargs, "difficulty": "heroic"})
    with patch("who_messed_up.services.defensive_reference._get", side_effect=requests.Timeout):
        assert fetch_defensive_references({62}, encounter_id=3445, difficulty="mythic")["62"]["status"] == "unavailable"


def test_registry_and_typed_page_preserve_defensive_data():
    report_id = "entombed-sentinels-defensive-usage-mythic"
    result = build_report_job_request(report_id, {"report_codes": ["abcdefghijklmnop"]})
    assert result[0] == "v2_report_defensive_usage" and result[1]["defensive_version"] == 7
    assert "include_reference" not in result[1]
    assert len([d for d in list_report_definitions() if "-defensive-usage-" in d.id]) == 18
    pull = build(dict(casts=[event(6262, 10)])); pull["label"] = "Pull 1"
    data = dict(boss="Boss", patch="12.1", catalogueDate="2026-09-23", binSeconds=2, pulls=[pull], references={})
    page = build_defensive_usage_page(data, report_id).model_dump(by_alias=True)
    assert page["content"]["variant"] == "defensive_timeline"
    assert page["content"]["timeline"]["pulls"][0]["players"][0]["lanes"] == pull["players"][0]["lanes"]


def test_removed_comparison_never_fetches_lorrgs_even_for_legacy_requests():
    fight = Fight(1, "Entombed Sentinels", 100000, 160000, False, 5, 3445, (1,))
    with patch("who_messed_up.services.defensive_usage.load_env"), \
         patch("who_messed_up.services.defensive_usage._resolve_token", return_value="test"), \
         patch("who_messed_up.services.defensive_usage.fetch_fights", return_value=([fight], {1: "Player"}, {1: "Mage"}, {})), \
         patch("who_messed_up.services.defensive_usage._fetch_ability_labels", return_value={}), \
         patch("who_messed_up.services.defensive_usage.fetch_event_streams", return_value={}), \
         patch("who_messed_up.services.defensive_reference.fetch_defensive_references") as references:
        timeline = fetch_defensive_usage(report_codes=["abcdefghijklmnop"], encounter_id=3445,
                                         difficulty="mythic", include_reference=True)
    assert len(timeline["pulls"]) == 1
    assert timeline["references"] == {}
    references.assert_not_called()
