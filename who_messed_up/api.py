"""
Utilities for querying the Warcraft Logs GraphQL API.
"""
from __future__ import annotations

import os
import logging
import time
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Any, Tuple

import requests

LOGGER = logging.getLogger(__name__)

API_URL = "https://www.warcraftlogs.com/api/v2/client"
OAUTH_URL = "https://www.warcraftlogs.com/oauth/token"

REPORT_OVERVIEW_QUERY = """
query($code: String!) {
  reportData {
    report(code: $code) {
      title
      startTime
      endTime
      fights {
        id
        encounterID
        name
        startTime
        endTime
        kill
        difficulty
      }
      masterData {
        actors {
          id
          name
          type
          subType
          petOwner
        }
        abilities {
          gameID
          name
        }
      }
    }
  }
}
"""

REPORT_FIGHTS_QUERY = """
query($code: String!) {
  reportData {
    report(code: $code) {
      fights {
        id
        encounterID
        name
        startTime
        endTime
        kill
        difficulty
        friendlyPlayers
        friendlySpecs
      }
      masterData {
        actors {
          id
          name
          type
          subType
          petOwner
        }
      }
    }
  }
}
"""

PLAYER_DETAILS_QUERY = """
query($code: String!, $fightIDs: [Int!], $includeCombatantInfo: Boolean) {
  reportData {
    report(code: $code) {
      playerDetails(fightIDs: $fightIDs, includeCombatantInfo: $includeCombatantInfo)
    }
  }
}
"""

EVENTS_QUERY = """
query($code: String!, $dataType: EventDataType!, $start: Float!, $end: Float!, $limit: Int!, $filter: String, $includeResources: Boolean, $useActorIDs: Boolean, $fightIDs: [Int!], $abilityID: Float, $sourceID: Int, $targetID: Int, $wipeCutoff: Int) {
  reportData {
    report(code: $code) {
      events(dataType: $dataType, startTime: $start, endTime: $end, limit: $limit, filterExpression: $filter, includeResources: $includeResources, useActorIDs: $useActorIDs, fightIDs: $fightIDs, abilityID: $abilityID, sourceID: $sourceID, targetID: $targetID, wipeCutoff: $wipeCutoff) {
        data
        nextPageTimestamp
      }
    }
  }
}
"""

TABLE_QUERY = """
query($code: String!, $dataType: TableDataType!, $fightIDs: [Int!], $startTime: Float!, $endTime: Float!, $filter: String) {
  reportData {
    report(code: $code) {
      table(dataType: $dataType, fightIDs: $fightIDs, startTime: $startTime, endTime: $endTime, filterExpression: $filter)
    }
  }
}
"""



@dataclass
class Fight:
    id: int
    name: str
    start: float
    end: float
    kill: bool
    difficulty: Optional[int] = None
    encounter_id: Optional[int] = None
    friendly_player_ids: Tuple[int, ...] = ()
    friendly_specs: Tuple[Optional[str], ...] = ()


@dataclass
class ReportMetadata:
    fights: List[Fight]
    actors: Dict[int, str]
    abilities: Dict[int, str]


_TOKEN_EXPIRY_SKEW_SECONDS = 60.0
_token_cache: Dict[Tuple[str, str], Tuple[float, str]] = {}
_token_cache_lock = threading.Lock()


def _bounded_env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


_report_context_cache_ttl = _bounded_env_float(
    "WCL_REPORT_CONTEXT_CACHE_TTL_SECONDS", 60.0, minimum=0.0, maximum=600.0
)
_report_context_cache_max_entries = 256
_report_context_cache: "OrderedDict[Tuple[Any, ...], Tuple[float, Any]]" = OrderedDict()
_report_context_cache_lock = threading.Lock()
_CACHE_MISS = object()


