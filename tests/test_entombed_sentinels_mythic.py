"""Protect Mythic spell classification and difficulty routing through real page builders."""
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


def test_manifest_covers_observed_npc_damage_and_separates_assignments_from_failures():
    observed = json.loads(
        (Path(__file__).parent / "fixtures/entombed_sentinels_mythic_observed.json").read_text()
    )
    manifest = get_boss_manifest("entombed-sentinels", 5)
    assert {ability.game_id for ability in manifest.abilities} == {
        ability["game_id"] for ability in observed["damage_abilities"]
    }
    assert not set(observed["ignored_ability_ids"]) & {
        ability.game_id for ability in manifest.abilities
    }
    assert len(manifest.targets) == 3
    assert is_avoidable_ability(manifest.ability_for(ability_id=1296962))
    for ability_id in (1296882, 1284451, 1284452, 1288282, 1303097, 1284813, 1284487, 1310126, 1284458):
        assert not is_avoidable_ability(manifest.ability_for(ability_id=ability_id))
    # The manifest describes damage subspells; cast/aura IDs are reserved
    # for the future assignment and timing analysis.
    assert manifest.ability_for(ability_id=1296878) is None
    assert manifest.ability_for(ability_id=1296880) is None
    assert "not necessarily" in manifest.ability_for(ability_id=1296962).description


@pytest.mark.parametrize("difficulty,suffix", [("heroic", ""), ("mythic", "-mythic"), (5, "-mythic")])
@pytest.mark.parametrize("kind", ["damage", "deaths", "avoidable_damage"])
def test_job_routes_manifest_and_page_difficulty(kind, difficulty, suffix):
    common = dict(
        report_code="REPORT", fight_filter="Entombed Sentinels", fight_ids=[],
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
        f"who_messed_up.services.entombed_sentinels_{kind}.{shared_function}",
        return_value=summary,
    ) as fetch:
        execute = getattr(application, f"_execute_v2_entombed_sentinels_{kind}_job")
        page = execute({"report": "REPORT", "difficulty": difficulty})
    expected_difficulty = "mythic" if suffix else "heroic"
    assert page["reportId"] == f"entombed-sentinels-{kind.replace('_', '-')}{suffix}"
    assert page["title"].startswith(expected_difficulty.title())
    assert fetch.call_args.kwargs["difficulty"] == difficulty
    manifest = get_boss_manifest("entombed-sentinels", expected_difficulty)
    if kind == "damage":
        assert fetch.call_args.kwargs["target_configs"] == manifest.target_configs
    else:
        assert fetch.call_args.kwargs["boss_manifest"] is manifest
