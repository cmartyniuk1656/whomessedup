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

    table = page.content.table
    assert table.view_control.default_value == "aggregate"
    assert [option.label for option in table.view_control.options] == ["All pulls", "Pull 1", "Pull 2"]
    assert table.secondary_view_control.default_value == "death_bars"
    assert [option.label for option in table.secondary_view_control.options] == [
        "Death bars",
        "Table",
    ]
    rate_filter = table.column_filter_by_view["death_bars"]
    assert rate_filter.kind == "single_select"
    assert [option.id for option in rate_filter.options if option.default_selected] == [
        "death_rate"
    ]
    aggregate_bar_rows = table.rows_by_combined_view["aggregate::death_bars"]
    alice_bar = next(row for row in aggregate_bar_rows if row.id == "Alice")
    bob_bar = next(row for row in aggregate_bar_rows if row.id == "Bob")
    assert alice_bar.cells["death_rate"].value == 0.5
    assert alice_bar.cells["death_rate"].max_value == 0.5
    assert alice_bar.cells["avoidable_death_rate"].value == 0.0
    assert bob_bar.cells["death_rate"].value == 0.0
    assert alice_bar.details is not None
    assert "deaths" in table.rows_by_combined_view["aggregate::table"][0].cells
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


def test_avoidable_damage_report_defaults_to_relative_player_bars_with_hit_counts():
    alice_events = [
        AvoidableDamageEvent(
            source_report_code="report",
            player="Alice",
            fight_id=1,
            fight_name="Boss",
            pull_index=1,
            timestamp=10_000.0 + index,
            offset_ms=5_000.0 + index,
            ability_id=456,
            ability_label="Bad",
            damage_amount=150.0,
        )
        for index in range(2)
    ]
    bob_event = AvoidableDamageEvent(
        source_report_code="report",
        player="Bob",
        fight_id=1,
        fight_name="Boss",
        pull_index=1,
        timestamp=12_000.0,
        offset_ms=7_000.0,
        ability_id=789,
        ability_label="Worse",
        damage_amount=150.0,
    )
    summary = AvoidableDamageSummary(
        report_code="report",
        fight_filter="Boss",
        fight_ids=None,
        pull_count=1,
        ignore_after_deaths=None,
        total_damage=450.0,
        avg_damage_per_pull=450.0,
        entries=[
            AvoidableDamageEntry("Alice", "DPS", "Mage", 1, 300.0, 300.0, alice_events),
            AvoidableDamageEntry("Bob", "DPS", "Warrior", 1, 150.0, 150.0, [bob_event]),
        ],
        player_classes={"Alice": "Mage", "Bob": "Warrior"},
        player_roles={"Alice": "DPS", "Bob": "DPS"},
        player_specs={},
        player_events={"Alice": alice_events, "Bob": [bob_event]},
        abilities=[BossAbilityMetadata(name="Bad", game_id=456, avoidable=True)],
        pulls=[_pull(1, ("Alice", "Bob"))],
        source_reports=["report"],
    )

    page = build_avoidable_damage_report_page(
        summary,
        config=AvoidableDamagePageConfig("avoidable", "Avoidable"),
    )
    table = page.content.table

    assert table.secondary_view_control.default_value == "damage_bars"
    assert [option.label for option in table.secondary_view_control.options] == [
        "Damage bars",
        "Table",
    ]
    assert [column.id for column in table.columns_by_view["damage_bars"]] == [
        "damage",
        "hit_count",
    ]
    bar_rows = table.rows_by_combined_view["aggregate::damage_bars"]
    alice = next(row for row in bar_rows if row.id == "Alice")
    bob = next(row for row in bar_rows if row.id == "Bob")
    assert alice.cells["damage"].max_value == 300.0
    assert bob.cells["damage"].max_value == 300.0
    assert alice.cells["hit_count"].value == 2
    assert bob.cells["hit_count"].value == 1
    assert alice.details is not None
    assert len(alice.details.groups[0].items) == 2
    assert "average_damage" in table.rows_by_combined_view["aggregate::table"][0].cells


def test_avoidable_damage_groups_configured_dot_ticks_into_hit_instances():
    tick_timestamps = [1_000.0, 2_000.0, 3_000.0, 4_000.0, 20_000.0, 21_000.0]
    events = [
        AvoidableDamageEvent(
            source_report_code="report",
            player="Alice",
            fight_id=1,
            fight_name="Boss",
            pull_index=1,
            timestamp=timestamp,
            offset_ms=timestamp,
            ability_id=1300239,
            ability_label="Swirling Spirit",
            damage_amount=50.0,
        )
        for timestamp in tick_timestamps
    ]
    summary = AvoidableDamageSummary(
        report_code="report",
        fight_filter="Boss",
        fight_ids=None,
        pull_count=1,
        ignore_after_deaths=None,
        total_damage=300.0,
        avg_damage_per_pull=300.0,
        entries=[
            AvoidableDamageEntry("Alice", "DPS", "Mage", 1, 300.0, 300.0, events)
        ],
        player_classes={"Alice": "Mage"},
        player_roles={"Alice": "DPS"},
        player_specs={},
        player_events={"Alice": events},
        abilities=[
            BossAbilityMetadata(
                name="Swirling Spirit",
                game_id=1300239,
                avoidable=True,
                avoidable_hit_group_window_ms=2_000.0,
            )
        ],
        source_reports=["report"],
    )

    page = build_avoidable_damage_report_page(
        summary,
        config=AvoidableDamagePageConfig("avoidable", "Avoidable"),
    )
    row = page.content.table.rows[0]

    assert row.cells["hit_count"].value == 2
    assert row.cells["damage"].value == 300.0
    assert row.details is not None
    assert len(row.details.groups[0].items) == 2
    assert [item.description for item in row.details.groups[0].items] == [
        "for 200",
        "for 100",
    ]


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

    table = page.content.table
    assert table.secondary_view_control.default_value == "damage_bars"
    assert [option.label for option in table.secondary_view_control.options] == [
        "Damage bars",
        "Table",
    ]
    assert table.damage_filter_config_by_view[
        "damage_bars"
    ].metric_filter.kind == "single_select"
    assert [
        option.id
        for option in table.damage_filter_config_by_view[
            "damage_bars"
        ].metric_filter.options
        if option.default_selected
    ] == ["averages"]
    assert table.damage_filter_config_by_view[
        "table"
    ].metric_filter.kind == "multi_select"
    aggregate_bar = table.rows_by_combined_view["aggregate::damage_bars"][0]
    assert aggregate_bar.cells["bar_total_damage"].value == 300.0
    assert aggregate_bar.cells["bar_average_damage"].value == 150.0
    assert aggregate_bar.details is not None
    assert aggregate_bar.details.bar_chart.bars[0].label == "Boss"
    assert aggregate_bar.details.bar_chart.bars[0].value == 300.0
    assert aggregate_bar.details.bar_chart.bars[0].color_token == "mage"
    assert aggregate_bar.details.groups == []
    assert table.rows_by_view["pull:report:1"] == []
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
