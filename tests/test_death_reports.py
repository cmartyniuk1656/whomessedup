from unittest.mock import Mock, patch

from who_messed_up.api import Fight
from who_messed_up.services.death_reports import (
    DeathReportDamageHit,
    DeathReportEvent,
    is_avoidable_death_event,
    recent_hits_for_death,
)
from who_messed_up.services.consumables import (
    build_healing_consumable_statuses,
    collect_healing_consumable_uses,
    healing_consumable_ability_names,
)


def _hit(*, ability_id: int, avoidable: bool) -> DeathReportDamageHit:
    return DeathReportDamageHit(
        source_report_code="report",
        timestamp=900.0,
        offset_ms=900.0,
        ability_id=ability_id,
        ability_label="Recap ability",
        damage_amount=100.0,
        max_hit_points=1000.0,
        hit_points_percent=10.0,
        is_avoidable=avoidable,
    )


def _death_event(hits):
    return DeathReportEvent(
        source_report_code="report",
        player="Hunter",
        fight_id=1,
        fight_name="Boss",
        pull_index=1,
        timestamp=1000.0,
        offset_ms=1000.0,
        ability_id=None,
        ability_label=None,
        recent_hits=hits,
    )


def test_unattributed_death_does_not_promote_last_recap_hit_to_killing_blow():
    hits = recent_hits_for_death(
        [_hit(ability_id=123, avoidable=True)],
        death_timestamp=1000.0,
        death_offset_ms=1000.0,
        ability_id=None,
        ability_label=None,
        damage_amount=None,
        source_report_code="report",
    )

    assert not any(hit.is_killing_blow for hit in hits)
    assert not is_avoidable_death_event(_death_event(hits))


def test_attributed_death_marks_only_matching_ability_as_killing_blow():
    hits = recent_hits_for_death(
        [
            _hit(ability_id=123, avoidable=True),
            _hit(ability_id=456, avoidable=False),
        ],
        death_timestamp=1000.0,
        death_offset_ms=1000.0,
        ability_id=123,
        ability_label="Known killer",
        damage_amount=None,
        source_report_code="report",
    )

    assert [hit.is_killing_blow for hit in hits] == [True, False]
    assert is_avoidable_death_event(_death_event(hits))


def test_unmatched_killing_metadata_does_not_fall_back_to_last_hit():
    hits = recent_hits_for_death(
        [_hit(ability_id=123, avoidable=True)],
        death_timestamp=1000.0,
        death_offset_ms=1000.0,
        ability_id=999,
        ability_label="Missing killer",
        damage_amount=None,
        source_report_code="report",
    )

    assert not any(hit.is_killing_blow for hit in hits)
    assert not is_avoidable_death_event(_death_event(hits))


def test_both_silvermoon_potion_names_count_as_one_health_potion_slot():
    assert healing_consumable_ability_names() == (
        "Silvermoon Health Potion",
        "Concentrated Silvermoon Health Potion",
        "Healthstone",
    )

    statuses = build_healing_consumable_statuses(
        {
            "Silvermoon Health Potion": [1100.0],
            "Concentrated Silvermoon Health Potion": [1200.0],
        },
        fight_start=1000.0,
        reference_timestamp=1300.0,
    )

    health_potion = statuses[0]
    assert health_potion.label == "Health Potion"
    assert health_potion.used is True
    assert health_potion.timestamps == [1100.0, 1200.0]
    assert health_potion.offsets_ms == [100.0, 200.0]


def test_consumable_collection_resolves_concentrated_potion_by_game_id():
    events = [
        {
            "timestamp": 1200.0,
            "fight": 1,
            "targetName": "Hunter",
            "abilityGameID": 1295247,
        }
    ]
    with patch("who_messed_up.services.consumables.fetch_events", return_value=events):
        usage = collect_healing_consumable_uses(
            Mock(),
            "token",
            fights=[Fight(id=1, name="Boss", start=1000.0, end=2000.0, kill=False)],
            report_code="report",
            ability_names=healing_consumable_ability_names(),
            actor_names={},
        )

    assert usage[1]["Hunter"]["Concentrated Silvermoon Health Potion"] == [1200.0]
