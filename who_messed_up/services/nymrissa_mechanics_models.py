"""Mythic Nymrissa report vocabulary; shared mechanics rows carry the evidence."""
from .mechanics_models import MechanicsSummary

REPORT_ID = "nymrissa-wavecaller-mythic-mechanics"
REPORT_TITLE = "Mythic Nymrissa Wavecaller - Mechanics"
REPORT_DESCRIPTION = "Find who popped Frost Orbs during the Abyssal Rain channel, including one second before and after."
REPORT_DEFAULT_FIGHT = "Nymrissa Wavecaller"
VIEWS = {"overlaps": "Orb pops during Rain channel", "rain": "Rain channel windows", "orbs": "All orb pops"}
RAIN_CHANNEL = 1260837
RAIN_DAMAGE = 1260843
FROST_ORB = 1313448
BUFFER_MS = 1000
# Fallback only: channel damage pulses every second, with timestamp jitter.
RAIN_PULSE_GAP_MS = 1500
REPORT_FOOTNOTES = (
    "Flagged pops occur during the observed Abyssal Rain channel, or within one second before or after. The lingering raid DoT is excluded. Timings come from each pull, not a fixed boss schedule.",
    "Channel boundaries use the boss's logged channel buff application and removal. If a complete pair is missing, the report labels a fallback window using only direct Rain damage pulses, grouping hits at most 1.5 seconds apart. Such windows can be shorter than the full channel; outside a recorded window does not mean a pop was safe.",
    "The player struck by a non-periodic Frost Orb impact is the soaker. Immune and fully absorbed impacts count; subsequent DoT ticks and aura refreshes do not. Separate impacts count separately even when almost simultaneous.",
    "Frost Burst damages the raid but does not identify the soaker. The central bubble's Pop! and unattended orbs' Shatter are separate mechanics and are not counted as player orb pops. Flags identify timing to review, not an automatic mistake score.",
)
NymrissaMechanicsSummary = MechanicsSummary
