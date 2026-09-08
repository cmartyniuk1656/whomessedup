from unittest.mock import patch

from who_messed_up.api import Fight
from who_messed_up.services.nek_zali_the_soulcoiler_mechanics import (
    ADD_DAMAGE_VIEW_ID,
    CREMATION_ID,
    ESSENCE_REND_DISPELS_VIEW_ID,
    ESSENCE_REND_ID,
    GRASPING_DEPTHS_ID,
    HUNGERING_PYRE_ID,
    IMMORTAL_COIL_ID,
    KILL_SQUADS_VIEW_ID,
    PYRE_SOAKS_VIEW_ID,
    REPORT_ID,
    SOUL_EXHAUSTION_ID,
    SOULCOILED_IDS,
    VESSEL_OF_AWAKENING_ID,
    _fetch_mechanics_event_streams,
    build_kill_squad_sets,
    build_add_damage_sets,
    build_essence_rend_sets,
    build_pyre_sets,
)
from who_messed_up.services.report_registry import (
    JOB_V2_NEK_ZALI_THE_SOULCOILER_MECHANICS,
    build_report_job_request,
    get_registered_report,
)
from who_messed_up.services.report_pulls import ReportPull
from who_messed_up.services.view_models.nek_zali_the_soulcoiler_mechanics import (
    build_nek_zali_mechanics_report_page,
)
from who_messed_up.services.nek_zali_the_soulcoiler_mechanics import (
    MechanicsReportView,
    NekZaliMechanicsSummary,
)


def _damage_event(timestamp, ability_id, target_id, amount=1, source_id=None):
    event = {
        "timestamp": timestamp,
        "abilityGameID": ability_id,
        "targetID": target_id,
        "amount": amount,
    }
    if source_id is not None:
        event["sourceID"] = source_id
    return event


def test_kill_squad_sets_track_entry_time_and_exhaustion_remaining():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=210_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2, 3, 4, 5),
    )
    damage_events = []
    for window_start in (110_000, 180_000):
        damage_events.extend(
            _damage_event(timestamp, GRASPING_DEPTHS_ID, 1)
            for timestamp in range(window_start, window_start + 20_000, 1_000)
        )
    # A short transition fragment is not a real Kill Squad set.
    damage_events.extend(
        _damage_event(timestamp, GRASPING_DEPTHS_ID, 1)
        for timestamp in range(160_000, 166_000, 1_000)
    )
    for player_id in range(1, 6):
        damage_events.append(
            _damage_event(111_000 + player_id * 100, IMMORTAL_COIL_ID, player_id)
        )
        damage_events.append(
            _damage_event(185_000 + player_id * 100, IMMORTAL_COIL_ID, player_id)
        )

    sets = build_kill_squad_sets(
        report_code="REPORT",
        fights=[fight],
        damage_taken_by_fight={10: damage_events},
        exhaustion_by_fight={
            10: [
                {
                    "timestamp": 135_000,
                    "abilityGameID": SOUL_EXHAUSTION_ID,
                    "targetID": 1,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 195_000,
                    "abilityGameID": SOUL_EXHAUSTION_ID,
                    "targetID": 1,
                    "type": "removedebuff",
                },
                {
                    "timestamp": 190_000,
                    "abilityGameID": min(SOULCOILED_IDS),
                    "targetID": 1,
                    "type": "applydebuff",
                },
            ]
        },
        drowned_damage_by_fight={10: []},
        deaths_by_fight={10: [{"timestamp": 192_000, "targetID": 1}]},
        actor_names={1: "Alpha", 2: "Bravo", 3: "Charlie", 4: "Delta", 5: "Echo"},
        actor_classes={1: "Paladin", 2: "Mage", 3: "Monk", 4: "Warrior", 5: "Priest"},
        actor_owners={},
    )

    assert len(sets) == 2
    assert [kill_set.set_index for kill_set in sets] == [1, 2]
    assert [entrant.player for entrant in sets[0].entrants] == [
        "Alpha",
        "Bravo",
        "Charlie",
        "Delta",
        "Echo",
    ]
    exhausted_entry = sets[1].entrants[0]
    assert exhausted_entry.player == "Alpha"
    assert exhausted_entry.entry_offset_ms == 85_100
    assert exhausted_entry.exhaustion_remaining_ms == 9_900
    assert exhausted_entry.ejection_offset_ms == 90_000
    assert exhausted_entry.death_offset_ms == 92_000
    assert exhausted_entry.was_ejected is True
    assert exhausted_entry.died is True
    assert sets[1].exhausted_count == 1


