"""Mythic Twin Fangs vocabulary for the shared mechanics report contract."""
from .mechanics_models import MechanicsSummary

REPORT_ID = "the-twin-fangs-mythic-mechanics"
REPORT_TITLE = "Mythic The Twin Fangs - Mechanics"
REPORT_DESCRIPTION = "Review add damage, orb pickups, wave contacts and matched venom gains, shield-breaking CCs, and successful add interrupts."
REPORT_DEFAULT_FIGHT = "The Twin Fangs"
VIEWS = {"adds": "Add damage", "orbs": "Orb pickups", "waves": "Wave Contacts",
         "wave_stacks": "Wave Contact Stacks",
         "shields": "Orb shield CCs", "interrupts": "Add interrupts"}
GLOBULE = 1289201
WAVE = 1292807
ETERNAL_VENOM = 1290336
WAVE_STACK_WINDOW_MS = 100
ADD_NAMES = frozenset({"Spawn of Vexhul", "Broodling of Ithraz"})
BULWARK_NAME = "Barbed Bulwark"
BULWARK_SHIELD = 1303378
INTERRUPTED_SPELLS = {1308385: "Visceral Burst", 1291478: "Corrosive Spit"}
# Control auras verified in the Mythic research log, not cast or damage IDs.
SHIELD_CC_ABILITIES = {
    99: "Incapacitating Roar", 105421: "Blinding Light", 8122: "Psychic Scream",
    119381: "Leg Sweep", 5484: "Howl of Terror", 31661: "Dragon's Breath",
    132168: "Shockwave", 853: "Hammer of Justice", 118905: "Capacitor Totem",
    3355: "Freezing Trap", 179057: "Chaos Nova", 82691: "Ring of Frost",
    118345: "Pulverize", 115078: "Paralysis", 2094: "Blind",
}
SHIELD_CC_WINDOW_MS = 100
INTERRUPT_ABILITIES = {
    31935: "Avenger's Shield", 147362: "Counter Shot", 2139: "Counterspell",
    93985: "Skull Bash", 57994: "Wind Shear", 97547: "Solar Beam", 96231: "Rebuke",
    183752: "Disrupt", 220543: "Silence", 1766: "Kick", 116705: "Spear Hand Strike",
    19647: "Spell Lock", 351338: "Quell",
}
REPORT_FOOTNOTES = (
    "Add damage includes effective damage to Spawn of Vexhul and Broodlings of Ithraz, with pets credited to their owners. Boss damage is excluded. Lifetimes without a summon begin at the first observed event.",
    "Orb pickups count direct Caustic Globule soak impacts, including immune and fully absorbed impacts. An immune pickup need not grant a venom stack. Unsoaked ruptures and raid-wide Eternal Venom applications do not identify a soaker and are excluded.",
    "Wave contacts count Stir the Depths debuff applications, not damage ticks. Touching a wave can grant Eternal Venom without dealing damage when the player leaves within one second. Aura refreshes, removals, raid pulses and periodic damage are excluded.",
    "Wave Contact Stacks counts contacts with a matching Eternal Venom application or stack-increase event on the same player within 100ms either side, allowing combat-log ordering differences. Nearest matches are one-to-one: one gain cannot credit two contacts. Each matched contact counts once, not its resulting venom stack total. This is timing-based association; concurrent stack sources cannot always be distinguished. Contacts without a matching gain remain only in Wave Contacts.",
    "Contacts identify players to review; logs cannot establish intent. Counts are observed pickups and wave contacts, not a reconstruction of total Eternal Venom stacks.",
    "Orb shields are logged as Barbed Bulwark. Credit requires a verified CC aura followed within 100ms by removal of a previously observed shield on the same instance, with absorb remaining. This is timing-based attribution. Ambiguous or unsupported removals stay in the evidence table and do not inflate player bars. Each shield counts once; one area CC can break several shields.",
    "Successful interrupts use explicit interrupt events, not kick casts. Each row identifies the target add instance within its pull; pets and totems are credited to their owners. Missing instance IDs are labeled unavailable. Instance numbers are log identifiers, not room positions or raid-marker assignments.",
)
TwinFangsMechanicsSummary = MechanicsSummary
