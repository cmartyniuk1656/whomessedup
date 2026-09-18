"""Fetch Mythic Vashnik evidence; calculators also accept recorded event streams."""
from concurrent.futures import ThreadPoolExecutor

import requests

from ..api import fetch_events_grouped, fetch_fights
from ..env import load_env
from .common import _resolve_token, _sanitize_report_code, _select_fights
from .mechanics_context import PullContext
from .report_pulls import build_report_pulls, merge_report_pulls
from .vashnik_mechanics_adds import build_adds
from .vashnik_mechanics_bile import build_bile
from .vashnik_mechanics_infections import build_dispels, build_stygian
from .vashnik_mechanics_models import REPORT_DEFAULT_FIGHT, VIEWS, VashnikMechanicsSummary
from .vashnik_mechanics_waves import build_froth, build_totems, build_totem_waves

BUILDERS = dict(totems=build_totems, froth=build_froth, dispels=build_dispels,
                stygian=build_stygian, adds=build_adds, bile=build_bile, totem_waves=build_totem_waves)
ADD_FILTER = 'target.name in ("Burning Venom", "Shrouded Venom", "Clotting Venom")'
STREAM_SPECS = {
    "totems": dict(data_type="All", extra_filter='source.name = "Malignant Totem" or target.name = "Malignant Totem"'),
    "debuffs": dict(data_type="Debuffs", extra_filter="ability.id in (1281913,1295173,1294994,1285979)"),
    "deaths": dict(data_type="Deaths"),
    "enemy_casts": dict(data_type="Casts", hostility_type="Enemies",
                        extra_filter="ability.id in (1284663,1282509,1285979,1280189)"),
    "dispels": dict(data_type="Dispels"),
    "stygian_absorbs": dict(data_type="All", extra_filter='type = "healabsorbed" and ability.id = 1294994'),
    "enemy_deaths": dict(data_type="Deaths", hostility_type="Enemies", extra_filter=ADD_FILTER),
    "add_summons": dict(data_type="All", extra_filter='type = "summon" and ' + ADD_FILTER),
    "enemy_buffs": dict(data_type="Buffs", hostility_type="Enemies",
                        extra_filter="ability.id in (1312366,1293971,1293968)"),
    "add_damage": dict(data_type="DamageDone", extra_filter=ADD_FILTER),
    "damage_taken": dict(data_type="DamageTaken",
                         extra_filter="ability.id in (1281925,1295798,1295209,1302489,1282602,1282616,1285979,1305901,1280189,1305833,1286737)"),
}


def build_vashnik_mechanics_summary(*, report_code, fights, streams, actor_names, actor_classes, actor_owners):
    sets = {view: [] for view in BUILDERS}
    for index, fight in enumerate(fights, 1):
        ctx = PullContext(report_code, fight, index,
                          {key: grouped.get(fight.id, []) for key, grouped in streams.items()},
                          actor_names, actor_owners)
        for view, builder in BUILDERS.items():
            sets[view].extend(builder(ctx))
    return VashnikMechanicsSummary(
        report_code, sets, build_report_pulls(report_code, fights, {}),
        {name: actor_classes[aid] for aid, name in actor_names.items() if actor_classes.get(aid)}, [report_code],
    )


def _fetch_streams(code, fights, bearer, names):
    if not fights:
        return {}

    def fetch(item):
        name, spec = item
        with requests.Session() as session:
            grouped = fetch_events_grouped(session, bearer, code=code, fights=fights,
                                           actor_names=names, limit=10000, **spec)
        return name, grouped

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(fetch, STREAM_SPECS.items()))


def fetch_vashnik_mechanics_summary(*, report_code, fight_name=None, fight_ids=None,
                                    difficulty="mythic", extra_report_codes=None,
                                    token=None, client_id=None, client_secret=None):
    """Restrict the mechanics report to Mythic encounter 3455, including wipes."""
    load_env()
    bearer = _resolve_token(token, client_id, client_secret)
    codes = list(dict.fromkeys(_sanitize_report_code(c) for c in [report_code, *(extra_report_codes or [])]))
    summaries = []
    for code in codes:
        with requests.Session() as session:
            fights, names, classes, owners = fetch_fights(session, bearer, code)
        chosen = _select_fights([f for f in fights if f.encounter_id == 3455],
                                name_filter=fight_name or REPORT_DEFAULT_FIGHT,
                                fight_ids=fight_ids, difficulty="mythic")
        summaries.append(build_vashnik_mechanics_summary(
            report_code=code, fights=chosen, streams=_fetch_streams(code, chosen, bearer, names),
            actor_names=names, actor_classes=classes, actor_owners=owners,
        ))
    return VashnikMechanicsSummary(
        codes[0], {view: [row for summary in summaries for row in summary.sets[view]] for view in BUILDERS},
        merge_report_pulls([summary.pulls for summary in summaries]),
        {name: cls for summary in summaries for name, cls in summary.player_classes.items()}, codes,
    )
