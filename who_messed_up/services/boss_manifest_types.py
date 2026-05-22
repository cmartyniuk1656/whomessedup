"""
Shared boss manifest types for boss-scoped ability and enemy metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple

AVOIDABLE_TAG = "avoidable"
TANK_SOAK_TAG = "tank soak"
TANK_ROLE = "tank"
DIFFICULTY_ALIASES = {
    "4": "heroic",
    "heroic": "heroic",
    "5": "mythic",
    "mythic": "mythic",
}


class EncounterTargetBucket(str, Enum):
    BOSS = "boss"
    PRIORITY_ADD = "priority_add"
    PAD_ADD = "pad_add"


@dataclass(frozen=True)
class EncounterTargetConfig:
    slug: str
    label: str
    enemy_name: str
    bucket: Optional[EncounterTargetBucket] = None
    default_enabled: bool = True
    damage_filter: Optional[str] = None


@dataclass(frozen=True)
class BossAbilityMetadata:
    name: str
    game_id: Optional[int] = None
    description: Optional[str] = None
    url: Optional[str] = None
    tags: Tuple[str, ...] = ()
    avoidable: bool = False
    avoidable_exclusion_debuff_ability_id: Optional[int] = None
    avoidable_exclusion_debuff_event_types: Tuple[str, ...] = ()
    avoidable_exclusion_debuff_window_ms: float = 0.0


@dataclass(frozen=True)
class BossManifest:
    boss_id: str
    boss_name: str
    abilities: Tuple[BossAbilityMetadata, ...] = ()
    difficulty: Optional[str] = None
    targets: Tuple[EncounterTargetConfig, ...] = ()

    @property
    def target_configs(self) -> dict[str, EncounterTargetConfig]:
        return {target.slug: target for target in self.targets}

    @property
    def default_target_slugs(self) -> Tuple[str, ...]:
        return tuple(target.slug for target in self.targets if target.default_enabled)

    def ability_for(
        self,
        *,
        ability_id: Optional[int] = None,
        ability_name: Optional[str] = None,
    ) -> Optional[BossAbilityMetadata]:
        normalized_id = _normalize_ability_id(ability_id)
        if normalized_id is not None:
            for ability in self.abilities:
                if ability.game_id is not None and _normalize_ability_id(ability.game_id) == normalized_id:
                    return ability

        normalized_name = _normalize_ability_name(ability_name)
        if not normalized_name:
            return None
        name_matches = [
            ability
            for ability in self.abilities
            if _normalize_ability_name(ability.name) == normalized_name
        ]
        if len(name_matches) == 1:
            return name_matches[0]
        return None


def _normalize_ability_id(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_ability_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return " ".join(str(value).strip().lower().split())


def _normalize_metadata_value(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().lower().split())


def normalize_manifest_difficulty(value: Any) -> Optional[str]:
    if value is None:
        return None
    raw_value = getattr(value, "value", value)
    normalized = _normalize_metadata_value(str(raw_value).replace("_", " ").replace("-", " "))
    if not normalized:
        return None
    return DIFFICULTY_ALIASES.get(normalized, normalized)


def ability_has_tag(ability: BossAbilityMetadata, tag: str) -> bool:
    normalized_tag = _normalize_metadata_value(tag)
    if not normalized_tag:
        return False
    return any(_normalize_metadata_value(candidate) == normalized_tag for candidate in ability.tags)


def is_avoidable_ability(ability: BossAbilityMetadata) -> bool:
    return ability.avoidable or ability_has_tag(ability, AVOIDABLE_TAG)


def is_tank_soak_ability(ability: BossAbilityMetadata) -> bool:
    return ability_has_tag(ability, TANK_SOAK_TAG)


def is_avoidable_for_role(ability: Optional[BossAbilityMetadata], role: Optional[str]) -> bool:
    if not ability or not is_avoidable_ability(ability):
        return False
    if is_tank_soak_ability(ability) and _normalize_metadata_value(role) == TANK_ROLE:
        return False
    return True


def find_ambiguous_ability_names(manifest: BossManifest) -> Tuple[str, ...]:
    counts: dict[str, int] = {}
    display_names: dict[str, str] = {}
    for ability in manifest.abilities:
        normalized = _normalize_ability_name(ability.name)
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
        display_names.setdefault(normalized, ability.name)
    return tuple(
        display_names[name]
        for name, count in sorted(counts.items(), key=lambda item: display_names[item[0]].lower())
        if count > 1
    )


__all__ = [
    "ability_has_tag",
    "BossAbilityMetadata",
    "BossManifest",
    "EncounterTargetBucket",
    "EncounterTargetConfig",
    "find_ambiguous_ability_names",
    "is_avoidable_ability",
    "is_avoidable_for_role",
    "is_tank_soak_ability",
    "normalize_manifest_difficulty",
]
