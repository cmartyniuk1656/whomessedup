"""View-model builder for the Heroic and Mythic Vashnik avoidable damage report."""
from __future__ import annotations

from dataclasses import replace

from ..boss_manifest_types import normalize_manifest_difficulty
from ..avoidable_damage import AvoidableDamageSummary
from ..vashnik_the_malignant_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "vashnik-the-malignant-avoidable-damage"
MYTHIC_REPORT_ID = "vashnik-the-malignant-avoidable-damage-mythic"
REPORT_TITLE = "Heroic Vashnik the Malignant - Avoidable Damage Report"
MYTHIC_REPORT_TITLE = "Mythic Vashnik the Malignant - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic Vashnik the Malignant pulls."
MYTHIC_REPORT_DESCRIPTION = "Track avoidable damage taken during Mythic Vashnik the Malignant pulls."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]
REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


MYTHIC_REPORT_CONFIG = replace(
    REPORT_CONFIG,
    report_id=MYTHIC_REPORT_ID,
    title=MYTHIC_REPORT_TITLE,
)


def build_vashnik_the_malignant_avoidable_damage_report_page(
    summary: AvoidableDamageSummary,
    *,
    difficulty: str | int | None = None,
):
    config = MYTHIC_REPORT_CONFIG if normalize_manifest_difficulty(difficulty) == "mythic" else REPORT_CONFIG
    return build_avoidable_damage_report_page(summary, config=config)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "MYTHIC_REPORT_ID",
    "MYTHIC_REPORT_TITLE",
    "MYTHIC_REPORT_DESCRIPTION",
    "REPORT_TITLE",
    "build_vashnik_the_malignant_avoidable_damage_report_page",
]
