"""Mythic Nymrissa report vocabulary; shared mechanics rows carry the evidence."""
from .mechanics_models import MechanicsSummary

REPORT_ID = "nymrissa-wavecaller-mythic-mechanics"
REPORT_TITLE = "Mythic Nymrissa Wavecaller - Mechanics"
REPORT_DESCRIPTION = "Find who popped Frost Orbs during Abyssal Rain damage, including one second before and after."
REPORT_DEFAULT_FIGHT = "Nymrissa Wavecaller"
VIEWS = {"overlaps": "Orb pops during Rain", "rain": "Rain damage windows", "orbs": "All orb pops"}
RAIN_DAMAGE = 1260843
FROST_ORB = 1313448
BUFFER_MS = 1000
# Rain ticks every two seconds. Allow timestamp jitter, without bridging long gaps.
RAIN_TICK_GAP_MS = 2500
REPORT_FOOTNOTES = (
    "Flagged pops fall between the first and last logged Abyssal Rain damage hits (including the lingering DoT), or within one second before or after. Timings come from each pull, not a fixed boss schedule.",
    "Rain damage hits separated by at most 2.5 seconds form one continuous window, allowing for the two-second DoT tick interval. Windows stop at the last observed hit; missing events or a wipe can shorten them. Outside a recorded window does not mean a pop was safe.",
    "The player struck by a non-periodic Frost Orb impact is the soaker. Immune and fully absorbed impacts count; subsequent DoT ticks and aura refreshes do not. Separate impacts count separately even when almost simultaneous.",
    "Frost Burst damages the raid but does not identify the soaker. The central bubble's Pop! and unattended orbs' Shatter are separate mechanics and are not counted as player orb pops. Flags identify timing to review, not an automatic mistake score.",
)
NymrissaMechanicsSummary = MechanicsSummary
