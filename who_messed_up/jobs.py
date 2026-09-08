"""
In-process job queue for long-running Warcraft Logs reports.
"""
from __future__ import annotations

import queue
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from .api import clear_report_context_cache
from .cache import ResultCache, result_cache

JobHandler = Callable[[Dict[str, Any]], Any]


@dataclass
class JobRecord:
    id: str
    job_type: str
    payload: Dict[str, Any]
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    cache_key: Optional[str] = None
    bust_cache: bool = False


def _format_ts(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


class JobManager:
    """
    Bounded worker queue with coalescing for identical in-flight reports.
    """

    def __init__(self, cache: ResultCache, *, worker_count: Optional[int] = None):
        self._cache = cache
        self._handlers: Dict[str, JobHandler] = {}
        self._jobs: Dict[str, JobRecord] = {}
        self._pending_order: list[str] = []
        self._active_by_cache_key: Dict[str, str] = {}
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._lock = threading.Lock()
        configured_workers = worker_count
        if configured_workers is None:
            try:
                configured_workers = int(os.getenv("WHO_MESSED_UP_JOB_WORKERS", "2"))
            except ValueError:
                configured_workers = 2
        self._worker_count = min(max(int(configured_workers), 1), 8)
        self._workers = [
            threading.Thread(
                target=self._worker_loop,
                name=f"report-worker-{index + 1}",
                daemon=True,
            )
            for index in range(self._worker_count)
        ]
        for worker in self._workers:
            worker.start()

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    def execute_registered(self, job_type: str, payload: Dict[str, Any]) -> Any:
        """Execute a registered handler inline for composite report jobs."""
        handler = self._handlers.get(job_type)
        if handler is None:
            raise KeyError(f"No handler registered for job type '{job_type}'")
        return handler(payload)

    def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        *,
        bust_cache: bool = False,
    ) -> Tuple[JobRecord, bool]:
        handler = self._handlers.get(job_type)
        if handler is None:
            raise KeyError(f"No handler registered for job type '{job_type}'")

        cache_key = self._cache.make_key(job_type, payload)
        if not bust_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                now = time.time()
                job = JobRecord(
                    id=str(uuid.uuid4()),
                    job_type=job_type,
                    payload=payload,
                    status="completed",
                    created_at=now,
                    started_at=now,
                    finished_at=now,
                    result=cached,
                    cache_key=cache_key,
                    bust_cache=False,
                )
                with self._lock:
                    self._jobs[job.id] = job
                return job, True

        with self._lock:
            if not bust_cache:
                active_job_id = self._active_by_cache_key.get(cache_key)
                active_job = self._jobs.get(active_job_id) if active_job_id else None
                if active_job is not None and active_job.status in {"pending", "running"}:
                    return active_job, False
            job = JobRecord(
                id=str(uuid.uuid4()),
                job_type=job_type,
                payload=payload,
                cache_key=cache_key,
                bust_cache=bust_cache,
            )
            self._jobs[job.id] = job
            self._pending_order.append(job.id)
            if not bust_cache:
                self._active_by_cache_key[cache_key] = job.id
        # Store handler association separately to avoid looking up later under lock
        self._queue.put(job.id)
        return job, False

    def snapshot(self, job_id: str, *, include_result: bool = False) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            position = self._position_locked(job_id, job.status)
            data: Dict[str, Any] = {
                "id": job.id,
                "type": job.job_type,
                "status": job.status,
                "position": position,
                "created_at": _format_ts(job.created_at),
                "started_at": _format_ts(job.started_at),
                "finished_at": _format_ts(job.finished_at),
                "error": job.error,
            }
            if include_result and job.status == "completed":
                data["result"] = job.result
            return data

    def result_if_ready(self, job_id: str) -> Optional[Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != "completed":
                return None
            return job.result

    def cached_result(self, job_type: str, payload: Dict[str, Any]) -> Optional[Any]:
        cache_key = self._cache.make_key(job_type, payload)
        return self._cache.get(cache_key)

    def _position_locked(self, job_id: str, status: str) -> Optional[int]:
        if status == "pending":
            try:
                idx = self._pending_order.index(job_id)
            except ValueError:
                return None
            return idx + 1
        if status == "running":
            return 0
        return None

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            job = self._jobs.get(job_id)
            if job is None:
                self._queue.task_done()
                continue
            handler = self._handlers.get(job.job_type)
            if handler is None:
                self._queue.task_done()
                continue
            with self._lock:
                job.status = "running"
                job.started_at = time.time()
                try:
                    self._pending_order.remove(job_id)
                except ValueError:
                    pass
            try:
                if job.bust_cache:
                    # A fresh run must also bypass the short-lived metadata cache.
                    clear_report_context_cache()
                result = handler(job.payload)
                if job.cache_key:
                    self._cache.set(job.cache_key, result)
                with self._lock:
                    job.result = result
                    job.status = "completed"
            except Exception as exc:  # pragma: no cover - defensive
                with self._lock:
                    job.error = str(exc)
                    job.status = "failed"
            finally:
                with self._lock:
                    job.finished_at = time.time()
                    if (
                        job.cache_key
                        and self._active_by_cache_key.get(job.cache_key) == job.id
                    ):
                        self._active_by_cache_key.pop(job.cache_key, None)
                self._queue.task_done()


job_manager = JobManager(result_cache)