def test_mechanics_view_model_uses_player_list_and_expandable_entry_details():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=140_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2),
    )
    damage_events = [
        *(
            _damage_event(timestamp, GRASPING_DEPTHS_ID, 1)
            for timestamp in range(110_000, 130_000, 1_000)
        ),
        _damage_event(112_345, IMMORTAL_COIL_ID, 1),
    ]
    sets = build_kill_squad_sets(
        report_code="REPORT",
        fights=[fight],
        damage_taken_by_fight={10: damage_events},
        exhaustion_by_fight={
            10: [
                {
                    "timestamp": 120_000,
                    "abilityGameID": min(SOULCOILED_IDS),
                    "targetID": 1,
                    "type": "applydebuff",
                }
            ]
        },
        drowned_damage_by_fight={
            10: [
                _damage_event(115_000, 999, 100, 1_500_000, source_id=1),
                _damage_event(116_000, 999, 100, 750_000, source_id=2),
                _damage_event(117_000, 999, 100, 250_000, source_id=20),
            ]
        },
        deaths_by_fight={10: [{"timestamp": 125_000, "targetID": 1}]},
        actor_names={1: "Alpha", 2: "Bravo", 20: "Alpha's Guardian"},
        actor_classes={1: "Paladin", 2: "Mage", 20: None},
        actor_owners={20: 1},
    )
    summary = NekZaliMechanicsSummary(
        report_code="REPORT",
        fight_filter="Nek'zali the Soulcoiler",
        pull_count=1,
        views=[
            MechanicsReportView(
                id=KILL_SQUADS_VIEW_ID,
                label="Kill Squads",
                description="Test",
                sets=sets,
            )
        ],
        pulls=[
            ReportPull(
                source_report_code="REPORT",
                fight_id=10,
                fight_name="Nek'zali the Soulcoiler",
                pull_index=1,
                view_id="pull:REPORT:10",
                label="Pull 1",
                duration_ms=40_000,
            )
        ],
        player_classes={"Alpha": "Paladin"},
        source_reports=["REPORT"],
    )

    page = build_nek_zali_mechanics_report_page(summary)
    table = page.content.table
    assert table.view_control.default_value == "aggregate"
    assert [option.value for option in table.view_control.options] == [
        "aggregate",
        "pull:REPORT:10",
    ]
    assert table.secondary_view_control.default_value == KILL_SQUADS_VIEW_ID
    assert len(table.rows_by_combined_view["pull:REPORT:10::kill-squads"]) == 1
    assert page.summary_by_view["pull:REPORT:10"][0].value == 1
    assert next(column for column in table.columns if column.id == "players").cell_kind == "player_list"
    assert "pull" not in {column.id for column in table.columns}
    row = table.rows[0]
    assert row.group.label == "Pull 1"
    assert row.group.subtitle == "1 set - 0:40 - Fight 10"
    assert row.group.href.endswith("/REPORT#fight=10")
    assert row.cells["players"].players[0].name == "Alpha"
    assert row.cells["players"].players[0].color_token == "paladin"
    assert row.cells["players"].players[0].tone == "danger"
    assert [
        indicator.icon for indicator in row.cells["players"].players[0].indicators
    ] == ["skull", "ejected"]
    detail = row.details.groups[0].items[0]
    assert detail.timestamp_label == "0:12.35"
    assert detail.badges == [
        "Soul Exhaustion: clear",
        "Ejected - Soulcoiled: 0:20.00",
        "Died: 0:25.00",
    ]
    damage_chart = row.details.bar_chart
    assert damage_chart.title == "Drowned Echo damage"
    assert [bar.label for bar in damage_chart.bars] == ["Alpha", "Bravo"]
    assert [bar.value for bar in damage_chart.bars] == [1_750_000, 750_000]
    assert [bar.display for bar in damage_chart.bars] == ["1,750,000", "750,000"]
    assert [bar.color_token for bar in damage_chart.bars] == ["paladin", "mage"]


