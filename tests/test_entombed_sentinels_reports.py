import unittest

from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_ENTOMBED_SENTINELS_AVOIDABLE_DAMAGE,
    JOB_V2_ENTOMBED_SENTINELS_DAMAGE,
    JOB_V2_ENTOMBED_SENTINELS_DEATHS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class EntombedSentinelsReportRegistryTests(unittest.TestCase):
    def test_all_baseline_reports_are_registered_for_heroic(self):
        expected_ids = {
            "entombed-sentinels-deaths",
            "entombed-sentinels-avoidable-damage",
            "entombed-sentinels-damage",
            "entombed-sentinels-cooldowns",
            "entombed-sentinels-mechanics-scorecard",
            "entombed-sentinels-heroic-aggregate-reports",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "entombed-sentinels"
        }

        self.assertEqual(set(definitions), expected_ids)
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_uses_all_verified_targets_by_default(self):
        report_id = "entombed-sentinels-damage"
        registered = get_registered_report(report_id)

        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_blood_of_ula_tek",
                "include_breath_of_ula_tek",
                "include_venom_coagulation",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_ENTOMBED_SENTINELS_DAMAGE)
        self.assertEqual(payload["fight"], "Entombed Sentinels")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(
            payload["targets"],
            ["blood_of_ula_tek", "breath_of_ula_tek", "venom_coagulation"],
        )
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "entombed-sentinels-avoidable-damage",
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "entombed-sentinels-deaths",
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(avoidable_job, JOB_V2_ENTOMBED_SENTINELS_AVOIDABLE_DAMAGE)
        self.assertEqual(
            avoidable_payload["ability_keys"],
            ["1284210", "1284209", "1284948", "1284941", "1297338"],
        )
        self.assertEqual(death_job, JOB_V2_ENTOMBED_SENTINELS_DEATHS)
        self.assertEqual(death_payload["fight"], "Entombed Sentinels")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_cooldown_report_uses_generic_job_and_specific_fight_scope(self):
        reminder = (
            "EncounterID:3445;Name:Entombed Sentinels - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Player;spellid:31884;"
        )
        job_type, payload, _ = build_report_job_request(
            "entombed-sentinels-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/ZARtb8Dxjhg9H4BF?fight=12",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )

        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["fight"], "Entombed Sentinels")
        self.assertEqual(payload["fight_ids"], [12])
        self.assertEqual(payload["difficulty"], "heroic")


if __name__ == "__main__":
    unittest.main()
