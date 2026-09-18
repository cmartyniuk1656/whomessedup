import asyncio
import gzip
import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

import pytest

import app as application


async def request(path, *, method="GET", encoding="gzip", body=None, query=""):
    messages = []
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
             "query_string": query.encode(), "root_path": "",
             "headers": [(b"accept-encoding", encoding.encode()), (b"content-type", b"application/json")],
             "server": ("test", 80), "client": ("test", 1)}

    async def receive():
        return {"type": "http.request", "body": json.dumps(body or {}).encode(), "more_body": False}

    async def send(message):
        messages.append(message)

    await application.app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    data = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), data


@pytest.mark.parametrize("endpoint", ["poll", "post", "cached"])
def test_large_reports_compress_without_changing_results(endpoint):
    page = {"reportId": "R", "reportCode": "R", "title": "Report" * 1000,
            "header": {"subtitle": "test", "tags": []}, "content": {"variant": "table", "table": {
                "columns": [], "rows": [], "defaultSort": {"columnId": "name", "direction": "asc"},
                "emptyState": "No rows"}}}
    snapshot = dict(id="test", type="report", status="completed", position=None,
                    created_at=None, started_at=None, finished_at=None, result=page)
    args = ({"path": "/api/jobs/test"} if endpoint == "poll" else
            {"path": "/api/v2/reports/test/jobs", "method": "POST", "body": {"values": {}}} if endpoint == "post" else
            {"path": "/api/v2/reports/test/cached", "query": urlencode({"values": "e30="})})
    with (patch.object(application.job_manager, "snapshot", return_value=snapshot),
          patch.object(application.job_manager, "enqueue", return_value=(SimpleNamespace(status="completed", result=page), True)),
          patch.object(application.job_manager, "cached_result", return_value=page),
          patch.object(application, "get_registered_report"),
          patch.object(application, "build_report_job_request", return_value=("report", {}, False))):
        status, headers, compressed = asyncio.run(request(**args))
        plain_status, plain_headers, plain = asyncio.run(request(**args, encoding="identity"))
    assert status == plain_status == 200
    assert headers[b"content-encoding"] == b"gzip"
    assert b"Accept-Encoding" in headers[b"vary"]
    assert b"content-encoding" not in plain_headers
    assert gzip.decompress(compressed) == plain
    assert len(compressed) < len(plain) / 2


def test_health_response_stays_small_and_uncompressed():
    status, headers, body = asyncio.run(request("/health"))
    assert status == 200
    assert b"content-encoding" not in headers
    assert json.loads(body) == {"status": "ok"}
