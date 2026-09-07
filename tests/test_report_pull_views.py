from who_messed_up.services.avoidable_damage import (
    AvoidableDamageEntry,
    AvoidableDamageEvent,
    AvoidableDamageSummary,
)
from who_messed_up.services.boss_manifest_types import (
    BossAbilityMetadata,
    EncounterTargetBucket,
    EncounterTargetConfig,
)
from who_messed_up.services.cooldown_usage import (
    COOLDOWN_STATUS_CORRECT,
    CooldownReminderHeader,
    CooldownReminderPlan,
    CooldownUsageEntry,
    CooldownUsageEvent,
    CooldownUsagePull,
    CooldownUsageSummary,
)
from who_messed_up.services.death_reports import (
    DeathReportEntry,
    DeathReportEvent,
    DeathReportSummary,
)
from who_messed_up.services.report_pulls import ReportPull, merge_report_pulls
from who_messed_up.services.target_damage import (
    EncounterTargetDamageBreakdown,
    EncounterTargetDamageEntry,
    EncounterTargetDamageSummary,
    EncounterTargetSummary,
    fetch_encounter_target_damage_summary,
)
from who_messed_up.services.view_models.avoidable_damage import (
    AvoidableDamagePageConfig,
    build_avoidable_damage_report_page,
)
from who_messed_up.services.view_models.death_reports import (
    DeathReportPageConfig,
    build_death_report_page,
)
from who_messed_up.services.view_models.lightblinded_vanguard_cooldowns import (
    build_cooldown_usage_report_page,
)
from who_messed_up.services.view_models.target_damage import (
    TargetDamageReportConfig,
    build_target_damage_report_page,
)


def _pull(index: int, participants=("Alice",)) -> ReportPull:
    return ReportPull(
        source_report_code="report",
        fight_id=index,
        fight_name="Boss",
        pull_index=index,
        view_id=f"pull:report:{index}",
        label=f"Pull {index}",
        duration_ms=60_000.0,
        participants=participants,
    )


def _row_values(page, view_id: str, player: str):
    rows = page.content.table.rows_by_view[view_id]
    row = next(item for item in rows if item.id == player)
    return {key: cell.value for key, cell in row.cells.items()}


def _summary_values(page, view_id: str):
    return {metric.id: metric.value for metric in page.summary_by_view[view_id]}


def test_merged_pull_labels_and_view_ids_disambiguate_source_reports():
    first = _pull(1)
    second = ReportPull(
        source_report_code="extra",
        fight_id=1,
        fight_name="Boss",
        pull_index=1,
        view_id="pull:extra:1",
        label="Pull 1",
        duration_ms=60_000.0,
        participants=("Alice",),
    )

    merged = merge_report_pulls([[first], [second]])

    assert [pull.view_id for pull in merged] == ["pull:report:1", "pull:extra:1"]
    assert [pull.label for pull in merged] == ["report Pull 1", "extra Pull 1"]


def test_death_report_defaults_to_all_pulls_and_scopes_rows_by_pull():
    event = DeathReportEvent(
        source_report_code="report",
        player="Alice",
        fight_id=1,
        fight_name="Boss",
        pull_index=1,
        timestamp=10_000.0,
        offset_ms=10_000.0,
        ability_id=123,
        ability_label="Hit",
    )
    summary = DeathReportSummary(
        report_code="report",
        fight_filter="Boss",
        fight_ids=None,
        pull_count=2,
        ignore_after_deaths=None,
        ignore_unavoidable_after_healer_deaths=None,
        total_deaths=1,
        total_avoidable_deaths=0,
        entries=[
            DeathReportEntry("Alice", "DPS", "Mage", 2, 1, 0, 0.5, [event]),
            DeathReportEntry("Bob", "DPS", "Warrior", 1, 0, 0, 0.0, []),
        ],
        player_classes={"Alice": "Mage", "Bob": "Warrior"},
        player_roles={"Alice": "DPS", "Bob": "DPS"},
        player_specs={},
        player_events={"Alice": [event]},
        ability_labels={123: "Hit"},
        pulls=[_pull(1, ("Alice",)), _pull(2, ("Alice", "Bob"))],
        source_reports=["report"],
    )

    page = build_death_report_page(summary, config=DeathReportPageConfig("deaths", "Deaths"))

    assert page.content.table.view_control.default_value == "aggregate"
    assert [option.label for option in page.content.table.view_control.options] == ["All pulls", "Pull 1", "Pull 2"]
    assert _row_values(page, "pull:report:1", "Alice")["deaths"] == 1
    assert _row_values(page, "pull:report:2", "Alice")["deaths"] == 0
    assert _row_values(page, "pull:report:2", "Bob")["pulls"] == 1
    assert _summary_values(page, "pull:report:1")["total_deaths"] == 1
    assert _summary_values(page, "pull:report:2")["total_deaths"] == 0


