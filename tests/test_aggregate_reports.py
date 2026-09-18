from unittest.mock import patch

import pytest

import app as application
from who_messed_up.services.report_registry import (
    JOB_V2_AGGREGATE_REPORT,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)
from who_messed_up.services.view_models.common import ReportPageModel


VASHNIK_AGGREGATE_ID = "vashnik-the-malignant-heroic-aggregate-reports"


def _minimal_page(report_id: str, title: str) -> dict:
    return {
        "reportId": report_id,
        "title": title,
        "reportCode": "REPORT",
        "header": {"subtitle": title, "tags": []},
        "summary": [],
        "content": {
            "variant": "table",
            "table": {
                "defaultSort": {"columnId": "player", "direction": "asc"},
                "columns": [],
                "rows": [],
                "emptyState": "No rows.",
            },
        },
        "footnotes": [],
    }


def test_aggregate_definition_includes_every_non_cooldown_report_for_fight():
    definition = get_registered_report(VASHNIK_AGGREGATE_ID).definition
    field_ids = [field.id for field in definition.request_schema.fields]

    assert definition.fight_id == "vashnik-the-malignant"
    assert "aggregate_include__vashnik-the-malignant-deaths" in field_ids
    assert "aggregate_include__vashnik-the-malignant-avoidable-damage" in field_ids
    assert "aggregate_include__vashnik-the-malignant-damage" in field_ids
    assert not any("cooldown" in field_id for field_id in field_ids)
    assert any(
        field_id.startswith("aggregate__vashnik-the-malignant-damage__")
        for field_id in field_ids
    )


def test_aggregate_payload_maps_namespaced_settings_to_selected_children():
    values = {
        "report_codes": ["REPORT", "EXTRA"],
        "aggregate_include__vashnik-the-malignant-deaths": False,
        "aggregate_include__vashnik-the-malignant-avoidable-damage": False,
        "aggregate_include__vashnik-the-malignant-damage": True,
        "aggregate__vashnik-the-malignant-damage__kill_only": True,
        "aggregate__vashnik-the-malignant-damage__omit_dead_players": True,
        "fresh_run": True,
    }

    job_type, payload, fresh_run = build_report_job_request(
        VASHNIK_AGGREGATE_ID, values
    )

    assert job_type == JOB_V2_AGGREGATE_REPORT
    assert fresh_run is True
    assert payload["kill_only"] is True
    assert [child["report_id"] for child in payload["reports"]] == [
        "vashnik-the-malignant-damage"
    ]
    child_payload = payload["reports"][0]["payload"]
    assert child_payload["report"] == "REPORT"
    assert child_payload["extra_reports"] == ["EXTRA"]
    assert child_payload["kill_only"] is True
    assert child_payload["omit_dead_players"] is True


def test_aggregate_payload_requires_one_selected_report():
    with pytest.raises(ValueError, match="Select at least one report"):
        build_report_job_request(
            VASHNIK_AGGREGATE_ID,
            {
                "report_codes": ["REPORT"],
                "aggregate_include__vashnik-the-malignant-deaths": False,
                "aggregate_include__vashnik-the-malignant-avoidable-damage": False,
                "aggregate_include__vashnik-the-malignant-damage": False,
            },
        )


def test_no_aggregate_is_registered_when_cooldown_is_the_only_report():
    definition_ids = {definition.id for definition in list_report_definitions()}
    assert "nymrissa-wavecaller-heroic-aggregate-reports" not in definition_ids


