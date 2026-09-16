"""View-model builder for the Heroic and Mythic Entombed Sentinels death report."""
from __future__ import annotations

from dataclasses import replace

from ..boss_manifest_types import normalize_manifest_difficulty
from ..death_reports import DeathReportSummary
from ..entombed_sentinels_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "entombed-sentinels-deaths"
REPORT_TITLE = "Heroic Entombed Sentinels - Death Report"
REPORT_DESCRIPTION = "Death report for Heroic Entombed Sentinels."
MYTHIC_REPORT_ID = "entombed-sentinels-deaths-mythic"
MYTHIC_REPORT_TITLE = "Mythic Entombed Sentinels - Death Report"
MYTHIC_REPORT_DESCRIPTION = "Death Report for Mythic Entombed Sentinels."
REPORT_FOOTNOTES: list[str] = []

REPORT_CONFIG = DeathReportPageConfig(
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


def build_entombed_sentinels_deaths_report_page(
    summary: DeathReportSummary,
    *,
    difficulty: str | int | None = None,
):
    config = (
        MYTHIC_REPORT_CONFIG
        if normalize_manifest_difficulty(difficulty) == "mythic"
        else REPORT_CONFIG
    )
    return build_death_report_page(summary, config=config)


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
    "build_entombed_sentinels_deaths_report_page",
]
