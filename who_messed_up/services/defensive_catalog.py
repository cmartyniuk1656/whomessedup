"""Adapt the supplied defensive research to observed usage, without scoring readiness.

Talent access uses the fight's selected entry AND node. Missing build/inventory
evidence stays unknown. Candidate aliases are not silently treated as casts.
"""
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "defensives"


@lru_cache(maxsize=1)
def defensive_catalog():
    research = json.loads((DATA / "defensives.json").read_text(encoding="utf-8"))
    supplemental = json.loads((DATA / "supplemental-abilities.json").read_text(encoding="utf-8"))
    research["abilities"].extend(supplemental["abilities"])
    research["talent_modifiers"].extend(supplemental["talent_modifiers"])
    consumables = json.loads((DATA / "consumables.json").read_text(encoding="utf-8"))
    abilities = {a["spell_id"]: a for a in research["abilities"] if a["category"] != "support"}
    abilities.update({a["spell_id"]: a for a in consumables["abilities"]})
    return abilities, {s["specialization_id"]: s for s in research["specializations"]}, research


def selected_rank(combatant, talent):
    for node in combatant.get("talentTree") or []:
        if node.get("nodeID") != talent.get("node_id"):
            continue
        mapped = defensive_talent_entries().get(str(node.get("id")), {})
        # The supplied research uses trait-definition IDs where WCL logs contain
        # node-entry IDs. Never infer choices from a shared node alone.
        if node.get("id") == talent.get("entry_id") or (mapped.get("nodeId") == node.get("nodeID")
                and mapped.get("spellId") == talent.get("spell_id")
                and mapped.get("definitionId") == talent.get("entry_id")):
            return min(int(node.get("rank", 0)), talent.get("maximum_rank", 1))
    return 0


@lru_cache(maxsize=1)
def defensive_talent_entries():
    return json.loads((DATA / "talent-entry-map.json").read_text(encoding="utf-8"))["entries"]


def ability_access(ability, combatant):
    if ability["category"] == "consumable":
        return "unknown"
    spec = combatant.get("specID", combatant.get("specId"))
    profile = next((p for p in ability["specialization_profiles"] if p["specialization_id"] == spec), None)
    if not profile:
        return "unavailable" if spec else "unknown"
    unknown = False
    for condition in profile["access"]["all_of"]:
        kind = condition["kind"]
        if kind == "baseline":
            continue
        if kind == "selected_talent":
            if not combatant.get("talentTree"):
                unknown = True
            elif selected_rank(combatant, condition["talent"]) < condition.get("required_rank", 1):
                return "unavailable"
        elif kind == "talent_not_selected":
            # Locate the replacement's access node rather than guessing from spell IDs.
            abilities, _, _ = defensive_catalog()
            nodes = [c["talent"] for a in abilities.values() for p in a["specialization_profiles"]
                     if p["specialization_id"] == spec for c in p["access"]["all_of"]
                     if c["kind"] == "selected_talent" and c["talent"]["spell_id"] == condition["spell_id"]]
            if any(selected_rank(combatant, node) for node in nodes):
                return "unavailable"
            if not nodes or not combatant.get("talentTree"):
                unknown = True
        else:
            unknown = True
    return "unknown" if unknown else "available"


def defensive_display(ability, combatant):
    _, specs, research = defensive_catalog()
    duration = ability["duration"].get("nominal_seconds")
    modifiers = []
    for modifier in research["talent_modifiers"]:
        if ability["spell_id"] not in modifier["affected_ability_spell_ids"]:
            continue
        for applies in modifier["applicability"]:
            if applies["specialization_id"] != combatant.get("specID", combatant.get("specId")):
                continue
            rank = selected_rank(combatant, applies["talent"])
            if not rank:
                continue
            modifiers.append(modifier["name"] + ": " + modifier["summary"])
            # Nominal window only. Conditional effects and recovery aren't replayed.
            if modifier.get("trigger") or duration is None:
                continue
            for operation in modifier.get("operations", []):
                if operation["field"] != "duration_seconds" or (operation.get("only_ability_spell_ids")
                        and ability["spell_id"] not in operation["only_ability_spell_ids"]):
                    continue
                values = operation.get("values_by_rank", [])
                value = values[rank - 1] if rank <= len(values) else None
                if isinstance(value, (int, float)):
                    if operation["operation"] == "add": duration += value
                    elif operation["operation"] == "multiply": duration *= value
                    elif operation["operation"] == "set": duration = value
    category = "consumable" if ability["spell_id"] == 452930 else ability["category"]
    return dict(spellId=ability["spell_id"], name=ability["name"], category=category,
                icon="/defensives/" + ability["icon"]["file"], description=ability["summary"],
                duration=duration, access=ability_access(ability, combatant), modifiers=modifiers,
                spec=specs.get(combatant.get("specID", combatant.get("specId")), {}).get("name", "Unknown specialization"))