def test_drowned_echo_damage_does_not_leak_past_kill_blow_into_next_set():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=180_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2),
    )
    damage_events = []
    for window_start in (110_000, 140_000):
        damage_events.extend(
            _damage_event(timestamp, GRASPING_DEPTHS_ID, 1)
            for timestamp in range(window_start, window_start + 20_000, 1_000)
        )
    damage_events.extend(
        [
            _damage_event(111_000, IMMORTAL_COIL_ID, 1),
            _damage_event(141_000, IMMORTAL_COIL_ID, 2),
        ]
    )
    drowned_events = [
        {
            **_damage_event(112_000, 999, 100, 900_000, source_id=1),
            "targetInstance": 1,
        },
        {
            **_damage_event(120_000, 999, 100, 100_000, source_id=1),
            "targetInstance": 1,
            "overkill": 5_000,
        },
        {
            **_damage_event(135_000, 999, 100, 1, source_id=1),
            "targetInstance": 1,
            "overkill": 10_000,
        },
        {
            **_damage_event(142_000, 999, 100, 1_200_000, source_id=2),
            "targetInstance": 2,
        },
    ]

    sets = build_kill_squad_sets(
        report_code="REPORT",
        fights=[fight],
        damage_taken_by_fight={10: damage_events},
        exhaustion_by_fight={10: []},
        drowned_damage_by_fight={10: drowned_events},
        deaths_by_fight={10: []},
        actor_names={1: "Alpha", 2: "Bravo"},
        actor_classes={1: "Paladin", 2: "Mage"},
        actor_owners={},
    )

    assert len(sets) == 2
    assert [(entry.player, entry.damage) for entry in sets[0].damage_contributions] == [
        ("Alpha", 1_000_000),
    ]
    assert [(entry.player, entry.damage) for entry in sets[1].damage_contributions] == [
        ("Bravo", 1_200_000),
    ]


def test_pyre_sets_are_cast_anchored_and_track_unique_soakers_and_deaths():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=180_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2),
    )
    pyre_sets = build_pyre_sets(
        report_code="REPORT",
        fights=[fight],
        casts_by_fight={
            10: [
                {"timestamp": 120_000, "abilityGameID": HUNGERING_PYRE_ID, "type": "begincast"},
                {"timestamp": 123_000, "abilityGameID": HUNGERING_PYRE_ID, "type": "cast"},
                {"timestamp": 160_000, "abilityGameID": HUNGERING_PYRE_ID, "type": "cast"},
            ]
        },
        damage_taken_by_fight={
            10: [
                _damage_event(123_120, HUNGERING_PYRE_ID, 1, 500_000),
                _damage_event(123_120, HUNGERING_PYRE_ID, 2, 600_000),
                _damage_event(123_121, HUNGERING_PYRE_ID, 1, 100_000),
            ]
        },
        deaths_by_fight={
            10: [
                {
                    "timestamp": 123_200,
                    "targetID": 2,
                    "killingAbilityGameID": HUNGERING_PYRE_ID,
                }
            ]
        },
        actor_names={1: "Alpha", 2: "Bravo", 99: "Restless Amani"},
        actor_classes={1: "Paladin", 2: "Mage"},
        aura_events_by_fight={
            10: [
                {
                    "timestamp": 125_000,
                    "abilityGameID": CREMATION_ID,
                    "targetID": 2,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 145_000,
                    "abilityGameID": CREMATION_ID,
                    "targetID": 2,
                    "type": "removedebuff",
                },
            ]
        },
        enemy_deaths_by_fight={
            10: [
                {"timestamp": 110_000, "targetID": 99, "targetInstance": 1},
                {"timestamp": 110_050, "targetID": 99, "targetInstance": 1},
                {"timestamp": 150_000, "targetID": 99, "targetInstance": 2},
            ]
        },
        vessel_damage_by_fight={
            10: [
                {
                    "timestamp": 140_000,
                    "abilityGameID": VESSEL_OF_AWAKENING_ID,
                    "sourceID": 99,
                    "sourceInstance": 1,
                    "targetID": 1,
                    "amount": 100_000,
                },
                {
                    "timestamp": 141_000,
                    "abilityGameID": VESSEL_OF_AWAKENING_ID,
                    "sourceID": 99,
                    "sourceInstance": 1,
                    "targetID": 2,
                    "amount": 100_000,
                },
            ]
        },
    )

    assert len(pyre_sets) == 2
    assert [pyre_set.set_index for pyre_set in pyre_sets] == [1, 2]
    assert [(soaker.player, soaker.damage) for soaker in pyre_sets[0].soakers] == [
        ("Alpha", 600_000),
        ("Bravo", 600_000),
    ]
    assert pyre_sets[0].impact_offset_ms == 23_120
    assert pyre_sets[0].death_count == 1
    assert pyre_sets[0].soakers[1].death_offset_ms == 23_200
    assert [carrier.player for carrier in pyre_sets[0].cremation_carriers] == [
        "Bravo"
    ]
    assert pyre_sets[0].cremation_carriers[0].removal_offset_ms == 45_000
    assert pyre_sets[0].corpse_opportunity_count == 1
    assert pyre_sets[0].confirmed_miss_count == 1
    assert pyre_sets[0].confirmed_misses[0].source_instance == 1
    assert pyre_sets[1].soakers == ()
    assert pyre_sets[1].corpse_opportunity_count == 1


