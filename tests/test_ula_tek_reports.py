import unittest

from who_messed_up.api import Fight
from who_messed_up.services.boss_manifests import get_boss_manifest
from who_messed_up.services.mechanic_scorecard_analyzers import (
    FightMechanicContext,
    analyze_fight,
)
from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_MECHANIC_SCORECARD,
    JOB_V2_ULA_TEK_AVOIDABLE_DAMAGE,
    JOB_V2_ULA_TEK_DAMAGE,
    JOB_V2_ULA_TEK_DEATHS,
    JOB_V2_ULA_TEK_FUCKUPS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)
from who_messed_up.services.ula_tek_fuckups import CAUSTIC_WAVES_ID, collect_caustic_waves_hits


class UlaTekReportTests(unittest.TestCase):
    def test_manifest_resolves_with_observed_targets_and_damage_abilities(self):
        manifest = get_boss_manifest("ula-tek", "heroic")

        self.assertIsNotNone(manifest)
        self.assertIsNone(get_boss_manifest("ula-tek", "mythic"))
        self.assertEqual(
            [target.enemy_name for target in manifest.targets],
            [
                "Ula'tek",
                "Gore Rattle",
                "Venomous Heart",
                "Doomscale Warden",
                "Blightscale Clutch",
                "Weakened Doomscale",
                "Blightscale Shrieker",
                "Blightscale Viper",
                "Blightscale Rawling",
            ],
        )
        ability_ids = {ability.game_id for ability in manifest.abilities}
        self.assertTrue(
            {
                1286835,
                1298418,
                1287265,
                1307367,
                1316357,
                1313531,
                1317955,
                1293146,
                1296301,
                1297213,
                1305878,
                1292403,
                1301510,
                1297338,
                1308275,
                1318329,
                1302982,
                1299206,
                1301007,
                1311612,
                1301122,
                1295838,
                1286885,
                1310764,
                1305709,
                1290409,
                1306119,
            }.issubset(ability_ids)
        )

    def test_avoidable_rules_are_conservative_and_tank_aware(self):
        manifest = get_boss_manifest("ula-tek", "heroic")
        avoidable = [ability for ability in manifest.abilities if ability.avoidable]

        self.assertEqual(
            [ability.game_id for ability in avoidable],
            [1292403, 1302982, 1286885, 1305709, 1290409, 1306119],
        )
        self.assertIn("Tank Soak", manifest.ability_for(ability_id=1305709).tags)
        for mixed_or_team_failure in (1297338, 1305878, 1316357, 1301510, 1318329, 1299206, 1301007, 1301122):
            self.assertFalse(manifest.ability_for(ability_id=mixed_or_team_failure).avoidable)

    def test_all_baseline_reports_are_registered_for_heroic(self):
        definitions = {
            definition.id: definition
            for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "ula-tek"
        }
        self.assertEqual(
            set(definitions),
            {
                "ula-tek-deaths",
                "ula-tek-avoidable-damage",
                "ula-tek-damage",
                "ula-tek-cooldowns",
                "ula-tek-fuckups",
                "ula-tek-mechanics-scorecard",
                "ula-tek-heroic-aggregate-reports",
            },
        )
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_defaults_exclude_only_pad_rawlings(self):
        registered = get_registered_report("ula-tek-damage")
        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_ula_tek",
                "include_gore_rattle",
                "include_venomous_heart",
                "include_doomscale_warden",
                "include_blightscale_clutch",
                "include_weakened_doomscale",
                "include_blightscale_shrieker",
                "include_blightscale_viper",
                "include_blightscale_rawling",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )
        job_type, payload, fresh_run = build_report_job_request(
            "ula-tek-damage",
            {"report_codes": "xK1bZJTLdrVhqHDg"},
        )
        self.assertEqual(job_type, JOB_V2_ULA_TEK_DAMAGE)
        self.assertEqual(payload["fight"], "Ula'tek")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(
            payload["targets"],
            [
                "ula_tek",
                "gore_rattle",
                "venomous_heart",
                "doomscale_warden",
                "blightscale_clutch",
                "weakened_doomscale",
                "blightscale_shrieker",
                "blightscale_viper",
            ],
        )
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "ula-tek-avoidable-damage",
            {"report_codes": "xK1bZJTLdrVhqHDg"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "ula-tek-deaths",
            {"report_codes": "xK1bZJTLdrVhqHDg"},
        )
        self.assertEqual(avoidable_job, JOB_V2_ULA_TEK_AVOIDABLE_DAMAGE)
        self.assertEqual(
            avoidable_payload["ability_keys"],
            ["1292403", "1302982", "1286885", "1305709", "1290409", "1306119"],
        )
        self.assertEqual(death_job, JOB_V2_ULA_TEK_DEATHS)
        self.assertEqual(death_payload["fight"], "Ula'tek")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_fuckup_report_uses_heroic_ula_tek_defaults(self):
        registered = get_registered_report("ula-tek-fuckups")
        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            ["report_codes", "ignore_after_deaths", "fresh_run"],
        )
        job_type, payload, fresh_run = build_report_job_request(
            "ula-tek-fuckups",
            {"report_codes": "xK1bZJTLdrVhqHDg"},
        )
        self.assertEqual(job_type, JOB_V2_ULA_TEK_FUCKUPS)
        self.assertEqual(payload["fight"], "Ula'tek")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertFalse(fresh_run)

    def test_each_distinct_caustic_waves_contact_is_one_fuckup(self):
        fight = Fight(6, "Ula'tek", 1_000.0, 20_000.0, True, difficulty=4)
        events = collect_caustic_waves_hits(
            report_code="REPORT",
            fight=fight,
            pull_index=2,
            pull_duration_ms=19_000.0,
            event_end=15_000.0,
            known_players={"Alpha", "Bravo"},
            participants={"Alpha", "Bravo"},
            raw_events=[
                {"timestamp": 5_000.0, "abilityGameID": CAUSTIC_WAVES_ID, "targetName": "Alpha", "amount": 100},
                {"timestamp": 5_100.0, "abilityGameID": CAUSTIC_WAVES_ID, "targetName": "Alpha", "amount": 0, "absorbed": 200},
                {"timestamp": 9_000.0, "abilityGameID": CAUSTIC_WAVES_ID, "targetName": "Alpha", "amount": 300},
                {"timestamp": 6_000.0, "abilityGameID": 1, "targetName": "Alpha", "amount": 100},
                {"timestamp": 7_000.0, "abilityGameID": CAUSTIC_WAVES_ID, "targetName": "Outsider", "amount": 100},
                {"timestamp": 16_000.0, "abilityGameID": CAUSTIC_WAVES_ID, "targetName": "Bravo", "amount": 100},
            ],
        )

        self.assertEqual(len(events), 2)
        self.assertEqual([event.player for event in events], ["Alpha", "Alpha"])
        self.assertEqual([event.offset_ms for event in events], [4_000.0, 8_000.0])
        self.assertEqual(events[0].tick_count, 2)
        self.assertEqual(events[0].absorbed, 200.0)

    def test_cooldown_and_mechanics_reports_target_encounter_3492(self):
        reminder = (
            "EncounterID:3492;Name:Ula'tek - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Player;spellid:31884;"
        )
        cooldown_job, cooldown_payload, _ = build_report_job_request(
            "ula-tek-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/xK1bZJTLdrVhqHDg?fight=6",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )
        scorecard_job, scorecard_payload, _ = build_report_job_request(
            "ula-tek-mechanics-scorecard",
            {"report_codes": "xK1bZJTLdrVhqHDg"},
        )
        self.assertEqual(cooldown_job, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(cooldown_payload["fight_ids"], [6])
        self.assertEqual(cooldown_payload["expected_encounter_id"], 3492)
        self.assertEqual(cooldown_payload["difficulty"], "heroic")
        self.assertEqual(scorecard_job, JOB_V2_MECHANIC_SCORECARD)
        self.assertEqual(scorecard_payload["boss_id"], "ula-tek")
        self.assertEqual(scorecard_payload["fight"], "Ula'tek")

    def test_scorecard_collapses_periodic_hazards_and_scores_direct_aura_failures(self):
        context = FightMechanicContext(
            report_code="REPORT",
            fight=Fight(1, "Ula'tek", 0.0, 60_000.0, False, difficulty=4),
            pull_index=1,
            participants={"Alpha", "Bravo", "Charlie"},
            known_players={"Alpha", "Bravo", "Charlie"},
            events_by_type={
                "DamageTaken": [
                    {"type": "damage", "timestamp": 30_000.0, "abilityGameID": 1292403, "targetName": "Alpha"},
                    {"type": "damage", "timestamp": 31_000.0, "abilityGameID": 1292403, "targetName": "Alpha"},
                    {"type": "damage", "timestamp": 35_000.0, "abilityGameID": 1292403, "targetName": "Alpha"},
                    {"type": "damage", "timestamp": 40_000.0, "abilityGameID": 1297338, "targetName": "Alpha"},
                ],
                "Debuffs": [
                    {"type": "applydebuff", "timestamp": 1_000.0, "abilityGameID": 1288879, "targetName": "Alpha"},
                    {"type": "removedebuff", "timestamp": 5_000.0, "abilityGameID": 1288879, "targetName": "Alpha"},
                    {"type": "applydebuff", "timestamp": 5_000.0, "abilityGameID": 1306119, "targetName": "Alpha"},
                    {"type": "applydebuff", "timestamp": 10_000.0, "abilityGameID": 1316356, "targetName": "Bravo"},
                    {"type": "applydebuffstack", "timestamp": 11_000.0, "abilityGameID": 1316356, "targetName": "Bravo", "stack": 2},
                    {"type": "applydebuff", "timestamp": 10_000.0, "abilityGameID": 1316356, "targetName": "Charlie"},
                    {"type": "removedebuff", "timestamp": 20_000.0, "abilityGameID": 1311611, "targetName": "Alpha"},
                    {"type": "removedebuff", "timestamp": 20_100.0, "abilityGameID": 1311611, "targetName": "Bravo"},
                    {"type": "removedebuff", "timestamp": 20_200.0, "abilityGameID": 1311611, "targetName": "Charlie"},
                ],
                "Interrupts": [],
            },
        )

        observations = analyze_fight("ula-tek", context)
        hazards = [item for item in observations if item.mechanic_id == "hazard-dodging"]
        bites = [item for item in observations if item.mechanic_id == "bite-rescue"]
        purges = {item.player: item.outcome for item in observations if item.mechanic_id == "purge-spread"}
        fangs = [item for item in observations if item.mechanic_id == "fang-pacing"]

        self.assertEqual(len(hazards), 2)
        self.assertEqual([(item.player, item.outcome) for item in bites], [("Alpha", "mistake")])
        self.assertEqual(purges, {"Bravo": "mistake", "Charlie": "success"})
        self.assertEqual(len(fangs), 3)
        self.assertTrue(all(item.outcome == "mistake" for item in fangs))


if __name__ == "__main__":
    unittest.main()
