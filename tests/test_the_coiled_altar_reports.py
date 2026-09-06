import unittest

from who_messed_up.services.boss_manifests import get_boss_manifest
from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_THE_COILED_ALTAR_AVOIDABLE_DAMAGE,
    JOB_V2_THE_COILED_ALTAR_DAMAGE,
    JOB_V2_THE_COILED_ALTAR_DEATHS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class TheCoiledAltarReportTests(unittest.TestCase):
    def test_manifest_resolves_with_observed_targets_and_abilities(self):
        manifest = get_boss_manifest("the-coiled-altar", "heroic")

        self.assertIsNotNone(manifest)
        self.assertIsNone(get_boss_manifest("the-coiled-altar", "mythic"))
        self.assertEqual(
            [target.enemy_name for target in manifest.targets],
            ["Zul'jan", "Hex Lord Malacrass", "Spiteful Soulcoiler"],
        )
        ability_ids = {ability.game_id for ability in manifest.abilities}
        self.assertTrue(
            {
                1282408,
                1282288,
                1299838,
                1285017,
                1310883,
                1297906,
                1286918,
                1287722,
                1299301,
                1307292,
                1312424,
            }.issubset(ability_ids)
        )

    def test_avoidable_rules_exclude_orb_carriers_and_handle_marks_and_tank_frontals(self):
        manifest = get_boss_manifest("the-coiled-altar", "heroic")
        avoidable = [ability for ability in manifest.abilities if ability.avoidable]

        self.assertEqual(
            [ability.game_id for ability in avoidable],
            [1283290, 1300137, 1299684, 1285017, 1310883, 1297906, 1286620, 1312630, 1307292, 1312424],
        )
        volatile = manifest.ability_for(ability_id=1282288)
        gloombomb = manifest.ability_for(ability_id=1310883)
        self.assertFalse(volatile.avoidable)
        self.assertIsNone(volatile.avoidable_excludes_active_debuff_ability_id)
        self.assertEqual(gloombomb.avoidable_exclusion_debuff_ability_id, 1310881)
        for ability_id in (1299684, 1286620, 1312630, 1307292):
            self.assertIn("Tank Soak", manifest.ability_for(ability_id=ability_id).tags)

    def test_all_baseline_reports_are_registered_for_heroic(self):
        definitions = {
            definition.id: definition
            for definition in list_report_definitions()
            if definition.fight_id == "the-coiled-altar"
        }
        self.assertEqual(
            set(definitions),
            {
                "the-coiled-altar-deaths",
                "the-coiled-altar-avoidable-damage",
                "the-coiled-altar-damage",
                "the-coiled-altar-cooldowns",
                "the-coiled-altar-mechanics-scorecard",
            },
        )
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_uses_bosses_and_priority_add(self):
        registered = get_registered_report("the-coiled-altar-damage")
        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_zuljan",
                "include_hex_lord_malacrass",
                "include_spiteful_soulcoiler",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )
        job_type, payload, fresh_run = build_report_job_request(
            "the-coiled-altar-damage",
            {"report_codes": "p4mPajMdJRgKqQBT"},
        )
        self.assertEqual(job_type, JOB_V2_THE_COILED_ALTAR_DAMAGE)
        self.assertEqual(payload["fight"], "The Coiled Altar")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(payload["targets"], ["zuljan", "hex_lord_malacrass", "spiteful_soulcoiler"])
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "the-coiled-altar-avoidable-damage",
            {"report_codes": "p4mPajMdJRgKqQBT"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "the-coiled-altar-deaths",
            {"report_codes": "p4mPajMdJRgKqQBT"},
        )
        self.assertEqual(avoidable_job, JOB_V2_THE_COILED_ALTAR_AVOIDABLE_DAMAGE)
        self.assertEqual(
            avoidable_payload["ability_keys"],
            ["1283290", "1300137", "1299684", "1285017", "1310883", "1297906", "1286620", "1312630", "1307292", "1312424"],
        )
        self.assertEqual(death_job, JOB_V2_THE_COILED_ALTAR_DEATHS)
        self.assertEqual(death_payload["fight"], "The Coiled Altar")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_cooldown_report_supports_the_kill_as_a_specific_fight(self):
        reminder = (
            "EncounterID:3429;Name:The Coiled Altar - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Player;spellid:31884;"
        )
        job_type, payload, _ = build_report_job_request(
            "the-coiled-altar-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/p4mPajMdJRgKqQBT?fight=30",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )
        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["fight"], "The Coiled Altar")
        self.assertEqual(payload["fight_ids"], [30])
        self.assertEqual(payload["expected_encounter_id"], 3429)
        self.assertEqual(payload["difficulty"], "heroic")


if __name__ == "__main__":
    unittest.main()