def test_pyre_view_has_its_own_columns_rows_details_and_summary():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=140_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2),
    )
    pyre_sets = build_pyre_sets(
        report_code="REPORT",
        fights=[fight],
        casts_by_fight={
            10: [
                {"timestamp": 123_000, "abilityGameID": HUNGERING_PYRE_ID, "type": "cast"}
            ]
        },
        damage_taken_by_fight={
            10: [_damage_event(123_100, HUNGERING_PYRE_ID, 1, 750_000)]
        },
        deaths_by_fight={10: []},
        actor_names={1: "Alpha", 2: "Bravo", 99: "Restless Amani"},
        actor_classes={1: "Paladin", 2: "Mage"},
        aura_events_by_fight={
            10: [
                {
                    "timestamp": 125_000,
                    "abilityGameID": CREMATION_ID,
                    "targetID": 2,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 139_000,
                    "abilityGameID": CREMATION_ID,
                    "targetID": 2,
                    "type": "removedebuff",
                },
            ]
        },
        enemy_deaths_by_fight={
            10: [{"timestamp": 110_000, "targetID": 99, "targetInstance": 4}]
        },
        vessel_damage_by_fight={
            10: [
                {
                    "timestamp": 130_000,
                    "abilityGameID": VESSEL_OF_AWAKENING_ID,
                    "sourceID": 99,
                    "sourceInstance": 4,
                    "targetID": 1,
                }
            ]
        },
    )
    summary = NekZaliMechanicsSummary(
        report_code="REPORT",
        fight_filter="Nek'zali the Soulcoiler",
        pull_count=1,
        views=[
            MechanicsReportView(
                id=KILL_SQUADS_VIEW_ID,
                label="Kill Squads",
                description="Test",
                sets=[],
            ),
            MechanicsReportView(
                id=PYRE_SOAKS_VIEW_ID,
                label="Pyre Soaks",
                description="Test",
                sets=pyre_sets,
            ),
        ],
        pulls=[
            ReportPull(
                source_report_code="REPORT",
                fight_id=10,
                fight_name="Nek'zali the Soulcoiler",
                pull_index=1,
                view_id="pull:REPORT:10",
                label="Pull 1",
                duration_ms=40_000,
            )
        ],
        source_reports=["REPORT"],
    )

    page = build_nek_zali_mechanics_report_page(summary)
    table = page.content.table
    assert [option.value for option in table.secondary_view_control.options] == [
        KILL_SQUADS_VIEW_ID,
        PYRE_SOAKS_VIEW_ID,
    ]
    assert [column.id for column in table.columns_by_view[PYRE_SOAKS_VIEW_ID]] == [
        "set",
        "start",
        "players",
        "cremation_carriers",
        "soakers",
        "corpse_opportunities",
        "confirmed_misses",
    ]
    row = table.rows_by_combined_view["aggregate::pyre-soaks"][0]
    assert row.cells["players"].players[0].name == "Alpha"
    assert row.cells["cremation_carriers"].players[0].name == "Bravo"
    assert row.cells["corpse_opportunities"].value == 1
    assert row.cells["confirmed_misses"].value == 1
    assert row.details.groups[0].items[0].description == "took 750,000 damage"
    assert row.details.groups[1].items[0].label == "Bravo"
    assert row.details.groups[2].items[1].badges == [
        "Vessel 4 active at 0:30.00"
    ]
    pyre_summary = page.summary_by_combined_view["aggregate::pyre-soaks"]
    assert [metric.value for metric in pyre_summary] == [1, 1, 1, 1, 1, 1]


