import threading
from unittest.mock import patch

import pytest

from who_messed_up.api import Fight
from who_messed_up.services.event_streams import fetch_event_streams


def fights(count):
    return [Fight(id=i * 3 + 1, name="Boss", start=i * 1000, end=i * 1000 + 900,
                  kill=False) for i in range(count)]


def test_partitions_preserve_full_fights_and_paginated_event_order():
    selected = fights(9)
    calls = []

    def gql(session, token, query, variables):
        ids = variables["fightIDs"]
        subset = [f for f in selected if f.id in ids]
        start = min(f.start for f in subset)
        assert variables["end"] == max(f.end for f in subset)
        calls.append((tuple(ids), variables["start"]))
        first = variables["start"] == start
        # Only one event at the first cursor; all remaining fights on page two.
        rows = ([{"fight": ids[0], "timestamp": start, "sequence": 1}] if first else
                [{"fight": f.id, "timestamp": f.start + 2, "sequence": 2} for f in subset])
        return {"reportData": {"report": {"events": {
            "data": rows, "nextPageTimestamp": start + 1 if first else None,
        }}}}

    with patch("who_messed_up.api.gql", side_effect=gql):
        result = fetch_event_streams(
            code="R", fights=selected, token="T", actor_names={},
            streams={"damage": {"data_type": "DamageDone", "sleep_seconds": 0}},
            partitioned_streams=("damage",), max_workers=3,
        )["damage"]
    assert list(result) == [f.id for f in selected]
    assert len(calls) == 6
    assert sorted(i for ids, start in calls if start == min(f.start for f in selected if f.id in ids)
                  for i in ids) == sorted(f.id for f in selected)
    assert all([e["sequence"] for e in events] == sorted(e["sequence"] for e in events)
               for events in result.values())
    assert sum(map(len, result.values())) == 12


def test_one_pool_bounds_concurrent_streams_and_owns_sessions():
    barrier = threading.Barrier(2)
    sessions = []

    def fetch(session, token, **kw):
        sessions.append(session)
        barrier.wait(timeout=2)
        return {f.id: [] for f in kw["fights"]}

    with patch("who_messed_up.services.event_streams.fetch_events_grouped", side_effect=fetch):
        result = fetch_event_streams(
            code="R", fights=fights(8), token="T", actor_names={}, max_workers=2,
            streams={"heavy": {}, "small": {}, "other": {}}, partitioned_streams=("heavy",),
        )
    assert len(sessions) == len({id(s) for s in sessions}) == 4
    assert list(result) == ["heavy", "small", "other"]


def test_empty_and_small_selections_do_not_create_extra_requests():
    with patch("who_messed_up.services.event_streams.fetch_events_grouped", return_value={}) as fetch:
        assert fetch_event_streams(code="R", fights=[], token="T", actor_names={}, streams={"a": {}}) == {}
        fetch.assert_not_called()
        fetch_event_streams(code="R", fights=fights(3), token="T", actor_names={},
                            streams={"a": {}}, partitioned_streams=("a",))
        assert fetch.call_count == 1


def test_failed_partition_does_not_return_partial_evidence():
    with patch("who_messed_up.services.event_streams.fetch_events_grouped", side_effect=RuntimeError("WCL failed")):
        with pytest.raises(RuntimeError, match="WCL failed"):
            fetch_event_streams(code="R", fights=fights(8), token="T", actor_names={},
                                streams={"a": {}}, partitioned_streams=("a",))
