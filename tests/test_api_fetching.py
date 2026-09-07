import threading
from unittest.mock import Mock, patch

from who_messed_up import api
from who_messed_up.services.common import _fight_roster_from_metadata, compute_death_cutoffs


def test_fetch_events_reuses_exact_next_page_timestamp():
    responses = [
        {
            "reportData": {
                "report": {
                    "events": {
                        "data": [{"timestamp": 1000, "type": "damage"}],
                        "nextPageTimestamp": 1000,
                    }
                }
            }
        },
        {
            "reportData": {
                "report": {
                    "events": {
                        "data": [{"timestamp": 1000, "type": "damage", "sourceID": 2}],
                        "nextPageTimestamp": None,
                    }
                }
            }
        },
    ]
    with patch("who_messed_up.api.gql", side_effect=responses) as gql:
        events = list(
            api.fetch_events(
                Mock(),
                "token",
                code="report",
                data_type="DamageDone",
                start=0,
                end=2000,
                sleep_seconds=0,
            )
        )

    assert len(events) == 2
    assert gql.call_args_list[1].args[3]["start"] == 1000.0


def test_fetch_tables_aliases_requests_and_preserves_order():
    def fake_gql(session, token, query, variables):
        assert "q0: table(" in query
        assert "q1: table(" in query
        assert variables["fightIDs0"] == [1, 2]
        assert variables["dataType1"] == "Healing"
        return {
            "reportData": {
                "report": {
                    "q0": {"data": {"entries": [{"id": 1}]}},
                    "q1": {"data": {"entries": [{"id": 2}]}},
                }
            }
        }

    with patch("who_messed_up.api.gql", side_effect=fake_gql):
        tables = api.fetch_tables(
            Mock(),
            "token",
            code="report",
            table_requests=[
                {
                    "data_type": "DamageDone",
                    "fight_ids": [1, 2],
                    "start": 10,
                    "end": 20,
                },
                {
                    "data_type": "Healing",
                    "fight_ids": [3],
                    "start": 30,
                    "end": 40,
                    "filter_expr": "encounterPhase = 1",
                },
            ],
        )

    assert tables == [
        {"entries": [{"id": 1}]},
        {"entries": [{"id": 2}]},
    ]


def test_fetch_tables_runs_chunks_concurrently_and_preserves_order():
    started = threading.Barrier(2)

    def fake_gql(session, token, query, variables):
        started.wait(timeout=2)
        fight_id = variables["fightIDs0"][0]
        return {
            "reportData": {
                "report": {"q0": {"data": {"entries": [{"fightID": fight_id}]}}}
            }
        }

    requests = [
        {
            "data_type": "DamageDone",
            "fight_ids": [fight_id],
            "start": 10,
            "end": 20,
        }
        for fight_id in (1, 2)
    ]
    with (
        patch("who_messed_up.api.gql", side_effect=fake_gql),
        patch("who_messed_up.api._table_batch_workers", 2),
    ):
        tables = api.fetch_tables(
            Mock(),
            "token",
            code="report",
            table_requests=requests,
            batch_size=1,
        )

    assert tables == [
        {"entries": [{"fightID": 1}]},
        {"entries": [{"fightID": 2}]},
    ]


def test_client_credentials_token_is_reused_until_expiry():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"access_token": "bearer", "expires_in": 3600}
    with api._token_cache_lock:
        api._token_cache.clear()
    with patch("who_messed_up.api.requests.post", return_value=response) as post:
        first = api.get_token_from_client("client", "secret")
        second = api.get_token_from_client("client", "secret")

    assert first == second == "bearer"
    assert post.call_count == 1


