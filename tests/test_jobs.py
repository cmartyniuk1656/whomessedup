import threading
import time
from concurrent.futures import ThreadPoolExecutor
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


def test_inline_children_reuse_completed_standalone_results_and_populate_cache():
    manager = JobManager(ResultCache(), worker_count=1)
    calls = []
    manager.register_handler("child", lambda payload: calls.append(payload) or {"value": len(calls)})
    job, _ = manager.enqueue("child", {"id": 1})
    assert _wait_until(lambda: job.status == "completed")
    assert manager.execute_registered("child", {"id": 1}, use_cache=True) == {"value": 1}
    manager.execute_registered("child", {"id": 2}, use_cache=True)
    second, cached = manager.enqueue("child", {"id": 2})
    assert cached and second.result == {"value": 2}
    assert len(calls) == 2


def test_inline_child_does_not_wait_for_a_job_queued_behind_parent():
    manager = JobManager(ResultCache(), worker_count=1)
    calls = []
    manager.register_handler("child", lambda payload: calls.append(payload) or payload)

    def parent(payload):
        manager.enqueue("child", payload)
        return manager.execute_registered("child", payload, use_cache=True)

    manager.register_handler("parent", parent)
    job, _ = manager.enqueue("parent", {"id": 1})
    assert _wait_until(lambda: job.status == "completed")
    assert _wait_until(lambda: all(j.status == "completed" for j in manager._jobs.values()))
    assert len(calls) == 1


def test_concurrent_inline_children_share_one_execution():
    manager = JobManager(ResultCache(), worker_count=1)
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def child(payload):
        calls.append(payload)
        entered.set()
        assert release.wait(2)
        return payload

    manager.register_handler("child", child)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(manager.execute_registered, "child", {"id": 1}, use_cache=True)
        assert entered.wait(1)
        second = pool.submit(manager.execute_registered, "child", {"id": 1}, use_cache=True)
        release.set()
        assert first.result() == second.result() == {"id": 1}
    assert len(calls) == 1


def test_fresh_execution_bypasses_inflight_work_and_prevents_stale_cache_write():
    manager = JobManager(ResultCache(), worker_count=1)
    entered = threading.Event()
    release = threading.Event()

    def child(payload):
        if manager.fresh_run:
            return {"fresh": True}
        entered.set()
        assert release.wait(2)
        return {"fresh": False}

    manager.register_handler("child", child)
    with ThreadPoolExecutor(max_workers=1) as pool:
        older = pool.submit(manager.execute_registered, "child", {}, use_cache=True)
        assert entered.wait(1)
        assert manager.execute_registered("child", {}, use_cache=True, bust_cache=True) == {"fresh": True}
        release.set()
        assert older.result() == {"fresh": False}
    assert manager.cached_result("child", {}) == {"fresh": True}
    assert manager.fresh_run is False


def test_failed_execution_does_not_poison_later_retry():
    manager = JobManager(ResultCache(), worker_count=1)
    def fail(payload):
        raise ValueError("failed")
    manager.register_handler("child", fail)
    import pytest
    with pytest.raises(ValueError, match="failed"):
        manager.execute_registered("child", {}, use_cache=True)
    manager.register_handler("child", lambda payload: {"ok": True})
    assert manager.execute_registered("child", {}, use_cache=True) == {"ok": True}
