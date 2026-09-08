import unittest

from who_messed_up.services.boss_manifests import get_boss_manifest
from who_messed_up.services.boss_manifest_types import (
    EncounterTargetBucket,
    is_avoidable_ability,
)


class NekZaliHeroicManifestTests(unittest.TestCase):
    def test_manifest_resolves_for_heroic(self):
        manifest = get_boss_manifest("nek-zali-the-soulcoiler", "heroic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "Nek'zali the Soulcoiler")

    def test_manifest_contains_observed_targets_and_documented_damage_abilities(self):
        manifest = get_boss_manifest("nek-zali-the-soulcoiler", "heroic")

        self.assertEqual(
            {target.enemy_name for target in manifest.targets},
            {"Nek'zali the Soulcoiler", "Restless Amani", "Echo of Jawae"},
        )
        self.assertEqual(
            {ability.game_id for ability in manifest.abilities},
            {
                1284109,
                1287434,
                1288554,
                1288772,
                1289855,
                1289875,
                1290390,
                1292034,
                1292315,
                1292899,
                1294729,
                1294846,
                1294933,
                1295085,
                1297630,
                1307939,
            },
        )

    def test_only_individually_avoidable_damage_is_flagged(self):
        manifest = get_boss_manifest("nek-zali-the-soulcoiler", "heroic")

        self.assertEqual(
            {ability.game_id for ability in manifest.abilities if is_avoidable_ability(ability)},
            {1288554, 1290390, 1292899, 1294846, 1295085},
        )

    def test_restless_amani_is_classified_as_pad_damage(self):
        manifest = get_boss_manifest("nek-zali-the-soulcoiler", "heroic")

        self.assertEqual(
            manifest.target_configs["restless_amani"].bucket,
            EncounterTargetBucket.PAD_ADD,
        )


class NekZaliMythicManifestTests(unittest.TestCase):
    def test_manifest_resolves_for_mythic(self):
        manifest = get_boss_manifest("nek-zali-the-soulcoiler", "mythic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "Nek'zali the Soulcoiler")

    def test_manifest_extends_heroic_with_drowned_echo_mechanics(self):
        heroic = get_boss_manifest("nek-zali-the-soulcoiler", "heroic")
        mythic = get_boss_manifest("nek-zali-the-soulcoiler", "mythic")

        self.assertEqual(
            {target.enemy_name for target in mythic.targets},
            {"Nek'zali the Soulcoiler", "Restless Amani", "Echo of Jawae", "Drowned Echo"},
        )
        self.assertEqual(
            {ability.game_id for ability in mythic.abilities} - {ability.game_id for ability in heroic.abilities},
            {1293214, 1300239, 1308227},
        )

    def test_swirling_spirit_is_the_only_new_avoidable_ability(self):
        heroic = get_boss_manifest("nek-zali-the-soulcoiler", "heroic")
        mythic = get_boss_manifest("nek-zali-the-soulcoiler", "mythic")

        heroic_avoidable = {
            ability.game_id for ability in heroic.abilities if is_avoidable_ability(ability)
        }
        mythic_avoidable = {
            ability.game_id for ability in mythic.abilities if is_avoidable_ability(ability)
        }
        self.assertEqual(mythic_avoidable - heroic_avoidable, {1300239})

        swirling_spirit = mythic.ability_for(ability_id=1300239)
        self.assertEqual(swirling_spirit.avoidable_hit_group_window_ms, 2_000.0)


class EntombedSentinelsHeroicManifestTests(unittest.TestCase):
    def test_manifest_resolves_only_for_heroic(self):
        manifest = get_boss_manifest("entombed-sentinels", "heroic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "Entombed Sentinels")
        self.assertIsNone(get_boss_manifest("entombed-sentinels", "mythic"))

    def test_manifest_contains_observed_targets_and_damage_abilities(self):
        manifest = get_boss_manifest("entombed-sentinels", "heroic")

        self.assertEqual(
            {target.enemy_name for target in manifest.targets},
            {"Blood of Ula'tek", "Breath of Ula'tek", "Venom Coagulation"},
        )
        self.assertEqual(
            {ability.game_id for ability in manifest.abilities},
            {
                1284209,
                1284210,
                1284258,
                1284451,
                1284452,
                1284458,
                1284471,
                1284487,
                1284500,
                1284506,
                1284813,
                1284941,
                1284948,
                1288282,
                1297338,
                1303097,
                1310126,
            },
        )

    def test_only_individually_avoidable_damage_is_flagged(self):
        manifest = get_boss_manifest("entombed-sentinels", "heroic")

        self.assertEqual(
            {ability.game_id for ability in manifest.abilities if is_avoidable_ability(ability)},
            {1284209, 1284210, 1284941, 1284948, 1297338},
        )


class TheLostExplorersHeroicManifestTests(unittest.TestCase):
    def test_manifest_resolves_only_for_heroic(self):
        manifest = get_boss_manifest("the-lost-explorers", "heroic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "The Lost Explorers")
        self.assertIsNone(get_boss_manifest("the-lost-explorers", "mythic"))

    def test_manifest_contains_observed_targets_and_damage_abilities(self):
        manifest = get_boss_manifest("the-lost-explorers", "heroic")

        self.assertEqual(
            {target.enemy_name for target in manifest.targets},
            {"First Mate Nama", "Scrollsage Iku", "Trader Gebbo"},
        )
        self.assertEqual(
            {ability.game_id for ability in manifest.abilities},
            {
                1286922,
                1291935,
                1292764,
                1292780,
                1294334,
                1295450,
                1295893,
                1295952,
                1295985,
                1296245,
                1296251,
                1297648,
                1297649,
                1300237,
                1305618,
                1305844,
                1308853,
                1310027,
                1310500,
                1310616,
                1310662,
                1310667,
            },
        )

    def test_only_individually_avoidable_damage_is_flagged(self):
        manifest = get_boss_manifest("the-lost-explorers", "heroic")

        self.assertEqual(
            {ability.game_id for ability in manifest.abilities if is_avoidable_ability(ability)},
            {1291935, 1292764, 1296245, 1305618, 1305844, 1310500},
        )


class VashnikTheMalignantHeroicManifestTests(unittest.TestCase):
    def test_manifest_resolves_only_for_heroic(self):
        manifest = get_boss_manifest("vashnik-the-malignant", "heroic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "Vashnik the Malignant")
        self.assertIsNone(get_boss_manifest("vashnik-the-malignant", "mythic"))

    def test_manifest_contains_observed_targets_and_damage_abilities(self):
        manifest = get_boss_manifest("vashnik-the-malignant", "heroic")

        self.assertEqual(
            {target.enemy_name for target in manifest.targets},
            {"Vashnik", "Burning Venom", "Clotting Venom", "Shrouded Venom"},
        )
        self.assertEqual(
            {ability.game_id for ability in manifest.abilities},
            {
                1280189,
                1280934,
                1280935,
                1281925,
                1282525,
                1282602,
                1282616,
                1284561,
                1285979,
                1286737,
                1291467,
                1294994,
                1295173,
                1295209,
                1295224,
                1295229,
                1295798,
                1298582,
                1298583,
                1298587,
                1302489,
                1305833,
                1305901,
            },
        )

    def test_only_directly_dodgeable_damage_is_flagged(self):
        manifest = get_boss_manifest("vashnik-the-malignant", "heroic")

        self.assertEqual(
            {ability.game_id for ability in manifest.abilities if is_avoidable_ability(ability)},
            {1286737, 1291467, 1295798},
        )


class SszorakHeroicManifestTests(unittest.TestCase):
    def test_manifest_resolves_only_for_heroic(self):
        manifest = get_boss_manifest("sszorak", "heroic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "Sszorak")
        self.assertIsNone(get_boss_manifest("sszorak", "mythic"))

    def test_manifest_contains_observed_target_and_damage_abilities(self):
        manifest = get_boss_manifest("sszorak", "heroic")

        self.assertEqual({target.enemy_name for target in manifest.targets}, {"Sszorak"})
        self.assertEqual(
            {ability.game_id for ability in manifest.abilities},
            {
                1277101,
                1285616,
                1285965,
                1285998,
                1285999,
                1287083,
                1287205,
                1296667,
                1305998,
                1306120,
                1312156,
                1312219,
            },
        )

    def test_only_directly_avoidable_damage_is_flagged(self):
        manifest = get_boss_manifest("sszorak", "heroic")

        self.assertEqual(
            {ability.game_id for ability in manifest.abilities if is_avoidable_ability(ability)},
            {1277101, 1285999, 1287083, 1296667, 1305998},
        )


class TheTwinFangsHeroicManifestTests(unittest.TestCase):
    def test_manifest_resolves_only_for_heroic(self):
        manifest = get_boss_manifest("the-twin-fangs", "heroic")

        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.boss_name, "The Twin Fangs")
        self.assertIsNone(get_boss_manifest("the-twin-fangs", "mythic"))

    def test_manifest_contains_observed_targets_and_damage_abilities(self):
        manifest = get_boss_manifest("the-twin-fangs", "heroic")

        self.assertEqual(
            {target.enemy_name for target in manifest.targets},
            {"Vexhul", "Ithraz", "Spawn of Vexhul"},
        )
        self.assertEqual(
            {ability.game_id for ability in manifest.abilities},
            {
                1289153,
                1289201,
                1289237,
                1289994,
                1290338,
                1290480,
                1290662,
                1290878,
                1292552,
                1292806,
                1292807,
                1293295,
                1294605,
                1294976,
                1295107,
                1295115,
                1297338,
                1306876,
                1306925,
                1308122,
                1308835,
                1308841,
                1309471,
                1310371,
                1313533,
            },
        )

    def test_only_personally_attributable_damage_is_flagged(self):
        manifest = get_boss_manifest("the-twin-fangs", "heroic")

        self.assertEqual(
            {ability.game_id for ability in manifest.abilities if is_avoidable_ability(ability)},
            {
                1289994,
                1290662,
                1292552,
                1292807,
                1293295,
                1294605,
                1297338,
                1306876,
                1306925,
                1309471,
                1310371,
            },
        )


if __name__ == "__main__":
    unittest.main()
