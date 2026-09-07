"""Shared view-control helpers for aggregate and per-pull report tables."""
from __future__ import annotations

from typing import Iterable, Optional

from ..report_pulls import ReportPull
from .common import TableViewControlModel, TableViewOptionModel


AGGREGATE_VIEW_ID = "aggregate"


def build_pull_view_control(
    pulls: Iterable[ReportPull],
    *,
    control_id: str = "pull_view",
) -> Optional[TableViewControlModel]:
    selected_pulls = list(pulls)
    if not selected_pulls:
        return None
    return TableViewControlModel(
        id=control_id,
        label="Pull",
        defaultValue=AGGREGATE_VIEW_ID,
        options=[TableViewOptionModel(value=AGGREGATE_VIEW_ID, label="All pulls")]
        + [TableViewOptionModel(value=pull.view_id, label=pull.label) for pull in selected_pulls],
    )


__all__ = ["AGGREGATE_VIEW_ID", "build_pull_view_control"]
