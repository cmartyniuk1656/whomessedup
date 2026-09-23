"""Death recap totals, lifetime boundaries and conservative lethal attribution."""
from who_messed_up.api import Fight
from who_messed_up.services.coverage_deaths import add_death_recaps, MAX_EVENTS


def event(seconds, kind="damage", target=1, **fields):
    return dict(timestamp=100000 + seconds * 1000, type=kind, targetID=target,
                sourceID=90, abilityGameID=123, amount=100, **fields)


def recaps(pressure=(), healing=(), times=(10,)):
    deaths = [dict(time=t, playerId=1, player="Alice") for t in times]
    add_death_recaps(deaths, streams=dict(pressure=pressure, healing=healing),
                     fight=Fight(1, "Boss", 100000, 130000, False, 5, 3379, (1, 2)),
                     actor_names={90: "Boss"}, ability_labels={123: "Rain"})
    return [death["recap"] for death in deaths]


def test_window_boundaries_healing_and_absorbs_are_not_double_counted():
    recap, = recaps(
        [event(4.999), event(5, absorbed=50), event(9, "healabsorbed"),
         event(10, overkill=60), event(10.001), event(9, target=2)],
        [event(8, "heal", overheal=200), event(8, "absorbed")],
    )
    assert recap["windowSeconds"] == 5
    assert recap["totalEvents"] == 5
    assert recap["damageTaken"] == 200  # amount already excludes overkill
    assert recap["healingReceived"] == 100  # neither overheal nor shields restore health
    assert recap["healingAbsorbed"] == 100
    assert recap["damageAbsorbed"] == 50
    assert recap["events"][0]["offset"] == -5
    lethal = recap["events"][-1]
    assert lethal["killingBlow"] and lethal["amount"] == 160 and lethal["overkill"] == 60
    assert lethal["name"] == "Rain" and lethal["source"] == "Boss"


def test_last_damage_is_not_automatically_a_killing_blow():
    recap, = recaps([event(10)])
    assert not recap["events"][0]["killingBlow"]
    stale, = recaps([event(8, overkill=40)])
    assert not stale["events"][0]["killingBlow"]


def test_repeat_deaths_never_reuse_previous_life_events():
    first, second = recaps([event(10, overkill=60), event(11)], times=(10, 12))
    assert first["events"][0]["killingBlow"]
    assert second["damageTaken"] == 100
    assert len(second["events"]) == 1
    assert not second["events"][0]["killingBlow"]
    assert second["windowSeconds"] == 2


def test_capped_event_tail_preserves_totals_and_confirmed_killing_blow():
    recap, = recaps([event(9.1, overkill=50)], [event(9.2 + i / 1000, "heal") for i in range(MAX_EVENTS + 10)])
    assert recap["totalEvents"] == MAX_EVENTS + 11 and len(recap["events"]) == MAX_EVENTS
    assert recap["healingReceived"] == (MAX_EVENTS + 10) * 100
    assert recap["events"][0]["killingBlow"]


def test_unknown_names_empty_window_and_pull_start():
    empty, = recaps([], times=(0,))
    assert empty["windowSeconds"] == 0 and empty["totalEvents"] == 0
    hit = {**event(1), "sourceID": 900, "abilityGameID": 999}
    recap, = recaps([event(-1), hit], times=(2,))
    assert recap["windowSeconds"] == 2 and recap["totalEvents"] == 1
    assert recap["events"][0]["source"] == "Unknown source"
    assert recap["events"][0]["name"] == "Spell 999"


def test_full_overheal_and_zero_events_do_not_drown_out_effective_events():
    healing = [{**event(9, "heal"), "amount": 0, "overheal": 200}]
    recap, = recaps([{**event(9), "amount": 0}, event(10, absorbed=10)], healing)
    assert recap["totalEvents"] == 1 and recap["healingReceived"] == 0
