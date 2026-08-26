import unittest

from who_messed_up.services.ability_event_filters import is_avoidable_event_excluded
from who_messed_up.services.boss_manifest_types import BossAbilityMetadata


class AvoidableEventExclusionTests(unittest.TestCase):
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