def test_essence_rend_sets_group_applications_and_match_dispels_by_target():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=200_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2, 10, 11),
    )
    sets = build_essence_rend_sets(
        report_code="REPORT",
        fights=[fight],
        aura_events_by_fight={
            10: [
                {
                    "timestamp": 120_000,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 1,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 120_020,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 2,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 123_000,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 1,
                    "type": "removedebuff",
                },
                {
                    "timestamp": 135_020,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 2,
                    "type": "removedebuff",
                },
                {
                    "timestamp": 160_000,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 1,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 164_000,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 1,
                    "type": "removedebuff",
                },
            ]
        },
        dispels_by_fight={
            10: [
                {
                    "timestamp": 123_000,
                    "abilityGameID": 527,
                    "extraAbilityGameID": ESSENCE_REND_ID,
                    "sourceID": 10,
                    "targetID": 1,
                    "type": "dispel",
                },
                {
                    "timestamp": 164_000,
                    "abilityGameID": 88423,
                    "extraAbilityGameID": ESSENCE_REND_ID,
                    "sourceID": 11,
                    "targetID": 1,
                    "type": "dispel",
                },
            ]
        },
        actor_names={
            1: "Alpha",
            2: "Bravo",
            10: "Healz",
            11: "Trees",
        },
        actor_classes={
            1: "Paladin",
            2: "Mage",
            10: "Priest",
            11: "Druid",
        },
    )

    assert len(sets) == 2
    assert [rend_set.set_index for rend_set in sets] == [1, 2]
    assert [application.player for application in sets[0].applications] == [
        "Alpha",
        "Bravo",
    ]
    assert sets[0].dispelled_count == 1
    assert sets[0].undispelled_count == 1
    assert sets[0].applications[0].dispeller == "Healz"
    assert sets[0].applications[0].dispel_offset_ms == 23_000
    assert sets[0].applications[0].dispel_delay_ms == 3_000
    assert sets[0].applications[0].dispel_ability_id == 527
    assert sets[0].applications[1].was_dispelled is False
    assert sets[0].applications[1].removal_offset_ms == 35_020
    assert sets[1].applications[0].dispeller == "Trees"


