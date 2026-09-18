"""Complete death recaps despite WCL's unpaginated 200-entry table limit.

Split saturated requests on fight boundaries, retaining each fight's full time
range so the killing blow and preceding damage recap are not cropped. Short
reports still need only one request. Never silently accept a saturated leaf.
"""
from ..api import fetch_table

DEATH_TABLE_LIMIT = 200


def fetch_complete_death_table(session, token, *, code, fights):
    selected = list(fights)
    if not selected:
        return {"entries": []}

    def fetch_batch(batch):
        table = fetch_table(
            session, token, code=code, data_type="Deaths",
            fight_ids=[fight.id for fight in batch],
            start=min(float(fight.start) for fight in batch),
            end=max(float(fight.end) for fight in batch),
        )
        entries = table.get("entries") or []
        if len(entries) < DEATH_TABLE_LIMIT:
            return entries
        if len(batch) == 1:
            raise RuntimeError(
                f"WCL returned the {DEATH_TABLE_LIMIT}-death table limit for fight {batch[0].id}. "
                "Cannot verify complete death recaps for this pull; refusing to return a partial report."
            )
        midpoint = len(batch) // 2
        return fetch_batch(batch[:midpoint]) + fetch_batch(batch[midpoint:])

    return {"entries": fetch_batch(selected)}
