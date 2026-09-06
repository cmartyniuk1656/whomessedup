from unittest import TestCase
from unittest.mock import Mock, patch

from who_messed_up.services.wcl_report_discovery import (
    GuildNotFoundError,
    WarcraftLogsCredentialsError,
    discover_guild_reports,
)


class GuildReportDiscoveryTests(TestCase):
    @patch("who_messed_up.services.wcl_report_discovery.gql")
    @patch("who_messed_up.services.wcl_report_discovery.get_token_from_client", return_value="token")
    def test_resolves_guild_and_sorts_reports_newest_first(self, _get_token, gql_mock):
        gql_mock.side_effect = [{
            "guildData": {
                "guild": {
                    "id": 42,
                    "name": "Example Guild",
                    "server": {"name": "Area 52", "slug": "area-52"},
                }
            },
        }, {
            "reportData": {
                "reports": {
                    "data": [
                        {"code": "older", "title": "Older", "startTime": 10, "endTime": 20, "zone": None},
                        {"code": "newer", "title": "Newer", "startTime": 30, "endTime": 40, "zone": {"name": "The Voidspire"}},
                    ]
                }
            },
        }]

        result = discover_guild_reports(
            guild_name=" Example Guild ",
            server_slug="Area-52",
            server_region="us",
            client_id="client",
            client_secret="secret",
            session=Mock(),
        )

        self.assertEqual(result.guild.id, 42)
        self.assertEqual(result.guild.server_region, "US")
        self.assertEqual([report.code for report in result.reports], ["newer", "older"])
        self.assertEqual(result.reports[0].zone_name, "The Voidspire")
        variables = gql_mock.call_args_list[0].args[3]
        self.assertEqual(variables["guildName"], "Example Guild")
        self.assertEqual(variables["serverSlug"], "area-52")
        self.assertEqual(variables["serverRegion"], "US")
        self.assertEqual(gql_mock.call_args_list[1].args[3]["guildID"], 42)

    @patch("who_messed_up.services.wcl_report_discovery.get_token_from_client", return_value=None)
    def test_requires_server_credentials(self, _get_token):
        with self.assertRaises(WarcraftLogsCredentialsError):
            discover_guild_reports(
                guild_name="Guild",
                server_slug="realm",
                server_region="US",
                client_id=None,
                client_secret=None,
            )

    @patch("who_messed_up.services.wcl_report_discovery.gql")
    @patch("who_messed_up.services.wcl_report_discovery.get_token_from_client", return_value="token")
    def test_rejects_unknown_guild(self, _get_token, gql_mock):
        gql_mock.return_value = {"guildData": {"guild": None}}

        with self.assertRaises(GuildNotFoundError):
            discover_guild_reports(
                guild_name="Missing",
                server_slug="realm",
                server_region="EU",
                client_id="client",
                client_secret="secret",
                session=Mock(),
            )
