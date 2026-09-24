"""Conservative, talent-aware defensive recharge estimates after recorded casts.

Static research timers are not a usability verdict. Unreplayed recovery, ambiguous
free/proc activations and unvalidated modifier combinations remain unknown. Charge
queues explicitly assume full charges at pull start; contradictory casts invalidate
pending estimates instead of displaying a ready marker after an observed reuse.
"""
from .defensive_catalog import ability_access, defensive_catalog, selected_rank


TIMING_FIELDS = {"cooldown_seconds", "max_charges"}
RECOVERY_FIELDS = {"remaining_cooldown_seconds", "cooldown_recovery_rate", "eligible_cooldown",
                   "cooldown_consumed", "activation_origin", "available_charges"}


def resolve_defensive_readiness(ability, combatant):
    _, _, research = defensive_catalog()
    sid = ability["spell_id"]
    spec = combatant.get("specID", combatant.get("specId"))
    profile = next((p for p in ability["specialization_profiles"] if p["specialization_id"] == spec), None)
    result = dict(cooldown=None, charges=None, status="unavailable", note="")

    def unknown(note):
        return {**result, "note": note}

    if ability["category"] == "consumable" or sid == 452930:
        return unknown("Item inventory, remaining uses and shared item cooldowns are not established.")
    if ability.get("track_stance"):
        return unknown("This form or stance lasts until cancelled; no defensive recharge marker is shown.")
    if not profile or not combatant.get("talentTree"):
        return unknown("Fight-time specialization and talent data are required for a readiness estimate.")
    if ability_access(ability, combatant) != "available":
        return unknown("The recorded build does not confirm access to this ability.")
    if sid == 342245:
        return unknown("Alter Time's initial activation and return must be distinguished before estimating recharge.")
    if "holy_armaments" in ability.get("shared_pool_ids", []):
        return unknown("Holy Armaments shares alternating charges with Sacred Weapon; that pool is not replayed.")

    cooldown, charges = profile.get("base_cooldown_seconds"), profile.get("base_max_charges", 1)
    operations, applied, uncertain = [], [], []
    for modifier in research["talent_modifiers"]:
        if sid not in modifier["affected_ability_spell_ids"]:
            continue
        for applies in modifier["applicability"]:
            if applies["specialization_id"] != spec:
                continue
            rank = selected_rank(combatant, applies["talent"])
            if not rank:
                continue
            for operation in modifier.get("operations", []):
                if operation.get("only_ability_spell_ids") and sid not in operation["only_ability_spell_ids"]:
                    continue
                field = operation["field"]
                if field not in TIMING_FIELDS | RECOVERY_FIELDS:
                    continue
                values = operation.get("values_by_rank", [])
                value = values[rank - 1] if rank <= len(values) else None
                if field in RECOVERY_FIELDS or (modifier.get("trigger") and field != "max_charges"):
                    uncertain.append(modifier["name"])
                elif operation["operation"] not in ("add", "multiply", "set") or not isinstance(value, (int, float)):
                    uncertain.append(modifier["name"])
                else:
                    operations.append((field, operation["operation"], value))
                    applied.append(modifier["name"])

    # Baseline resource/hit recovery exists even without an optional modifier.
    # Support/reset abilities are intentionally not displayed as defensive lanes.
    support = {a["spell_id"]: a for a in research["abilities"]}
    for rule in research["baseline_and_support_rules"]:
        if sid not in rule["affected_ability_spell_ids"] or spec not in rule["specialization_ids"]:
            continue
        trigger = support.get(rule.get("trigger_spell_id"))
        if trigger and trigger["category"] == "support" and ability_access(trigger, combatant) == "unavailable":
            continue
        uncertain.append(trigger["name"] if trigger else rule["condition"])
    if uncertain:
        return unknown("Readiness uncertain: " + "; ".join(dict.fromkeys(uncertain))
                       + ". Recovery, resets or cooldown consumption are not replayed for these effects.")
    timer_ops = [op for op in operations if op[0] == "cooldown_seconds"]
    if len(timer_ops) > 1 and any(op[1] != "add" for op in timer_ops):
        return unknown("Combined cooldown modifier stacking is not validated: " + ", ".join(dict.fromkeys(applied)) + ".")
    for field, operation, value in operations:
        current = cooldown if field == "cooldown_seconds" else charges
        if current is None:
            return unknown("The research does not establish a base recharge timer.")
        updated = current + value if operation == "add" else current * value if operation == "multiply" else value
        if field == "cooldown_seconds":
            cooldown = updated
        else:
            charges = updated
    if cooldown is None or cooldown <= 0 or charges is None or charges < 1:
        return unknown("The research does not establish a positive recharge timer and charge count.")
    note = f"{cooldown:g}s recharge from the recorded cast"
    note += " · " + ", ".join(dict.fromkeys(applied)) if applied else " · specialization base timer"
    if charges > 1:
        note += f". {int(charges)} charges; assumes full charges at pull start and sequential recharge"
    note += ". Estimated cooldown recovery only; resources, target lockouts and suitability are not inferred."
    return dict(cooldown=cooldown, charges=int(charges), status="estimated", note=note)


def add_defensive_readiness(players, combatants):
    abilities, _, _ = defensive_catalog()
    for player in players:
        pools = {}
        for lane in player["lanes"]:
            ability = abilities[lane["spellId"]]
            lane["readiness"] = resolve_defensive_readiness(ability, combatants.get(player["actorId"], {}))
            for event in lane["events"]:
                event.update(ready=None, readyBasis=None, readyNote=lane["readiness"]["note"])
            if lane["readiness"]["status"] != "estimated":
                continue
            pool = next(iter(ability.get("shared_pool_ids", [])), lane["spellId"])
            pools.setdefault(pool, []).extend((event, lane) for event in lane["events"])
        for entries in pools.values():
            pending = []
            for event, lane in sorted(entries, key=lambda item: item[0]["time"]):
                timing = lane["readiness"]
                pending = [old for old in pending if old["ready"] > event["time"]]
                if len(pending) >= timing["charges"]:
                    # A cast is stronger evidence than a nominal cooldown prediction.
                    # Restart the pool estimate at this observed use; don't fabricate
                    # an exact reset timestamp or carry an impossible queue forward.
                    for old in pending:
                        old.update(ready=None, readyBasis=None,
                                   readyNote="A recorded reuse occurred before the predicted recharge; this estimate was withdrawn.")
                    pending = []
                event["ready"] = round(max(event["time"], pending[-1]["ready"] if pending else 0)
                                       + timing["cooldown"], 3)
                event["readyBasis"] = "Estimated charge replenished" if timing["charges"] > 1 else "Estimated ready"
                pending.append(event)
