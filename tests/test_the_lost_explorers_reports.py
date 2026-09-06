import unittest

from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_THE_LOST_EXPLORERS_AVOIDABLE_DAMAGE,
    JOB_V2_THE_LOST_EXPLORERS_DAMAGE,
    JOB_V2_THE_LOST_EXPLORERS_DEATHS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class TheLostExplorersReportRegistryTests(unittest.TestCase):
    def test_all_baseline_reports_are_registered_for_heroic(self):
        expected_ids = {
            "the-lost-explorers-deaths",
            "the-lost-explorers-avoidable-damage",
            "the-lost-explorers-damage",
            "the-lost-explorers-cooldowns",
            "the-lost-explorers-mechanics-scorecard",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "the-lost-explorers"
        }

        self.assertEqual(set(definitions), expected_ids)
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_uses_all_three_explorers_by_default(self):
        report_id = "the-lost-explorers-damage"
        registered = get_registered_report(report_id)

        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_first_mate_nama",
                "include_scrollsage_iku",
                "include_trader_gebbo",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_THE_LOST_EXPLORERS_DAMAGE)
        self.assertEqual(payload["fight"], "The Lost Explorers")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(payload["targets"], ["first_mate_nama", "scrollsage_iku", "trader_gebbo"])
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "the-lost-explorers-avoidable-damage",
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "the-lost-explorers-deaths",
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(avoidable_job, JOB_V2_THE_LOST_EXPLORERS_AVOIDABLE_DAMAGE)
        self.assertEqual(
            avoidable_payload["ability_keys"],
            ["1292764", "1291935", "1305618", "1296245", "1305844", "1310500"],
        )
        self.assertEqual(death_job, JOB_V2_THE_LOST_EXPLORERS_DEATHS)
        self.assertEqual(death_payload["fight"], "The Lost Explorers")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_cooldown_report_supports_the_kill_as_a_specific_fight(self):
        reminder = (
            "EncounterID:3497;Name:The Lost Explorers - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Player;spellid:31884;"
        )
        job_type, payload, _ = build_report_job_request(
            "the-lost-explorers-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/ZARtb8Dxjhg9H4BF?fight=41",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )

        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["fight"], "The Lost Explorers")
        self.assertEqual(payload["fight_ids"], [41])
        self.assertEqual(payload["difficulty"], "heroic")


if __name__ == "__main__":
    unittest.main()
