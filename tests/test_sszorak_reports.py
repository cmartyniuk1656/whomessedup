import unittest

from who_messed_up.services.ability_event_filters import is_avoidable_event_requirement_met
from who_messed_up.services.boss_manifest_types import BossAbilityMetadata
from who_messed_up.services.sszorak_tempest import (
    _collapse_tempest_contacts,
    _credited_dispeller,
)
from who_messed_up.services.report_registry import (
    JOB_V2_COOLDOWN_USAGE,
    JOB_V2_SSZORAK_AVOIDABLE_DAMAGE,
    JOB_V2_SSZORAK_DAMAGE,
    JOB_V2_SSZORAK_DEATHS,
    JOB_V2_SSZORAK_TEMPEST,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class SszorakReportRegistryTests(unittest.TestCase):
    def test_tempest_contacts_collapse_same_timestamp_stack_and_refresh(self):
        events = [
            {"timestamp": 1000, "type": "applydebuff", "abilityGameID": 1287083, "targetName": "Player"},
            {"timestamp": 1200, "type": "applydebuffstack", "abilityGameID": 1287083, "targetName": "Player", "stack": 3},
            {"timestamp": 1200, "type": "refreshdebuff", "abilityGameID": 1287083, "targetName": "Player"},
            {"timestamp": 1500, "type": "removedebuff", "abilityGameID": 1287083, "targetName": "Player"},
            {"timestamp": 1600, "type": "applydebuff", "abilityGameID": 123, "targetName": "Player"},
        ]

        contacts = _collapse_tempest_contacts(events)

        self.assertEqual(len(contacts), 2)
        self.assertEqual(contacts[1]["type"], "applydebuffstack")
        self.assertEqual(contacts[1]["stack"], 3)

    def test_poison_cleansing_totem_is_credited_to_its_owner(self):
        player, pet = _credited_dispeller(
            {"source": {"id": 106, "name": "Poison Cleansing Totem"}},
            {4: "Elementalzz", 106: "Poison Cleansing Totem"},
            {106: 4},
        )

        self.assertEqual(player, "Elementalzz")
        self.assertEqual(pet, "Poison Cleansing Totem")

    def test_mutilate_requires_a_preexisting_gash_window(self):
        ability = BossAbilityMetadata(
            name="Mutilate",
            game_id=1285999,
            avoidable=True,
            avoidable_requires_active_debuff_ability_id=1277051,
            avoidable_requires_active_debuff_min_age_ms=100.0,
        )
        requirements = {"1285999": {"Player": [(1_000.0, 23_000.0)]}}

        self.assertFalse(
            is_avoidable_event_requirement_met(
                ability,
                {"timestamp": 1_000.0},
                "Player",
                requirements,
            )
        )
        self.assertTrue(
            is_avoidable_event_requirement_met(
                ability,
                {"timestamp": 10_000.0},
                "Player",
                requirements,
            )
        )
        self.assertFalse(
            is_avoidable_event_requirement_met(
                ability,
                {"timestamp": 24_000.0},
                "Player",
                requirements,
            )
        )

    def test_all_baseline_reports_are_registered_for_heroic(self):
        expected_ids = {
            "sszorak-deaths",
            "sszorak-avoidable-damage",
            "sszorak-damage",
            "sszorak-cooldowns",
            "sszorak-tempest",
            "sszorak-mechanics-scorecard",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions()
            if definition.fight_id == "sszorak"
        }

        self.assertEqual(set(definitions), expected_ids)
        self.assertEqual({definition.difficulty for definition in definitions.values()}, {"heroic"})

    def test_damage_report_uses_sszorak_target(self):
        report_id = "sszorak-damage"
        registered = get_registered_report(report_id)

        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            [
                "report_codes",
                "include_sszorak",
                "kill_only",
                "omit_dead_players",
                "fresh_run",
            ],
        )

        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {"report_codes": "bHB9CK3yQnN2AmYq"},
        )

        self.assertEqual(job_type, JOB_V2_SSZORAK_DAMAGE)
        self.assertEqual(payload["fight"], "Sszorak")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(payload["targets"], ["sszorak"])
        self.assertFalse(fresh_run)

    def test_avoidable_and_death_reports_use_manifest_defaults(self):
        avoidable_job, avoidable_payload, _ = build_report_job_request(
            "sszorak-avoidable-damage",
            {"report_codes": "bHB9CK3yQnN2AmYq"},
        )
        death_job, death_payload, _ = build_report_job_request(
            "sszorak-deaths",
            {"report_codes": "bHB9CK3yQnN2AmYq"},
        )

        self.assertEqual(avoidable_job, JOB_V2_SSZORAK_AVOIDABLE_DAMAGE)
        self.assertEqual(
            avoidable_payload["ability_keys"],
            ["1285999", "1277101", "1287083", "1296667", "1305998"],
        )
        self.assertEqual(death_job, JOB_V2_SSZORAK_DEATHS)
        self.assertEqual(death_payload["fight"], "Sszorak")
        self.assertEqual(death_payload["difficulty"], "heroic")

    def test_cooldown_report_supports_the_kill_as_a_specific_fight(self):
        reminder = (
            "EncounterID:3420;Name:Sszorak - Heroic;Difficulty:Heroic\n"
            "time:11;ph:1;tag:Impalerr;spellid:31884;"
        )
        job_type, payload, _ = build_report_job_request(
            "sszorak-cooldowns",
            {
                "report_codes": "https://www.warcraftlogs.com/reports/bHB9CK3yQnN2AmYq?fight=7",
                "fight_selection": "specific",
                "nsrt_reminders": reminder,
            },
        )

        self.assertEqual(job_type, JOB_V2_COOLDOWN_USAGE)
        self.assertEqual(payload["fight"], "Sszorak")
        self.assertEqual(payload["fight_ids"], [7])
        self.assertEqual(payload["difficulty"], "heroic")

    def test_tempest_report_uses_heroic_sszorak_defaults(self):
        registered = get_registered_report("sszorak-tempest")

        self.assertEqual(
            [field.id for field in registered.definition.request_schema.fields],
            ["report_codes", "ignore_after_deaths", "fresh_run"],
        )
        job_type, payload, fresh_run = build_report_job_request(
            "sszorak-tempest",
            {"report_codes": "bHB9CK3yQnN2AmYq", "ignore_after_deaths": 5},
        )

        self.assertEqual(job_type, JOB_V2_SSZORAK_TEMPEST)
        self.assertEqual(payload["fight"], "Sszorak")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertEqual(payload["ignore_after_deaths"], 5)
        self.assertFalse(fresh_run)


if __name__ == "__main__":
    unittest.main()