def test_aggregate_handler_returns_independent_report_pages_with_selector():
    payload = {
        "report": "REPORT",
        "report_id": VASHNIK_AGGREGATE_ID,
        "report_title": "Aggregate Reports",
        "reports": [
            {
                "report_id": "deaths",
                "title": "Death Report",
                "job_type": "child-deaths",
                "payload": {"report": "REPORT"},
            },
            {
                "report_id": "damage",
                "title": "Damage Report",
                "job_type": "child-damage",
                "payload": {"report": "REPORT"},
            },
        ],
    }

    def execute(job_type, _payload, **_options):
        page = _minimal_page(
            "deaths" if job_type == "child-deaths" else "damage",
            "Death Report" if job_type == "child-deaths" else "Damage Report",
        )
        if job_type == "child-damage":
            page["content"]["table"]["viewControl"] = {
                "id": "damage_pull_view",
                "label": "Pull",
                "defaultValue": "aggregate",
                "options": [
                    {"value": "aggregate", "label": "All pulls"},
                    {"value": "pull:REPORT:1", "label": "Pull 1"},
                ],
            }
        return page

    with (
        patch.dict(
            application.os.environ,
            {"WHO_MESSED_UP_AGGREGATE_REPORT_WORKERS": "1"},
        ),
        patch.object(application.job_manager, "execute_registered", side_effect=execute),
    ):
        result = application._execute_v2_aggregate_report_job(payload)

    parsed = (
        ReportPageModel.model_validate(result)
        if hasattr(ReportPageModel, "model_validate")
        else ReportPageModel.parse_obj(result)
    )
    assert parsed.report_id == VASHNIK_AGGREGATE_ID
    assert parsed.report_control.default_value == "deaths"
    assert [option.value for option in parsed.report_control.options] == [
        "deaths",
        "damage",
    ]
    assert parsed.content.table.view_control.id == "damage_pull_view"
    assert set(parsed.reports_by_view) == {"deaths", "damage"}


@pytest.mark.parametrize(
    ("included_report_ids", "expected_default"),
    [
        (["deaths", "avoidable-damage", "mechanics"], "mechanics"),
        (["deaths", "avoidable-damage", "damage"], "avoidable-damage"),
    ],
)
def test_aggregate_handler_prefers_mechanics_then_avoidable_damage(
    included_report_ids, expected_default
):
    payload = {
        "report": "REPORT",
        "report_id": VASHNIK_AGGREGATE_ID,
        "report_title": "Aggregate Reports",
        "reports": [
            {
                "report_id": report_id,
                "title": report_id.replace("-", " ").title(),
                "job_type": f"child-{report_id}",
                "payload": {"report": "REPORT"},
            }
            for report_id in included_report_ids
        ],
    }

    with (
        patch.dict(
            application.os.environ,
            {"WHO_MESSED_UP_AGGREGATE_REPORT_WORKERS": "1"},
        ),
        patch.object(
            application.job_manager,
            "execute_registered",
            side_effect=lambda job_type, _payload, **_options: _minimal_page(
                job_type.removeprefix("child-"), job_type
            ),
        ),
    ):
        result = application._execute_v2_aggregate_report_job(payload)

    parsed = (
        ReportPageModel.model_validate(result)
        if hasattr(ReportPageModel, "model_validate")
        else ReportPageModel.parse_obj(result)
    )
    assert parsed.report_control.default_value == expected_default


def test_mechanics_runs_first_without_reordering_selector_or_copying_child_rows():
    children = [{"report_id": name, "title": name, "job_type": name, "payload": {}}
                for name in ("deaths", "mechanics", "damage")]
    calls = []

    def execute(name, payload, **options):
        calls.append(name)
        assert options == {"use_cache": True, "bust_cache": False}
        page = _minimal_page(name, name)
        page["content"]["table"]["rows"] = [{"id": name, "cells": {}}]
        return page

    with (patch.dict(application.os.environ, {"WHO_MESSED_UP_AGGREGATE_REPORT_WORKERS": "1"}),
          patch.object(application.job_manager, "execute_registered", side_effect=execute)):
        result = application._execute_v2_aggregate_report_job({"reports": children})
    assert calls == ["mechanics", "deaths", "damage"]
    assert [o["value"] for o in result["reportControl"]["options"]] == ["deaths", "mechanics", "damage"]
    assert result["content"]["table"]["rows"] == []
    assert result["reportsByView"]["deaths"]["content"]["table"]["rows"]


def test_fresh_aggregate_propagates_freshness_through_child_pool():
    from who_messed_up.cache import ResultCache
    from who_messed_up.jobs import JobManager

    manager = JobManager(ResultCache(), worker_count=1)
    observed = []

    def child(payload):
        observed.append(manager.fresh_run)
        return _minimal_page("child", "Fresh" if manager.fresh_run else "Cached")

    manager.register_handler("child", child)
    manager.register_handler("aggregate", application._execute_v2_aggregate_report_job)
    manager.execute_registered("child", {}, use_cache=True)
    payload = {"reports": [{"report_id": name, "title": name, "job_type": "child", "payload": {}}
                           for name in ("mechanics", "damage")]}
    with patch.object(application, "job_manager", manager):
        result = manager.execute_registered("aggregate", payload, use_cache=True, bust_cache=True)
    assert observed == [False, True, True]
    assert all(page["title"] == "Fresh" for page in result["reportsByView"].values())
