"""Warcraft Logs guild lookup and recent-report discovery."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import requests

from who_messed_up.api import get_token_from_client, gql


class WarcraftLogsCredentialsError(RuntimeError):
    """Raised when server-side Warcraft Logs credentials are unavailable."""


class GuildNotFoundError(ValueError):
    """Raised when Warcraft Logs cannot resolve the requested guild."""


@dataclass(frozen=True)
class DiscoveredGuild:
    id: int
    name: str
    server_name: str
    server_slug: str
    server_region: str


@dataclass(frozen=True)
class DiscoveredReport:
    code: str
    title: str
    start_time: float
    end_time: float
    zone_name: Optional[str]


@dataclass(frozen=True)
class GuildReportDiscovery:
    guild: DiscoveredGuild
    reports: List[DiscoveredReport]


_GUILD_QUERY = """
query Guild(
  $guildName: String!
  $serverSlug: String!
  $serverRegion: String!
) {
  guildData {
    guild(name: $guildName, serverSlug: $serverSlug, serverRegion: $serverRegion) {
      id
      name
      server {
        name
        slug
      }
    }
  }
}
"""

_GUILD_REPORTS_QUERY = """
query GuildReports($guildID: Int!, $limit: Int!) {
  reportData {
    reports(
      guildID: $guildID
      limit: $limit
      page: 1
    ) {
      data {
        code
        title
        startTime
        endTime
        zone { name }
      }
    }
  }
}
"""


def discover_guild_reports(
    *,
    guild_name: str,
    server_slug: str,
    server_region: str,
    client_id: Optional[str],
    client_secret: Optional[str],
    limit: int = 20,
    session: Optional[requests.Session] = None,
) -> GuildReportDiscovery:
    """Resolve a public guild and return its newest public reports."""
    normalized_name = guild_name.strip()
    normalized_server = server_slug.strip().lower()
    normalized_region = server_region.strip().upper()
    if not normalized_name or not normalized_server or not normalized_region:
        raise ValueError("Guild name, realm slug, and region are required.")

    bearer = get_token_from_client(client_id, client_secret)
    if not bearer:
        raise WarcraftLogsCredentialsError(
            "Warcraft Logs credentials are not configured on the server."
        )

    request_session = session or requests.Session()
    guild_payload = gql(
        request_session,
        bearer,
        _GUILD_QUERY,
        {
            "guildName": normalized_name,
            "serverSlug": normalized_server,
            "serverRegion": normalized_region,
        },
    )
    guild_data = (guild_payload.get("guildData") or {}).get("guild")
    if not guild_data:
        raise GuildNotFoundError(
            "Guild not found. Check the guild name, realm slug, and region."
        )

    server = guild_data.get("server") or {}
    guild = DiscoveredGuild(
        id=int(guild_data["id"]),
        name=str(guild_data["name"]),
        server_name=str(server.get("name") or normalized_server),
        server_slug=str(server.get("slug") or normalized_server),
        server_region=normalized_region,
    )
    reports_payload = gql(
        request_session,
        bearer,
        _GUILD_REPORTS_QUERY,
        {"guildID": guild.id, "limit": max(1, min(int(limit), 50))},
    )
    report_rows = ((reports_payload.get("reportData") or {}).get("reports") or {}).get("data") or []
    reports = [
        DiscoveredReport(
            code=str(row["code"]),
            title=str(row.get("title") or row["code"]),
            start_time=float(row.get("startTime") or 0),
            end_time=float(row.get("endTime") or 0),
            zone_name=str((row.get("zone") or {}).get("name"))
            if (row.get("zone") or {}).get("name")
            else None,
        )
        for row in report_rows
        if row and row.get("code")
    ]
    reports.sort(key=lambda report: report.end_time, reverse=True)
    return GuildReportDiscovery(guild=guild, reports=reports)
