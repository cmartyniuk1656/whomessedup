from copy import deepcopy

from who_messed_up.services.view_models.common import ReportPageModel
from who_messed_up.services.view_models.indexed_rows import index_report_rows


def page():
    row = {"id": "one", "cells": {"value": {"value": 5}}, "details": {
        "variant": "event_groups", "groups": [{"id": "evidence", "title": "Evidence", "items": [
            {"id": "event", "label": "Player", "description": "Full evidence"}]}]}}
    return ReportPageModel.model_validate({
        "reportId": "test", "reportCode": "R", "title": "Report",
        "header": {"subtitle": "test", "tags": []}, "content": {"variant": "table", "table": {
            "layout": "compact", "columns": [], "rows": [row], "rowsByView": {"all": [row], "empty": []},
            "rowsByCombinedView": {"all::sets": [row, row]}, "emptyState": "Empty",
            "defaultSort": {"columnId": "value", "direction": "asc"},
        }},
    }).model_dump(by_alias=True)


def test_indexing_preserves_evidence_and_all_ordered_views_after_model_round_trip():
    original = page()
    before = deepcopy(original)
    indexed = index_report_rows(original)
    reparsed = ReportPageModel.model_validate(indexed).model_dump(by_alias=True)
    assert reparsed == indexed
    table = indexed["content"]["table"]
    assert table["layout"] == "compact"
    assert len(table["rowsById"]) == 1
    assert table["rowIdsByView"]["empty"] == []
    assert [table["rowsById"][key] for key in table["rowIdsByCombinedView"]["all::sets"]] == before["content"]["table"]["rowsByCombinedView"]["all::sets"]
    assert original == before
    assert index_report_rows(indexed) is indexed


def test_reused_display_id_with_different_content_does_not_drop_data():
    original = page()
    variant = deepcopy(original["content"]["table"]["rows"][0])
    variant["cells"]["value"]["value"] = 99
    original["content"]["table"]["rowsByView"]["variant"] = [variant]
    table = index_report_rows(original)["content"]["table"]
    assert len(table["rowsById"]) == 2
    assert table["rowsById"][table["rowIdsByView"]["variant"][0]] == variant


def test_legacy_model_does_not_gain_indexed_fields():
    assert "rowStorage" not in page()["content"]["table"]