def test_essence_rend_view_shows_dispeller_timestamps_details_and_summary():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=140_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2, 10),
    )
    rend_sets = build_essence_rend_sets(
        report_code="REPORT",
        fights=[fight],
        aura_events_by_fight={
            10: [
                {
                    "timestamp": 120_000,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 1,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 120_010,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 2,
                    "type": "applydebuff",
                },
                {
                    "timestamp": 123_000,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 1,
                    "type": "removedebuff",
                },
                {
                    "timestamp": 135_010,
                    "abilityGameID": ESSENCE_REND_ID,
                    "targetID": 2,
                    "type": "removedebuff",
                },
            ]
        },
        dispels_by_fight={
            10: [
                {
                    "timestamp": 123_000,
                    "abilityGameID": 527,
                    "extraAbilityGameID": ESSENCE_REND_ID,
                    "sourceID": 10,
                    "targetID": 1,
                    "type": "dispel",
                }
            ]
        },
        actor_names={1: "Alpha", 2: "Bravo", 10: "Healz"},
        actor_classes={1: "Paladin", 2: "Mage", 10: "Priest"},
    )
    summary = NekZaliMechanicsSummary(
        report_code="REPORT",
        fight_filter="Nek'zali the Soulcoiler",
        pull_count=1,
        views=[
            MechanicsReportView(
                id=ESSENCE_REND_DISPELS_VIEW_ID,
                label="Essence Rend Dispels",
                description="Test",
                sets=rend_sets,
            )
        ],
        pulls=[
            ReportPull(
                source_report_code="REPORT",
                fight_id=10,
                fight_name="Nek'zali the Soulcoiler",
                pull_index=1,
                view_id="pull:REPORT:10",
                label="Pull 1",
                duration_ms=40_000,
            )
        ],
        source_reports=["REPORT"],
    )

    page = build_nek_zali_mechanics_report_page(summary)
    table = page.content.table
    assert [column.id for column in table.columns_by_view[ESSENCE_REND_DISPELS_VIEW_ID]] == [
        "set",
        "start",
        "players",
        "dispels",
        "dispelled",
        "not_dispelled",
    ]
    sub_view_control = table.sub_view_control_by_view[
        ESSENCE_REND_DISPELS_VIEW_ID
    ]
    assert sub_view_control.default_value == "essence-rend-by-set"
    assert [option.value for option in sub_view_control.options] == [
        "essence-rend-by-set",
        "essence-rend-by-healer",
    ]
    assert [
        column.id
        for column in table.columns_by_view["essence-rend-by-healer"]
    ] == ["dispels"]
    assert (
        table.columns_by_view["essence-rend-by-healer"][0].cell_kind
        == "relative_bar"
    )
    assert table.default_sort_by_view["essence-rend-by-healer"].column_id == (
        "dispels"
    )
    assert table.default_sort_by_view["essence-rend-by-healer"].direction == "desc"
    column_filter = table.column_filter_by_view["essence-rend-by-set"]
    assert [option.id for option in column_filter.options] == [
        "start",
        "players",
        "dispelled",
        "not_dispelled",
    ]
    assert [option.default_selected for option in column_filter.options] == [
        True,
        False,
        True,
        True,
    ]
    row = table.rows_by_combined_view["aggregate::essence-rend-dispels"][0]
    assert row.group.subtitle == "1 Essence Rend set - 0:40 - Fight 10"
    assert [player.name for player in row.cells["players"].players] == [
        "Alpha",
        "Bravo",
    ]
    assert [player.name for player in row.cells["dispels"].players] == [
        "Healz · 0:23.00 → Alpha"
    ]
    dispel_cell = row.cells["dispels"].players[0]
    assert [segment.color_token for segment in dispel_cell.segments] == [
        "priest",
        None,
        "paladin",
    ]
    assert dispel_cell.segments[-1].text == "Alpha"
    assert row.cells["not_dispelled"].value == 1
    assert row.details.groups[0].items[0].description == (
        "dispelled by Healz at 0:23.00 (3.00s after application)"
    )
    assert row.details.groups[0].items[1].badges == [
        "Not dispelled",
        "Aura removed: 0:35.01",
    ]
    assert table.rows_by_combined_view[
        "aggregate::essence-rend-dispels::essence-rend-by-set"
    ] == [row]
    healer_rows = table.rows_by_combined_view[
        "aggregate::essence-rend-dispels::essence-rend-by-healer"
    ]
    assert [healer_row.group.label for healer_row in healer_rows] == [
        "All pulls",
        "Pull 1",
    ]
    all_pulls_row, pull_row = healer_rows
    assert all_pulls_row.group.subtitle == "1 dispel by 1 healer across 1 pull"
    assert all_pulls_row.cells["dispels"].label == "Healz"
    assert all_pulls_row.cells["dispels"].value == 1
    assert all_pulls_row.cells["dispels"].max_value == 1
    assert all_pulls_row.cells["dispels"].unit_label == "dispels"
    assert pull_row.group.subtitle == "1 dispel by 1 healer - 0:40 - Fight 10"
    assert pull_row.cells["dispels"].label == "Healz"
    assert pull_row.cells["dispels"].value == 1
    assert pull_row.cells["dispels"].max_value == 1
    assert table.rows_by_combined_view[
        "pull:REPORT:10::essence-rend-dispels::essence-rend-by-healer"
    ] == [pull_row]
    rend_summary = page.summary_by_combined_view[
        "aggregate::essence-rend-dispels"
    ]
    assert [metric.value for metric in rend_summary] == [1, 1, 2, 1, 1, 3.0]


