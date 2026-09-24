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
            "vashnik-the-malignant-cooldown-coverage-heroic",
            "vashnik-the-malignant-defensive-usage-heroic",
            "vashnik-the-malignant-mechanics-scorecard",
            "vashnik-the-malignant-heroic-aggregate-reports",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "vashnik-the-malignant"
            and definition.difficulty == "heroic"
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


class VashnikMythicReportRegistryTests(unittest.TestCase):
    def test_mythic_base_reports_and_aggregate_are_registered(self):
        definitions = {
            definition.id for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "vashnik-the-malignant" and definition.difficulty == "mythic"
        }
        self.assertEqual(definitions, {
            "vashnik-the-malignant-damage-mythic",
            "vashnik-the-malignant-deaths-mythic",
            "vashnik-the-malignant-avoidable-damage-mythic",
            "vashnik-the-malignant-mythic-mechanics",
            "vashnik-the-malignant-cooldowns-mythic",
            "vashnik-the-malignant-cooldown-coverage-mythic",
            "vashnik-the-malignant-defensive-usage-mythic",
            "vashnik-the-malignant-mythic-aggregate-reports",
        })
        _, aggregate, _ = build_report_job_request(
            "vashnik-the-malignant-mythic-aggregate-reports",
            {"report_codes": ["6x4fbqFQLagcRCKD"]},
        )
        self.assertEqual({child["report_id"] for child in aggregate["reports"]}, {
            "vashnik-the-malignant-damage-mythic",
            "vashnik-the-malignant-deaths-mythic",
            "vashnik-the-malignant-avoidable-damage-mythic",
            "vashnik-the-malignant-mythic-mechanics",
        })
        for child in aggregate["reports"]:
            self.assertEqual(child["payload"]["difficulty"], "mythic")
            self.assertEqual(child["payload"]["fight"], "Vashnik the Malignant")

    def test_mythic_targets_ability_toggles_and_heroic_defaults(self):
        values = {"report_codes": ["6x4fbqFQLagcRCKD"]}
        _, damage, _ = build_report_job_request("vashnik-the-malignant-damage-mythic", values)
        self.assertEqual(damage["targets"], [
            "vashnik_the_malignant", "burning_venom", "clotting_venom", "shrouded_venom",
        ])
        self.assertFalse(damage["kill_only"])
        _, avoidable, _ = build_report_job_request("vashnik-the-malignant-avoidable-damage-mythic", values)
        self.assertEqual(avoidable["ability_keys"], ["1302489", "1295798", "1291467", "1286737", "1297338"])
        _, excluded, _ = build_report_job_request(
            "vashnik-the-malignant-avoidable-damage-mythic",
            {**values, "include_avoidable_1302489": False, "include_avoidable_1297338": False},
        )
        _, heroic, _ = build_report_job_request("vashnik-the-malignant-avoidable-damage", values)
        self.assertEqual(excluded["ability_keys"], heroic["ability_keys"])
        self.assertEqual(heroic["difficulty"], "heroic")

    def test_mythic_cooldown_report_preserves_specific_pull_scope(self):
        job_type, payload, _ = build_report_job_request(
            "vashnik-the-malignant-cooldowns-mythic",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/6x4fbqFQLagcRCKD?fight=43",
                "fight_selection": "specific",
                "nsrt_reminders": (
                    "EncounterID:3455;Name:Vashnik the Malignant - Mythic;Difficulty:Mythic\n"
                    "time:11;ph:1;tag:Player;spellid:31884;"
                ),
            },
        )
        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["difficulty"], "mythic")
        self.assertEqual(payload["fight_ids"], [43])


if __name__ == "__main__":
    unittest.main()
