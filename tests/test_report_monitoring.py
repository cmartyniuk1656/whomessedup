from unittest.mock import Mock, patch

import app as application
from who_messed_up.services.report_monitoring import (
    ReportWatchFight,
    ReportWatchSnapshot,
    clear_report_watch_cache,
    fetch_report_watch_snapshot,
)


def _watch_payload():
    return {
        "reportData": {
            "report": {
                "code": "REPORT",
                "endTime": 5000,
                "revision": 3,
                "segments": 4,
                "fights": [
                    {
                        "id": 11,
                        "encounterID": 100,
                        "name": "Vashnik the Malignant",
                        "startTime": 1000,
                        "endTime": 2000,
                        "kill": False,
                        "difficulty": 4,
                    },
                    {
                        "id": 12,
                        "encounterID": 100,
                        "name": "Vashnik the Malignant",
                        "startTime": 3000,
                        "endTime": 4000,
                        "kill": True,
                        "difficulty": 5,
                    },
                    {
                        "id": 13,
                        "encounterID": 101,
                        "name": "Another Boss",
                        "startTime": 4100,
                        "endTime": 5000,
                        "kill": False,
                        "difficulty": 4,
                    },
                ],
            }
        }
    }


def test_report_watch_filters_fights_and_shares_short_lived_metadata():
    clear_report_watch_cache()
    try:
        with (
            patch("who_messed_up.services.report_monitoring._resolve_token", return_value="token"),
            patch("who_messed_up.services.report_monitoring.gql", return_value=_watch_payload()) as gql,
        ):
            heroic = fetch_report_watch_snapshot(
                report_code="REPORT",
                fight_name="vashnik",
                difficulty="heroic",
                client_id="client",
                client_secret="secret",
                session=Mock(),
            )
            mythic = fetch_report_watch_snapshot(
                report_code="REPORT",
                fight_name="Vashnik the Malignant",
                difficulty="mythic",
                client_id="client",
                client_secret="secret",
                session=Mock(),
            )
            kill = fetch_report_watch_snapshot(
                report_code="REPORT",
                fight_name="Vashnik",
                kill_only=True,
                client_id="client",
                client_secret="secret",
                session=Mock(),
            )

        assert [fight.id for fight in heroic.fights] == [11]
        assert [fight.id for fight in mythic.fights] == [12]
        assert [fight.id for fight in kill.fights] == [12]
        assert heroic.revision == 3
        assert heroic.segments == 4
        assert gql.call_count == 1
    finally:
        clear_report_watch_cache()


def test_report_watch_force_refresh_bypasses_short_lived_metadata_cache():
    clear_report_watch_cache()
    try:
        with (
            patch("who_messed_up.services.report_monitoring._resolve_token", return_value="token"),
            patch("who_messed_up.services.report_monitoring.gql", return_value=_watch_payload()) as gql,
        ):
            fetch_report_watch_snapshot(
                report_code="REPORT",
                client_id="client",
                client_secret="secret",
                session=Mock(),
            )
            fetch_report_watch_snapshot(
                report_code="REPORT",
                force_refresh=True,
                client_id="client",
                client_secret="secret",
                session=Mock(),
            )

        assert gql.call_count == 2
    finally:
        clear_report_watch_cache()


def test_report_watch_endpoint_derives_scope_from_registered_report():
    snapshot = ReportWatchSnapshot(
        report_code="REPORT",
        end_time=2000,
        revision=2,
        segments=3,
        fights=[
            ReportWatchFight(
                id=7,
                encounter_id=100,
                name="Vashnik the Malignant",
                start_time=1000,
                end_time=2000,
                kill=False,
                difficulty=4,
            )
        ],
    )
    request = application.ReportWatchRequestModel(
        values={"report_codes": "REPORT"},
        force_refresh=True,
    )
    with (
        patch("app._client_credentials", return_value={"client_id": "id", "client_secret": "secret"}),
        patch("app.fetch_report_watch_snapshot", return_value=snapshot) as fetch,
    ):
        response = application.watch_v2_report(
            "vashnik-the-malignant-damage", request
        )

    assert response.report_code == "REPORT"
    assert response.fights[0].id == 7
    assert fetch.call_args.kwargs["fight_name"] == "Vashnik the Malignant"
    assert fetch.call_args.kwargs["difficulty"] == "heroic"
    assert fetch.call_args.kwargs["force_refresh"] is True
