import unittest

from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_VASHNIK_THE_MALIGNANT_AVOIDABLE_DAMAGE,
    JOB_V2_VASHNIK_THE_MALIGNANT_DAMAGE,
    JOB_V2_VASHNIK_THE_MALIGNANT_DEATHS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class VashnikTheMalignantReportRegistryTests(unittest.TestCase):
    def test_all_baseline_reports_are_registered_for_heroic(self):
        expected_ids = {
            "vashnik-the-malignant-deaths",
            "vashnik-the-malignant-avoidable-damage",
            "vashnik-the-malignant-damage",
            "vashnik-the-malignant-cooldowns",
            "vashnik-the-malignant-mechanics-scorecard",
            "vashnik-the-malignant-heroic-aggregate-reports",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "vashnik-the-malignant"
        }

        self.assertEqual(set(definitions), expected_ids)
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_uses_boss_and_all_living_venom_types(self):
        report_id = "vashnik-the-malignant-damage"
        registered = get_registered_report(report_id)

        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_vashnik_the_malignant",
                "include_burning_venom",
                "include_clotting_venom",
                "include_shrouded_venom",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_VASHNIK_THE_MALIGNANT_DAMAGE)
        self.assertEqual(payload["fight"], "Vashnik the Malignant")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(
            payload["targets"],
            ["vashnik_the_malignant", "burning_venom", "clotting_venom", "shrouded_venom"],
        )
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "vashnik-the-malignant-avoidable-damage",
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "vashnik-the-malignant-deaths",
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(avoidable_job, JOB_V2_VASHNIK_THE_MALIGNANT_AVOIDABLE_DAMAGE)
        self.assertEqual(avoidable_payload["ability_keys"], ["1295798", "1291467", "1286737"])
        self.assertEqual(death_job, JOB_V2_VASHNIK_THE_MALIGNANT_DEATHS)
        self.assertEqual(death_payload["fight"], "Vashnik the Malignant")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_cooldown_report_supports_the_kill_as_a_specific_fight(self):
        reminder = (
            "EncounterID:3455;Name:Vashnik the Malignant - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Player;spellid:31884;"
        )
        job_type, payload, _ = build_report_job_request(
            "vashnik-the-malignant-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/ZARtb8Dxjhg9H4BF?fight=35",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )

        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["fight"], "Vashnik the Malignant")
        self.assertEqual(payload["fight_ids"], [35])
        self.assertEqual(payload["difficulty"], "heroic")


if __name__ == "__main__":
    unittest.main()
