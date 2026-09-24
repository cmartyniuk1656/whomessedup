"""Health uses recorded resources, retains dips, and never invents missing HP."""
from who_messed_up.api import Fight
from who_messed_up.services.defensive_health import player_health_series

FIGHT = Fight(1, "Boss", 1000, 61000, False, 5, 3445, (1, 2))


def snapshot(time, hp, maximum=1000, **extra):
    return dict(timestamp=1000 + time * 1000, sourceID=2, targetID=1,
                resourceActor=2, hitPoints=hp, maxHitPoints=maximum, **extra)


def test_resource_owner_and_changing_max_health():
    source = {**snapshot(1, 500), "resourceActor": 1}
    result = player_health_series({"pressure": [snapshot(0, 500), source, snapshot(2, 500, 2000),
        {**snapshot(3, 900), "resourceActor": None}, snapshot(4, 1, 0), snapshot(5, float("nan"))]}, FIGHT, {1, 2})
    assert result[1] == [{"time": 0, "percent": 50}, {"time": 2, "percent": 25}]
    assert result[2] == [{"time": 1, "percent": 50}]


def test_short_dips_are_not_averaged_away_and_death_is_last_at_same_timestamp():
    result = player_health_series({"pressure": [snapshot(1, 1000), snapshot(1.05, 800), snapshot(1.1, 100),
        snapshot(1.15, 400), snapshot(1.2, 900)], "deaths": [{"timestamp": 2200, "targetID": 1}]}, FIGHT, {1})[1]
    assert result[0]["percent"] == 100
    # Death is the low for this bucket; earlier nonfatal minima need not survive a fatal bin.
    assert result[-1] == {"time": 1.2, "percent": 0}
    alive = player_health_series({"pressure": [snapshot(1, 1000), snapshot(1.1, 100), snapshot(1.2, 900)]}, FIGHT, {1})[1]
    assert [p["percent"] for p in alive] == [100, 10, 90]


def test_no_lines_through_unknown_gaps_or_resurrection():
    result = player_health_series({"healing": [snapshot(1, 1000), snapshot(10, 800), snapshot(13, 500)],
        "deaths": [{"timestamp": 13000, "targetID": 1}]}, FIGHT, {1})[1]
    assert result[1]["breakBefore"]
    assert result[-1]["breakBefore"]  # resurrection after 0% death marker
    assert result[-2]["percent"] == 0
    assert player_health_series({"deaths": [{"timestamp": 2000, "targetID": 1}]}, FIGHT, {1}) == {}


def test_plateau_compression_keeps_edges_and_existing_gaps():
    result = player_health_series({"healing": [snapshot(t, 1000) for t in (0, 1, 2, 3, 4, 20, 21)]}, FIGHT, {1})[1]
    assert result == [{"time": 0, "percent": 100}, {"time": 4, "percent": 100},
                      {"time": 20, "percent": 100, "breakBefore": True}, {"time": 21, "percent": 100}]
