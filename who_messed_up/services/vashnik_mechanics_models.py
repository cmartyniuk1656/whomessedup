"""Vashnik mechanics vocabulary and report metadata; evidence uses shared rows."""
from .mechanics_models import MechanicsSummary

REPORT_ID = "vashnik-the-malignant-mythic-mechanics"
REPORT_TITLE = "Mythic Vashnik the Malignant - Mechanics"
REPORT_DESCRIPTION = "Review totem waves, infections, add control, and bile soaks."
REPORT_DEFAULT_FIGHT = "Vashnik the Malignant"
VIEWS = {
    "totems": "Totems & Plague Waves",
    "froth": "Plague Froth Spreading",
    "dispels": "Exploding Infection Dispels",
    "stygian": "Stygian Infection Healing",
    "adds": "Living Venom Control",
    "bile": "Catalytic Bile Soaks",
}
REPORT_FOOTNOTES = (
    "Totem deaths have no player kill credit. Wave associations use observed Froth removals within 10 seconds, with 250 ms of timestamp tolerance. A single candidate is labeled inferred, never confirmed; most clears belong to a five-player wave group. No inferred credit does not mean no clears.",
    "Early Froth releases can occur on death. Surviving totems and missing deaths at encounter end remain unresolved; a totem removed after Malignance is still a detonation. Waves released before a totem spawns can clear it.",
    "Froth splash on unmarked players identifies exposure, not which carrier caused it. Marked players may also take overlapping splash. Fully absorbed hits count; immunity-only events do not.",
    "Only explicit dispel events receive healer credit. Explosion spacing is context, not a fastest-dispel score. Unmatched dispels remain visible without invented applications.",
    "Stygian contributions use the logged healer on heal-absorb events. Clear averages exclude deaths, missing removals, encounter cleanup, and removals without nearby absorb-healing evidence. Burst victims do not identify which infected player created the impact.",
    "Add lifetimes start at a logged summon or the first instance-specific signal. Burning summon packets may be absent. Damage includes owned pets, separates health and shield damage, and excludes post-death residue. A missing death is not a kill. Burning explosions less than three seconds apart are flagged for review, not automatically scored as mistakes.",
    "Bile hits show participation, not unique circles. Missed-soak bursts group damage within 100 ms; simultaneous failures may merge. Missing impact evidence is not proof of a missed soak.",
)

FROTH = 1281913
FROTH_DAMAGE = 1281925
PLAGUE_WAVE = 1295798
IMBIBE = 1284663
TOTEM_SUMMON = 1306820
MALIGNANCE = 1304459
EXPLODING = 1295173
EXPLOSION = 1295209
STYGIAN = 1294994
STYGIAN_BURST = 1302489
CATALYST = 1282509
BILE = 1282602
MISSED_BILE = 1282616
SURGE = 1285979
LEAK = 1280189
COATING = 1312366
ADD_NAMES = {"Burning Venom", "Shrouded Venom", "Clotting Venom"}

VashnikMechanicsSummary = MechanicsSummary