def _report_context_cache_get(key: Tuple[Any, ...]) -> Any:
    if _report_context_cache_ttl <= 0:
        return _CACHE_MISS
    now = time.monotonic()
    with _report_context_cache_lock:
        cached = _report_context_cache.get(key)
        if cached is None:
            return _CACHE_MISS
        expires_at, value = cached
        if expires_at <= now:
            _report_context_cache.pop(key, None)
            return _CACHE_MISS
        _report_context_cache.move_to_end(key)
        return deepcopy(value)


def _report_context_cache_set(key: Tuple[Any, ...], value: Any) -> None:
    if _report_context_cache_ttl <= 0:
        return
    with _report_context_cache_lock:
        _report_context_cache[key] = (
            time.monotonic() + _report_context_cache_ttl,
            deepcopy(value),
        )
        _report_context_cache.move_to_end(key)
        while len(_report_context_cache) > _report_context_cache_max_entries:
            _report_context_cache.popitem(last=False)


def clear_report_context_cache(report_code: Optional[str] = None) -> None:
    """Clear cached report metadata, optionally for one report code."""
    with _report_context_cache_lock:
        if report_code is None:
            _report_context_cache.clear()
            return
        matching_keys = [
            key for key in _report_context_cache if len(key) > 1 and key[1] == report_code
        ]
        for key in matching_keys:
            _report_context_cache.pop(key, None)


def _bounded_env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


_request_slots = threading.BoundedSemaphore(
    _bounded_env_int("WCL_MAX_CONCURRENT_REQUESTS", 4, minimum=1, maximum=16)
)
_request_attempts = _bounded_env_int("WCL_REQUEST_ATTEMPTS", 3, minimum=1, maximum=6)
_table_batch_workers = _bounded_env_int(
    "WCL_TABLE_BATCH_WORKERS", 4, minimum=1, maximum=8
)