def test_avoidable_damage_report_recalculates_single_pull_totals():
    event = AvoidableDamageEvent(
        source_report_code="report",
        player="Alice",
        fight_id=2,
        fight_name="Boss",
        pull_index=2,
        timestamp=20_000.0,
        offset_ms=5_000.0,
        ability_id=456,
        ability_label="Bad",
        damage_amount=250.0,
    )
    summary = AvoidableDamageSummary(
        report_code="report",
        fight_filter="Boss",
        fight_ids=None,
        pull_count=2,
        ignore_after_deaths=None,
        total_damage=250.0,
        avg_damage_per_pull=125.0,
        entries=[AvoidableDamageEntry("Alice", "DPS", "Mage", 2, 250.0, 125.0, [event])],
        player_classes={"Alice": "Mage"},
        player_roles={"Alice": "DPS"},
        player_specs={},
        player_events={"Alice": [event]},
        abilities=[BossAbilityMetadata(name="Bad", game_id=456, avoidable=True)],
        pulls=[_pull(1), _pull(2)],
        source_reports=["report"],
    )

    page = build_avoidable_damage_report_page(
        summary,
        config=AvoidableDamagePageConfig("avoidable", "Avoidable"),
    )

    assert _row_values(page, "aggregate", "Alice")["average_damage"] == 125.0
    assert _row_values(page, "pull:report:1", "Alice")["total_damage"] == 0
    assert _row_values(page, "pull:report:2", "Alice")["average_damage"] == 250.0
    assert _summary_values(page, "pull:report:2")["total_damage"] == 250.0


def test_damage_report_uses_preserved_per_pull_target_breakdowns():
    target = EncounterTargetSummary("boss", "Boss", EncounterTargetBucket.BOSS, 300.0, 150.0)
    aggregate = EncounterTargetDamageEntry(
        "Alice",
        "DPS",
        "Mage",
        2,
        300.0,
        150.0,
        {"boss": EncounterTargetDamageBreakdown("boss", "Boss", 300.0, 150.0)},
    )
    pull_entry = EncounterTargetDamageEntry(
        "Alice",
        "DPS",
        "Mage",
        1,
        225.0,
        225.0,
        {"boss": EncounterTargetDamageBreakdown("boss", "Boss", 225.0, 225.0)},
    )
    summary = EncounterTargetDamageSummary(
        report_code="report",
        fight_filter="Boss",
        fight_ids=None,
        entries=[aggregate],
        player_classes={"Alice": "Mage"},
        player_roles={"Alice": "DPS"},
        player_specs={"Alice": "Frost"},
        pull_count=2,
        total_damage=300.0,
        avg_damage_per_pull=150.0,
        targets=[target],
        pulls=[_pull(1), _pull(2)],
        entries_by_pull={"pull:report:1": [], "pull:report:2": [pull_entry]},
        source_reports=["report"],
    )
    config = TargetDamageReportConfig(
        report_id="damage",
        title="Damage",
        combined_total_label="Total",
        combined_average_label="Average",
        table_total_label="Total",
        table_average_label="Average",
    )

    page = build_target_damage_report_page(summary, config=config)

    assert page.content.table.rows_by_view["pull:report:1"] == []
    assert _row_values(page, "pull:report:2", "Alice")["target_total_boss"] == 225.0
    assert _summary_values(page, "pull:report:2")["total_damage"] == 225.0


