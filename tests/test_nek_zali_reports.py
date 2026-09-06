import unittest

from who_messed_up.services.report_registry import (
    JOB_V2_NEK_ZALI_THE_SOULCOILER_AVOIDABLE_DAMAGE,
    JOB_V2_NEK_ZALI_THE_SOULCOILER_DAMAGE,
    JOB_V2_NEK_ZALI_THE_SOULCOILER_DEATHS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class NekZaliReportRegistryTests(unittest.TestCase):
    def test_heroic_and_mythic_reports_are_both_registered(self):
        definitions = {definition.id: definition for definition in list_report_definitions()}
        heroic_ids = {
            "nek-zali-the-soulcoiler-damage",
            "nek-zali-the-soulcoiler-avoidable-damage",
            "nek-zali-the-soulcoiler-deaths",
            "nek-zali-the-soulcoiler-mechanics-scorecard",
        }
        mythic_ids = {
            "nek-zali-the-soulcoiler-damage-mythic",
            "nek-zali-the-soulcoiler-avoidable-damage-mythic",
            "nek-zali-the-soulcoiler-deaths-mythic",
            "nek-zali-the-soulcoiler-cooldowns",
        }

        self.assertTrue(heroic_ids.issubset(definitions))
        self.assertTrue(mythic_ids.issubset(definitions))
        self.assertEqual({definitions[report_id].difficulty for report_id in heroic_ids}, {"heroic"})
        self.assertEqual({definitions[report_id].difficulty for report_id in mythic_ids}, {"mythic"})

    def test_every_season_two_boss_has_a_cooldown_report_at_current_progression_difficulty(self):
        expected_ids = {
            "nymrissa-wavecaller-cooldowns",
            "nek-zali-the-soulcoiler-cooldowns",
            "entombed-sentinels-cooldowns",
            "the-lost-explorers-cooldowns",
            "vashnik-the-malignant-cooldowns",
            "sszorak-cooldowns",
            "the-twin-fangs-cooldowns",
            "the-coiled-altar-cooldowns",
            "ula-tek-cooldowns",
        }
        definitions = {definition.id: definition for definition in list_report_definitions()}

        self.assertTrue(expected_ids.issubset(definitions))
        self.assertEqual(definitions["nek-zali-the-soulcoiler-cooldowns"].difficulty, "mythic")
        self.assertEqual(
            {
                definitions[report_id].difficulty
                for report_id in expected_ids
                if report_id != "nek-zali-the-soulcoiler-cooldowns"
            },
            {"heroic"},
        )

    def test_cooldown_report_supports_all_last_and_specific_fight_scopes(self):
        report_id = "nek-zali-the-soulcoiler-cooldowns"
        reminder = "EncounterID:3470;Name:Nek'zali - Mythic;Difficulty:Mythic\ntime:11;ph:1;tag:Player;spellid:31884;"
        registered = get_registered_report(report_id)
        fight_id_field = next(field for field in registered.definition.request_schema.fields if field.id == "fight_id")

        self.assertEqual(fight_id_field.visible_when, {"fieldId": "fight_selection", "equals": "specific"})

        _, all_payload, _ = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF", "nsrt_reminders": reminder},
        )
        _, last_payload, _ = build_report_job_request(
            report_id,
            {
                "report_codes": "ZARtb8Dxjhg9H4BF",
                "fight_selection": "last",
                "nsrt_reminders": reminder,
            },
        )
        _, specific_payload, _ = build_report_job_request(
            report_id,
            {
                "report_codes": "https://www.warcraftlogs.com/reports/ZARtb8Dxjhg9H4BF?fight=3",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )

        self.assertEqual(all_payload["fight_selection"], "all")
        self.assertIsNone(all_payload["fight_ids"])
        self.assertEqual(last_payload["fight_selection"], "last")
        self.assertIsNone(last_payload["fight_ids"])
        self.assertEqual(specific_payload["report"], "ZARtb8Dxjhg9H4BF")
        self.assertEqual(specific_payload["fight_selection"], "specific")
        self.assertEqual(specific_payload["fight_ids"], [3])
        self.assertEqual(specific_payload["difficulty"], "mythic")

        _, fragment_payload, _ = build_report_job_request(
            report_id,
            {
                "report_codes": "https://www.warcraftlogs.com/reports/ZARtb8Dxjhg9H4BF#fight=7&type=casts",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )
        self.assertEqual(fragment_payload["report"], "ZARtb8Dxjhg9H4BF")
        self.assertEqual(fragment_payload["fight_ids"], [7])

    def test_specific_cooldown_scope_requires_one_report_and_fight_id(self):
        report_id = "nek-zali-the-soulcoiler-cooldowns"
        reminder = "EncounterID:3470;Difficulty:Mythic\ntime:11;ph:1;tag:Player;spellid:31884;"

        with self.assertRaisesRegex(ValueError, "Enter a fight ID"):
            build_report_job_request(
                report_id,
                {
                    "report_codes": "ZARtb8Dxjhg9H4BF",
                    "fight_selection": "specific",
                    "nsrt_reminders": reminder,
                },
            )

        with self.assertRaisesRegex(ValueError, "one Warcraft Logs report"):
            build_report_job_request(
                report_id,
                {
                    "report_codes": ["ZARtb8Dxjhg9H4BF?fight=3", "SECONDREPORT"],
                    "fight_selection": "specific",
                    "nsrt_reminders": reminder,
                },
            )

    def test_damage_report_uses_all_verified_targets_by_default(self):
        report_id = "nek-zali-the-soulcoiler-damage-mythic"
        registered = get_registered_report(report_id)

        self.assertEqual(registered.definition.fight_id, "nek-zali-the-soulcoiler")
        self.assertEqual(registered.definition.difficulty, "mythic")
        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_nek_zali_the_soulcoiler",
                "include_restless_amani",
                "include_echo_of_jawae",
                "include_drowned_echo",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_NEK_ZALI_THE_SOULCOILER_DAMAGE)
        self.assertEqual(payload["fight"], "Nek'zali the Soulcoiler")
        self.assertEqual(payload["difficulty"], "mythic")
        self.assertEqual(
            payload["targets"],
            ["nek_zali_the_soulcoiler", "restless_amani", "echo_of_jawae", "drowned_echo"],
        )
        self.assertFalse(payload["kill_only"])
        self.assertFalse(payload["omit_dead_players"])
        self.assertFalse(fresh_run)

    def test_original_damage_report_id_keeps_heroic_defaults(self):
        report_id = "nek-zali-the-soulcoiler-damage"

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_NEK_ZALI_THE_SOULCOILER_DAMAGE)
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(
            payload["targets"],
            ["nek_zali_the_soulcoiler", "restless_amani", "echo_of_jawae"],
        )
        self.assertFalse(fresh_run)

    def test_avoidable_damage_report_uses_mythic_manifest_defaults(self):
        report_id = "nek-zali-the-soulcoiler-avoidable-damage-mythic"
        registered = get_registered_report(report_id)

        self.assertEqual(registered.definition.fight_id, "nek-zali-the-soulcoiler")
        self.assertEqual(registered.definition.difficulty, "mythic")
        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_avoidable_1290390",
                "include_avoidable_1292899",
                "include_avoidable_1288554",
                "include_avoidable_1294846",
                "include_avoidable_1295085",
                "include_avoidable_1300239",
                "ignore_after_deaths",
                "fresh_run",
            ],
        )

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_NEK_ZALI_THE_SOULCOILER_AVOIDABLE_DAMAGE)
        self.assertEqual(payload["fight"], "Nek'zali the Soulcoiler")
        self.assertEqual(payload["difficulty"], "mythic")
        self.assertEqual(
            payload["ability_keys"],
            ["1290390", "1292899", "1288554", "1294846", "1295085", "1300239"],
        )
        self.assertFalse(fresh_run)

    def test_death_report_uses_mythic_defaults(self):
        report_id = "nek-zali-the-soulcoiler-deaths-mythic"
        registered = get_registered_report(report_id)

        self.assertEqual(registered.definition.fight_id, "nek-zali-the-soulcoiler")
        self.assertEqual(registered.definition.difficulty, "mythic")

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "ZARtb8Dxjhg9H4BF"},
        )

        self.assertEqual(job_type, JOB_V2_NEK_ZALI_THE_SOULCOILER_DEATHS)
        self.assertEqual(payload["fight"], "Nek'zali the Soulcoiler")
        self.assertEqual(payload["difficulty"], "mythic")
        self.assertFalse(fresh_run)


if __name__ == "__main__":
    unittest.main()
