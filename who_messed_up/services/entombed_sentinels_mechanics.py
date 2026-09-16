"""Fetch and merge Mythic Sentinels mechanics evidence.

Analysis is isolated in entombed_sentinels_mechanics_analysis so recorded logs
and synthetic boundary cases exercise the same calculators as live reports.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import requests

from ..api import fetch_events_grouped, fetch_fights
from ..env import load_env
from .common import _resolve_token, _sanitize_report_code, _select_fights
from .entombed_sentinels_mechanics_analysis import BUILDERS, PullContext
from .entombed_sentinels_mechanics_models import (
    REPORT_DEFAULT_FIGHT, REPORT_DESCRIPTION, REPORT_FOOTNOTES, REPORT_ID,
    REPORT_TITLE, VIEWS, SentinelsMechanicsSummary,
)
from .report_pulls import build_report_pulls, merge_report_pulls


def build_sentinels_mechanics_summary(*, report_code, fights, streams,
                                      actor_names, actor_classes, actor_owners):
    sets = {view: [] for view in VIEWS}
    for index, fight in enumerate(fights, 1):
        ctx = PullContext(report_code, fight, index,
                          {key: grouped.get(fight.id, []) for key, grouped in streams.items()},
                          actor_names, actor_owners)
        for view, builder in BUILDERS.items():
            sets[view].extend(builder(ctx))
    return SentinelsMechanicsSummary(
        report_code, sets, build_report_pulls(report_code, fights, {}),
        {name: actor_classes.get(actor_id) for actor_id, name in actor_names.items()
         if actor_classes.get(actor_id)}, [report_code],
    )


def _fetch_streams(code, fights, bearer, names):
    specs = {
        "enemy_casts": dict(data_type="Casts", hostility_type="Enemies",
                            extra_filter="ability.id in (1296878,1284588,1284606,1288232,1284434,1284251,1284257,1284483)"),
        "debuffs": dict(data_type="Debuffs",
                        extra_filter="ability.id in (1296880,1284590,1288260,1284947,1284471)"),
        "enemy_buffs": dict(data_type="Buffs", hostility_type="Enemies",
                            extra_filter="ability.id in (1284257,1284588,1284606)"),
        "dispels": dict(data_type="Dispels"),
        "boss_healing": dict(data_type="Healing", hostility_type="Enemies", ability_id=1284635,
                             extra_filter='target.name in ("Blood of Ula\'tek", "Breath of Ula\'tek")'),
        "damage_taken": dict(data_type="DamageTaken",
                             extra_filter="ability.id in (1296962,1284941,1284948,1288282,1284451,1284452,1284258)"),
        "deaths": dict(data_type="Deaths"),
        "enemy_deaths": dict(data_type="Deaths", hostility_type="Enemies",
                             extra_filter='target.name = "Venom Coagulation"'),
        "add_damage": dict(data_type="DamageDone",
                           extra_filter='target.name = "Venom Coagulation" and effectiveDamage > 1'),
    }

    def fetch(item):
        name, spec = item
        with requests.Session() as session:
            events = fetch_events_grouped(session, bearer, code=code, fights=fights,
                                          actor_names=names, limit=10000, **spec)
        return name, events

    with ThreadPoolExecutor(max_workers=4) as executor:
        return dict(executor.map(fetch, specs.items()))


def fetch_sentinels_mechanics_summary(*, report_code, fight_name=None, fight_ids=None,
                                     difficulty="mythic", extra_report_codes=None,
                                     token=None, client_id=None, client_secret=None):
    """Only Mythic encounter 3445 is eligible, including all selected wipes."""
    load_env()
    bearer = _resolve_token(token, client_id, client_secret)
    codes = [_sanitize_report_code(report_code)]
    for raw in extra_report_codes or ():
        code = _sanitize_report_code(raw)
        if code not in codes:
            codes.append(code)
    summaries = []
    for code in codes:
        with requests.Session() as session:
            fights, names, classes, owners = fetch_fights(session, bearer, code)
        chosen = _select_fights([f for f in fights if f.encounter_id == 3445],
                                name_filter=fight_name or REPORT_DEFAULT_FIGHT,
                                fight_ids=fight_ids, difficulty="mythic")
        streams = _fetch_streams(code, chosen, bearer, names)
        summaries.append(build_sentinels_mechanics_summary(
            report_code=code, fights=chosen, streams=streams,
            actor_names=names, actor_classes=classes, actor_owners=owners,
        ))
    return SentinelsMechanicsSummary(
        codes[0],
        {view: [row for summary in summaries for row in summary.sets[view]] for view in VIEWS},
        merge_report_pulls([summary.pulls for summary in summaries]),
        {name: cls for summary in summaries for name, cls in summary.player_classes.items()}, codes,
    )


__all__ = ["REPORT_ID", "REPORT_TITLE", "REPORT_DESCRIPTION", "REPORT_DEFAULT_FIGHT",
           "REPORT_FOOTNOTES", "SentinelsMechanicsSummary", "fetch_sentinels_mechanics_summary",
           "build_sentinels_mechanics_summary"]
