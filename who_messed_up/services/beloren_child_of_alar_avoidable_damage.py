"""
Belo'ren, Child of Al'ar avoidable-damage summary wrapper.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Dict, Iterable, List, Optional, Tuple

from .avoidable_damage import AvoidableDamageEvent, AvoidableDamageSummary, fetch_avoidable_damage_summary
from .boss_manifest_types import BossAbilityMetadata
from .boss_manifests import BELOREN_CHILD_OF_ALAR_MANIFEST
from .beloren_child_of_alar_mechanics import (
    FLAMES_REQUIRED_FEATHER,
    LIGHT_FEATHER_ID,
    LIGHT_QUILL_ID,
    LIGHT_QUILL_MARKER_ID,
    QUILL_REQUIRED_FEATHER,
    VOID_FEATHER_ID,
    VOID_QUILL_ID,
    VOID_QUILL_MARKER_ID,
    VOIDLIGHT_RUPTURE_ID,
    active_flame_penalty_window,
    active_rupture_mistake_window,
    collect_feather_timelines,
    collect_flame_damage_classifications,
    collect_flame_penalty_windows,
    collect_quill_assignments,
    collect_quill_damage_classifications,
    collect_rupture_mistake_windows,
    event_timestamp,
    flame_damage_event_key,
    flame_penalty_window_key,
    quill_damage_event_key,
    rupture_mistake_window_key,
)

REPORT_DEFAULT_FIGHT = "Belo'ren, Child of Al'ar"

def fetch_beloren_child_of_alar_avoidable_damage_summary(
    *,
    report_code: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    difficulty: Optional[str | int] = None,
    ability_keys: Optional[Iterable[str]] = None,
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> AvoidableDamageSummary:
    return fetch_avoidable_damage_summary(
        report_code=report_code,
        boss_manifest=BELOREN_CHILD_OF_ALAR_MANIFEST,
        fight_name=fight_name or REPORT_DEFAULT_FIGHT,
        fight_ids=fight_ids,
        difficulty=difficulty,
        ability_keys=ability_keys,
        ignore_after_deaths=ignore_after_deaths,
        extra_report_codes=extra_report_codes,
        token=token,
        client_id=client_id,
        client_secret=client_secret,
        event_filter_factory=_build_beloren_avoidable_event_filter,
        event_aggregator_factory=_build_beloren_avoidable_event_aggregator,
    )


def _build_beloren_avoidable_event_filter(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players,
    participants,
):
    feather_timelines = collect_feather_timelines(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
    )
    quill_assignments = collect_quill_assignments(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
    )
    quill_classifications = collect_quill_damage_classifications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=set(known_players or ()),
        participants=set(participants or ()),
        feather_timelines=feather_timelines,
        quill_assignments=quill_assignments,
    )
    flame_classifications = collect_flame_damage_classifications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=set(known_players or ()),
        participants=set(participants or ()),
        feather_timelines=feather_timelines,
    )

    def include_event(ability: BossAbilityMetadata, event: Dict[str, object], target_name: str) -> bool:
        ability_id = int(ability.game_id) if ability.game_id is not None else None
        required_feather_id = QUILL_REQUIRED_FEATHER.get(ability_id)
        if required_feather_id is not None:
            timestamp = event_timestamp(event)
            if timestamp is None:
                return False
            return quill_damage_event_key(ability_id, timestamp, target_name) in quill_classifications

        required_feather_id = FLAMES_REQUIRED_FEATHER.get(ability_id)
        if required_feather_id is not None:
            timestamp = event_timestamp(event)
            if timestamp is None:
                return False
            return flame_damage_event_key(ability_id, timestamp, target_name) in flame_classifications

        return True

    return include_event


def _build_beloren_avoidable_event_aggregator(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players,
    participants,
):
    feather_timelines = collect_feather_timelines(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
    )
    rupture_windows = collect_rupture_mistake_windows(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=set(known_players or ()),
        participants=set(participants or ()),
        feather_timelines=feather_timelines,
    )
    windows_by_player = defaultdict(list)
    for window in rupture_windows:
        windows_by_player[window.player].append(window)
    flame_windows = collect_flame_penalty_windows(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=set(known_players or ()),
        participants=set(participants or ()),
        feather_timelines=feather_timelines,
    )
    flame_windows_by_player = defaultdict(list)
    for window in flame_windows:
        flame_windows_by_player[(window.ability_id, window.player)].append(window)

    def aggregate(events: List[AvoidableDamageEvent]) -> List[AvoidableDamageEvent]:
        passthrough: List[AvoidableDamageEvent] = []
        grouped: Dict[Tuple[str, int, str, int, int], Dict[str, object]] = {}
        for event in events:
            source_report = event.source_report_code or report_code
            if event.ability_id in FLAMES_REQUIRED_FEATHER:
                window = active_flame_penalty_window(
                    flame_windows_by_player.get((int(event.ability_id), event.player), []),
                    event.timestamp,
                )
                if window is None:
                    passthrough.append(event)
                    continue
                ability_id, _, window_start = flame_penalty_window_key(window)
                key = (source_report, int(event.fight_id), event.player, ability_id, window_start)
            elif event.ability_id == VOIDLIGHT_RUPTURE_ID:
                window = active_rupture_mistake_window(windows_by_player.get(event.player, []), event.timestamp)
                if window is None:
                    passthrough.append(event)
                    continue
                key = (source_report, int(event.fight_id), event.player, VOIDLIGHT_RUPTURE_ID, rupture_mistake_window_key(window)[1])
            else:
                passthrough.append(event)
                continue

            bucket = grouped.setdefault(key, {"event": event, "damage": 0.0, "window_start": getattr(window, "timestamp", getattr(window, "start", event.timestamp))})
            bucket["damage"] = float(bucket["damage"]) + float(event.damage_amount or 0.0)

        aggregated = [
            replace(
                bucket["event"],
                timestamp=float(bucket["window_start"]),
                offset_ms=float(bucket["window_start"]) - float(fight.start),
                damage_amount=float(bucket["damage"]),
            )
            for bucket in grouped.values()
            if float(bucket["damage"]) > 0
        ]
        return sorted(
            passthrough + aggregated,
            key=lambda item: (item.source_report_code or "", item.pull_index, item.fight_id, item.timestamp, item.player),
        )

    return aggregate


__all__ = [
    "LIGHT_FEATHER_ID",
    "LIGHT_QUILL_ID",
    "LIGHT_QUILL_MARKER_ID",
    "REPORT_DEFAULT_FIGHT",
    "VOID_FEATHER_ID",
    "VOID_QUILL_ID",
    "VOID_QUILL_MARKER_ID",
    "fetch_beloren_child_of_alar_avoidable_damage_summary",
]
