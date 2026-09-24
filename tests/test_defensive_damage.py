"""Protection is logged evidence, not a causal cooldown or immunity estimate."""
from who_messed_up.api import Fight
from who_messed_up.services.defensive_damage import damage_evidence, personal_damage_series
from test_defensive_usage import build, event, lane


def test_mitigation_includes_block_and_keeps_absorbs_overkill_separate():
    result = damage_evidence([dict(type="damage", amount=100, absorbed=40,
        mitigated=60, blocked=20, overkill=10, unmitigatedAmount=210),
        dict(type="healabsorbed", amount=999), dict(type="absorbed", amount=40)])
    assert result == dict(damageTaken=100, absorbed=40, mitigated=60, overkill=10,
                          immuneEvents=0, damageEvents=1, mitigationEvents=1)


def test_missing_mitigation_does_not_invent_an_amount_or_immunity():
    result = damage_evidence([dict(type="damage", amount=0, absorbed=100),
        dict(type="damage", amount=50, unmitigatedAmount=1000),
        dict(type="immune", amount=0), dict(type="damage", amount=10, mitigated=-5)])
    assert result["mitigated"] == 0
    assert result["immuneEvents"] == 1
    assert result["damageTaken"] == 60
    assert result["absorbed"] == 100


def test_personal_bins_keep_full_absorbs_immunities_and_partial_final_bin():
    fight = Fight(1, "Boss", 100000, 105000, False, 5, 3445, (1,))
    points = personal_damage_series([event(123, 1, "damage", target=1, amount=0, absorbed=200, mitigated=100),
        event(123, 4, "immune", target=1), event(123, 5, "damage", target=1, amount=50),
        event(123, 4, "healabsorbed", target=1, amount=300),
        event(123, 6, "damage", target=1, amount=999)], fight, {}, {123: "Mechanic"})
    assert points[0]["absorbed"] == 100 and points[0]["mitigated"] == 50
    assert points[2]["damage"] == 50 and points[2]["immuneEvents"] == 1
    assert points[2]["healAbsorbs"] == 300
    assert points[2]["sources"] == [dict(name="Mechanic", amount=50, immuneEvents=1)]


def test_external_window_measures_recipient_and_self_shield_matches_source_spell():
    pull = build(dict(casts=[event(33206, 10, target=2), event(235450, 20)],
        auras=[event(33206, 10, "applybuff", target=2), event(33206, 12, "removebuff", target=2),
               event(235450, 20, "applybuff", target=1), event(235450, 25, "removebuff", target=1)],
        pressure=[event(123, 11, "damage", target=1, amount=999),
                  event(123, 11, "damage", target=2, amount=30, absorbed=20, mitigated=50),
                  event(123, 12.5, "damage", target=2, amount=999),
                  event(123, 21, "damage", target=1, amount=10, absorbed=90)],
        immunities=[event(123, 11.5, "damage", target=2, hitType=10, amount=0)],
        healing=[event(235450, 21, "absorbed", target=1, amount=40),
                 event(235450, 21, "absorbed", source=2, target=1, amount=50),
                 event(999, 21, "absorbed", target=1, amount=100),
                 event(235450, 26, "absorbed", target=1, amount=100)]))
    external = lane(pull, 33206)["events"][0]
    assert external["damageTaken"] == 30 and external["observationSeconds"] == 2
    assert external["protection"]["subject"] == "Recipient"
    assert external["protection"]["mitigated"] == 50 and external["protection"]["immuneEvents"] == 1
    shield = lane(pull, 235450)["events"][0]["protection"]
    assert shield["absorbed"] == 90 and shield["spellAbsorbed"] == 40
    # Everyone gets raid totals; individual series still isolate the recipient.
    assert pull["pressure"][5]["damage"] == (999 + 30) / 2
    assert pull["pressure"][5]["absorbed"] == 10


def test_nominal_shield_does_not_claim_absorption_from_its_next_cast():
    pull = build(dict(casts=[event(235450, 10), event(235450, 20)],
        healing=[event(235450, 15, "absorbed", target=1, amount=40),
                 event(235450, 20, "absorbed", target=1, amount=60)]))
    uses = lane(pull, 235450)["events"]
    assert [e["protection"]["spellAbsorbed"] for e in uses] == [40, 60]
