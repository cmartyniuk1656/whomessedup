import unittest
from unittest.mock import Mock, patch

from who_messed_up.api import Fight
from who_messed_up.services.ability_event_filters import (
    collect_avoidable_exclusion_events_by_fight,
    is_avoidable_event_excluded,
)
from who_messed_up.services.boss_manifest_types import BossAbilityMetadata


class AvoidableEventExclusionTests(unittest.TestCase):
    def test_exclusion_debuffs_are_fetched_once_for_all_fights(self):
        ability = BossAbilityMetadata(
            name="Ground Effect",
            game_id=123,
            avoidable=True,
            avoidable_exclusion_debuff_ability_id=456,
            avoidable_exclusion_debuff_event_types=("applydebuff",),
        )
        fights = [
            Fight(id=1, name="Boss", start=100, end=200, kill=False),
            Fight(id=2, name="Boss", start=300, end=400, kill=False),
        ]
        grouped = {
            1: [{"type": "applydebuff", "abilityGameID": 456, "targetName": "One", "timestamp": 150}],
            2: [{"type": "applydebuff", "abilityGameID": 456, "targetName": "Two", "timestamp": 350}],
        }
        with patch(
            "who_messed_up.services.ability_event_filters.fetch_events_grouped",
            return_value=grouped,
        ) as fetch:
            result = collect_avoidable_exclusion_events_by_fight(
                Mock(),
                "token",
                report_code="report",
                fights=fights,
                actor_names={},
                abilities=[ability],
            )

        self.assertEqual(result[1]["123"]["One"], [150.0])
        self.assertEqual(result[2]["123"]["Two"], [350.0])
        self.assertEqual(fetch.call_count, 1)

    def test_active_debuff_excludes_only_the_debuff_carrier(self):
        ability = BossAbilityMetadata(
            name="Proximity Pulse",
            game_id=123,
            avoidable=True,
            avoidable_excludes_active_debuff_ability_id=456,
        )
        windows = {"123": {"Carrier": [(1_000.0, 6_000.0)]}}

        self.assertTrue(
            is_avoidable_event_excluded(
                ability,
                {"timestamp": 3_000.0},
                "Carrier",
                {},
                windows,
            )
        )
        self.assertFalse(
            is_avoidable_event_excluded(
                ability,
                {"timestamp": 3_000.0},
                "Bystander",
                {},
                windows,
            )
        )
        self.assertFalse(
            is_avoidable_event_excluded(
                ability,
                {"timestamp": 6_001.0},
                "Carrier",
                {},
                windows,
            )
        )


if __name__ == "__main__":
    unittest.main()
