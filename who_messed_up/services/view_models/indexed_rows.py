"""Opt-in wire format that stores row bodies once and references them per view.

Apply after presentation has finished. Row objects and all evidence stay intact;
only the table's row lists change. Equal IDs with different content receive
different storage keys, so encounter-specific row-ID reuse never loses data.
"""


def index_report_rows(page):
    table = page["content"]["table"]
    if table.get("rowStorage") == "indexed":
        return page
    rows_by_id = {}
    keys_by_id = {}

    def references(rows):
        keys = []
        for row in rows:
            candidates = keys_by_id.setdefault(row["id"], [])
            key = next((key for key in candidates if rows_by_id[key] == row), None)
            if key is None:
                # Storage keys are deliberately separate from display row IDs.
                key = str(len(rows_by_id))
                rows_by_id[key] = row
                candidates.append(key)
            keys.append(key)
        return keys

    indexed = {
        **table, "rowStorage": "indexed", "rowsById": rows_by_id,
        "rowIds": references(table["rows"]),
        "rowIdsByView": {key: references(rows) for key, rows in table["rowsByView"].items()},
        "rowIdsByCombinedView": {key: references(rows) for key, rows in table["rowsByCombinedView"].items()},
        "rows": [], "rowsByView": {}, "rowsByCombinedView": {},
    }
    return {**page, "content": {**page["content"], "table": indexed}}
