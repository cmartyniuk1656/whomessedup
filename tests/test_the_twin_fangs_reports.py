import unittest

from who_messed_up.services.ability_event_filters import is_avoidable_event_requirement_met
from who_messed_up.services.boss_manifest_types import BossAbilityMetadata
from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_THE_TWIN_FANGS_AVOIDABLE_DAMAGE,
    JOB_V2_THE_TWIN_FANGS_DAMAGE,
    JOB_V2_THE_TWIN_FANGS_DEATHS,
    JOB_V2_THE_TWIN_FANGS_FUCKUPS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)
from who_messed_up.services.the_twin_fangs_fuckups import (
    CAUSTIC_DELUGE_SPLASH_ID,
    CAUSTIC_GLOBULE_ID,
    CORROSIVE_SPIT_DAMAGE_ID,
    STIR_THE_DEPTHS_ID,
    VENOMOUS_EMERGENCE_ID,
    VILE_FLOOD_ID,
    classify_eternal_venom_application,
)


class TheTwinFangsReportRegistryTests(unittest.TestCase):
    def test_ravenous_feast_requires_preexisting_feasted(self):
        ability = BossAbilityMetadata(
            name="Ravenous Feast",
            game_id=1290662,
            avoidable=True,
            avoidable_requires_active_debuff_ability_id=1310096,
            avoidable_requires_active_debuff_min_age_ms=100.0,
        )
        requirements = {"1290662": {"Player": [(1_000.0, 9_000.0)]}}

        self.assertFalse(
            is_avoidable_event_requirement_met(ability, {"timestamp": 1_000.0}, "Player", requirements)
        )
        self.assertTrue(
            is_avoidable_event_requirement_met(ability, {"timestamp": 2_500.0}, "Player", requirements)
        )
        self.assertFalse(
            is_avoidable_event_requirement_met(ability, {"timestamp": 10_000.0}, "Player", requirements)
        )

    def test_all_baseline_reports_are_registered_for_heroic(self):
        expected_ids = {
            "the-twin-fangs-deaths",
            "the-twin-fangs-avoidable-damage",
            "the-twin-fangs-damage",
            "the-twin-fangs-cooldowns",
            "the-twin-fangs-fuckups",
            "the-twin-fangs-mechanics-scorecard",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions()
            if definition.fight_id == "the-twin-fangs"
        }

        self.assertEqual(set(definitions), expected_ids)
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_uses_bosses_and_spawn(self):
        registered = get_registered_report("the-twin-fangs-damage")

        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_vexhul",
                "include_ithraz",
                "include_spawn_of_vexhul",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )
        job_type, payload, fresh_run = build_report_job_request(
            "the-twin-fangs-damage",
            {"report_codes": "6CqvafhpjRc9nrAX"},
        )

        self.assertEqual(job_type, JOB_V2_THE_TWIN_FANGS_DAMAGE)
        self.assertEqual(payload["fight"], "The Twin Fangs")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(payload["targets"], ["vexhul", "ithraz", "spawn_of_vexhul"])
        self.assertFalse(fresh_run)

    def test_eternal_venom_scoring_preserves_intentional_globules(self):
        self.assertIsNone(
            classify_eternal_venom_application(
                resulting_stack=9,
                cause_ability_id=CAUSTIC_GLOBULE_ID,
                player="Soaker",
            )
        )
        lethal_globule = classify_eternal_venom_application(
            resulting_stack=10,
            cause_ability_id=CAUSTIC_GLOBULE_ID,
            player="Soaker",
        )
        self.assertEqual(lethal_globule.mechanic_type, "fatal_globule")
        self.assertIsNone(
            classify_eternal_venom_application(
                resulting_stack=5,
                cause_ability_id=VENOMOUS_EMERGENCE_ID,
                player="Player",
            )
        )

    def test_corrosive_spit_only_scores_collateral_players(self):
        self.assertIsNone(
            classify_eternal_venom_application(
                resulting_stack=4,
                cause_ability_id=CORROSIVE_SPIT_DAMAGE_ID,
                player="Target",
                corrosive_spit_target="Target",
            )
        )
        collateral = classify_eternal_venom_application(
            resulting_stack=4,
            cause_ability_id=CORROSIVE_SPIT_DAMAGE_ID,
            player="Bystander",
            corrosive_spit_target="Target",
        )
        self.assertEqual(collateral.mechanic_type, "corrosive_spit_collateral")

    def test_avoidable_wave_beam_and_splash_applications_are_scored(self):
        expected = {
            CAUSTIC_DELUGE_SPLASH_ID: "caustic_deluge_splash",
            STIR_THE_DEPTHS_ID: "stir_the_depths",
            VILE_FLOOD_ID: "vile_flood",
        }
        for ability_id, mechanic_type in expected.items():
            with self.subTest(ability_id=ability_id):
                classification = classify_eternal_venom_application(
                    resulting_stack=3,
                    cause_ability_id=ability_id,
                    player="Player",
                )
                self.assertEqual(classification.mechanic_type, mechanic_type)

    def test_fuckups_report_uses_heroic_twin_fangs_defaults(self):
        registered = get_registered_report("the-twin-fangs-fuckups")
        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            ["report_codes", "ignore_after_deaths", "fresh_run"],
        )
        job_type, payload, fresh_run = build_report_job_request(
            "the-twin-fangs-fuckups",
            {"report_codes": "6CqvafhpjRc9nrAX"},
        )
        self.assertEqual(job_type, JOB_V2_THE_TWIN_FANGS_FUCKUPS)
        self.assertEqual(payload["fight"], "The Twin Fangs")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "the-twin-fangs-avoidable-damage",
            {"report_codes": "6CqvafhpjRc9nrAX"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "the-twin-fangs-deaths",
            {"report_codes": "6CqvafhpjRc9nrAX"},
        )

        self.assertEqual(avoidable_job, JOB_V2_THE_TWIN_FANGS_AVOIDABLE_DAMAGE)
        self.assertEqual(
            avoidable_payload["ability_keys"],
            [
                "1290662",
                "1293295",
                "1310371",
                "1306876",
                "1289994",
                "1294605",
                "1297338",
                "1292552",
                "1292807",
                "1309471",
                "1306925",
            ],
        )
        self.assertEqual(death_job, JOB_V2_THE_TWIN_FANGS_DEATHS)
        self.assertEqual(death_payload["fight"], "The Twin Fangs")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_cooldown_report_supports_the_kill_as_a_specific_fight(self):
        reminder = (
            "EncounterID:3421;Name:The Twin Fangs - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Impalerr;spellid:31884;"
        )
        job_type, payload, _ = build_report_job_request(
            "the-twin-fangs-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/6CqvafhpjRc9nrAX?fight=17",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )

        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["fight"], "The Twin Fangs")
        self.assertEqual(payload["fight_ids"], [17])
        self.assertEqual(payload["difficulty"], "heroic")


if __name__ == "__main__":
    unittest.main()
