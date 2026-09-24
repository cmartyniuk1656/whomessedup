"""Optional read-only Lorrgs reference samples; failures never hide the user's logs.

Lorrgs can track buff applications as well as casts. Keep its observation type
and compare only personal defensives/consumables, not received externals.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import lru_cache

import requests

from .defensive_catalog import defensive_catalog

API = "https://api2.lorrgs.io/api/"


@lru_cache(maxsize=128)
def _get(path, hour):
    response = requests.get(API + path, timeout=12)
    response.raise_for_status()
    return response.json()


def normalize_reference(ranking, tracked, *, spec_id, spec_slug, boss_slug, difficulty):
    if ranking.get("spec_slug") != spec_slug or ranking.get("boss_slug") != boss_slug or ranking.get("difficulty") != difficulty:
        raise ValueError("Reference does not match this specialization, boss and difficulty")
    abilities, _, _ = defensive_catalog()
    supported = {}
    for sid, ability in abilities.items():
        # External/raid records may describe a received buff, not the player's cast.
        if (ability["category"] not in ("personal", "consumable") or str(sid) not in tracked
                or tracked[str(sid)].get("query") is False):
            continue
        supported[sid] = tracked[str(sid)]
    samples, seen = [], set()
    for report in ranking.get("reports", []):
        for fight in report.get("fights", []):
            for player in fight.get("players", []):
                key = (report["report_id"], fight["fight_id"], player["source_id"])
                if key in seen or player.get("spec_slug") != spec_slug: continue
                seen.add(key)
                duration = fight["duration"] / 1000
                samples.append(dict(id=":".join(map(str, key)), duration=duration,
                    url=f"https://www.warcraftlogs.com/reports/{key[0]}?fight={key[1]}&source={key[2]}",
                    date=fight.get("start_time"),
                    events=[dict(spellId=c["id"], time=round(c["ts"]/1000, 3),
                                 observation=supported[c["id"]].get("event_type", "unknown"))
                            for c in player.get("casts", []) if c["id"] in supported and 0 <= c["ts"] <= fight["duration"]],
                    bossEvents=[dict(spellId=c["id"], time=round(c["ts"]/1000, 3))
                                for c in (fight.get("boss") or {}).get("casts", []) if 0 <= c["ts"] <= fight["duration"]]))
                if len(samples) >= 50: break
            if len(samples) >= 50: break
        if len(samples) >= 50: break
    return dict(status="available" if samples else "unavailable", specId=spec_id, samples=samples,
                trackedSpellIds=list(supported), metric=ranking.get("metric"), difficulty=difficulty,
                sourceUrl=f"https://lorrgs.io/spec_ranking/{spec_slug}/{boss_slug}?difficulty={difficulty}",
                retrievedAt=datetime.now(timezone.utc).isoformat(),
                note="Top parses are reference observations, not a defensive score. Builds, assignments and damage exposure differ. Lorrgs may record buffs rather than casts; untracked spells are not counted as unused.")


def fetch_defensive_references(spec_ids, *, encounter_id, difficulty):
    hour = int(time.time() // 3600)
    try:
        specs = {s["id"]: s["full_name_slug"] for s in _get("specs", hour)["specs"]}
        bosses = {b["id"]: b["full_name_slug"] for b in _get("bosses", hour)["bosses"]}
        boss_slug = bosses[encounter_id]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return {str(spec): dict(status="unavailable", samples=[], note="Lorrgs reference data is unavailable. Your recorded usage is unaffected.") for spec in spec_ids}

    def fetch(spec):
        try:
            slug = specs[spec]
            ranking = _get(f"spec_ranking/{slug}/{boss_slug}?difficulty={difficulty}", hour)
            tracked = _get(f"specs/{slug}/spells", hour)
            result = normalize_reference(ranking, tracked, spec_id=spec, spec_slug=slug,
                                         boss_slug=boss_slug, difficulty=difficulty)
        except (requests.RequestException, ValueError, KeyError, TypeError):
            result = dict(status="unavailable", samples=[], note="No matching Lorrgs sample is available for this boss, difficulty and specialization.")
        return str(spec), result

    with ThreadPoolExecutor(max_workers=4) as executor:
        return dict(executor.map(fetch, sorted(spec_ids)))
