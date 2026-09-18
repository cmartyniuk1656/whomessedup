"""Small aggregate-report helpers shared across encounters.

The shell retains pull controls for live watching; actual report content belongs
only to the selected child. Fetch expensive mechanics first without reordering
the user-facing report selector.
"""


def aggregate_execution_order(children):
    return sorted(range(len(children)), key=lambda index:
                  "mechanics" not in children[index]["report_id"].split("-"))


def aggregate_shell(page):
    table = page["content"]["table"]
    return {
        **page,
        "summary": [], "summaryByView": {}, "summaryByCombinedView": {},
        "specAnalysis": None, "footnotes": [],
        "content": {"variant": "table", "table": {
            "columns": [], "rows": [], "defaultSort": table["defaultSort"],
            "viewControl": table.get("viewControl"), "emptyState": table["emptyState"],
        }},
    }
