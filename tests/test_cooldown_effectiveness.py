"""Measured cast context must not invent healing attribution or active windows."""
from who_messed_up.api import Fight
from who_messed_up.services.cooldown_effectiveness import add_cast_effectiveness


def cast(time, end=None, **extra):
    return {"time": time, "end": end, "durationBasis": "nominal", **extra}


def lane(events, source=1):
    return {"id": f"{source}:740", "kind": "healer", "name": "Cooldown", "player": f"Healer {source}", "events": events}


def measure(lanes, streams, duration=30):
    add_cast_effectiveness(lanes, fight=Fight(1, "Boss", 100000, 100000 + duration * 1000, False, 5, 1, (1, 2)),
                           streams=streams, participants={1, 2}, actor_owners={9: 1, 10: 9}, ability_labels={42: "Heal"})
    return lanes[0]["events"][0]["effectiveness"]


def event(time, kind="heal", source=1, target=2, amount=100, **extra):
    return {"timestamp": 100000 + time * 1000, "type": kind, "sourceID": source,
            "targetID": target, "amount": amount, "abilityGameID": 42, **extra}


def test_healer_pet_output_excludes_other_healers_pets_as_targets_and_window_end():
    data = measure([lane([cast(5, 10)])], {"healing": [
        event(5, overheal=100), event(6, source=10, amount=50),
        event(7, "absorbed", amount=80), event(8, source=2, amount=230),
        event(8, target=9, amount=9000), event(10, amount=9000),
        event(9, "removebuff", amount=9000),
    ]})
    assert data["status"] == "measured"
    assert data["healthRestored"] == 150
    assert data["shieldsConsumed"] == 80
    assert data["effectiveHealing"] == 230
    assert data["effectiveHps"] == 46
    assert data["overhealPercent"] == 40
    assert data["raidHealingShare"] == 50
    assert data["targetsHelped"] == 1
    assert data["abilities"] == [{"name": "Heal", "effective": 230, "overheal": 100}]


def test_pressure_preceding_window_and_overlap_are_context_only():
    lanes = [lane([cast(5, 10)]), lane([cast(4, 6), cast(9, 9), cast(10, 12), cast(8, label="Store")], 2)]
    data = measure(lanes, {"healing": [], "pressure": [
        event(4, "damage", amount=200), event(5, "damage", amount=110, overkill=10),
        event(6, "healabsorbed", amount=50), event(6, "absorbed", amount=999),
        event(7, "damage", target=9, amount=999),
    ]})
    assert data["raidDamage"] == 100
    assert data["healAbsorbsConsumed"] == 50
    assert data["precedingPressure"] == 200
    assert data["precedingSeconds"] == 5
    assert [item["kind"] for item in data["overlaps"]] == ["window", "cast"]
    assert data["overhealPercent"] is None
    assert data["raidHealingShare"] is None


def test_observation_windows_do_not_change_active_durations_and_clip_at_pull_end():
    instant, unknown, ending, past = cast(3, 3), cast(8), cast(28, 40), cast(30, 30)
    lanes = [lane([instant, unknown, ending, past])]
    measure(lanes, {"healing": []})
    assert instant["end"] == 3
    assert instant["effectiveness"]["windowEnd"] == 6
    assert "observation" in instant["effectiveness"]["windowBasis"]
    assert unknown["end"] is None
    assert unknown["effectiveness"]["windowEnd"] == 13
    assert ending["effectiveness"]["windowEnd"] == 30
    assert past["effectiveness"]["status"] == "unavailable"


def test_stasis_preparation_and_missing_data_are_not_reported_as_zero_effectiveness():
    lanes = [lane([cast(2, label="Store"), cast(5, label="Release")])]
    data = measure(lanes, {})
    assert data["status"] == "preparation"
    assert "effectiveHealing" not in data
    assert lanes[0]["events"][1]["effectiveness"]["status"] == "unavailable"


def test_delay_after_estimated_ready_is_measured_only_for_subsequent_uses():
    lanes = [lane([cast(2, 4, ready=12), cast(15, 17)])]
    data = measure(lanes, {"healing": []})
    assert data["heldSeconds"] is None
    assert lanes[0]["events"][1]["effectiveness"]["heldSeconds"] == 3


def test_stasis_store_does_not_erase_previous_release_readiness():
    lanes = [lane([cast(2, label="Release", ready=12), cast(13, label="Store"), cast(15, label="Release")])]
    measure(lanes, {"healing": []})
    assert lanes[0]["events"][2]["effectiveness"]["heldSeconds"] == 3
