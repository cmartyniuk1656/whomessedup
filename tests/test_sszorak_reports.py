import unittest
from dataclasses import replace
from unittest.mock import patch

from who_messed_up.api import Fight
from who_messed_up.services.sszorak_tempest import fetch_sszorak_tempest_summary
from who_messed_up.services.view_models.sszorak_mechanics import build_sszorak_mechanics_report_page
from who_messed_up.services.view_models.sszorak_tempest import build_sszorak_tempest_report_page

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
    JOB_V2_SSZORAK_MECHANICS,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


class SszorakReportRegistryTests(unittest.TestCase):
    def test_mythic_mechanics_registration_and_payload(self):
        registered = get_registered_report("sszorak-mythic-mechanics")
        self.assertEqual(registered.definition.difficulty, "mythic")
        self.assertIn(registered.definition, list_report_definitions())
        job, payload, fresh = build_report_job_request("sszorak-mythic-mechanics", {
            "report_codes": ["yCHTdpBrV19zDLvg", "bHB9CK3yQnN2AmYq"],
            "ignore_after_deaths": 5, "fresh_run": True,
        })
        self.assertEqual(job, JOB_V2_SSZORAK_MECHANICS)
        self.assertEqual(payload, {
            "report": "yCHTdpBrV19zDLvg", "extra_reports": ["bHB9CK3yQnN2AmYq"],
            "fight": "Sszorak", "difficulty": "mythic", "ignore_after_deaths": 5,
            "mechanics_version": 2,
            "tempest_version": 2,
        })
        self.assertTrue(fresh)

    def test_mythic_hits_exclude_ticks_duplicates_other_difficulties_and_late_events(self):
        service = "who_messed_up.services.sszorak_tempest."
        fights = [Fight(1, "Sszorak", 0, 10000, False, difficulty=4, friendly_player_ids=(1, 2)),
                  Fight(2, "Sszorak", 20000, 30000, False, difficulty=5, friendly_player_ids=(1, 2))]
        def event(at, kind, player="Alice", **extra):
            return dict(timestamp=at, type=kind, targetName=player, abilityGameID=1287083, **extra)
        events = [event(21000, "applydebuff"), event(22000, "applydebuffstack", stack=2),
                  event(22000, "refreshdebuff"), event(23000, "refreshdebuff", stack=3),
                  event(23500, "damage"), event(24000, "removedebuff"),
                  event(26000, "applydebuff"), event(21000, "applydebuff", player="Pet")]
        def fetch_events(*args, **kwargs):
            self.assertEqual([fight.id for fight in kwargs["fights"]], [2])
            return {2: events if kwargs["data_type"] == "Debuffs" else []}
        with patch(service + "_resolve_token", return_value="token"), \
             patch(service + "fetch_fights", return_value=(fights, {1: "Alice", 2: "Bob", 3: "Pet"}, {1: "Mage", 2: "Priest"}, {})), \
             patch(service + "fetch_player_details", return_value={}), \
             patch(service + "compute_death_cutoffs", return_value={2: 25000}), \
             patch(service + "fetch_events_grouped", side_effect=fetch_events):
            summary = fetch_sszorak_tempest_summary(report_code="yCHTdpBrV19zDLvg", difficulty="mythic", ignore_after_deaths=5)
        self.assertEqual(summary.pull_count, 1)
        self.assertEqual(summary.total_contacts, 3)
        self.assertEqual({entry.player: entry.contacts for entry in summary.entries}, {"Alice": 3, "Bob": 0})
        page = build_sszorak_mechanics_report_page(summary)
        heroic = build_sszorak_tempest_report_page(summary)
        self.assertEqual(page.report_id, "sszorak-mythic-mechanics")
        self.assertEqual(heroic.report_id, "sszorak-tempest")
        self.assertEqual(page.content.table.rows_by_combined_view["tempest::table"], heroic.content.table.rows)
        self.assertEqual(page.content.table.view_control.options[0].label, "Tempest Hits")
        self.assertEqual(page.content.table.rows_by_view["tempest"], page.content.table.rows)
        alice = page.content.table.rows[0]
        self.assertEqual(alice.cells["contacts"].value, 3)
        self.assertEqual(alice.cells["contacts"].label, "Alice")
        self.assertEqual(alice.cells["contacts"].max_value, 3)
        self.assertEqual(alice.cells["contacts"].color_token, heroic.content.table.rows[0].cells["player"].color_token)
        self.assertEqual(page.content.table.rows[1].cells["contacts"].value, 0)
        self.assertEqual(page.content.table.secondary_view_control.default_value, "bars")
        self.assertEqual(page.content.table.columns[0].cell_kind, "relative_bar")
        self.assertEqual(page.content.table.default_sort.direction, "desc")
        self.assertEqual(page.content.table.rows_by_combined_view["tempest::table"][0].cells["contacts_per_pull"].value, 3)
        self.assertEqual(len(alice.details.groups[0].items), 3)
        empty_page = build_sszorak_mechanics_report_page(replace(summary, entries=[]))
        self.assertEqual(empty_page.content.table.rows, [])
        zero_page = build_sszorak_mechanics_report_page(replace(summary, entries=[summary.entries[1]]))
        self.assertEqual(zero_page.content.table.rows[0].cells["contacts"].max_value, 0)

    def test_tempest_contacts_collapse_same_timestamp_stack_and_refresh(self):
        events = [
            {"timestamp": 1000, "type": "applydebuff", "abilityGameID": 1287083, "targetName": "Player"},
            {"timestamp": 1300, "type": "applydebuffstack", "abilityGameID": 1287083, "targetName": "Player", "stack": 3},
            {"timestamp": 1300, "type": "refreshdebuff", "abilityGameID": 1287083, "targetName": "Player"},
            {"timestamp": 1500, "type": "removedebuff", "abilityGameID": 1287083, "targetName": "Player"},
            {"timestamp": 1600, "type": "applydebuff", "abilityGameID": 123, "targetName": "Player"},
        ]

        contacts = _collapse_tempest_contacts(events)

        self.assertEqual(len(contacts), 2)
        self.assertEqual(contacts[1]["type"], "applydebuffstack")
        self.assertEqual(contacts[1]["stack"], 3)

    def test_tempest_nearby_records_use_fixed_player_contact_windows(self):
        def event(timestamp, player="Alice", stack=1):
            return dict(timestamp=timestamp, targetName=player, stack=stack,
                        type="applydebuffstack", abilityGameID=1287083)
        events = [event(70840), event(70870, stack=2), event(71090, stack=3),
                  event(70850, "Bob"), event(71091), event(71341, stack=2),
                  event(71342), event(70840)]
        original = [dict(item) for item in events]
        contacts = _collapse_tempest_contacts(reversed(events))
        self.assertEqual([(item["targetName"], item["timestamp"], item["stack"]) for item in contacts],
                         [("Alice", 70840, 3), ("Bob", 70850, 1),
                          ("Alice", 71091, 2), ("Alice", 71342, 1)])
        self.assertEqual(events, original)

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
            "sszorak-cooldown-coverage-heroic",
            "sszorak-defensive-usage-heroic",
            "sszorak-tempest",
            "sszorak-mechanics-scorecard",
            "sszorak-heroic-aggregate-reports",
        }
        definitions = {
            definition.id: definition
            for definition in list_report_definitions(include_hidden=True)
            if definition.fight_id == "sszorak"
            and definition.difficulty == "heroic"
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