def get_token_from_client(
    client_id: Optional[str], client_secret: Optional[str], *, timeout: int = 30
) -> Optional[str]:
    """
    Exchange a client id/secret pair for a bearer token via the OAuth client credentials flow.
    """
    if not client_id or not client_secret:
        return None
    cache_key = (client_id, client_secret)
    now = time.monotonic()
    # Serialize cache misses so a newly enabled worker pool does not perform the
    # same OAuth exchange more than once at startup.
    with _token_cache_lock:
        cached = _token_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]
        try:
            resp = requests.post(
                OAUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
            access_token = payload.get("access_token")
            if not access_token:
                return None
            try:
                expires_in = max(float(payload.get("expires_in") or 3600.0), 0.0)
            except (TypeError, ValueError):
                expires_in = 3600.0
            expires_at = time.monotonic() + max(expires_in - _TOKEN_EXPIRY_SKEW_SECONDS, 1.0)
            _token_cache[cache_key] = (expires_at, access_token)
            return access_token
        except Exception:
            return None


def gql(session: requests.Session, token: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a GraphQL query against the Warcraft Logs API.
    """
    headers = {"Authorization": f"Bearer {token}"}
    resp = None
    started_at = time.perf_counter()
    attempts_used = 0
    for attempt in range(_request_attempts):
        attempts_used = attempt + 1
        try:
            with _request_slots:
                resp = session.post(
                    API_URL,
                    json={"query": query, "variables": variables},
                    headers=headers,
                    timeout=60,
                )
        except (requests.ConnectionError, requests.Timeout):
            if attempt + 1 >= _request_attempts:
                raise
            time.sleep(0.5 * (2**attempt))
            continue
        if resp.status_code != 429 and resp.status_code < 500:
            break
        if attempt + 1 >= _request_attempts:
            break
        retry_after = resp.headers.get("Retry-After")
        try:
            delay = float(retry_after) if retry_after is not None else 0.5 * (2**attempt)
        except ValueError:
            delay = 0.5 * (2**attempt)
        time.sleep(max(delay, 0.0))
    if resp is None:  # pragma: no cover - defensive
        raise RuntimeError("Warcraft Logs request did not produce a response.")
    LOGGER.debug(
        "Warcraft Logs GraphQL request completed status=%s elapsed_ms=%.1f bytes=%s attempts=%s",
        resp.status_code,
        (time.perf_counter() - started_at) * 1000.0,
        len(resp.content or b""),
        attempts_used,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        detail = ""
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise requests.HTTPError(f"{exc} | Response: {detail}") from exc
    data = resp.json()
    errors = data.get("errors")
    if errors:
        raise RuntimeError(f"GraphQL error(s): {errors}")
    return data["data"]


def _build_actor_maps(report: Dict[str, Any]) -> Tuple[Dict[int, str], Dict[int, Optional[str]], Dict[int, Optional[int]]]:
    master = report.get("masterData") or {}
    actors = master.get("actors") or []
    names: Dict[int, str] = {}
    classes: Dict[int, Optional[str]] = {}
    owners: Dict[int, Optional[int]] = {}
    for actor in actors:
        try:
            actor_id = int(actor.get("id"))
        except (TypeError, ValueError):
            continue
        name = actor.get("name")
        if name:
            names[actor_id] = name
        if (actor.get("type") or "").lower() == "player":
            subtype = actor.get("subType") or actor.get("subtype")
            if subtype:
                classes[actor_id] = subtype
        owner_id = actor.get("petOwner")
        if owner_id not in (None, ""):
            try:
                owners[actor_id] = int(owner_id)
            except (TypeError, ValueError):
                continue
    return names, classes, owners


def _coerce_optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def fetch_fights(session: requests.Session, token: str, code: str) -> Tuple[List[Fight], Dict[int, str], Dict[int, Optional[str]], Dict[int, Optional[int]]]:
    cache_key = ("fights", code)
    cached = _report_context_cache_get(cache_key)
    if cached is not _CACHE_MISS:
        return cached
    overview = gql(session, token, REPORT_FIGHTS_QUERY, {"code": code})
    report = overview["reportData"]["report"]
    fights: List[Fight] = []
    for raw in report.get("fights") or []:
        if raw.get("startTime") is None or raw.get("endTime") is None:
            continue
        difficulty = raw.get("difficulty")
        try:
            difficulty_value = int(difficulty) if difficulty not in (None, "") else None
        except (TypeError, ValueError):
            difficulty_value = None
        fights.append(
            Fight(
                id=int(raw["id"]),
                name=raw.get("name") or f"Fight {raw['id']}",
                start=float(raw["startTime"]),
                end=float(raw["endTime"]),
                kill=bool(raw.get("kill")),
                difficulty=difficulty_value,
                encounter_id=_coerce_optional_int(raw.get("encounterID")),
                friendly_player_ids=tuple(
                    player_id
                    for player_id in (
                        _coerce_optional_int(value) for value in (raw.get("friendlyPlayers") or [])
                    )
                    if player_id is not None
                ),
                friendly_specs=tuple(
                    str(value) if value not in (None, "") else None
                    for value in (raw.get("friendlySpecs") or [])
                ),
            )
        )
    actor_names, actor_classes, actor_owners = _build_actor_maps(report)
    result = (fights, actor_names, actor_classes, actor_owners)
    _report_context_cache_set(cache_key, result)
    return result


def _apply_actor_names(event: Dict[str, Any], actor_names: Dict[int, str]) -> None:
    """
    Mutate an event dict in-place to inject target/source names from actor metadata.
    """
    target_id = event.get("targetID")
    if target_id is None and isinstance(event.get("target"), dict):
        target_id = event["target"].get("id")
    if target_id is not None:
        try:
            target_id_int = int(target_id)
        except (TypeError, ValueError):
            target_id_int = None
        if target_id_int is not None:
            name = actor_names.get(target_id_int)
            if name:
                if not isinstance(event.get("target"), dict):
                    event["target"] = {}
                event["target"]["name"] = event["target"].get("name") or name
                event.setdefault("targetName", name)

    source_id = event.get("sourceID")
    if source_id is None and isinstance(event.get("source"), dict):
        source_id = event["source"].get("id")
    if source_id is not None:
        try:
            source_id_int = int(source_id)
        except (TypeError, ValueError):
            source_id_int = None
        if source_id_int is not None:
            name = actor_names.get(source_id_int)
            if name:
                if not isinstance(event.get("source"), dict):
                    event["source"] = {}
                event["source"]["name"] = event["source"].get("name") or name
                event.setdefault("sourceName", name)


def _compose_filter_expression(
    *,
    ability_id: Optional[int],
    ability_name: Optional[str],
    extra_filter: Optional[str],
) -> Optional[str]:
    parts: List[str] = []
    if extra_filter:
        parts.append(f"({extra_filter})")
    if ability_id is not None:
        ability_int = int(ability_id)
        parts.append(f"(ability.id = {ability_int} or abilityGameID = {ability_int})")
    if ability_name:
        safe_name = ability_name.replace('"', '\\"')
        parts.append(f'ability.name = "{safe_name}"')
    if not parts:
        return None
    return " and ".join(parts)


def filter_fights(fights: List[Fight], name_filter: Optional[str]) -> List[Fight]:
    """
    Filter fights by substring match on the fight name.
    """
    if not name_filter:
        return fights
    needle = name_filter.lower()
    return [fight for fight in fights if needle in (fight.name or "").lower()]


def fetch_events(
    session: requests.Session,
    token: str,
    *,
    code: str,
    data_type: str,
    start: float,
    end: float,
    limit: int = 5000,
    ability_id: Optional[int] = None,
    ability_name: Optional[str] = None,
    extra_filter: Optional[str] = None,
    include_resources: Optional[bool] = None,
    use_actor_ids: Optional[bool] = None,
    fight_ids: Optional[Iterable[int]] = None,
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    wipe_cutoff: Optional[int] = None,
    actor_names: Optional[Dict[int, str]] = None,
    sleep_seconds: float = 0.1,
) -> Iterator[Dict[str, Any]]:
    """
    Stream paginated events for a report window and optional fight selection.
    """
    cursor: float = float(start)
    selected_fight_ids = [int(fight_id) for fight_id in fight_ids] if fight_ids else None

    while True:
        direct_ability_id = ability_id if ability_id is not None and not ability_name and not extra_filter else None
        variables = {
            "code": code,
            "dataType": data_type,
            "start": float(cursor),
            "end": float(end),
            "limit": int(limit),
            "filter": _compose_filter_expression(
                ability_id=None if direct_ability_id is not None else ability_id,
                ability_name=ability_name,
                extra_filter=extra_filter,
            ),
            "includeResources": include_resources,
            "useActorIDs": use_actor_ids,
            "fightIDs": selected_fight_ids,
            "abilityID": float(direct_ability_id) if direct_ability_id is not None else None,
            "sourceID": int(source_id) if source_id is not None else None,
            "targetID": int(target_id) if target_id is not None else None,
            "wipeCutoff": int(wipe_cutoff) if wipe_cutoff is not None else None,
        }
        payload = gql(session, token, EVENTS_QUERY, variables)
        events_data = payload["reportData"]["report"]["events"]
        rows = events_data.get("data") or []
        for row in rows:
            if actor_names:
                _apply_actor_names(row, actor_names)
            yield row

        next_ts = events_data.get("nextPageTimestamp")

        if next_ts is not None:
            if next_ts >= end:
                break
            next_cursor = float(next_ts)
            if next_cursor <= cursor:
                raise RuntimeError(
                    f"Warcraft Logs pagination did not advance (cursor={cursor}, next={next_cursor})."
                )
            cursor = next_cursor
        else:
            break

        time.sleep(sleep_seconds)


def events_for_fights(
    session: requests.Session,
    token: str,
    *,
    code: str,
    data_type: str,
    fights: Iterable[Fight],
    limit: int = 5000,
    ability_id: Optional[int] = None,
    ability_name: Optional[str] = None,
    extra_filter: Optional[str] = None,
    actor_names: Optional[Dict[int, str]] = None,
    use_actor_ids: Optional[bool] = None,
    sleep_seconds: float = 0.1,
) -> Iterator[Dict[str, Any]]:
    """
    Iterate events for each fight in ``fights`` with the same parameters.
    """
    for fight in fights:
        for event in fetch_events(
            session,
            token,
            code=code,
            data_type=data_type,
            start=fight.start,
            end=fight.end,
            limit=limit,
            ability_id=ability_id,
            ability_name=ability_name,
            extra_filter=extra_filter,
            actor_names=actor_names,
            use_actor_ids=use_actor_ids,
            sleep_seconds=sleep_seconds,
        ):
            yield event


def fetch_events_grouped(
    session: requests.Session,
    token: str,
    *,
    code: str,
    data_type: str,
    fights: Iterable[Fight],
    limit: int = 5000,
    ability_id: Optional[int] = None,
    ability_name: Optional[str] = None,
    extra_filter: Optional[str] = None,
    include_resources: Optional[bool] = None,
    use_actor_ids: Optional[bool] = True,
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    wipe_cutoff: Optional[int] = None,
    actor_names: Optional[Dict[int, str]] = None,
    sleep_seconds: float = 0.1,
) -> Dict[int, List[Dict[str, Any]]]:
    """Fetch one event stream for several fights and partition it by fight ID."""
    selected_fights = list(fights)
    grouped: Dict[int, List[Dict[str, Any]]] = {
        int(fight.id): [] for fight in selected_fights
    }
    if not selected_fights:
        return grouped

    fights_by_id = {int(fight.id): fight for fight in selected_fights}
    for event in fetch_events(
        session,
        token,
        code=code,
        data_type=data_type,
        start=min(fight.start for fight in selected_fights),
        end=max(fight.end for fight in selected_fights),
        limit=limit,
        ability_id=ability_id,
        ability_name=ability_name,
        extra_filter=extra_filter,
        include_resources=include_resources,
        use_actor_ids=use_actor_ids,
        fight_ids=fights_by_id.keys(),
        source_id=source_id,
        target_id=target_id,
        wipe_cutoff=wipe_cutoff,
        actor_names=actor_names,
        sleep_seconds=sleep_seconds,
    ):
        fight_id = _coerce_optional_int(event.get("fight"))
        if fight_id not in fights_by_id:
            timestamp = event.get("timestamp")
            try:
                event_timestamp = float(timestamp)
            except (TypeError, ValueError):
                continue
            fight_id = next(
                (
                    int(fight.id)
                    for fight in selected_fights
                    if fight.start <= event_timestamp <= fight.end
                ),
                None,
            )
        if fight_id in grouped:
            grouped[fight_id].append(event)
    return grouped


def fetch_player_details(session: requests.Session, token: str, *, code: str, fight_ids: List[int]) -> Dict[str, Any]:
    """
    Retrieve the playerDetails JSON block for the given fights.
    """
    if not fight_ids:
        return {}
    normalized_fight_ids = tuple(sorted({int(fid) for fid in fight_ids}))
    cache_key = ("player_details", code, normalized_fight_ids)
    cached = _report_context_cache_get(cache_key)
    if cached is not _CACHE_MISS:
        return cached
    variables = {
        "code": code,
        "fightIDs": list(normalized_fight_ids),
        "includeCombatantInfo": False,
    }
    payload = gql(session, token, PLAYER_DETAILS_QUERY, variables)
    player_details = (((payload["reportData"]["report"].get("playerDetails") or {}).get("data") or {}).get("playerDetails") or {})
    _report_context_cache_set(cache_key, player_details)
    return player_details


def fetch_table(
    session: requests.Session,
    token: str,
    *,
    code: str,
    data_type: str,
    start: float,
    end: float,
    fight_id: Optional[int] = None,
    fight_ids: Optional[Iterable[int]] = None,
    filter_expr: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch aggregated table data (Damage, Healing, etc.) for a specific fight.
    """
    variables = {
        "code": code,
        "dataType": data_type,
        "fightIDs": (
            [int(value) for value in fight_ids]
            if fight_ids is not None
            else ([int(fight_id)] if fight_id is not None else [])
        ),
        "startTime": float(start),
        "endTime": float(end),
        "filter": filter_expr,
    }
    payload = gql(session, token, TABLE_QUERY, variables)
    table = ((payload["reportData"]["report"].get("table") or {}).get("data") or {})
    return table


def fetch_tables(
    session: requests.Session,
    token: str,
    *,
    code: str,
    table_requests: Iterable[Dict[str, Any]],
    batch_size: int = 12,
) -> List[Dict[str, Any]]:
    """Fetch several independent report tables with GraphQL aliases.

    Warcraft Logs still accounts for the work behind each table, but combining
    them removes an HTTP round trip per phase/target. Requests are chunked to
    keep individual GraphQL documents and responses bounded.
    """
    requested = list(table_requests)
    if not requested:
        return []
    safe_batch_size = max(1, int(batch_size))
    chunks = [
        requested[chunk_start : chunk_start + safe_batch_size]
        for chunk_start in range(0, len(requested), safe_batch_size)
    ]
    if len(chunks) == 1 or _table_batch_workers == 1:
        chunk_results = [
            _fetch_table_chunk(session, token, code=code, requests_chunk=chunk)
            for chunk in chunks
        ]
    else:
        # Each GraphQL document is independent. Running bounded chunks in
        # parallel removes serial network waits while gql() still enforces the
        # process-wide Warcraft Logs concurrency and retry limits.
        with ThreadPoolExecutor(
            max_workers=min(len(chunks), _table_batch_workers),
            thread_name_prefix="wcl-tables",
        ) as executor:
            futures = [
                executor.submit(
                    _fetch_table_chunk,
                    session,
                    token,
                    code=code,
                    requests_chunk=chunk,
                )
                for chunk in chunks
            ]
            chunk_results = [future.result() for future in futures]
    return [table for chunk in chunk_results for table in chunk]


def _fetch_table_chunk(
    session: requests.Session,
    token: str,
    *,
    code: str,
    requests_chunk: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Fetch one bounded GraphQL table batch and preserve request order."""
    definitions = ["$code: String!"]
    fields: List[str] = []
    variables: Dict[str, Any] = {"code": code}
    for index, request in enumerate(requests_chunk):
        definitions.extend(
            [
                f"$dataType{index}: TableDataType!",
                f"$fightIDs{index}: [Int!]",
                f"$startTime{index}: Float!",
                f"$endTime{index}: Float!",
                f"$filter{index}: String",
            ]
        )
        fields.append(
            f"q{index}: table("
            f"dataType: $dataType{index}, fightIDs: $fightIDs{index}, "
            f"startTime: $startTime{index}, endTime: $endTime{index}, "
            f"filterExpression: $filter{index})"
        )
        variables.update(
            {
                f"dataType{index}": request["data_type"],
                f"fightIDs{index}": [
                    int(value) for value in request.get("fight_ids") or []
                ],
                f"startTime{index}": float(request["start"]),
                f"endTime{index}": float(request["end"]),
                f"filter{index}": request.get("filter_expr"),
            }
        )
    query = (
        f"query({', '.join(definitions)}) {{ reportData {{ report(code: $code) {{ "
        f"{' '.join(fields)} }} }} }}"
    )
    payload = gql(session, token, query, variables)
    report = payload["reportData"]["report"]
    return [
        ((report.get(f"q{index}") or {}).get("data") or {})
        for index in range(len(requests_chunk))
    ]

