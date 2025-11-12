"""
Shared constants and helpers used across backend report services.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Literal

from ..api import Fight, filter_fights, get_token_from_client

# Role/Spec metadata ---------------------------------------------------------

SPEC_ROLE_BY_CLASS: Dict[Tuple[str, str], str] = {
    ("DeathKnight", "Blood"): "Tank",
    ("DeathKnight", "Frost"): "Melee",
    ("DeathKnight", "Unholy"): "Melee",
    ("DemonHunter", "Havoc"): "Melee",
    ("DemonHunter", "Vengeance"): "Tank",
    ("Druid", "Balance"): "Ranged",
    ("Druid", "Feral"): "Melee",
    ("Druid", "Guardian"): "Tank",
    ("Druid", "Restoration"): "Healer",
    ("Evoker", "Devastation"): "Ranged",
    ("Evoker", "Preservation"): "Healer",
    ("Evoker", "Augmentation"): "Ranged",
    ("Hunter", "Beast Mastery"): "Ranged",
    ("Hunter", "Marksmanship"): "Ranged",
    ("Hunter", "Survival"): "Melee",
    ("Mage", "Arcane"): "Ranged",
    ("Mage", "Fire"): "Ranged",
    ("Mage", "Frost"): "Ranged",
    ("Monk", "Brewmaster"): "Tank",
    ("Monk", "Mistweaver"): "Healer",
    ("Monk", "Windwalker"): "Melee",
    ("Paladin", "Holy"): "Healer",
    ("Paladin", "Protection"): "Tank",
    ("Paladin", "Retribution"): "Melee",
    ("Priest", "Discipline"): "Healer",
    ("Priest", "Holy"): "Healer",
    ("Priest", "Shadow"): "Ranged",
    ("Rogue", "Assassination"): "Melee",
    ("Rogue", "Outlaw"): "Melee",
    ("Rogue", "Subtlety"): "Melee",
    ("Shaman", "Elemental"): "Ranged",
    ("Shaman", "Enhancement"): "Melee",
    ("Shaman", "Restoration"): "Healer",
    ("Warlock", "Affliction"): "Ranged",
    ("Warlock", "Demonology"): "Ranged",
    ("Warlock", "Destruction"): "Ranged",
    ("Warrior", "Arms"): "Melee",
    ("Warrior", "Fury"): "Melee",
    ("Warrior", "Protection"): "Tank",
}

CLASS_DEFAULT_ROLE: Dict[str, str] = {
    "Mage": "Ranged",
    "Warlock": "Ranged",
    "Hunter": "Ranged",
    "Priest": "Ranged",
    "Shaman": "Ranged",
    "Evoker": "Ranged",
    "DemonHunter": "Melee",
    "DeathKnight": "Melee",
    "Druid": "Melee",
    "Monk": "Melee",
    "Paladin": "Melee",
    "Rogue": "Melee",
    "Warrior": "Melee",
}

ROLE_UNKNOWN = "Unknown"

ROLE_PRIORITY: Dict[str, int] = {
    "Tank": 0,
    "Healer": 1,
    "Melee": 2,
    "Ranged": 3,
    ROLE_UNKNOWN: 4,
}

NEXUS_PHASE_LABELS: Dict[str, str] = {
    "full": "Full Fight",
    "1": "Stage One: Oath Breakers",
    "2": "Stage Two: Rider's of the Dark",
    "3": "Intermission One: Nexus Descent",
    "4": "Intermission Two: King's Hunger",
    "5": "Stage Three: World in Twilight",
}

DIMENSIUS_PHASE_LABELS: Dict[str, str] = {
    "full": "Full Fight",
    "1": "Stage One: Critical Mass",
    "2": "Intermission: Event Horizon",
    "3": "Stage Two: The Dark Heart",
    "4": "Stage Three: Singularity",
}

PHASE_LABEL_PRESETS: Dict[str, Dict[str, str]] = {
    "nexus": NEXUS_PHASE_LABELS,
    "dimensius": DIMENSIUS_PHASE_LABELS,
}
DEFAULT_PHASE_PROFILE = "nexus"

LIVING_MASS_NAME = "Living Mass"
DIMENSIUS_LIVING_MASS_FILTER = f'encounterPhase = 1 and target.name = "{LIVING_MASS_NAME}"'
DIMENSIUS_INITIAL_ADD_IGNORE_COUNT = 6

# Exceptions -----------------------------------------------------------------


class TokenError(RuntimeError):
    pass


class FightSelectionError(RuntimeError):
    pass


# Ghost miss helpers ---------------------------------------------------------

GhostMissMode = Literal["first_per_set", "first_per_pull", "all"]
DEFAULT_GHOST_MISS_MODE: GhostMissMode = "first_per_set"
GHOST_SET_WINDOW_MS = 5000
_GHOST_MODE_ALIASES: Dict[str, GhostMissMode] = {
    "first_per_set": "first_per_set",
    "firstperset": "first_per_set",
    "per_set": "first_per_set",
    "perset": "first_per_set",
    "set_first": "first_per_set",
    "setfirst": "first_per_set",
    "first_set": "first_per_set",
    "firstset": "first_per_set",
    "first_per_pull": "first_per_pull",
    "firstperpull": "first_per_pull",
    "per_pull": "first_per_pull",
    "perpull": "first_per_pull",
    "pull_first": "first_per_pull",
    "pullfirst": "first_per_pull",
    "first_pull": "first_per_pull",
    "firstpull": "first_per_pull",
    "all": "all",
    "all_hits": "all",
    "allhits": "all",
    "all_misses": "all",
    "allmisses": "all",
    "every": "all",
}


def normalize_ghost_miss_mode(value: Any) -> GhostMissMode:
    """
    Normalize user-provided ghost miss mode values into the canonical set.
    """
    if isinstance(value, bool):
        return "first_per_pull" if value else "all"
    if isinstance(value, (int, float)) and value in (0, 1):
        return "first_per_pull" if int(value) == 1 else "all"
    if value is None:
        return DEFAULT_GHOST_MISS_MODE
    if isinstance(value, str):
        cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        normalized = _GHOST_MODE_ALIASES.get(cleaned)
        if normalized:
            return normalized
    raise ValueError(f"Invalid ghost miss mode: {value}")


# Shared utility helpers -----------------------------------------------------


def _sanitize_report_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Report code cannot be empty.")
    lowered = text.lower()
    if "/reports/" in lowered:
        parts = text.split("/reports/", 1)
        if len(parts) == 2:
            remainder = parts[1]
            remainder = remainder.split("/", 1)[0]
            remainder = remainder.split("?", 1)[0]
            cleaned = remainder.strip()
            if cleaned:
                return cleaned
    return text


def _extract_spec(entry: Dict[str, Any]) -> Optional[str]:
    specs = entry.get("specs") or []
    for spec_obj in specs:
        spec = spec_obj.get("spec")
        if spec:
            return spec
    icon = entry.get("icon")
    if icon and "-" in icon:
        return icon.split("-", 1)[1].replace("_", " ")
    return None


def _infer_player_roles(details: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Optional[str]]]:
    roles: Dict[str, str] = {}
    specs: Dict[str, Optional[str]] = {}

    def register(entry: Dict[str, Any], role: str) -> None:
        name = entry.get("name")
        if not name:
            return
        spec = _extract_spec(entry)
        specs[name] = spec
        roles[name] = role

    for category, role in (("tanks", "Tank"), ("healers", "Healer")):
        for entry in details.get(category, []):
            register(entry, role)

    for entry in details.get("dps", []):
        name = entry.get("name")
        if not name:
            continue
        spec = _extract_spec(entry)
        class_name = entry.get("type")
        inferred_role = None
        if spec and class_name:
            inferred_role = SPEC_ROLE_BY_CLASS.get((class_name, spec))
        if inferred_role is None and class_name:
            inferred_role = CLASS_DEFAULT_ROLE.get(class_name)
        if inferred_role is None:
            inferred_role = ROLE_UNKNOWN
        register(entry, inferred_role)

    return roles, specs


def _players_from_details(details: Dict[str, Any]) -> List[str]:
    players: List[str] = []
    for category in ("tanks", "healers", "dps"):
        for entry in details.get(category, []):
            name = entry.get("name")
            if name:
                players.append(name)
    return players


def _resolve_token(
    token: Optional[str], client_id: Optional[str], client_secret: Optional[str]
) -> str:
    if token:
        return token
    fetched = get_token_from_client(client_id, client_secret)
    if not fetched:
        raise TokenError("Unable to retrieve bearer token. Provide --token or client credentials.")
    return fetched


def _select_fights(
    fights: List[Fight],
    *,
    name_filter: Optional[str],
    fight_ids: Optional[Iterable[int]],
) -> List[Fight]:
    chosen = filter_fights(fights, name_filter)
    if fight_ids:
        id_set = {int(fid) for fid in fight_ids}
        chosen = [fight for fight in chosen if fight.id in id_set]
    if not chosen:
        raise FightSelectionError("No fights matched the supplied criteria.")
    return chosen


def _normalize_phase_ids(phases: Optional[Iterable[str]], *, phase_labels: Dict[str, str]) -> List[str]:
    normalized: List[str] = []
    seen: Set[str] = set()
    if phases:
        for raw in phases:
            if raw is None:
                continue
            text_value = str(raw).strip()
            if not text_value:
                continue
            lowered = text_value.lower()
            if lowered in {"full", "all"} and "full" in phase_labels:
                key = "full"
            else:
                try:
                    phase_int = int(lowered)
                except ValueError:
                    continue
                key = str(phase_int)
            if key not in phase_labels or key in seen:
                continue
            normalized.append(key)
            seen.add(key)
    if not normalized:
        if "full" in phase_labels:
            normalized.append("full")
        else:
            first_key = next(iter(phase_labels.keys()), None)
            if first_key:
                normalized.append(first_key)
    return normalized


def _resolve_phase_labels(profile: Optional[str]) -> Dict[str, str]:
    if profile:
        key = str(profile).strip().lower()
    else:
        key = DEFAULT_PHASE_PROFILE
    if key not in PHASE_LABEL_PRESETS:
        key = DEFAULT_PHASE_PROFILE
    return PHASE_LABEL_PRESETS[key]


def _extract_target_key(event: Dict[str, Any]) -> Optional[Tuple[Any, ...]]:
    target = event.get("target")
    guid = None
    instance = None
    if isinstance(target, dict):
        guid = target.get("guid") or target.get("id")
        instance = target.get("instance")
    target_id = event.get("targetID")
    instance_id = event.get("targetInstance") or event.get("targetInstanceID")
    if any(component is not None for component in (guid, target_id, instance, instance_id)):
        return (guid, target_id, instance, instance_id)
    return None


def _resolve_event_source_player(
    event: Dict[str, Any],
    actor_names: Dict[int, str],
    actor_owners: Dict[int, Optional[int]],
) -> Tuple[Optional[str], Optional[int]]:
    source = event.get("source")
    raw_name: Optional[str] = None
    raw_id: Optional[int] = None
    if isinstance(source, dict):
        raw_name = source.get("name") or raw_name
        candidate_id = source.get("guid") or source.get("id")
        try:
            raw_id = int(candidate_id)
        except (TypeError, ValueError):
            raw_id = None
    if raw_id is None:
        candidate_id = event.get("sourceID")
        try:
            raw_id = int(candidate_id)
        except (TypeError, ValueError):
            raw_id = None
    if not raw_name:
        raw_name = event.get("sourceName")

    resolved_id = raw_id
    if raw_id is not None:
        current = raw_id
        seen: Set[int] = set()
        while True:
            owner = actor_owners.get(current)
            if owner in (None, 0) or owner in seen:
                break
            seen.add(current)
            current = owner
        resolved_id = current

    resolved_name = raw_name
    if resolved_id is not None:
        resolved_name = actor_names.get(resolved_id, resolved_name)

    return resolved_name, resolved_id
