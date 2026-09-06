import unittest

from who_messed_up.api import Fight
from who_messed_up.services.mechanic_scorecard_analyzers import (
    FightMechanicContext,
    MECHANICS_BY_BOSS,
    analyze_fight,
)
from who_messed_up.services.mechanic_scorecard_types import (
    OUTCOME_CONTRIBUTION,
    OUTCOME_MISTAKE,
    OUTCOME_SUCCESS,
)
from who_messed_up.services.report_registry import (
    JOB_V2_MECHANIC_SCORECARD,
    build_report_job_request,
    get_registered_report,
    list_report_definitions,
)


SCORECARD_BOSSES = {
    "nek-zali-the-soulcoiler",
    "entombed-sentinels",
    "the-lost-explorers",
    "vashnik-the-malignant",
    "sszorak",
    "the-twin-fangs",
    "the-coiled-altar",
}


def _event(event_type, timestamp, ability_id, target="Player", **extra):
    return {
        "type": event_type,
        "timestamp": float(timestamp),
        "abilityGameID": ability_id,
        "targetName": target,
        **extra,
    }


def _context(events_by_type, players=None):
    players = set(players or {"Player"})
    return FightMechanicContext(
        report_code="REPORT",
        fight=Fight(1, "Test Fight", 0.0, 60_000.0, True, difficulty=4),
        pull_index=1,
        participants=players,
        known_players=players,
        events_by_type=events_by_type,
    )


class MechanicScorecardRegistryTests(unittest.TestCase):
    def test_all_extrapolated_heroic_bosses_have_scorecards(self):
        definitions = {
            definition.fight_id: definition
            for definition in list_report_definitions()
            if definition.id.endswith("-mechanics-scorecard")
        }

        self.assertEqual(set(definitions), SCORECARD_BOSSES)
        self.assertEqual(
            {definition.difficulty for definition in definitions.values()},
            {"heroic"},
        )
        for boss_id in SCORECARD_BOSSES:
            fields = [
                field.id
                for field in get_registered_report(
                    f"{boss_id}-mechanics-scorecard"
                ).definition.request_schema.fields
            ]
            self.assertEqual(
                fields,
                [
                    "report_codes",
                    "fight_selection",
                    "fight_id",
                    "ignore_after_deaths",
                    "fresh_run",
                ],
            )

    def test_specific_fight_can_be_read_from_warcraft_logs_url(self):
        report_id = "the-coiled-altar-mechanics-scorecard"
        job_type, payload, fresh_run = build_report_job_request(
            report_id,
            {
                "report_codes": [
                    "https://www.warcraftlogs.com/reports/p4mPajMdJRgKqQBT?fight=30"
                ],
                "fight_selection": "specific",
                "fresh_run": True,
            },
        )

        self.assertEqual(job_type, JOB_V2_MECHANIC_SCORECARD)
        self.assertEqual(payload["boss_id"], "the-coiled-altar")
        self.assertEqual(payload["fight_ids"], [30])
        self.assertEqual(payload["fight_selection"], "specific")
        self.assertEqual(payload["difficulty"], "heroic")
        self.assertTrue(fresh_run)

    def test_specific_fight_rejects_multiple_reports(self):
        with self.assertRaisesRegex(ValueError, "one Warcraft Logs report"):
            build_report_job_request(
                "sszorak-mechanics-scorecard",
                {
                    "report_codes": ["first?fight=7", "second"],
                    "fight_selection": "specific",
                },
            )


class MechanicScorecardAnalyzerTests(unittest.TestCase):
    def test_coiled_altar_does_not_score_venomfang_dispels(self):
        observations = analyze_fight(
            "the-coiled-altar",
            _context(
                {
                    "Debuffs": [
                        _event("applydebuff", 1_000, 1306906),
                        _event("removedebuff", 8_000, 1306906),
                    ],
                    "Dispels": [],
                    "DamageTaken": [],
                    "Interrupts": [],
                    "Casts": [],
                }
            ),
        )

        self.assertNotIn(
            "venomfang-dispels",
            {definition.id for definition in MECHANICS_BY_BOSS["the-coiled-altar"]},
        )
        self.assertFalse(any(event.ability_id == 1306906 for event in observations))

    def test_coiled_orb_pickup_is_positive_without_claiming_placement(self):
        observations = analyze_fight(
            "the-coiled-altar",
            _context(
                {
                    "Debuffs": [
                        _event("applydebuff", 1_000, 1282419),
                        _event("removedebuff", 6_000, 1282419),
                    ],
                    "DamageTaken": [],
                    "Dispels": [],
                    "Interrupts": [],
                    "Casts": [],
                }
            ),
        )
        orb_events = [
            event for event in observations if event.mechanic_id == "orb-relocation"
        ]

        self.assertEqual(len(orb_events), 1)
        self.assertEqual(orb_events[0].outcome, OUTCOME_CONTRIBUTION)
        self.assertEqual(orb_events[0].value, 5.0)
        self.assertIn("not inferred", orb_events[0].description)

    def test_mutilate_detects_a_preexisting_gash(self):
        observations = analyze_fight(
            "sszorak",
            _context(
                {
                    "Debuffs": [
                        _event("applydebuff", 1_000, 1277051),
                        _event("removedebuff", 10_000, 1277051),
                    ],
                    "DamageTaken": [
                        _event("damage", 5_000, 1285999),
                    ],
                }
            ),
        )
        player_events = [
            event
            for event in observations
            if event.mechanic_id == "mutilate-rotation"
            and event.player == "Player"
        ]

        self.assertEqual(len(player_events), 1)
        self.assertEqual(player_events[0].outcome, OUTCOME_MISTAKE)

    def test_elemental_aura_removed_before_next_wave_is_clean(self):
        observations = analyze_fight(
            "the-lost-explorers",
            _context(
                {
                    "Debuffs": [
                        _event("applydebuff", 1_000, 1295928),
                        _event("removedebuff", 8_000, 1295928),
                        _event("applydebuff", 20_000, 1295954, target="Other"),
                    ],
                    "Interrupts": [],
                    "DamageTaken": [],
                    "Casts": [],
                },
                {"Player", "Other"},
            ),
        )
        event = next(
            event
            for event in observations
            if event.mechanic_id == "elemental-cleanse"
            and event.player == "Player"
        )
        self.assertEqual(event.outcome, OUTCOME_SUCCESS)
        self.assertEqual(event.value, 7.0)

    def test_gravebound_counts_recovered_fragments_and_clean_resolution(self):
        observations = analyze_fight(
            "the-coiled-altar",
            _context(
                {
                    "Debuffs": [
                        _event("applydebuff", 1_000, 1286837),
                        _event("removedebuffstack", 3_000, 1286837),
                        _event("removedebuffstack", 5_000, 1286837),
                        _event("removedebuff", 7_000, 1286837),
                    ],
                    "DamageTaken": [],
                    "Dispels": [],
                    "Interrupts": [],
                    "Casts": [],
                }
            ),
        )
        gravebound = [
            event for event in observations if event.mechanic_id == "gravebound"
        ]

        self.assertEqual(
            [event.outcome for event in gravebound].count(OUTCOME_SUCCESS), 1
        )
        self.assertEqual(
            [event.outcome for event in gravebound].count(OUTCOME_CONTRIBUTION), 2
        )


if __name__ == "__main__":
    unittest.main()
