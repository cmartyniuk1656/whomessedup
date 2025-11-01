"""
Simple in-memory result cache with configurable TTL.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from typing import Any, Dict, Optional

DEFAULT_CACHE_TTL = float(os.getenv("WHO_MESSED_UP_CACHE_TTL", "600"))


class ResultCache:
    """
    Store serialized job results for a short period to avoid redundant upstream calls.
    """

    def __init__(self, ttl_seconds: float = DEFAULT_CACHE_TTL) -> None:
        self._ttl = ttl_seconds
        self._entries: Dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def make_key(job_type: str, payload: Dict[str, Any]) -> str:
        """
        Stable hash for a job type + payload combination.
        """
        serialized = json.dumps({"job_type": job_type, "payload": payload}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if expires_at <= now:
                self._entries.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        expires_at = time.time() + self._ttl
        with self._lock:
            self._entries[key] = (expires_at, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def set_ttl(self, ttl_seconds: float) -> None:
        with self._lock:
            self._ttl = ttl_seconds


result_cache = ResultCache()

