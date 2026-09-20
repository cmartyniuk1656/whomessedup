"""Coverage regression cases use independent recorded event times per pull."""
import unittest
from unittest.mock import patch

from who_messed_up.api import Fight
from who_messed_up.services.cooldown_catalog import coverage_catalog, resolve_timing, talent_ranks
from who_messed_up.services.cooldown_coverage import build_coverage_pull, pressure_series, fetch_cooldown_coverage
from who_messed_up.services.report_registry import build_report_job_request, list_report_definitions
from who_messed_up.services.view_models.cooldown_coverage import build_cooldown_coverage_page


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.spells, self.bosses = coverage_catalog()
        self.fight = Fight(1, "Vashnik the Malignant", 100000, 400000, False, 5, 3455, (1, 2))
        self.boss = self.bosses[3455]

    def event(self, spell, seconds, source=1, kind="cast", **extra):
        return dict(timestamp=self.fight.start + seconds * 1000, abilityGameID=spell,
                    sourceID=source, type=kind, **extra)

    def build(self, streams, fight=None):
        return build_coverage_pull(code="abcdefghijklmnop", fight=fight or self.fight, boss=self.boss,
            streams=streams, actor_names={1: "Healer", 2: "DPS"}, player_ids={1, 2})

    def test_trait_entry_ids_and_rank_specific_variants(self):
        info = {"talentTree": [{"id": 102578, "nodeID": 81592, "rank": 1}]}
        self.assertEqual(talent_ranks(info), {53376: 1})
        self.assertEqual(resolve_timing(self.spells[31884], info)[:2], (120, 30))
        self.assertEqual(talent_ranks({"talentTree": [{"id": 102578, "nodeID": 123, "rank": 1}]}), {})
        for rank, seconds in [(1, 105), (2, 90)]:
            self.assertEqual(resolve_timing(self.spells[31884], {"talentTree": [{"spellID": 1241511, "rank": rank}]})[:2], (seconds, 20))

    def test_null_duration_and_instant_are_distinct(self):
        pull = self.build({"casts": [self.event(370537, 5), self.event(115310, 10)]})
        lanes = {l["spellId"]: l for l in pull["lanes"]}
        self.assertIsNone(lanes[370537]["events"][0]["end"])
        self.assertEqual(lanes[115310]["events"][0]["end"], 10)

    def test_stasis_recovery_starts_at_release_not_preparation(self):
        pull = self.build({"casts": [self.event(370537, 10), self.event(370564, 30)]})
        events = pull["lanes"][0]["events"]
        self.assertEqual([event["label"] for event in events], ["Store", "Release"])
        self.assertIsNone(events[0]["ready"])
        self.assertIsNone(events[0]["end"])
        self.assertEqual(events[1]["ready"], 120)
        prepull_store = self.build({"casts": [self.event(370564, 5)]})
        self.assertEqual(prepull_store["lanes"][0]["events"][0]["ready"], 95)

    def test_conditional_healing_windows_do_not_assign_other_secondary_effects(self):
        for spell_id, talent_id, duration in [(370553, 431695, 30), (472433, 197862, 18), (472433, 1280137, 12), (120517, 453109, 10)]:
            self.assertEqual(resolve_timing(self.spells[spell_id], {"talentTree": [{"spellID": talent_id, "rank": 1}]})[1], duration)
        self.assertIsNone(resolve_timing(self.spells[370537], {"talentTree": [{"spellID": 1242745, "rank": 1}]})[1])

    def test_actual_boss_timing_differs_across_pulls_and_deduplicates(self):
        spell = self.boss["abilities"][0]["spell_id"]
        event = self.event(spell, 13.25, source=99)
        first = self.build({"bossCasts": [event, event, self.event(spell, 55, 99, "begincast")]})
        second = self.build({"bossCasts": [self.event(spell, 29.5, source=99)]})
        self.assertEqual([e["time"] for e in first["lanes"][0]["events"]], [13.25])
        self.assertEqual(second["lanes"][0]["events"][0]["time"], 29.5)

    def test_dps_excluded_unused_talents_and_observed_aura(self):
        pull = self.build({"combatants": [dict(sourceID=1, specID=65, talentTree=[{"spellID": 31821, "rank": 1}]), dict(sourceID=2, specID=70)],
            "casts": [self.event(31884, 5), self.event(31884, 8, 2)],
            "auras": [self.event(31884, 5, kind="applybuff", targetID=1), self.event(31884, 17, kind="removebuff", targetID=1)]})
        self.assertEqual(len(pull["lanes"]), 2)
        wings = next(l for l in pull["lanes"] if l["spellId"] == 31884)
        self.assertEqual(wings["events"][0]["end"], 17)
        self.assertEqual(wings["events"][0]["durationBasis"], "observed aura")
        self.assertFalse(next(l for l in pull["lanes"] if l["spellId"] == 31821)["events"])

    def test_reuse_caps_readiness_and_pull_end_clips_duration(self):
        pull = self.build({"casts": [self.event(740, 10), self.event(740, 90), self.event(740, 298)]})
        events = pull["lanes"][0]["events"]
        self.assertEqual(events[0]["ready"], 90)
        self.assertEqual(events[0]["readyBasis"], "Available by observed next cast")
        self.assertEqual(events[-1]["end"], 300)
        self.assertEqual(events[-1]["ready"], 478)

    def test_pressure_counts_heal_absorbs_once_and_excludes_pets_and_overkill(self):
        self.fight.end = self.fight.start + 3500
        events = [self.event(9, 1, kind="damage", targetID=1, amount=100, absorbed=50, overkill=20),
                  self.event(9, 1, kind="healabsorbed", targetID=1, amount=40),
                  self.event(9, 1, kind="absorbed", targetID=1, amount=500),
                  self.event(9, 1, kind="damage", targetID=99, amount=999),
                  self.event(9, 3, kind="damage", targetID=2, amount=150),
                  self.event(9, 4, kind="damage", targetID=1, amount=999)]
        bins = pressure_series(events, self.fight, {1, 2}, {}, ability_labels={9: "Actual mechanic"})
        self.assertEqual((bins[0]["damage"], bins[0]["healAbsorbs"]), (40, 20))
        self.assertEqual(bins[1]["damage"], 100)
        self.assertEqual(bins[0]["sources"][0]["name"], "Actual mechanic")

    def test_registry_and_typed_page(self):
        reports = [r for r in list_report_definitions() if "cooldown-coverage" in r.id]
        self.assertEqual(len(reports), 18)
        _, payload, fresh = build_report_job_request("vashnik-the-malignant-cooldown-coverage-mythic", {"report_codes": ["abcdefghijklmnop"], "fresh_run": True})
        self.assertEqual(payload["encounter_id"], 3455)
        self.assertEqual(payload["difficulty"], "mythic")
        self.assertTrue(fresh)
        pull = {**self.build({}), "label": "Pull 1"}
        page = build_cooldown_coverage_page({"boss": "Boss", "patch": "12.1", "binSeconds": 2, "pulls": [pull]}, reports[0].id)
        self.assertEqual(page.model_dump(by_alias=True)["content"]["timeline"]["pulls"][0]["fightId"], 1)

    @patch("who_messed_up.services.cooldown_coverage._fetch_ability_labels", return_value={})
    @patch("who_messed_up.services.cooldown_coverage.fetch_event_streams")
    @patch("who_messed_up.services.cooldown_coverage.fetch_fights")
    def test_fetches_all_matching_pulls_and_separate_enemy_cast_stream(self, fights, streams, labels):
        another = Fight(2, self.fight.name, 500000, 700000, True, 5, 3455, (1,))
        other_boss = Fight(3, "Other", 800000, 900000, True, 5, 3445)
        fights.return_value = ([another, self.fight, other_boss], {1: "Healer"}, {1: "Druid"}, {})
        streams.return_value = {}
        result = fetch_cooldown_coverage(report_codes=["abcdefghijklmnop"], encounter_id=3455, difficulty="mythic", token="test")
        self.assertEqual([p["fightId"] for p in result["pulls"]], [1, 2])
        self.assertEqual(streams.call_args.kwargs["streams"]["bossCasts"]["hostility_type"], "Enemies")