def test_fight_metadata_roster_normalizes_compact_spec_names():
    fight = api.Fight(
        id=1,
        name="Boss",
        start=0,
        end=10,
        kill=False,
        friendly_player_ids=(10, 11),
        friendly_specs=("BeastMastery", "Devourer"),
    )

    participants, roles, specs = _fight_roster_from_metadata(
        fight,
        {10: "Hunter", 11: "Demon Hunter"},
        {10: "Hunter", 11: "DemonHunter"},
    )

    assert participants == {"Hunter", "Demon Hunter"}
    assert roles == {"Hunter": "Ranged", "Demon Hunter": "Melee"}
    assert specs == {"Hunter": "BeastMastery", "Demon Hunter": "Devourer"}


def test_fetch_events_grouped_uses_one_id_only_request_and_partitions_rows():
    fights = [
        api.Fight(id=1, name="Boss", start=100, end=200, kill=False),
        api.Fight(id=2, name="Boss", start=300, end=400, kill=False),
    ]
    rows = [
        {"fight": 1, "timestamp": 150, "targetID": 10},
        {"timestamp": 350, "targetID": 11},
    ]
    with patch("who_messed_up.api.fetch_events", return_value=iter(rows)) as fetch:
        grouped = api.fetch_events_grouped(
            Mock(),
            "token",
            code="report",
            data_type="DamageTaken",
            fights=fights,
        )

    assert grouped == {1: [rows[0]], 2: [rows[1]]}
    assert fetch.call_count == 1
    assert list(fetch.call_args.kwargs["fight_ids"]) == [1, 2]
    assert fetch.call_args.kwargs["use_actor_ids"] is True


def test_report_fight_metadata_is_short_lived_cached_and_copied():
    response = {
        "reportData": {
            "report": {
                "fights": [
                    {
                        "id": 1,
                        "name": "Boss",
                        "startTime": 100,
                        "endTime": 200,
                        "kill": False,
                        "friendlyPlayers": [10],
                        "friendlySpecs": ["Frost"],
                    }
                ],
                "masterData": {
                    "actors": [
                        {"id": 10, "name": "Mage", "type": "Player", "subType": "Mage"}
                    ]
                },
            }
        }
    }
    api.clear_report_context_cache()
    try:
        with patch("who_messed_up.api.gql", return_value=response) as gql:
            first = api.fetch_fights(Mock(), "token", "cached-report")
            first[0][0].name = "Mutated"
            second = api.fetch_fights(Mock(), "token", "cached-report")

        assert gql.call_count == 1
        assert second[0][0].name == "Boss"
    finally:
        api.clear_report_context_cache()


def test_death_cutoffs_fetch_all_fights_in_one_event_stream():
    fights = [
        api.Fight(id=1, name="Boss", start=100, end=200, kill=False),
        api.Fight(id=2, name="Boss", start=300, end=400, kill=False),
    ]
    grouped = {
        1: [{"type": "death", "timestamp": 120}, {"type": "death", "timestamp": 140}],
        2: [{"type": "death", "timestamp": 320}],
    }
    with patch("who_messed_up.services.common.fetch_events_grouped", return_value=grouped) as fetch:
        cutoffs = compute_death_cutoffs(
            Mock(),
            "token",
            fights=fights,
            report_code="report",
            actor_names={},
            max_deaths=2,
        )

    assert cutoffs == {1: 140.0}
    assert fetch.call_count == 1


def test_aggregate_player_details_are_cached_by_normalized_fight_selection():
    response = {
        "reportData": {
            "report": {
                "playerDetails": {
                    "data": {"playerDetails": {"dps": [{"name": "Mage"}]}}
                }
            }
        }
    }
    api.clear_report_context_cache()
    try:
        with patch("who_messed_up.api.gql", return_value=response) as gql:
            first = api.fetch_player_details(Mock(), "token", code="report", fight_ids=[2, 1])
            first["dps"].append({"name": "Mutation"})
            second = api.fetch_player_details(Mock(), "token", code="report", fight_ids=[1, 2])

        assert gql.call_count == 1
        assert second == {"dps": [{"name": "Mage"}]}
    finally:
        api.clear_report_context_cache()
