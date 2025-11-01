"""
In-process job queue for long-running Warcraft Logs reports.
"""
from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

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
    return datetime.utcfromtimestamp(value).isoformat() + "Z"


class JobManager:
    """
    Minimal single-worker queue. Ensures we only run one heavy report at a time.
    """

    def __init__(self, cache: ResultCache):
        self._cache = cache
        self._handlers: Dict[str, JobHandler] = {}
        self._jobs: Dict[str, JobRecord] = {}
        self._pending_order: list[str] = []
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

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

        job = JobRecord(
            id=str(uuid.uuid4()),
            job_type=job_type,
            payload=payload,
            cache_key=cache_key,
            bust_cache=bust_cache,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._pending_order.append(job.id)
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
                result = handler(job.payload)
                job.result = result
                job.status = "completed"
                if job.cache_key and not job.bust_cache:
                    self._cache.set(job.cache_key, result)
            except Exception as exc:  # pragma: no cover - defensive
                job.error = str(exc)
                job.status = "failed"
            finally:
                job.finished_at = time.time()
                self._queue.task_done()


job_manager = JobManager(result_cache)