def test_damage_fetch_batches_tables_per_fight_and_preserves_pull_totals():
    fights = [
        Fight(1, "Boss", 0.0, 10_000.0, False, friendly_player_ids=(10,)),
        Fight(2, "Boss", 20_000.0, 35_000.0, False, friendly_player_ids=(10, 20)),
    ]
    requested_tables = []

    def fake_fetch_tables(_session, _token, *, code, table_requests):
        assert code == "report"
        requests = list(table_requests)
        requested_tables.extend(requests)
        return [
            {"entries": [{"id": 10, "total": 100.0}]},
            {"entries": [{"id": 10, "total": 300.0}, {"id": 20, "total": 200.0}]},
        ]

    with (
        patch(
            "who_messed_up.services.target_damage.fetch_fights",
            return_value=(fights, {10: "Alice", 20: "Bob"}, {10: "Mage", 20: "Warrior"}, {}),
        ),
        patch("who_messed_up.services.target_damage.fetch_player_details", return_value={}),
        patch("who_messed_up.services.target_damage.fetch_tables", side_effect=fake_fetch_tables),
    ):
        summary = fetch_encounter_target_damage_summary(
            report_code="report",
            fight_name="Boss",
            target_configs={
                "boss": EncounterTargetConfig("boss", "Boss", "Boss", EncounterTargetBucket.BOSS)
            },
            token="token",
        )

    assert [request["fight_ids"] for request in requested_tables] == [[1], [2]]
    assert {entry.player: entry.total_damage for entry in summary.entries} == {"Alice": 400.0, "Bob": 200.0}
    assert {
        entry.player: entry.total_damage
        for entry in summary.entries_by_pull["pull:report:1"]
    } == {"Alice": 100.0}
    assert {
        entry.player: entry.total_damage
        for entry in summary.entries_by_pull["pull:report:2"]
    } == {"Alice": 300.0, "Bob": 200.0}


def test_cooldown_usage_report_uses_the_shared_all_pulls_selector():
    pull = CooldownUsagePull("report", 1, "Boss", 1, "pull:report:1", "Pull 1", 60_000.0)
    event = CooldownUsageEvent(
        source_report_code="report",
        player="Alice",
        fight_id=1,
        fight_name="Boss",
        pull_index=1,
        pull_view_id=pull.view_id,
        status=COOLDOWN_STATUS_CORRECT,
        line_number=1,
        spell_id=123,
        ability_label="Cooldown",
        scheduled_timestamp=1_000.0,
        scheduled_offset_ms=1_000.0,
        phase=1,
        phase_time_seconds=1.0,
    )
    entry = CooldownUsageEntry("Alice", "Healer", "Priest", 1, 1, 1, 0, 0, 0, 1.0, 0.0, [event])
    summary = CooldownUsageSummary(
        report_code="report",
        fight_filter="Boss",
        fight_ids=None,
        pull_count=1,
        tolerance_seconds=7.5,
        ignore_after_deaths=None,
        ignore_after_healer_death=False,
        ignore_stasis=True,
        plan=CooldownReminderPlan(CooldownReminderHeader(1, "Heroic", "Boss"), []),
        pulls=[pull],
        entries=[entry],
        player_classes={"Alice": "Priest"},
        player_roles={"Alice": "Healer"},
        player_specs={"Alice": "Holy"},
        player_events={"Alice": [event]},
        pulls_by_player={"Alice": 1},
        source_reports=["report"],
    )

    page = build_cooldown_usage_report_page(summary)

    assert page.content.table.view_control.label == "Pull"
    assert [option.label for option in page.content.table.view_control.options] == ["All pulls", "Pull 1"]
    assert _summary_values(page, "pull:report:1")["assignments_checked"] == 1
from unittest.mock import patch

from who_messed_up.api import Fight
