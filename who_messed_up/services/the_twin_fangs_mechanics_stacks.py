"""Match wave contacts to distinct Eternal Venom gains within combat-log jitter.

Counts are one stack-associated contact per matched application, not the total
venom stack level. Nearest one-to-one matching prevents reusing one gain for
multiple contacts; removal/refresh/damage events never establish a gain.
"""
from .mechanics_events import ability, timestamp
from .mechanics_models import MechanicDetail
from .the_twin_fangs_mechanics_events import contact_events
from .the_twin_fangs_mechanics_models import ETERNAL_VENOM, WAVE_STACK_WINDOW_MS


def build_wave_contact_stacks(ctx):
    contacts = list(contact_events(ctx, waves=True))
    gains, seen = [], set()
    for event in ctx.events("venom", {ETERNAL_VENOM}, friendly=True):
        if event.get("type") not in {"applydebuff", "applydebuffstack"}:
            continue
        if not ctx.fight.start <= timestamp(event) <= ctx.fight.end:
            continue
        if event.get("sourceID") in ctx.players or event.get("sourceID") in ctx.owners:
            continue
        signature = (timestamp(event), event.get("targetID"), ability(event), event.get("type"), event.get("stack"))
        if signature not in seen:
            gains.append(event)
            seen.add(signature)
    candidates = sorted(
        (abs(timestamp(gain) - timestamp(contact)), ci, gi)
        for ci, contact in enumerate(contacts) for gi, gain in enumerate(gains)
        if contact.get("targetID") == gain.get("targetID")
        and abs(timestamp(gain) - timestamp(contact)) <= WAVE_STACK_WINDOW_MS
    )
    matches, used = {}, set()
    for _, ci, gi in candidates:
        if ci not in matches and gi not in used:
            matches[ci] = gains[gi]
            used.add(gi)
    rows = []
    for ci, contact in enumerate(contacts):
        if ci not in matches:
            continue
        gain = matches[ci]
        player = ctx.name(contact["targetID"])
        row = ctx.row(timestamp(contact), len(rows) + 1, "Stir the Depths")
        row.players["players"] = [player]
        row.soak_counts = {player: 1}
        row.values["stacks"] = 1
        row.details = [
            MechanicDetail("Wave contact", player, timestamp(contact), "Stir the Depths debuff applied."),
            MechanicDetail("Matched venom gain", player, timestamp(gain),
                           f"Eternal Venom {'applied' if gain['type'] == 'applydebuff' else 'stack increased'} "
                           f"{abs(timestamp(gain) - timestamp(contact)):.0f}ms "
                           f"{'after' if timestamp(gain) >= timestamp(contact) else 'before'} the contact. "
                           "One matching gain is counted once; timing associates it with this contact."),
        ]
        rows.append(row)
    return rows
