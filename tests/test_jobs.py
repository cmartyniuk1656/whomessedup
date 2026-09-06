import threading
import time
from unittest.mock import patch

from who_messed_up.cache import ResultCache
from who_messed_up.jobs import JobManager


def _wait_until(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_identical_inflight_jobs_are_coalesced():
    started = threading.Event()
    release = threading.Event()
    executions = 0

    def handler(payload):
        nonlocal executions
        executions += 1
        started.set()
        assert release.wait(2)
        return {"value": payload["value"]}

    manager = JobManager(ResultCache(), worker_count=2)
    manager.register_handler("report", handler)
    first, first_cached = manager.enqueue("report", {"value": 7})
    assert started.wait(1)
    second, second_cached = manager.enqueue("report", {"value": 7})
    release.set()

    assert first_cached is False
    assert second_cached is False
    assert second.id == first.id
    assert _wait_until(lambda: manager.snapshot(first.id)["status"] == "completed")
    assert executions == 1


def test_worker_pool_runs_distinct_jobs_concurrently():
    both_started = threading.Event()
    release = threading.Event()
    start_count = 0
    start_lock = threading.Lock()

    def handler(payload):
        nonlocal start_count
        with start_lock:
            start_count += 1
            if start_count == 2:
                both_started.set()
        assert release.wait(2)
        return payload

    manager = JobManager(ResultCache(), worker_count=2)
    manager.register_handler("report", handler)
    first, _ = manager.enqueue("report", {"value": 1})
    second, _ = manager.enqueue("report", {"value": 2})
    assert both_started.wait(1)
    release.set()

    assert _wait_until(lambda: manager.snapshot(first.id)["status"] == "completed")
    assert _wait_until(lambda: manager.snapshot(second.id)["status"] == "completed")


def test_fresh_job_invalidates_report_context_cache_before_execution():
    manager = JobManager(ResultCache(), worker_count=1)
    observed = []
    manager.register_handler("report", lambda payload: observed.append(payload) or payload)

    with patch("who_messed_up.jobs.clear_report_context_cache") as clear:
        job, _ = manager.enqueue("report", {"value": 1}, bust_cache=True)
        assert _wait_until(lambda: manager.snapshot(job.id)["status"] == "completed")

    clear.assert_called_once_with()
    assert observed == [{"value": 1}]
