"""Fetch named event streams with one bounded pool and optional pull partitions.

Opt large streams into partitioning to shorten serial WCL pagination. Each task
owns a session and complete, disjoint fights; pagination and event order within
a fight remain the responsibility of fetch_events_grouped. The API's global
request semaphore still limits traffic across concurrent reports.
"""
from concurrent.futures import ThreadPoolExecutor

import requests

from ..api import fetch_events_grouped


def fetch_event_streams(*, code, fights, token, actor_names, streams,
                        partitioned_streams=(), max_workers=4, limit=10000):
    if max_workers < 1:
        raise ValueError("max_workers must be positive")
    selected = list(fights)
    if not selected:
        return {}
    if len({fight.id for fight in selected}) != len(selected):
        raise ValueError("Each fight must appear only once")
    partitioned = list(dict.fromkeys(partitioned_streams))
    if any(name not in streams for name in partitioned):
        raise ValueError("Unknown partitioned stream")

    # Keep small selections as one request per stream. Start the large streams
    # first so their pagination overlaps instead of sitting behind cheap tasks.
    count = min(max_workers, len(selected)) if len(selected) >= 4 else 1
    tasks = [(name, selected[index::count])
             for name in partitioned for index in range(count)]
    tasks.extend((name, selected) for name in streams if name not in partitioned)
    result = {name: {fight.id: [] for fight in selected} for name in streams}

    def fetch(task):
        name, subset = task
        with requests.Session() as session:
            grouped = fetch_events_grouped(
                session, token, code=code, fights=subset, actor_names=actor_names,
                limit=limit, **streams[name],
            )
        return name, grouped

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for name, grouped in pool.map(fetch, tasks):
            result[name].update(grouped)
    return result
