"""Shared pull metadata used by report-level aggregate and per-pull views."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .common import ROLE_UNKNOWN, compute_fight_duration_ms


@dataclass(frozen=True)
class ReportPull:
    source_report_code: str
    fight_id: int
    fight_name: Optional[str]
    pull_index: int
    view_id: str
    label: str
    duration_ms: Optional[float]
    participants: Tuple[str, ...] = ()
    player_roles: Dict[str, str] = field(default_factory=dict)


def report_pull_view_id(report_code: str, fight_id: int) -> str:
    """Return a stable view key that remains unique when reports are merged."""
    return f"pull:{report_code}:{int(fight_id)}"


def build_report_pulls(
    report_code: str,
    fights: Iterable[object],
    participants_by_fight: Mapping[int, Iterable[str]],
    roles_by_fight: Optional[Mapping[int, Mapping[str, str]]] = None,
) -> List[ReportPull]:
    pulls: List[ReportPull] = []
    for pull_index, fight in enumerate(fights, start=1):
        fight_id = int(getattr(fight, "id"))
        pulls.append(
            ReportPull(
                source_report_code=report_code,
                fight_id=fight_id,
                fight_name=getattr(fight, "name", None),
                pull_index=pull_index,
                view_id=report_pull_view_id(report_code, fight_id),
                label=f"Pull {pull_index}",
                duration_ms=compute_fight_duration_ms(fight),
                participants=tuple(sorted(set(participants_by_fight.get(fight_id, ())))),
                player_roles={
                    player: role
                    for player, role in (roles_by_fight or {}).get(fight_id, {}).items()
                    if role and role != ROLE_UNKNOWN
                },
            )
        )
    return pulls


def merge_report_pulls(pull_groups: Sequence[Sequence[ReportPull]]) -> List[ReportPull]:
    """Combine pull lists and disambiguate labels only when reports are merged."""
    multiple_reports = len(pull_groups) > 1
    return [
        replace(pull, label=f"{pull.source_report_code} {pull.label}" if multiple_reports else pull.label)
        for pulls in pull_groups
        for pull in pulls
    ]


def event_belongs_to_pull(event: object, pull: ReportPull, default_report_code: str) -> bool:
    source_report_code = getattr(event, "source_report_code", None) or default_report_code
    try:
        fight_id = int(getattr(event, "fight_id"))
    except (TypeError, ValueError):
        return False
    return source_report_code == pull.source_report_code and fight_id == pull.fight_id


__all__ = [
    "ReportPull",
    "build_report_pulls",
    "event_belongs_to_pull",
    "merge_report_pulls",
    "report_pull_view_id",
]
