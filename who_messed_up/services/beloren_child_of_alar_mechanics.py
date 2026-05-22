"""
Shared Belo'ren color-mechanic helpers.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Tuple

from ..api import fetch_events

LIGHT_FEATHER_ID = 1241162
VOID_FEATHER_ID = 1241163
LIGHT_ECHO_ID = 1242991
VOID_ECHO_ID = 1242996
LIGHT_DIVE_ID = 1241291
VOID_DIVE_ID = 1241340
LIGHT_QUILL_ID = 1242093
VOID_QUILL_ID = 1242094
LIGHT_QUILL_MARKER_ID = 1241992
VOID_QUILL_MARKER_ID = 1242091
LIGHT_FLAMES_ID = 1242803
VOID_FLAMES_ID = 1242815
VOIDLIGHT_RUPTURE_ID = 1243866
LIGHT_ERUPTION_ID = 1243852
VOID_ERUPTION_ID = 1243854

FEATHER_LABELS = {
    LIGHT_FEATHER_ID: "Light Feather",
    VOID_FEATHER_ID: "Void Feather",
}
ABILITY_LABELS = {
    LIGHT_ECHO_ID: "Light Echo",
    VOID_ECHO_ID: "Void Echo",
    LIGHT_DIVE_ID: "Light Dive",
    VOID_DIVE_ID: "Void Dive",
    LIGHT_QUILL_ID: "Light Quill",
    VOID_QUILL_ID: "Void Quill",
    LIGHT_FLAMES_ID: "Light Flames",
    VOID_FLAMES_ID: "Void Flames",
    VOIDLIGHT_RUPTURE_ID: "Voidlight Rupture",
    LIGHT_ERUPTION_ID: "Light Eruption",
    VOID_ERUPTION_ID: "Void Eruption",
}
ECHO_REQUIRED_FEATHER = {
    LIGHT_ECHO_ID: LIGHT_FEATHER_ID,
    VOID_ECHO_ID: VOID_FEATHER_ID,
}
ECHO_WRONG_FEATHER = {
    LIGHT_ECHO_ID: VOID_FEATHER_ID,
    VOID_ECHO_ID: LIGHT_FEATHER_ID,
}
QUILL_REQUIRED_FEATHER = {
    LIGHT_QUILL_ID: LIGHT_FEATHER_ID,
    VOID_QUILL_ID: VOID_FEATHER_ID,
}
QUILL_WRONG_FEATHER = {
    LIGHT_QUILL_ID: VOID_FEATHER_ID,
    VOID_QUILL_ID: LIGHT_FEATHER_ID,
}
QUILL_MARKERS = {
    LIGHT_QUILL_ID: LIGHT_QUILL_MARKER_ID,
    VOID_QUILL_ID: VOID_QUILL_MARKER_ID,
}
ERUPTION_REQUIRED_FEATHER = {
    LIGHT_ERUPTION_ID: LIGHT_FEATHER_ID,
    VOID_ERUPTION_ID: VOID_FEATHER_ID,
}
ERUPTION_WRONG_FEATHER = {
    LIGHT_ERUPTION_ID: VOID_FEATHER_ID,
    VOID_ERUPTION_ID: LIGHT_FEATHER_ID,
}
FLAMES_REQUIRED_FEATHER = {
    LIGHT_FLAMES_ID: LIGHT_FEATHER_ID,
    VOID_FLAMES_ID: VOID_FEATHER_ID,
}
FLAMES_WRONG_FEATHER = {
    LIGHT_FLAMES_ID: VOID_FEATHER_ID,
    VOID_FLAMES_ID: LIGHT_FEATHER_ID,
}

FEATHER_IDS = (LIGHT_FEATHER_ID, VOID_FEATHER_ID)
QUILL_ASSIGNMENT_WINDOW_MS = 8000.0
FLAMES_DAMAGE_WINDOW_TOLERANCE_MS = 100.0
RUPTURE_DAMAGE_WINDOW_TOLERANCE_MS = 1000.0

_FEATHER_APPLY_EVENTS = {"applydebuff", "applydebuffstack", "refreshdebuff", "refreshdebuffstack"}
_FEATHER_REMOVE_EVENTS = {"removedebuff", "removedebuffstack"}
_FLAMES_APPLY_EVENTS = {"applydebuff", "applydebuffstack", "refreshdebuff", "refreshdebuffstack"}
_FLAMES_REMOVE_EVENTS = {"removedebuff"}
_RUPTURE_APPLY_EVENTS = {"applydebuff", "applydebuffstack"}
_RUPTURE_REMOVE_EVENTS = {"removedebuff"}

FeatherTimeline = List[Tuple[float, Optional[int]]]
QuillAssignment = Tuple[float, str]


@dataclass(frozen=True)
class QuillDamageClassification:
    ability_id: int
    timestamp: float
    player: str
    assigned_target: str
    expected_feather_id: int
    actual_feather_id: int
    damage_amount: float
    mistake_label: str
    is_wrong_feather: bool


@dataclass(frozen=True)
class FlamePenaltyApplication:
    ability_id: int
    timestamp: float
    player: str
    expected_feather_id: int
    actual_feather_id: int
    stack_count: Optional[int] = None


@dataclass(frozen=True)
class FlameDamageClassification:
    ability_id: int
    timestamp: float
    player: str
    expected_feather_id: int
    actual_feather_id: int
    damage_amount: float


@dataclass(frozen=True)
class RuptureMistakeWindow:
    ability_id: int
    timestamp: float
    end: float
    player: str
    expected_feather_id: int
    actual_feather_id: int
    stack_count: Optional[int] = None


@dataclass(frozen=True)
class RuptureMistakeClassification:
    ability_id: int
    timestamp: float
    end: float
    player: str
    expected_feather_id: int
    actual_feather_id: int
    damage_amount: float
    damage_tick_count: int
    stack_count: Optional[int] = None


@dataclass(frozen=True)
class FlamePenaltyWindow:
    ability_id: int
    player: str
    start: float
    end: float
    expected_feather_id: int
    actual_feather_id: int


def collect_feather_timelines(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
) -> Dict[str, FeatherTimeline]:
    end_time = event_end if event_end is not None else fight.end
    changes: List[Tuple[float, str, str, int]] = []
    for feather_id in FEATHER_IDS:
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=end_time,
            ability_id=feather_id,
            actor_names=actor_names,
        ):
            timestamp = event_timestamp(event)
            target_name = target_name_from_event(event)
            event_type = str(event.get("type") or "").lower()
            if timestamp is None or not target_name:
                continue
            if event_type not in _FEATHER_APPLY_EVENTS and event_type not in _FEATHER_REMOVE_EVENTS:
                continue
            changes.append((timestamp, target_name, event_type, feather_id))

    changes.sort(key=lambda item: item[0])
    current_by_player: Dict[str, Optional[int]] = {}
    timelines: DefaultDict[str, FeatherTimeline] = defaultdict(list)
    for timestamp, target_name, event_type, feather_id in changes:
        if event_type in _FEATHER_APPLY_EVENTS:
            current_by_player[target_name] = feather_id
            timelines[target_name].append((timestamp, feather_id))
            continue
        if current_by_player.get(target_name) == feather_id:
            current_by_player[target_name] = None
            timelines[target_name].append((timestamp, None))
    return dict(timelines)


def collect_quill_assignments(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
) -> Dict[int, List[QuillAssignment]]:
    end_time = event_end if event_end is not None else fight.end
    assignments: DefaultDict[int, List[QuillAssignment]] = defaultdict(list)
    for damage_ability_id, marker_ability_id in QUILL_MARKERS.items():
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=end_time,
            ability_id=marker_ability_id,
            actor_names=actor_names,
        ):
            if str(event.get("type") or "").lower() != "applydebuff":
                continue
            timestamp = event_timestamp(event)
            target_name = target_name_from_event(event)
            if timestamp is None or not target_name:
                continue
            assignments[damage_ability_id].append((timestamp, target_name))
    for damage_ability_id in list(assignments.keys()):
        assignments[damage_ability_id].sort(key=lambda item: item[0])
    return dict(assignments)


def collect_quill_damage_classifications(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
    quill_assignments: Dict[int, List[QuillAssignment]],
) -> Dict[Tuple[int, int, str], QuillDamageClassification]:
    end_time = event_end if event_end is not None else fight.end
    classifications: Dict[Tuple[int, int, str], QuillDamageClassification] = {}
    for ability_id, expected_feather_id in QUILL_REQUIRED_FEATHER.items():
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="DamageTaken",
            start=fight.start,
            end=end_time,
            ability_id=ability_id,
            actor_names=actor_names,
        ):
            timestamp = event_timestamp(event)
            player = target_name_from_event(event)
            if timestamp is None or not _player_in_scope(player, known_players, participants):
                continue
            assignment = active_quill_assignment(quill_assignments.get(ability_id, []), timestamp)
            if assignment is None:
                continue
            assigned_target = assignment[1]
            if player == assigned_target:
                continue
            damage_amount = damage_amount_from_event(event)
            if damage_amount is None or damage_amount <= 0:
                continue
            actual_feather_id = active_feather_at(feather_timelines.get(player, []), timestamp)
            if actual_feather_id is None:
                continue
            if actual_feather_id == expected_feather_id:
                continue
            classifications[quill_damage_event_key(ability_id, timestamp, player)] = QuillDamageClassification(
                ability_id=ability_id,
                timestamp=timestamp,
                player=player,
                assigned_target=assigned_target,
                expected_feather_id=expected_feather_id,
                actual_feather_id=actual_feather_id,
                damage_amount=damage_amount,
                mistake_label="Wrong Quill Soak",
                is_wrong_feather=True,
            )
    return classifications


def quill_damage_event_key(ability_id: int, timestamp: float, player: str) -> Tuple[int, int, str]:
    return (int(ability_id), int(round(float(timestamp))), player)


def collect_flame_penalty_applications(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
) -> List[FlamePenaltyApplication]:
    _, applications = _collect_flame_penalty_windows_and_applications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
    )
    return applications


def collect_flame_damage_classifications(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
) -> Dict[Tuple[int, int, str], FlameDamageClassification]:
    end_time = event_end if event_end is not None else fight.end
    windows_by_player, _ = _collect_flame_penalty_windows_and_applications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
    )
    classifications: Dict[Tuple[int, int, str], FlameDamageClassification] = {}
    for ability_id in FLAMES_REQUIRED_FEATHER:
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="DamageTaken",
            start=fight.start,
            end=end_time,
            ability_id=ability_id,
            actor_names=actor_names,
        ):
            timestamp = event_timestamp(event)
            player = target_name_from_event(event)
            if timestamp is None or not _player_in_scope(player, known_players, participants):
                continue
            damage_amount = damage_amount_from_event(event)
            if damage_amount is None or damage_amount <= 0:
                continue
            window = active_flame_penalty_window(windows_by_player.get((ability_id, player), []), timestamp)
            if window is None:
                continue
            classifications[flame_damage_event_key(ability_id, timestamp, player)] = FlameDamageClassification(
                ability_id=ability_id,
                timestamp=timestamp,
                player=player,
                expected_feather_id=window.expected_feather_id,
                actual_feather_id=window.actual_feather_id,
                damage_amount=damage_amount,
            )
    return classifications


def flame_damage_event_key(ability_id: int, timestamp: float, player: str) -> Tuple[int, int, str]:
    return (int(ability_id), int(round(float(timestamp))), player)


def collect_flame_penalty_windows(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
) -> List[FlamePenaltyWindow]:
    windows_by_player, _ = _collect_flame_penalty_windows_and_applications(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
    )
    windows: List[FlamePenaltyWindow] = []
    for player_windows in windows_by_player.values():
        windows.extend(player_windows)
    windows.sort(key=lambda item: (item.start, item.ability_id, item.player))
    return windows


def active_flame_penalty_window(
    windows: List[FlamePenaltyWindow],
    timestamp: float,
) -> Optional[FlamePenaltyWindow]:
    for window in windows:
        if (
            window.start - FLAMES_DAMAGE_WINDOW_TOLERANCE_MS
            <= timestamp
            <= window.end + FLAMES_DAMAGE_WINDOW_TOLERANCE_MS
        ):
            return window
    return None


def flame_penalty_window_key(window: FlamePenaltyWindow) -> Tuple[int, str, int]:
    return (int(window.ability_id), window.player, int(round(float(window.start))))


def collect_rupture_mistake_windows(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
) -> List[RuptureMistakeWindow]:
    end_time = event_end if event_end is not None else fight.end
    raw_events: List[Tuple[float, str, str, Optional[int]]] = []
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="Debuffs",
        start=fight.start,
        end=end_time,
        ability_id=VOIDLIGHT_RUPTURE_ID,
        actor_names=actor_names,
    ):
        timestamp = event_timestamp(event)
        player = target_name_from_event(event)
        event_type = str(event.get("type") or "").lower()
        if timestamp is None or event_type not in _RUPTURE_APPLY_EVENTS | _RUPTURE_REMOVE_EVENTS:
            continue
        if not _player_in_scope(player, known_players, participants):
            continue
        raw_events.append((timestamp, event_type, player, _stack_count_from_event(event)))

    raw_events.sort(key=lambda item: item[0])
    open_windows: Dict[str, RuptureMistakeWindow] = {}
    windows: List[RuptureMistakeWindow] = []
    for timestamp, event_type, player, stack_count in raw_events:
        if event_type in _RUPTURE_APPLY_EVENTS:
            existing = open_windows.pop(player, None)
            if existing is not None:
                windows.append(_close_rupture_window(existing, timestamp))
            actual_feather_id = active_feather_at(feather_timelines.get(player, []), timestamp)
            expected_feather_id = opposite_feather_id(actual_feather_id)
            if expected_feather_id is None or actual_feather_id is None:
                continue
            open_windows[player] = RuptureMistakeWindow(
                ability_id=VOIDLIGHT_RUPTURE_ID,
                timestamp=timestamp,
                end=float(end_time),
                player=player,
                expected_feather_id=expected_feather_id,
                actual_feather_id=actual_feather_id,
                stack_count=stack_count,
            )
            continue

        existing = open_windows.pop(player, None)
        if existing is not None:
            windows.append(_close_rupture_window(existing, timestamp))

    windows.extend(open_windows.values())
    windows.sort(key=lambda item: (item.timestamp, item.player))
    return windows


def collect_rupture_mistake_classifications(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
) -> List[RuptureMistakeClassification]:
    end_time = event_end if event_end is not None else fight.end
    windows = collect_rupture_mistake_windows(
        session=session,
        bearer=bearer,
        report_code=report_code,
        fight=fight,
        actor_names=actor_names,
        event_end=event_end,
        known_players=known_players,
        participants=participants,
        feather_timelines=feather_timelines,
    )
    windows_by_player: DefaultDict[str, List[RuptureMistakeWindow]] = defaultdict(list)
    for window in windows:
        windows_by_player[window.player].append(window)

    damage_by_window: DefaultDict[Tuple[str, int], float] = defaultdict(float)
    ticks_by_window: DefaultDict[Tuple[str, int], int] = defaultdict(int)
    for event in fetch_events(
        session,
        bearer,
        code=report_code,
        data_type="DamageTaken",
        start=fight.start,
        end=end_time,
        ability_id=VOIDLIGHT_RUPTURE_ID,
        actor_names=actor_names,
    ):
        timestamp = event_timestamp(event)
        player = target_name_from_event(event)
        if timestamp is None or not _player_in_scope(player, known_players, participants):
            continue
        damage_amount = damage_amount_from_event(event)
        if damage_amount is None or damage_amount <= 0:
            continue
        window = active_rupture_mistake_window(windows_by_player.get(player, []), timestamp)
        if window is None:
            continue
        key = rupture_mistake_window_key(window)
        damage_by_window[key] += damage_amount
        ticks_by_window[key] += 1

    classifications: List[RuptureMistakeClassification] = []
    for window in windows:
        key = rupture_mistake_window_key(window)
        damage_amount = damage_by_window.get(key, 0.0)
        tick_count = ticks_by_window.get(key, 0)
        if damage_amount <= 0 or tick_count <= 0:
            continue
        classifications.append(
            RuptureMistakeClassification(
                ability_id=window.ability_id,
                timestamp=window.timestamp,
                end=window.end,
                player=window.player,
                expected_feather_id=window.expected_feather_id,
                actual_feather_id=window.actual_feather_id,
                damage_amount=damage_amount,
                damage_tick_count=tick_count,
                stack_count=window.stack_count,
            )
        )
    classifications.sort(key=lambda item: (item.timestamp, item.player))
    return classifications


def active_rupture_mistake_window(
    windows: List[RuptureMistakeWindow],
    timestamp: float,
) -> Optional[RuptureMistakeWindow]:
    for window in windows:
        if window.timestamp <= timestamp <= window.end + RUPTURE_DAMAGE_WINDOW_TOLERANCE_MS:
            return window
    return None


def rupture_mistake_window_key(window: RuptureMistakeWindow) -> Tuple[str, int]:
    return (window.player, int(round(float(window.timestamp))))


def active_feather_at(timeline: FeatherTimeline, timestamp: float) -> Optional[int]:
    if not timeline:
        return None
    index = bisect_right([point[0] for point in timeline], timestamp) - 1
    if index < 0:
        return None
    return timeline[index][1]


def active_quill_assignment(assignments: List[QuillAssignment], timestamp: float) -> Optional[QuillAssignment]:
    if not assignments:
        return None
    index = bisect_right([assignment[0] for assignment in assignments], timestamp) - 1
    if index < 0:
        return None
    assignment = assignments[index]
    if timestamp - assignment[0] > QUILL_ASSIGNMENT_WINDOW_MS:
        return None
    return assignment


def event_timestamp(event: Dict[str, object]) -> Optional[float]:
    timestamp = event.get("timestamp")
    if timestamp is None:
        return None
    try:
        return float(timestamp)
    except (TypeError, ValueError):
        return None


def source_name_from_event(event: Dict[str, object]) -> Optional[str]:
    source_name = event.get("sourceName")
    if not source_name and isinstance(event.get("source"), dict):
        source_name = event["source"].get("name")
    return str(source_name) if source_name else None


def target_name_from_event(event: Dict[str, object]) -> Optional[str]:
    target_name = event.get("targetName")
    if not target_name and isinstance(event.get("target"), dict):
        target_name = event["target"].get("name")
    return str(target_name) if target_name else None


def ability_id_from_event(event: Dict[str, object]) -> Optional[int]:
    return _coerce_int(event.get("abilityGameID") or _nested_id(event.get("ability")))


def extra_ability_id_from_event(event: Dict[str, object]) -> Optional[int]:
    return _coerce_int(event.get("extraAbilityGameID") or _nested_id(event.get("extraAbility")))


def damage_amount_from_event(event: Dict[str, object]) -> Optional[float]:
    amount = event.get("amount")
    if amount is None:
        amount = event.get("unmitigatedAmount")
    if amount is None:
        return None
    try:
        return float(amount)
    except (TypeError, ValueError):
        return None


def feather_label(feather_id: Optional[int]) -> str:
    if feather_id is None:
        return "Unknown Feather"
    return FEATHER_LABELS.get(feather_id, f"Spell #{feather_id}")


def ability_label(ability_id: Optional[int]) -> str:
    if ability_id is None:
        return "Unknown Ability"
    return ABILITY_LABELS.get(ability_id, f"Spell #{ability_id}")


def opposite_feather_id(feather_id: Optional[int]) -> Optional[int]:
    if feather_id == LIGHT_FEATHER_ID:
        return VOID_FEATHER_ID
    if feather_id == VOID_FEATHER_ID:
        return LIGHT_FEATHER_ID
    return None


def _collect_flame_penalty_windows_and_applications(
    *,
    session,
    bearer: str,
    report_code: str,
    fight,
    actor_names: Dict[int, str],
    event_end: Optional[float],
    known_players: set[str],
    participants: set[str],
    feather_timelines: Dict[str, FeatherTimeline],
) -> Tuple[Dict[Tuple[int, str], List[FlamePenaltyWindow]], List[FlamePenaltyApplication]]:
    end_time = event_end if event_end is not None else fight.end
    events: List[Tuple[float, int, str, str, Optional[int]]] = []
    for ability_id in FLAMES_REQUIRED_FEATHER:
        for event in fetch_events(
            session,
            bearer,
            code=report_code,
            data_type="Debuffs",
            start=fight.start,
            end=end_time,
            ability_id=ability_id,
            actor_names=actor_names,
        ):
            timestamp = event_timestamp(event)
            player = target_name_from_event(event)
            event_type = str(event.get("type") or "").lower()
            if timestamp is None or event_type not in _FLAMES_APPLY_EVENTS | _FLAMES_REMOVE_EVENTS:
                continue
            if not _player_in_scope(player, known_players, participants):
                continue
            events.append((timestamp, ability_id, event_type, player, _stack_count_from_event(event)))

    events.sort(key=lambda item: item[0])
    open_windows: Dict[Tuple[int, str], Tuple[float, int]] = {}
    windows: DefaultDict[Tuple[int, str], List[FlamePenaltyWindow]] = defaultdict(list)
    applications: List[FlamePenaltyApplication] = []

    for timestamp, ability_id, event_type, player, stack_count in events:
        key = (ability_id, player)
        expected_feather_id = FLAMES_REQUIRED_FEATHER[ability_id]
        wrong_feather_id = FLAMES_WRONG_FEATHER[ability_id]
        if event_type in _FLAMES_APPLY_EVENTS:
            actual_feather_id = active_feather_at(feather_timelines.get(player, []), timestamp)
            if actual_feather_id != wrong_feather_id:
                continue
            applications.append(
                FlamePenaltyApplication(
                    ability_id=ability_id,
                    timestamp=timestamp,
                    player=player,
                    expected_feather_id=expected_feather_id,
                    actual_feather_id=actual_feather_id,
                    stack_count=stack_count,
                )
            )
            open_windows.setdefault(key, (timestamp, actual_feather_id))
            continue

        open_window = open_windows.pop(key, None)
        if open_window is None:
            continue
        start, actual_feather_id = open_window
        windows[key].append(
            FlamePenaltyWindow(
                ability_id=ability_id,
                player=player,
                start=start,
                end=timestamp,
                expected_feather_id=expected_feather_id,
                actual_feather_id=actual_feather_id,
            )
        )

    for (ability_id, player), (start, actual_feather_id) in open_windows.items():
        windows[(ability_id, player)].append(
            FlamePenaltyWindow(
                ability_id=ability_id,
                player=player,
                start=start,
                end=float(end_time),
                expected_feather_id=FLAMES_REQUIRED_FEATHER[ability_id],
                actual_feather_id=actual_feather_id,
            )
        )

    for player_windows in windows.values():
        player_windows.sort(key=lambda item: item.start)
    applications.sort(key=lambda item: (item.timestamp, item.ability_id, item.player))
    return dict(windows), applications


def _stack_count_from_event(event: Dict[str, object]) -> Optional[int]:
    for key in ("stack", "stacks", "stackCount", "stack_count"):
        value = _coerce_int(event.get(key))
        if value is not None:
            return value
    return None


def _close_rupture_window(window: RuptureMistakeWindow, end: float) -> RuptureMistakeWindow:
    return RuptureMistakeWindow(
        ability_id=window.ability_id,
        timestamp=window.timestamp,
        end=end,
        player=window.player,
        expected_feather_id=window.expected_feather_id,
        actual_feather_id=window.actual_feather_id,
        stack_count=window.stack_count,
    )


def _nested_id(value: object) -> Optional[object]:
    if isinstance(value, dict):
        return value.get("id") or value.get("gameID")
    return None


def _coerce_int(value: object) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _player_in_scope(player: Optional[str], known_players: set[str], participants: set[str]) -> bool:
    if not player or player not in known_players:
        return False
    return not participants or player in participants


__all__ = [
    "ABILITY_LABELS",
    "ECHO_REQUIRED_FEATHER",
    "ECHO_WRONG_FEATHER",
    "ERUPTION_REQUIRED_FEATHER",
    "ERUPTION_WRONG_FEATHER",
    "FEATHER_IDS",
    "FEATHER_LABELS",
    "FeatherTimeline",
    "FLAMES_DAMAGE_WINDOW_TOLERANCE_MS",
    "FLAMES_REQUIRED_FEATHER",
    "FLAMES_WRONG_FEATHER",
    "FlameDamageClassification",
    "FlamePenaltyApplication",
    "FlamePenaltyWindow",
    "LIGHT_DIVE_ID",
    "LIGHT_ECHO_ID",
    "LIGHT_ERUPTION_ID",
    "LIGHT_FEATHER_ID",
    "LIGHT_FLAMES_ID",
    "LIGHT_QUILL_ID",
    "LIGHT_QUILL_MARKER_ID",
    "QUILL_ASSIGNMENT_WINDOW_MS",
    "QUILL_MARKERS",
    "QUILL_REQUIRED_FEATHER",
    "QUILL_WRONG_FEATHER",
    "QuillAssignment",
    "QuillDamageClassification",
    "RUPTURE_DAMAGE_WINDOW_TOLERANCE_MS",
    "RuptureMistakeClassification",
    "RuptureMistakeWindow",
    "VOID_DIVE_ID",
    "VOID_ECHO_ID",
    "VOID_ERUPTION_ID",
    "VOID_FEATHER_ID",
    "VOID_FLAMES_ID",
    "VOID_QUILL_ID",
    "VOID_QUILL_MARKER_ID",
    "VOIDLIGHT_RUPTURE_ID",
    "ability_id_from_event",
    "ability_label",
    "active_feather_at",
    "active_flame_penalty_window",
    "active_quill_assignment",
    "active_rupture_mistake_window",
    "collect_feather_timelines",
    "collect_flame_damage_classifications",
    "collect_flame_penalty_applications",
    "collect_flame_penalty_windows",
    "collect_quill_assignments",
    "collect_quill_damage_classifications",
    "collect_rupture_mistake_classifications",
    "collect_rupture_mistake_windows",
    "damage_amount_from_event",
    "event_timestamp",
    "extra_ability_id_from_event",
    "feather_label",
    "flame_damage_event_key",
    "flame_penalty_window_key",
    "opposite_feather_id",
    "quill_damage_event_key",
    "rupture_mistake_window_key",
    "source_name_from_event",
    "target_name_from_event",
]
