import unittest

from who_messed_up.api import Fight
from who_messed_up.services.cooldown_usage import (
    COOLDOWN_STATUS_CORRECT,
    COOLDOWN_STATUS_IGNORED_DEAD,
    COOLDOWN_STATUS_INCORRECT,
    CooldownCastEvent,
    CooldownLifeEvent,
    CooldownReminderAssignment,
    CooldownReminderHeader,
    CooldownReminderPlan,
    CooldownUsagePull,
    STASIS_SPELL_IDS,
    _filter_cooldown_plan,
    _match_assignments_for_fight,
)


class CooldownUsageDeathMatchingTests(unittest.TestCase):
    def setUp(self):
        self.fight = Fight(
            id=36,
            name="Lightblinded Vanguard",
            start=100000.0,
            end=350000.0,
            kill=False,
            difficulty=5,
            encounter_id=3180,
        )
        self.pull = CooldownUsagePull(
            source_report_code="report",
            fight_id=self.fight.id,
            fight_name=self.fight.name,
            pull_index=7,
            view_id="pull:report:36",
            label="Pull 7",
            duration_ms=250000.0,
        )
        self.assignment = CooldownReminderAssignment(
            line_number=4,
            time_seconds=92.0,
            phase=1,
            player="Taisuwu",
            spell_id=370537,
        )
        self.plan = CooldownReminderPlan(
            header=CooldownReminderHeader(encounter_id=3180, difficulty="Mythic", name="Vanguard - Mythic"),
            assignments=[self.assignment],
        )
        self.life_events = {
            "taisuwu": [
                CooldownLifeEvent(timestamp=self.fight.start + 90310.0, event_type="death"),
                CooldownLifeEvent(timestamp=self.fight.start + 98860.0, event_type="resurrect"),
            ]
        }

    def test_late_cast_after_resurrection_is_reported_instead_of_ignored_dead(self):
        casts = {
            (self.fight.id, "taisuwu", 370537): [
                CooldownCastEvent(
                    player="Taisuwu",
                    spell_id=370537,
                    timestamp=self.fight.start + 102560.0,
                    offset_ms=102560.0,
                    ability_label="Stasis (Store)",
                )
            ]
        }

        events = self._match(casts)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, COOLDOWN_STATUS_INCORRECT)
        self.assertEqual(events[0].actual_offset_ms, 102560.0)
        self.assertAlmostEqual(events[0].delta_seconds, 10.56)
        self.assertIsNone(events[0].ignore_reason)

    def test_dead_assignment_without_cast_remains_ignored(self):
        events = self._match({})

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, COOLDOWN_STATUS_IGNORED_DEAD)
        self.assertIsNone(events[0].actual_offset_ms)
        self.assertEqual(events[0].ignore_reason, "dead")

    def test_stasis_filter_removes_store_and_release_assignments(self):
        release = CooldownReminderAssignment(
            line_number=5,
            time_seconds=119.0,
            phase=1,
            player="Taisuwu",
            spell_id=370564,
        )
        rewind = CooldownReminderAssignment(
            line_number=6,
            time_seconds=130.0,
            phase=1,
            player="Taisuwu",
            spell_id=363534,
        )
        plan = CooldownReminderPlan(
            header=self.plan.header,
            assignments=[self.assignment, release, rewind],
        )

        filtered = _filter_cooldown_plan(plan, ignored_spell_ids=STASIS_SPELL_IDS)

        self.assertEqual([assignment.spell_id for assignment in filtered.assignments], [363534])

    def test_glowunit_alive_target_mismatch_is_incorrect(self):
        assignment = CooldownReminderAssignment(
            line_number=7,
            time_seconds=40.0,
            phase=1,
            player="Taisuwu",
            spell_id=29166,
            fields={"glowunit": "ellimist"},
        )
        plan = CooldownReminderPlan(header=self.plan.header, assignments=[assignment])
        casts = {
            (self.fight.id, "taisuwu", 29166): [
                CooldownCastEvent(
                    player="Taisuwu",
                    spell_id=29166,
                    timestamp=self.fight.start + 40100.0,
                    offset_ms=40100.0,
                    ability_label="Innervate",
                    target="Other",
                )
            ]
        }

        events = self._match(casts, plan=plan, participants={"taisuwu", "ellimist", "other"})

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, COOLDOWN_STATUS_INCORRECT)
        self.assertEqual(events[0].intended_target, "Ellimist")
        self.assertEqual(events[0].actual_target, "Other")
        self.assertTrue(events[0].target_was_alive)
        self.assertTrue(events[0].target_mismatch)

    def test_glowunit_target_match_is_correct(self):
        assignment = CooldownReminderAssignment(
            line_number=8,
            time_seconds=40.0,
            phase=1,
            player="Taisuwu",
            spell_id=29166,
            fields={"glowunit": "ellimist"},
        )
        plan = CooldownReminderPlan(header=self.plan.header, assignments=[assignment])
        casts = {
            (self.fight.id, "taisuwu", 29166): [
                CooldownCastEvent(
                    player="Taisuwu",
                    spell_id=29166,
                    timestamp=self.fight.start + 40100.0,
                    offset_ms=40100.0,
                    ability_label="Innervate",
                    target="Ellimist",
                )
            ]
        }

        events = self._match(casts, plan=plan, participants={"taisuwu", "ellimist"})

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, COOLDOWN_STATUS_CORRECT)
        self.assertEqual(events[0].actual_target, "Ellimist")
        self.assertFalse(events[0].target_mismatch)

    def test_glowunit_dead_target_does_not_force_target_mismatch(self):
        assignment = CooldownReminderAssignment(
            line_number=9,
            time_seconds=40.0,
            phase=1,
            player="Taisuwu",
            spell_id=29166,
            fields={"glowunit": "ellimist"},
        )
        plan = CooldownReminderPlan(header=self.plan.header, assignments=[assignment])
        casts = {
            (self.fight.id, "taisuwu", 29166): [
                CooldownCastEvent(
                    player="Taisuwu",
                    spell_id=29166,
                    timestamp=self.fight.start + 40100.0,
                    offset_ms=40100.0,
                    ability_label="Innervate",
                    target="Other",
                )
            ]
        }
        life_events = {
            **self.life_events,
            "ellimist": [CooldownLifeEvent(timestamp=self.fight.start + 30000.0, event_type="death")],
        }

        events = self._match(
            casts,
            plan=plan,
            participants={"taisuwu", "ellimist", "other"},
            life_events=life_events,
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, COOLDOWN_STATUS_CORRECT)
        self.assertFalse(events[0].target_was_alive)
        self.assertFalse(events[0].target_mismatch)

    def _match(self, casts, *, plan=None, participants=None, life_events=None):
        return _match_assignments_for_fight(
            report_code="report",
            fight=self.fight,
            pull=self.pull,
            plan=plan or self.plan,
            note_player_lookup={"taisuwu": "Taisuwu"},
            target_player_lookup={"taisuwu": "Taisuwu", "ellimist": "Ellimist", "other": "Other"},
            participants=participants or {"taisuwu"},
            cast_events=casts,
            life_events=life_events or self.life_events,
            ability_labels={370537: "Stasis (Store)"},
            tolerance_seconds=7.5,
            death_count_cutoff=None,
            healer_death_cutoff=None,
        )


if __name__ == "__main__":
    unittest.main()
