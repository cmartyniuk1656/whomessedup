"""
Utilities for querying the Warcraft Logs GraphQL API.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Any, Tuple

import requests

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
        name
        startTime
        endTime
        kill
      }
      masterData {
        actors {
          id
          name
          type
          subType
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

PLAYER_DETAILS_QUERY = """
query($code: String!, $fightIDs: [Int!]) {
  reportData {
    report(code: $code) {
      playerDetails(fightIDs: $fightIDs)
    }
  }
}
"""

EVENTS_QUERY = """
query($code: String!, $dataType: EventDataType!, $start: Float!, $end: Float!, $limit: Int!, $filter: String) {
  reportData {
    report(code: $code) {
      events(dataType: $dataType, startTime: $start, endTime: $end, limit: $limit, filterExpression: $filter) {
        data
        nextPageTimestamp
      }
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


@dataclass
class ReportMetadata:
    fights: List[Fight]
    actors: Dict[int, str]
    abilities: Dict[int, str]


def get_token_from_client(
    client_id: Optional[str], client_secret: Optional[str], *, timeout: int = 30
) -> Optional[str]:
    """
    Exchange a client id/secret pair for a bearer token via the OAuth client credentials flow.
    """
    if not client_id or not client_secret:
        return None
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
        return resp.json().get("access_token")
    except Exception:
        return None


def gql(session: requests.Session, token: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a GraphQL query against the Warcraft Logs API.
    """
    headers = {"Authorization": f"Bearer {token}"}
    resp = session.post(API_URL, json={"query": query, "variables": variables}, headers=headers, timeout=60)
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


def _build_actor_maps(report: Dict[str, Any]) -> Tuple[Dict[int, str], Dict[int, Optional[str]]]:
    master = report.get("masterData") or {}
    actors = master.get("actors") or []
    names: Dict[int, str] = {}
    classes: Dict[int, Optional[str]] = {}
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
    return names, classes


def fetch_fights(session: requests.Session, token: str, code: str) -> Tuple[List[Fight], Dict[int, str], Dict[int, Optional[str]]]:
    """
    Retrieve all fights for a report along with the actor id -> name map.
    """
    overview = gql(session, token, REPORT_OVERVIEW_QUERY, {"code": code})
    report = overview["reportData"]["report"]
    fights: List[Fight] = []
    for raw in report.get("fights") or []:
        if raw.get("startTime") is None or raw.get("endTime") is None:
            continue
        fights.append(
            Fight(
                id=int(raw["id"]),
                name=raw.get("name") or f"Fight {raw['id']}",
                start=float(raw["startTime"]),
                end=float(raw["endTime"]),
                kill=bool(raw.get("kill")),
            )
        )
    actor_names, actor_classes = _build_actor_maps(report)
    return fights, actor_names, actor_classes


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
    actor_names: Optional[Dict[int, str]] = None,
    sleep_seconds: float = 0.1,
) -> Iterator[Dict[str, Any]]:
    """
    Stream paginated events for a single fight window.
    """
    cursor: float = float(start)

    while True:
        variables = {
            "code": code,
            "dataType": data_type,
            "start": float(cursor),
            "end": float(end),
            "limit": int(limit),
            "filter": _compose_filter_expression(ability_id=ability_id, ability_name=ability_name, extra_filter=extra_filter),
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
            cursor = float(next_ts + 1)
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
            sleep_seconds=sleep_seconds,
        ):
            yield event


def fetch_player_details(session: requests.Session, token: str, *, code: str, fight_ids: List[int]) -> Dict[str, Any]:
    """
    Retrieve the playerDetails JSON block for the given fights.
    """
    if not fight_ids:
        return {}
    variables = {"code": code, "fightIDs": [int(fid) for fid in fight_ids]}
    payload = gql(session, token, PLAYER_DETAILS_QUERY, variables)
    player_details = (((payload["reportData"]["report"].get("playerDetails") or {}).get("data") or {}).get("playerDetails") or {})
    return player_details