def test_add_damage_sets_group_amani_waves_and_keep_jawae_together():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=300_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2),
    )
    events = [
        {
            **_damage_event(110_000, 900, 99, 500_000, source_id=1),
            "targetInstance": 1,
        },
        {
            **_damage_event(115_000, 900, 99, 250_000, source_id=20),
            "targetInstance": 1,
            "overkill": 10,
        },
        {
            **_damage_event(120_000, 900, 99, 600_000, source_id=2),
            "targetInstance": 2,
        },
        {
            **_damage_event(150_000, 900, 99, 700_000, source_id=2),
            "targetInstance": 3,
        },
        {
            **_damage_event(155_000, 900, 99, 800_000, source_id=1),
            "targetInstance": 1,
        },
        {
            **_damage_event(180_000, 901, 100, 2_000_000, source_id=1),
            "targetInstance": 1,
        },
        {
            **_damage_event(250_000, 901, 100, 3_000_000, source_id=2),
            "targetInstance": 2,
        },
    ]
    sets = build_add_damage_sets(
        report_code="REPORT",
        fights=[fight],
        damage_by_fight={10: events},
        actor_names={
            1: "Alpha",
            2: "Bravo",
            20: "Alpha Pet",
            99: "Restless Amani",
            100: "Echo of Jawae",
        },
        actor_classes={1: "Paladin", 2: "Mage", 20: None},
        actor_owners={20: 1},
    )

    assert [(add_set.set_index, add_set.add_name) for add_set in sets] == [
        (1, "Restless Amani"),
        (2, "Restless Amani"),
        (3, "Echo of Jawae"),
    ]
    assert [add_set.add_count for add_set in sets] == [2, 2, 2]
    assert [
        (entry.player, entry.damage) for entry in sets[0].damage_contributions
    ] == [("Alpha", 750_000), ("Bravo", 600_000)]
    assert sets[2].start_offset_ms == 80_000
    assert sets[2].end_offset_ms == 150_000


def test_add_damage_view_has_spawn_rows_and_relative_damage_chart():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=140_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1, 2),
    )
    add_sets = build_add_damage_sets(
        report_code="REPORT",
        fights=[fight],
        damage_by_fight={
            10: [
                {
                    **_damage_event(110_000, 900, 99, 1_500_000, source_id=1),
                    "targetInstance": 1,
                },
                {
                    **_damage_event(112_000, 900, 99, 750_000, source_id=2),
                    "targetInstance": 2,
                },
            ]
        },
        actor_names={
            1: "Alpha",
            2: "Bravo",
            99: "Restless Amani",
        },
        actor_classes={1: "Paladin", 2: "Mage"},
        actor_owners={},
    )
    summary = NekZaliMechanicsSummary(
        report_code="REPORT",
        fight_filter="Nek'zali the Soulcoiler",
        pull_count=1,
        views=[
            MechanicsReportView(
                id=ADD_DAMAGE_VIEW_ID,
                label="Add Damage",
                description="Test",
                sets=add_sets,
            )
        ],
        pulls=[
            ReportPull(
                source_report_code="REPORT",
                fight_id=10,
                fight_name="Nek'zali the Soulcoiler",
                pull_index=1,
                view_id="pull:REPORT:10",
                label="Pull 1",
                duration_ms=40_000,
            )
        ],
        source_reports=["REPORT"],
    )

    page = build_nek_zali_mechanics_report_page(summary)
    table = page.content.table
    assert [column.id for column in table.columns_by_view[ADD_DAMAGE_VIEW_ID]] == [
        "set",
        "start",
        "add_type",
        "players",
        "adds",
        "total_damage",
    ]
    add_filter = table.row_filter_by_view[ADD_DAMAGE_VIEW_ID]
    assert add_filter.id == "add_type"
    assert [option.id for option in add_filter.options] == [
        "Restless Amani",
        "Echo of Jawae",
    ]
    assert all(option.default_selected for option in add_filter.options)
    row = table.rows_by_combined_view["aggregate::add-damage"][0]
    assert row.cells["add_type"].value == "Restless Amani"
    assert [player.name for player in row.cells["players"].players] == [
        "Alpha",
        "Bravo",
    ]
    assert row.cells["adds"].value == 2
    assert row.cells["total_damage"].value == 2_250_000
    assert row.details.bar_chart.title == "Restless Amani damage"
    assert [bar.value for bar in row.details.bar_chart.bars] == [
        1_500_000,
        750_000,
    ]
    assert [metric.value for metric in page.summary] == [
        1,
        1,
        1,
        0,
        2,
        2_250_000,
    ]


