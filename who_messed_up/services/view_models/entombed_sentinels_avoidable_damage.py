"""View-model builder for the Heroic and Mythic Entombed Sentinels avoidable damage report."""
from __future__ import annotations

from dataclasses import replace

from ..boss_manifest_types import normalize_manifest_difficulty
from ..avoidable_damage import AvoidableDamageSummary
from ..entombed_sentinels_avoidable_damage import REPORT_DEFAULT_FIGHT
from .avoidable_damage import AvoidableDamagePageConfig, build_avoidable_damage_report_page

REPORT_ID = "entombed-sentinels-avoidable-damage"
REPORT_TITLE = "Heroic Entombed Sentinels - Avoidable Damage Report"
REPORT_DESCRIPTION = "Track avoidable damage taken during Heroic Entombed Sentinels pulls."
MYTHIC_REPORT_ID = "entombed-sentinels-avoidable-damage-mythic"
MYTHIC_REPORT_TITLE = "Mythic Entombed Sentinels - Avoidable Damage Report"
MYTHIC_REPORT_DESCRIPTION = "Avoidable Damage Report for Mythic Entombed Sentinels."
REPORT_FOOTNOTES = [
    "Additional Warcraft Logs reports can be combined when the same encounter spans multiple log reports.",
]

REPORT_CONFIG = AvoidableDamagePageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)

MYTHIC_REPORT_FOOTNOTES = [
    *REPORT_FOOTNOTES,
    "Protovenom Eruption records exposure to a failed collision, not proof that the player hit caused it.",
    "Shifting Protovenom carrier damage, Toxic Droplet soaks, and Noxious Blast raid damage are not individual avoidable hits.",
]

MYTHIC_REPORT_CONFIG = replace(
    REPORT_CONFIG,
    report_id=MYTHIC_REPORT_ID,
    title=MYTHIC_REPORT_TITLE,
    footnotes=tuple(MYTHIC_REPORT_FOOTNOTES),
)


def build_entombed_sentinels_avoidable_damage_report_page(
    summary: AvoidableDamageSummary,
    *,
    difficulty: str | int | None = None,
):
    config = (
        MYTHIC_REPORT_CONFIG
        if normalize_manifest_difficulty(difficulty) == "mythic"
        else REPORT_CONFIG
    )
    return build_avoidable_damage_report_page(summary, config=config)


__all__ = [
    "MYTHIC_REPORT_ID",
    "MYTHIC_REPORT_TITLE",
    "MYTHIC_REPORT_DESCRIPTION",
    "MYTHIC_REPORT_FOOTNOTES",
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_entombed_sentinels_avoidable_damage_report_page",
]
