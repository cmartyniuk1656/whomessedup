"""
Utilities for querying the Warcraft Logs GraphQL API.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Any

import requests

API_URL = "https://www.warcraftlogs.com/api/v2/client"
OAUTH_URL = "https://www.warcraftlogs.com/oauth/token"

FIGHTS_QUERY = """
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
    }
  }
}
"""

EVENTS_QUERY = """
query($code: String!, $dataType: ReportDataType!, $start: Float!, $end: Float!, $limit: Int!, $after: Float) {
  reportData {
    report(code: $code) {
      events(dataType: $dataType, startTime: $start, endTime: $end, limit: $limit, after: $after) {
        data
        nextPageTimestamp
        pageInfo { hasMorePages endTime }
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
    resp.raise_for_status()
    data = resp.json()
    errors = data.get("errors")
    if errors:
        raise RuntimeError(f"GraphQL error(s): {errors}")
    return data["data"]


def fetch_fights(session: requests.Session, token: str, code: str) -> List[Fight]:
    """
    Retrieve all fights for a report.
    """
    fights_data = gql(session, token, FIGHTS_QUERY, {"code": code})
    report = fights_data["reportData"]["report"]
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
    return fights


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
    sleep_seconds: float = 0.1,
) -> Iterator[Dict[str, Any]]:
    """
    Stream paginated events for a single fight window.
    """
    after: Optional[float] = None
    safety = 0

    while True:
        variables = {
            "code": code,
            "dataType": data_type,
            "start": float(start),
            "end": float(end),
            "limit": int(limit),
            "after": float(after) if after is not None else None,
        }
        payload = gql(session, token, EVENTS_QUERY, variables)
        events_data = payload["reportData"]["report"]["events"]
        rows = events_data.get("data") or []
        for row in rows:
            yield row

        next_ts = events_data.get("nextPageTimestamp")
        has_more = bool((events_data.get("pageInfo") or {}).get("hasMorePages"))

        if next_ts is not None:
            if next_ts >= end:
                break
            after = float(next_ts + 1)
        elif has_more:
            if rows:
                last_ts = rows[-1].get("timestamp")
                after = float(last_ts + 1) if last_ts is not None else (after or start) + 1.0
            else:
                safety += 1
                if safety > 5:
                    break
                after = (after or start) + 1000.0
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
            sleep_seconds=sleep_seconds,
        ):
            yield event
