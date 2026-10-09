"""Fetch scoped Mythic Twin Fangs evidence for damage, contacts, and add control."""
import requests

from ..api import fetch_fights
from ..env import load_env
from .common import _resolve_token, _sanitize_report_code, _select_fights
from .event_streams import fetch_event_streams
from .mechanics_context import PullContext
from .the_twin_fangs_mechanics_models import REPORT_DEFAULT_FIGHT, VIEWS, TwinFangsMechanicsSummary
from .the_twin_fangs_mechanics_events import build_add_damage, build_contacts
from .the_twin_fangs_mechanics_control import build_interrupts, build_shield_ccs
from .the_twin_fangs_mechanics_stacks import build_wave_contact_stacks
from .report_pulls import build_report_pulls, merge_report_pulls

ADD_FILTER = 'target.name in ("Spawn of Vexhul", "Broodling of Ithraz")'
STREAM_SPECS = {
    "pickups": dict(data_type="DamageTaken", extra_filter="ability.id = 1289201"),
    "debuffs": dict(data_type="Debuffs", extra_filter="ability.id = 1292807"),
    "venom": dict(data_type="Debuffs", extra_filter="ability.id = 1290336"),
    "add_damage": dict(data_type="DamageDone", extra_filter=ADD_FILTER),
    "summons": dict(data_type="All", extra_filter='type = "summon" and ' + ADD_FILTER),
    "enemy_deaths": dict(data_type="Deaths", hostility_type="Enemies", extra_filter=ADD_FILTER),
    "interrupts": dict(data_type="Interrupts", extra_filter=ADD_FILTER),
    "shield_control": dict(data_type="All", extra_filter='target.name = "Barbed Bulwark" and type in ("applybuff", "removebuff", "applydebuff")'),
}


def build_the_twin_fangs_mechanics_summary(*, report_code, fights, streams, actor_names, actor_classes, actor_owners):
    sets = {view: [] for view in VIEWS}
    for index, fight in enumerate(fights, 1):
        ctx = PullContext(report_code, fight, index,
                          {key: grouped.get(fight.id, []) for key, grouped in streams.items()},
                          actor_names, actor_owners)
        for view, rows in {"adds": build_add_damage(ctx), "orbs": build_contacts(ctx),
                           "waves": build_contacts(ctx, waves=True),
                           "wave_stacks": build_wave_contact_stacks(ctx),
                           "shields": build_shield_ccs(ctx), "interrupts": build_interrupts(ctx)}.items():
            sets[view].extend(rows)
    return TwinFangsMechanicsSummary(
        report_code, sets, build_report_pulls(report_code, fights, {}),
        {name: actor_classes[aid] for aid, name in actor_names.items() if actor_classes.get(aid)}, [report_code],
    )


def _fetch_streams(code, fights, bearer, names):
    return fetch_event_streams(code=code, fights=fights, token=bearer, actor_names=names,
                               streams=STREAM_SPECS, partitioned_streams=("add_damage",))


def fetch_the_twin_fangs_mechanics_summary(*, report_code, fight_name=None, fight_ids=None,
                                    difficulty="mythic", extra_report_codes=None,
                                    token=None, client_id=None, client_secret=None):
    """Query every matching Mythic pull, including wipes, with report-local IDs."""
    load_env()
    bearer = _resolve_token(token, client_id, client_secret)
    codes = list(dict.fromkeys(_sanitize_report_code(c) for c in [report_code, *(extra_report_codes or [])]))
    summaries = []
    for code in codes:
        with requests.Session() as session:
            fights, names, classes, owners = fetch_fights(session, bearer, code)
        chosen = _select_fights([f for f in fights if f.encounter_id == 3421],
                                name_filter=fight_name or REPORT_DEFAULT_FIGHT,
                                fight_ids=fight_ids, difficulty="mythic")
        summaries.append(build_the_twin_fangs_mechanics_summary(
            report_code=code, fights=chosen, streams=_fetch_streams(code, chosen, bearer, names),
            actor_names=names, actor_classes=classes, actor_owners=owners,
        ))
    return TwinFangsMechanicsSummary(
        codes[0], {view: [row for summary in summaries for row in summary.sets[view]] for view in VIEWS},
        merge_report_pulls([summary.pulls for summary in summaries]),
        {name: cls for summary in summaries for name, cls in summary.player_classes.items()}, codes,
    )
