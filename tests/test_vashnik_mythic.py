"""Guard observed Mythic damage coverage and routing through the shared report services."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import app as application
from who_messed_up.services.boss_manifests import get_boss_manifest
from who_messed_up.services.boss_manifest_types import is_avoidable_ability
from who_messed_up.services.avoidable_damage import AvoidableDamageSummary
from who_messed_up.services.death_reports import DeathReportSummary
from who_messed_up.services.target_damage import EncounterTargetDamageSummary


def test_manifest_covers_observed_damage_without_scoring_collective_failures():
    observed = json.loads(
        (Path(__file__).parent / "fixtures/vashnik_mythic_observed.json").read_text()
    )
    manifest = get_boss_manifest("vashnik-the-malignant", 5)
    ids = {ability.game_id for ability in manifest.abilities}
    assert len(ids) == len(manifest.abilities) == 25
    assert ids == {row["id"] for row in observed["damage_abilities"]} | set(observed["inherited_unobserved_ids"])
    assert not ids & {row["id"] for row in observed["ignored"]}
    assert {a.game_id for a in manifest.abilities if is_avoidable_ability(a)} == {
        1302489, 1295798, 1291467, 1286737, 1297338,
    }
    for ability_id in (1304459, 1280189, 1282616, 1282602, 1281925, 1295209, 1295229, 1295224, 1280934, 1280935):
        assert not is_avoidable_ability(manifest.ability_for(ability_id=ability_id))
    assert {target.enemy_name for target in manifest.targets} == {
        "Vashnik", "Burning Venom", "Clotting Venom", "Shrouded Venom",
    }
    heroic = get_boss_manifest("vashnik-the-malignant", "heroic")
    assert not is_avoidable_ability(heroic.ability_for(ability_id=1302489))
    assert heroic.ability_for(ability_id=1304459) is None


@pytest.mark.parametrize("difficulty,suffix", [("heroic", ""), ("mythic", "-mythic"), (5, "-mythic")])
@pytest.mark.parametrize("kind", ["damage", "deaths", "avoidable_damage"])
def test_job_routes_manifest_and_page_difficulty(kind, difficulty, suffix):
    common = dict(
        report_code="REPORT", fight_filter="Vashnik the Malignant", fight_ids=[],
        entries=[], player_classes={}, player_roles={}, player_specs={}, pull_count=0,
    )
    if kind == "damage":
        summary = EncounterTargetDamageSummary(
            **common, total_damage=0, avg_damage_per_pull=0, targets=[],
        )
        shared_function = "fetch_encounter_target_damage_summary"
    elif kind == "deaths":
        summary = DeathReportSummary(
            **common, ignore_after_deaths=None, ignore_unavoidable_after_healer_deaths=None,
            total_deaths=0, total_avoidable_deaths=0, player_events={}, ability_labels={},
        )
        shared_function = "fetch_death_report_summary"
    else:
        summary = AvoidableDamageSummary(
            **common, ignore_after_deaths=None, total_damage=0, avg_damage_per_pull=0,
            player_events={}, abilities=[],
        )
        shared_function = "fetch_avoidable_damage_summary"
    with patch(
        f"who_messed_up.services.vashnik_the_malignant_{kind}.{shared_function}",
        return_value=summary,
    ) as fetch:
        execute = getattr(application, f"_execute_v2_vashnik_the_malignant_{kind}_job")
        page = execute({"report": "REPORT", "difficulty": difficulty})
    expected_difficulty = "mythic" if suffix else "heroic"
    assert page["reportId"] == f"vashnik-the-malignant-{kind.replace('_', '-')}{suffix}"
    assert page["title"].startswith(expected_difficulty.title())
    assert fetch.call_args.kwargs["difficulty"] == difficulty
    manifest = get_boss_manifest("vashnik-the-malignant", expected_difficulty)
    if kind == "damage":
        assert fetch.call_args.kwargs["target_configs"] == manifest.target_configs
    else:
        assert fetch.call_args.kwargs["boss_manifest"] is manifest
