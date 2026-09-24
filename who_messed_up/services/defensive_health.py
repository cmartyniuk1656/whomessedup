"""Recorded player health, independent of damage rates and mitigation estimates.

WCL's flattened resourceActor identifies whose snapshot is attached (1 source,
2 target). Never derive HP by subtracting damage or adding healing. Within each
250ms bucket retain the first, lowest, highest and last observations in order,
so short dangerous dips survive compression. Gaps and resurrections break lines.
"""
from collections import defaultdict
from math import isfinite


def player_health_series(streams, fight, participants):
    observations = defaultdict(list)
    for name in ("pressure", "healing", "casts"):
        for event in streams.get(name, []):
            actor = event.get({1: "sourceID", 2: "targetID"}.get(event.get("resourceActor"), ""))
            hp, maximum = event.get("hitPoints"), event.get("maxHitPoints")
            at = event.get("timestamp")
            if actor not in participants or not isinstance(at, (int, float)) or not fight.start <= at <= fight.end:
                continue
            if not all(isinstance(n, (int, float)) and isfinite(n) for n in (hp, maximum)) or maximum <= 0 or hp < 0:
                continue
            observations[actor].append((at, min(100, hp / maximum * 100)))
    for event in streams.get("deaths", []):
        actor, at = event.get("targetID"), event.get("timestamp")
        if actor in participants and isinstance(at, (int, float)) and fight.start <= at <= fight.end:
            observations[actor].append((at, 0))

    result = {}
    for actor, samples in observations.items():
        # A death alone is not enough to draw a health history.
        if not any(percent > 0 for _, percent in samples):
            continue
        buckets = defaultdict(list)
        for at, percent in sorted(samples, key=lambda sample: sample[0]):
            buckets[int((at - fight.start) // 250)].append((at, percent))
        retained = []
        for bucket in buckets.values():
            indices = {0, len(bucket) - 1, min(range(len(bucket)), key=lambda i: bucket[i][1]),
                       max(range(len(bucket)), key=lambda i: bucket[i][1])}
            retained.extend(bucket[i] for i in sorted(indices))
        points = []
        for at, percent in retained:
            point = dict(time=round((at - fight.start) / 1000, 3), percent=round(percent, 2))
            previous = points[-1] if points else None
            if previous and (point["time"] - previous["time"] > 5 or previous["percent"] == 0 < percent):
                point["breakBefore"] = True
            # Collapse the middle of a constant plateau, retaining both edges.
            if len(points) >= 2 and not point.get("breakBefore") and not previous.get("breakBefore") \
                    and points[-2]["percent"] == previous["percent"] == point["percent"]:
                points[-1] = point
            else:
                points.append(point)
        result[actor] = points
    return result
