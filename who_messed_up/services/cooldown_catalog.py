"""Versioned research catalogue and conservative, rank-aware cooldown timing.

Keep original research/provenance in data; never infer talents from cast spacing.
"""
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "cooldown_coverage"


@lru_cache(maxsize=1)
def coverage_catalog():
    healers = json.loads((DATA / "midnight-12.1-healing-cooldowns.json").read_text(encoding="utf-8"))
    encounters = json.loads((DATA / "midnight-12.1-boss-abilities.json").read_text(encoding="utf-8"))
    spells = {c["spell_id"]: {**c, "specId": s["specialization_id"], "specName": s["name"]}
              for s in healers["specializations"] for c in s["cooldowns"]}
    bosses = {b["boss_id"]: b for r in encounters["raids"] for b in r["bosses"]}
    return spells, bosses


@lru_cache(maxsize=1)
def talent_entry_map():
    return json.loads((DATA / "talent-entry-map.json").read_text(encoding="utf-8"))["entries"]


def talent_ranks(combatant):
    """Only spell IDs are comparable to the research; node IDs are not spell IDs."""
    result = {}
    for node in combatant.get("talentTree") or []:
        spell = node.get("spellID") or node.get("spellId")
        if not spell:
            entry = talent_entry_map().get(str(node.get("id")), {})
            if node.get("nodeID") == entry.get("nodeId"):
                spell = entry.get("spellId")
        if spell and node.get("rank", 0) > 0:
            result[int(spell)] = int(node["rank"])
    return result


def resolve_timing(spell, combatant):
    ranks = talent_ranks(combatant)
    cooldown = spell["cooldown"]["base_seconds"]
    duration = spell["duration"]["base_seconds"]
    basis = "Base timing; talent information unavailable" if not ranks else "Base timing"
    for variant in spell["cooldown"]["static_variants"]:
        if not all(t in ranks for t in variant["required_talents"]):
            continue
        if any(t in ranks for t in variant.get("excluded_talent_spell_ids", [])):
            continue
        if any(ranks.get(int(t)) != rank for t, rank in variant.get("required_talent_ranks", {}).items()):
            continue
        cooldown = variant["cooldown_seconds"]
        if variant.get("duration_seconds") is not None:
            duration = variant["duration_seconds"]
        basis = variant["label"]
        if variant["status"] != "supported":
            basis += "; duration unresolved, nominal base shown"
    # These spells have no fixed base window; show the build's documented
    # throughput sequence, never a storage deadline or initial cast time.
    if spell["spell_id"] in (370553, 472433, 120517):
        effects = [effect for effect in spell["duration"]["secondary_effects"]
                   if effect.get("requires_talent_spell_id") in ranks]
        if effects:
            duration = effects[0]["seconds"]
            basis += "; " + effects[0]["kind"].replace("_", " ")
    dynamic_ids = set(spell["cooldown"].get("dynamic_recovery_talent_spell_ids", []))
    dynamic_ids.update(m["talent_spell_id"] for m in spell["modifiers"] if m["kind"] == "dynamic_cooldown")
    dynamic = bool(dynamic_ids.intersection(ranks)) if ranks else spell["cooldown"]["dynamic_recovery_possible"]
    if dynamic:
        basis += "; dynamic recovery may make this ready earlier"
    return cooldown, duration, basis, dynamic


def ability_display(spell):
    return {
        "spellId": spell["spell_id"], "name": spell["name"],
        "icon": "/cooldown-coverage/" + spell["icon"]["file"],
        "description": spell.get("description") or spell.get("inclusion_reason", ""),
    }
