// Resolve only the selected view. Indexed tables share evidence row objects
// instead of expanding every scope back into duplicate rows in browser memory.
export function resolveReportRows(table, viewId, combinedViewId, defaultViewId) {
  if (table?.rowStorage === "indexed") {
    const keys =
      (combinedViewId ? table.rowIdsByCombinedView?.[combinedViewId] : null) ??
      table.rowIdsByView?.[viewId] ??
      table.rowIdsByView?.[defaultViewId] ??
      table.rowIds ?? [];
    return keys.map((key) => table.rowsById[key]);
  }
  return (
    (combinedViewId ? table?.rowsByCombinedView?.[combinedViewId] : null) ??
    table?.rowsByView?.[viewId] ??
    table?.rowsByView?.[defaultViewId] ??
    table?.rows ?? []
  );
}
