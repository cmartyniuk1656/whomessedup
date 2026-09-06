"""View-model builder for the Heroic Ula'tek death report."""
from __future__ import annotations

from ..death_reports import DeathReportSummary
from ..ula_tek_deaths import REPORT_DEFAULT_FIGHT
from .death_reports import DeathReportPageConfig, build_death_report_page

REPORT_ID = "ula-tek-deaths"
REPORT_TITLE = "Heroic Ula'tek - Death Report"
REPORT_DESCRIPTION = "Death report for Heroic Ula'tek."
REPORT_FOOTNOTES = [
    "Caustic Waves, Falling Debris, Virulent Spit, clutch impacts, and non-tank Desperate Thrash killing blows are avoidable.",
    "Deadly Venom is unscored because assigned movement between sides can require players to cross it.",
    "Direct Calcified Corpse damage marks a failed Serpent's Bite rescue; raid-wide corpse toxin remains a team failure.",
    "Tank-uptime failures, missed interrupts, uncontrolled Viper damage, and mixed-distance mechanics are not assigned to their victims.",
]
REPORT_CONFIG = DeathReportPageConfig(
    report_id=REPORT_ID,
    title=REPORT_TITLE,
    footnotes=tuple(REPORT_FOOTNOTES),
)


def build_ula_tek_deaths_report_page(summary: DeathReportSummary):
    return build_death_report_page(summary, config=REPORT_CONFIG)


__all__ = [
    "REPORT_DEFAULT_FIGHT",
    "REPORT_DESCRIPTION",
    "REPORT_FOOTNOTES",
    "REPORT_ID",
    "REPORT_TITLE",
    "build_ula_tek_deaths_report_page",
]
