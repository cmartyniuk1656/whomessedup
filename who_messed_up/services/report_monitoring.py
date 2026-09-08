"""Lightweight Warcraft Logs metadata polling for near-real-time reports."""
from __future__ import annotations

import os
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from ..api import gql
from ..env import load_env
from .common import _normalize_fight_difficulty, _resolve_token


REPORT_WATCH_QUERY = """
query ReportWatch($code: String!) {
  reportData {
    report(code: $code) {
      code
      endTime
      revision
      segments
      fights(translate: false) {
        id
        encounterID
        name
        startTime
        endTime
        kill
        difficulty
      }
    }
  }
}
"""


@dataclass(frozen=True)
class ReportWatchFight:
    id: int
    encounter_id: Optional[int]
    name: str
    start_time: float
    end_time: float
    kill: bool
    difficulty: Optional[int]


@dataclass(frozen=True)
class ReportWatchSnapshot:
    report_code: str
    end_time: float
    revision: int
    segments: int
    fights: List[ReportWatchFight]


def _watch_cache_ttl() -> float:
    try:
        configured = float(os.getenv("WCL_REPORT_WATCH_CACHE_TTL_SECONDS", "5"))
    except ValueError:
        configured = 5.0
    return min(max(configured, 0.0), 30.0)


_watch_cache: Dict[str, Tuple[float, ReportWatchSnapshot]] = {}
_watch_cache_lock = threading.Lock()


def clear_report_watch_cache(report_code: Optional[str] = None) -> None:
    """Clear shared watch metadata, primarily for deterministic tests."""
    with _watch_cache_lock:
        if report_code is None:
            _watch_cache.clear()
        else:
            _watch_cache.pop(report_code, None)


def _cached_snapshot(report_code: str) -> Optional[ReportWatchSnapshot]:
    now = time.monotonic()
    with _watch_cache_lock:
        cached = _watch_cache.get(report_code)
        if cached is None:
            return None
        expires_at, snapshot = cached
        if expires_at <= now:
            _watch_cache.pop(report_code, None)
            return None
        return deepcopy(snapshot)


def _store_snapshot(snapshot: ReportWatchSnapshot) -> None:
    ttl = _watch_cache_ttl()
    if ttl <= 0:
        return
    with _watch_cache_lock:
        _watch_cache[snapshot.report_code] = (
            time.monotonic() + ttl,
            deepcopy(snapshot),
        )


def _fetch_raw_snapshot(
    *,
    report_code: str,
    force_refresh: bool,
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
    session: Optional[requests.Session],
) -> ReportWatchSnapshot:
    if not force_refresh:
        cached = _cached_snapshot(report_code)
        if cached is not None:
            return cached

    request_session = session or requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    payload = gql(request_session, bearer, REPORT_WATCH_QUERY, {"code": report_code})
    report = (payload.get("reportData") or {}).get("report")
    if not report:
        raise ValueError("Warcraft Logs report was not found or is not accessible.")

    fights: List[ReportWatchFight] = []
    for row in report.get("fights") or []:
        if not row or row.get("id") is None:
            continue
        encounter_id = row.get("encounterID")
        difficulty = row.get("difficulty")
        fights.append(
            ReportWatchFight(
                id=int(row["id"]),
                encounter_id=int(encounter_id) if encounter_id is not None else None,
                name=str(row.get("name") or ""),
                start_time=float(row.get("startTime") or 0.0),
                end_time=float(row.get("endTime") or 0.0),
                kill=bool(row.get("kill", False)),
                difficulty=int(difficulty) if difficulty is not None else None,
            )
        )
    snapshot = ReportWatchSnapshot(
        report_code=str(report.get("code") or report_code),
        end_time=float(report.get("endTime") or 0.0),
        revision=int(report.get("revision") or 0),
        segments=int(report.get("segments") or 0),
        fights=fights,
    )
    _store_snapshot(snapshot)
    return snapshot


def fetch_report_watch_snapshot(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    difficulty: Any = None,
    fight_ids: Optional[Iterable[int]] = None,
    kill_only: bool = False,
    force_refresh: bool = False,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> ReportWatchSnapshot:
    """Return current report metadata filtered to the configured encounter."""
    load_env()
    snapshot = _fetch_raw_snapshot(
        report_code=report_code,
        force_refresh=force_refresh,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        session=session,
    )
    name_filter = " ".join(str(fight_name or "").strip().lower().split())
    normalized_difficulty = _normalize_fight_difficulty(difficulty)
    selected_fight_ids = {int(fight_id) for fight_id in fight_ids or []}
    matching = [
        fight
        for fight in snapshot.fights
        if (not name_filter or name_filter in " ".join(fight.name.lower().split()))
        and (not selected_fight_ids or fight.id in selected_fight_ids)
        and (not kill_only or fight.kill)
        and (
            normalized_difficulty is None
            or fight.difficulty == normalized_difficulty
        )
    ]
    return ReportWatchSnapshot(
        report_code=snapshot.report_code,
        end_time=snapshot.end_time,
        revision=snapshot.revision,
        segments=snapshot.segments,
        fights=matching,
    )


__all__ = [
    "ReportWatchFight",
    "ReportWatchSnapshot",
    "clear_report_watch_cache",
    "fetch_report_watch_snapshot",
]