def test_mechanics_event_fetch_splits_large_streams_and_uses_maximum_pages():
    fight = Fight(
        id=10,
        name="Nek'zali the Soulcoiler",
        start=100_000,
        end=180_000,
        kill=False,
        difficulty=5,
        friendly_player_ids=(1,),
    )
    with patch(
        "who_messed_up.services.nek_zali_the_soulcoiler_mechanics.fetch_events_grouped",
        return_value={10: []},
    ) as fetch:
        streams = _fetch_mechanics_event_streams(
            report_code="REPORT",
            fights=[fight],
            bearer="TOKEN",
            actor_names={1: "Alpha"},
        )

    assert set(streams) == {
        "grasp",
        "immortal",
        "auras",
        "add_damage",
        "deaths",
        "pyre_casts",
        "pyre_damage",
        "enemy_deaths",
        "vessel_damage",
        "essence_rend_dispels",
    }
    assert fetch.call_count == 10
    assert all(call.kwargs["limit"] == 10_000 for call in fetch.call_args_list)
    selectors = {
        (
            call.kwargs["data_type"],
            call.kwargs.get("ability_id"),
            call.kwargs.get("extra_filter"),
        )
        for call in fetch.call_args_list
    }
    assert ("DamageTaken", GRASPING_DEPTHS_ID, None) in selectors
    assert ("DamageTaken", IMMORTAL_COIL_ID, None) in selectors
    assert ("Dispels", ESSENCE_REND_ID, None) in selectors
    assert (
        "DamageDone",
        None,
        'target.name in ("Drowned Echo","Restless Amani","Echo of Jawae") '
        "and effectiveDamage > 1",
    ) in selectors
    pyre_cast_call = next(
        call
        for call in fetch.call_args_list
        if call.kwargs["data_type"] == "Casts"
    )
    assert pyre_cast_call.kwargs["ability_id"] == HUNGERING_PYRE_ID
    assert pyre_cast_call.kwargs["hostility_type"] == "Enemies"
    enemy_death_call = next(
        call
        for call in fetch.call_args_list
        if call.kwargs["data_type"] == "Deaths"
        and call.kwargs.get("hostility_type") == "Enemies"
    )
    assert enemy_death_call.kwargs["extra_filter"] == (
        'target.name = "Restless Amani"'
    )


def test_mechanics_event_fetch_parallelizes_large_add_stream_by_fight():
    fights = [
        Fight(
            id=fight_id,
            name="Nek'zali the Soulcoiler",
            start=100_000 + index * 100_000,
            end=180_000 + index * 100_000,
            kill=False,
            difficulty=5,
            friendly_player_ids=(1,),
        )
        for index, fight_id in enumerate((10, 11))
    ]

    def empty_group(*args, **kwargs):
        return {fight.id: [] for fight in kwargs["fights"]}

    with patch(
        "who_messed_up.services.nek_zali_the_soulcoiler_mechanics.fetch_events_grouped",
        side_effect=empty_group,
    ) as fetch:
        streams = _fetch_mechanics_event_streams(
            report_code="REPORT",
            fights=fights,
            bearer="TOKEN",
            actor_names={1: "Alpha"},
        )

    assert set(streams["add_damage"]) == {10, 11}
    add_calls = [
        call
        for call in fetch.call_args_list
        if call.kwargs.get("extra_filter")
        == 'target.name in ("Drowned Echo","Restless Amani","Echo of Jawae") '
        "and effectiveDamage > 1"
    ]
    assert len(add_calls) == 2
    assert {call.kwargs["fights"][0].id for call in add_calls} == {10, 11}
    assert all(len(call.kwargs["fights"]) == 1 for call in add_calls)


def test_mechanics_report_is_registered_and_included_in_mythic_aggregate():
    job_type, payload, fresh_run = build_report_job_request(
        REPORT_ID,
        {"report_codes": ["REPORT", "EXTRA"], "fresh_run": True},
    )
    assert job_type == JOB_V2_NEK_ZALI_THE_SOULCOILER_MECHANICS
    assert payload["report"] == "REPORT"
    assert payload["extra_reports"] == ["EXTRA"]
    assert payload["difficulty"] == "mythic"
    assert fresh_run is True

    aggregate = get_registered_report(
        "nek-zali-the-soulcoiler-mythic-aggregate-reports"
    ).definition
    field_ids = {field.id for field in aggregate.request_schema.fields}
    assert f"aggregate_include__{REPORT_ID}" in field_ids
