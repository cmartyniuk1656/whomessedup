"""
Central registry for boss ability manifests.
"""
from __future__ import annotations

from .boss_manifest_types import (
    BossAbilityMetadata,
    BossManifest,
    EncounterTargetBucket,
    EncounterTargetConfig,
    normalize_manifest_difficulty,
)
from .manifests.midnight_season_1 import (
    IMPERATOR_AVERZIAN_MANIFEST,
    MIDNIGHT_SEASON_1_MANIFESTS,
    VORASIUS_MANIFEST,
)

MANIFEST_TIERS = {
    "midnight-season-1": MIDNIGHT_SEASON_1_MANIFESTS,
}


def _manifest_key(boss_id: str, difficulty: object = None) -> str:
    normalized_difficulty = normalize_manifest_difficulty(difficulty) or "default"
    return f"{boss_id}:{normalized_difficulty}"


ALL_BOSS_MANIFESTS = tuple(
    manifest
    for tier_manifests in MANIFEST_TIERS.values()
    for manifest in tier_manifests
)

BOSS_MANIFESTS_BY_KEY = {
    _manifest_key(manifest.boss_id, manifest.difficulty): manifest
    for manifest in ALL_BOSS_MANIFESTS
}

BOSS_MANIFESTS_BY_BOSS = {
    boss_id: tuple(manifest for manifest in ALL_BOSS_MANIFESTS if manifest.boss_id == boss_id)
    for boss_id in {manifest.boss_id for manifest in ALL_BOSS_MANIFESTS}
}

BOSS_MANIFESTS = {
    boss_id: manifests[0]
    for boss_id, manifests in BOSS_MANIFESTS_BY_BOSS.items()
    if len(manifests) == 1
}


def get_boss_manifest(boss_id: str, difficulty: object = None) -> BossManifest | None:
    if difficulty is not None:
        return BOSS_MANIFESTS_BY_KEY.get(_manifest_key(boss_id, difficulty))

    matches = BOSS_MANIFESTS_BY_BOSS.get(boss_id, ())
    if len(matches) == 1:
        return matches[0]
    defaults = [manifest for manifest in matches if normalize_manifest_difficulty(manifest.difficulty) is None]
    return defaults[0] if len(defaults) == 1 else None


__all__ = [
    "ALL_BOSS_MANIFESTS",
    "BOSS_MANIFESTS",
    "BOSS_MANIFESTS_BY_BOSS",
    "BOSS_MANIFESTS_BY_KEY",
    "MANIFEST_TIERS",
    "BossAbilityMetadata",
    "BossManifest",
    "EncounterTargetBucket",
    "EncounterTargetConfig",
    "IMPERATOR_AVERZIAN_MANIFEST",
    "VORASIUS_MANIFEST",
    "get_boss_manifest",
]
