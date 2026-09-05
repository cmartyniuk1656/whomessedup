"""Reusable Heroic encounter mechanic scorecards.

The encounter-specific inference rules live in ``mechanic_scorecard_analyzers``;
this module owns Warcraft Logs retrieval, fight selection, player metadata, and
cross-report aggregation.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Sequence, Set

import requests

from ..api import Fight, fetch_events, fetch_fights, fetch_player_details
from ..env import load_env
from .common import (
    ROLE_PRIORITY,
    ROLE_UNKNOWN,
    _infer_player_roles,
    _players_from_details,
    _resolve_token,
    _sanitize_report_code,
    _select_fights,
    compute_death_cutoffs,
)
from .mechanic_scorecard_analyzers import (
    MECHANICS_BY_BOSS,
    REQUIRED_DATA_TYPES,
    TEAM_PLAYER,
    FightMechanicContext,
    analyze_fight,
)
from .mechanic_scorecard_types import (
    MechanicObservation,
    MechanicScoreEntry,
    MechanicScoreView,
    MechanicScorecardSummary,
    OUTCOME_CONTRIBUTION,
    OUTCOME_MISTAKE,
    OUTCOME_SUCCESS,
)


FIGHT_SELECTION_ALL = "all"
FIGHT_SELECTION_LAST = "last"
FIGHT_SELECTION_SPECIFIC = "specific"
FIGHT_SELECTIONS = {
    FIGHT_SELECTION_ALL,
    FIGHT_SELECTION_LAST,
    FIGHT_SELECTION_SPECIFIC,
}

SCORECARD_ENCOUNTERS: Dict[str, Dict[str, str]] = {
    "nek-zali-the-soulcoiler": {
        "boss_name": "Nek'zali the Soulcoiler",
        "fight_name": "Nek'zali the Soulcoiler",
    },
    "entombed-sentinels": {
        "boss_name": "Entombed Sentinels",
        "fight_name": "Entombed Sentinels",
    },
    "the-lost-explorers": {
        "boss_name": "The Lost Explorers",
        "fight_name": "The Lost Explorers",
    },
    "vashnik-the-malignant": {
        "boss_name": "Vashnik the Malignant",
        "fight_name": "Vashnik the Malignant",
    },
    "sszorak": {
        "boss_name": "Sszorak",
        "fight_name": "Sszorak",
    },
    "the-twin-fangs": {
        "boss_name": "The Twin Fangs",
        "fight_name": "The Twin Fangs",
    },
    "the-coiled-altar": {
        "boss_name": "The Coiled Altar",
        "fight_name": "The Coiled Altar",
    },
}


def fetch_mechanic_scorecard_summary(
    *,
    report_code: str,
    boss_id: str,
    fight_name: Optional[str] = None,
    fight_ids: Optional[Iterable[int]] = None,
    fight_selection: str = FIGHT_SELECTION_ALL,
    difficulty: Optional[str | int] = "heroic",
    ignore_after_deaths: Optional[int] = None,
    extra_report_codes: Optional[Iterable[str]] = None,
    token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> MechanicScorecardSummary:
    """Build a mechanics scorecard for one supported encounter."""
    if boss_id not in SCORECARD_ENCOUNTERS:
        raise ValueError(f"Unsupported mechanics scorecard encounter '{boss_id}'.")
    selection = _normalize_fight_selection(fight_selection)
    normalized_fight_ids = [int(fight_id) for fight_id in fight_ids] if fight_ids else None
    if selection == FIGHT_SELECTION_SPECIFIC:
        if not normalized_fight_ids or len(normalized_fight_ids) != 1:
            raise ValueError("Specific-fight analysis requires exactly one fight ID.")
        if extra_report_codes:
            raise ValueError("Specific-fight analysis supports one Warcraft Logs report at a time.")

    primary_code = _sanitize_report_code(report_code)
    encounter = SCORECARD_ENCOUNTERS[boss_id]
    shared_args = {
        "boss_id": boss_id,
        "fight_name": fight_name or encounter["fight_name"],
        "fight_ids": normalized_fight_ids,
        "fight_selection": selection,
        "difficulty": difficulty,
        "ignore_after_deaths": ignore_after_deaths,
        "token": token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    summaries = [_fetch_single_summary(report_code=primary_code, **shared_args)]
    seen = {primary_code}
    for candidate in extra_report_codes or []:
        if not candidate:
            continue
        try:
            code = _sanitize_report_code(candidate)
        except ValueError:
            continue
        if code in seen:
            continue
        seen.add(code)
        summaries.append(_fetch_single_summary(report_code=code, **shared_args))
    return summaries[0] if len(summaries) == 1 else _merge_summaries(summaries)


def _fetch_single_summary(
    *,
    report_code: str,
    boss_id: str,
    fight_name: str,
    fight_ids: Optional[List[int]],
    fight_selection: str,
    difficulty: Optional[str | int],
    ignore_after_deaths: Optional[int],
    token: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[str],
) -> MechanicScorecardSummary:
    load_env()
    session = requests.Session()
    bearer = _resolve_token(token, client_id, client_secret)
    fights, actor_names, actor_classes, _actor_owners = fetch_fights(
        session, bearer, report_code
    )
    chosen = _select_fights(
        fights,
        name_filter=fight_name,
        fight_ids=fight_ids,
        difficulty=difficulty,
    )
    chosen = _apply_fight_selection(chosen, fight_selection)
    chosen_ids = [fight.id for fight in chosen]
    known_players = {
        name
        for actor_id, name in actor_names.items()
        if name and actor_classes.get(actor_id)
    }

    aggregated_details = fetch_player_details(
        session, bearer, code=report_code, fight_ids=chosen_ids
    )
    player_roles, player_specs = _infer_player_roles(aggregated_details)
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    participants_by_fight: Dict[int, Set[str]] = {}
    for fight in chosen:
        details = fetch_player_details(
            session, bearer, code=report_code, fight_ids=[fight.id]
        )
        fight_roles, fight_specs = _infer_player_roles(details)
        for player, role in fight_roles.items():
            if player_roles.get(player) in (None, ROLE_UNKNOWN):
                player_roles[player] = role or ROLE_UNKNOWN
        for player, spec in fight_specs.items():
            if not player_specs.get(player):
                player_specs[player] = spec
        participants = {
            player
            for player in _players_from_details(details)
            if player in known_players
        }
        participants_by_fight[fight.id] = participants
        for player in participants:
            pulls_by_player[player] += 1

    death_limit = ignore_after_deaths if ignore_after_deaths and ignore_after_deaths > 0 else None
    death_cutoffs = compute_death_cutoffs(
        session,
        bearer,
        fights=chosen,
        report_code=report_code,
        actor_names=actor_names,
        max_deaths=death_limit,
    )

    observations: List[MechanicObservation] = []
    for pull_index, fight in enumerate(chosen, start=1):
        cutoff = death_cutoffs.get(fight.id)
        event_end = min(float(fight.end), cutoff) if cutoff is not None else float(fight.end)
        events_by_type: Dict[str, List[dict]] = {}
        for data_type in sorted(REQUIRED_DATA_TYPES[boss_id]):
            events_by_type[data_type] = list(
                fetch_events(
                    session,
                    bearer,
                    code=report_code,
                    data_type=data_type,
                    start=fight.start,
                    end=event_end,
                    limit=10_000,
                    actor_names=actor_names,
                )
            )
        context = FightMechanicContext(
            report_code=report_code,
            fight=fight,
            pull_index=pull_index,
            participants=participants_by_fight.get(fight.id, set()),
            known_players=known_players,
            events_by_type=events_by_type,
        )
        observations.extend(analyze_fight(boss_id, context))

    player_classes = {
        name: actor_classes.get(actor_id)
        for actor_id, name in actor_names.items()
        if name in known_players
    }
    _apply_role_aware_rules(observations, player_roles)
    return _build_summary(
        report_code=report_code,
        boss_id=boss_id,
        fight_name=fight_name,
        fight_ids=fight_ids,
        fight_selection=fight_selection,
        pull_count=len(chosen),
        ignore_after_deaths=death_limit,
        observations=observations,
        pulls_by_player=dict(pulls_by_player),
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        source_reports=[report_code],
    )


def _build_summary(
    *,
    report_code: str,
    boss_id: str,
    fight_name: str,
    fight_ids: Optional[List[int]],
    fight_selection: str,
    pull_count: int,
    ignore_after_deaths: Optional[int],
    observations: Sequence[MechanicObservation],
    pulls_by_player: Dict[str, int],
    player_classes: Dict[str, Optional[str]],
    player_roles: Dict[str, str],
    player_specs: Dict[str, Optional[str]],
    source_reports: List[str],
) -> MechanicScorecardSummary:
    players = set(pulls_by_player)
    observations_by_mechanic: DefaultDict[str, DefaultDict[str, List[MechanicObservation]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for observation in observations:
        observations_by_mechanic[observation.mechanic_id][observation.player].append(observation)
        players.add(observation.player)

    views: List[MechanicScoreView] = []
    for mechanic in MECHANICS_BY_BOSS[boss_id]:
        entries: List[MechanicScoreEntry] = []
        mechanic_events = observations_by_mechanic.get(mechanic.id, {})
        view_players = set(players)
        if TEAM_PLAYER not in mechanic_events:
            view_players.discard(TEAM_PLAYER)
        for player in view_players:
            events = sorted(
                mechanic_events.get(player, []),
                key=lambda event: (event.source_report_code or "", event.pull_index, event.timestamp),
            )
            successes = sum(event.outcome == OUTCOME_SUCCESS for event in events)
            mistakes = sum(event.outcome == OUTCOME_MISTAKE for event in events)
            contributions = sum(event.outcome == OUTCOME_CONTRIBUTION for event in events)
            opportunities = successes + mistakes
            entries.append(
                MechanicScoreEntry(
                    player=player,
                    role="Team" if player == TEAM_PLAYER else player_roles.get(player, ROLE_UNKNOWN),
                    class_name=None if player == TEAM_PLAYER else player_classes.get(player),
                    pulls=pull_count if player == TEAM_PLAYER else pulls_by_player.get(player, 0),
                    opportunities=opportunities,
                    successes=successes,
                    mistakes=mistakes,
                    contributions=contributions,
                    success_rate=(successes / opportunities * 100.0) if opportunities else None,
                    events=events,
                )
            )
        entries.sort(
            key=lambda entry: (
                -entry.mistakes,
                -entry.successes,
                -entry.contributions,
                ROLE_PRIORITY.get(entry.role, 5),
                entry.player.casefold(),
            )
        )
        views.append(MechanicScoreView(mechanic=mechanic, entries=entries))

    return MechanicScorecardSummary(
        report_code=report_code,
        boss_id=boss_id,
        boss_name=SCORECARD_ENCOUNTERS[boss_id]["boss_name"],
        fight_filter=fight_name,
        fight_ids=fight_ids,
        fight_selection=fight_selection,
        pull_count=pull_count,
        ignore_after_deaths=ignore_after_deaths,
        views=views,
        player_classes={player: player_classes.get(player) for player in players if player != TEAM_PLAYER},
        player_roles={player: player_roles.get(player, ROLE_UNKNOWN) for player in players if player != TEAM_PLAYER},
        player_specs={player: player_specs.get(player) for player in players if player != TEAM_PLAYER},
        source_reports=source_reports,
    )


def _merge_summaries(summaries: Sequence[MechanicScorecardSummary]) -> MechanicScorecardSummary:
    first = summaries[0]
    observations: List[MechanicObservation] = []
    pulls_by_player: DefaultDict[str, int] = defaultdict(int)
    player_classes: Dict[str, Optional[str]] = {}
    player_roles: Dict[str, str] = {}
    player_specs: Dict[str, Optional[str]] = {}
    sources: List[str] = []
    for summary in summaries:
        sources.extend(code for code in summary.source_reports if code not in sources)
        for view_index, view in enumerate(summary.views):
            for entry in view.entries:
                if entry.player == TEAM_PLAYER:
                    continue
                if view_index == 0:
                    pulls_by_player[entry.player] += entry.pulls
                observations.extend(entry.events)
        for player, class_name in summary.player_classes.items():
            player_classes.setdefault(player, class_name)
        for player, role in summary.player_roles.items():
            if player_roles.get(player) in (None, ROLE_UNKNOWN):
                player_roles[player] = role
        for player, spec in summary.player_specs.items():
            if not player_specs.get(player):
                player_specs[player] = spec

    # Events live in exactly one mechanic view, while participant pull counts
    # appear in every view. Pulls are therefore collected from the first view.
    return _build_summary(
        report_code=first.report_code,
        boss_id=first.boss_id,
        fight_name=first.fight_filter,
        fight_ids=first.fight_ids,
        fight_selection=first.fight_selection,
        pull_count=sum(summary.pull_count for summary in summaries),
        ignore_after_deaths=first.ignore_after_deaths,
        observations=observations,
        pulls_by_player=dict(pulls_by_player),
        player_classes=player_classes,
        player_roles=player_roles,
        player_specs=player_specs,
        source_reports=sources,
    )


def _apply_role_aware_rules(
    observations: Iterable[MechanicObservation],
    player_roles: Dict[str, str],
) -> None:
    for observation in observations:
        if (
            observation.mechanic_id == "stone-breaker"
            and observation.outcome == OUTCOME_CONTRIBUTION
            and player_roles.get(observation.player) != "Tank"
        ):
            observation.outcome = OUTCOME_MISTAKE
            observation.label = "Non-tank Stone Breaker contact"
            observation.description = "A non-tank was hit by the tank split-damage mechanic."


def _normalize_fight_selection(value: Any) -> str:
    normalized = str(value or FIGHT_SELECTION_ALL).strip().lower()
    if normalized not in FIGHT_SELECTIONS:
        raise ValueError(f"Unknown fight selection '{value}'.")
    return normalized


def _apply_fight_selection(
    fights: Iterable[Fight], fight_selection: str
) -> List[Fight]:
    chosen = list(fights)
    selection = _normalize_fight_selection(fight_selection)
    if selection == FIGHT_SELECTION_LAST and chosen:
        return [
            max(
                chosen,
                key=lambda fight: (
                    float(getattr(fight, "start", 0.0) or 0.0),
                    int(fight.id),
                ),
            )
        ]
    return chosen


__all__ = [
    "FIGHT_SELECTION_ALL",
    "FIGHT_SELECTION_LAST",
    "FIGHT_SELECTION_SPECIFIC",
    "FIGHT_SELECTIONS",
    "SCORECARD_ENCOUNTERS",
    "fetch_mechanic_scorecard_summary",
]
