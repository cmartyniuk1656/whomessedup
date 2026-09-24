import { useReportViewState } from "./useReportViewState";
import { useMemo } from "react";

function defaultSelectedIds(filter) {
  const selected = (filter?.options ?? [])
    .filter((option) => option.defaultSelected !== false)
    .map((option) => option.id);
  return filter?.kind === "single_select" ? selected.slice(0, 1) : selected;
}

function toggleOption(current, optionId, options) {
  const selected = new Set(current);
  if (selected.has(optionId)) {
    selected.delete(optionId);
  } else {
    selected.add(optionId);
  }
  return (options ?? [])
    .map((option) => option.id)
    .filter((id) => selected.has(id));
}

export function useTableColumnFilters(table, viewKey = "") {
  const config = table?.columnFilter ?? null;
  const [selectedColumnIds, setSelectedColumnIds] = useReportViewState("columns", () => defaultSelectedIds(config), { resetKey: viewKey, validate: (ids) => ids.every((id) => config?.options?.some((option) => option.id === id)) });

  const filteredTable = useMemo(() => {
    if (!table || !config) {
      return table ?? null;
    }

    const optionalColumnIds = new Set(
      (config.options ?? []).map((option) => option.id)
    );
    const selected = new Set(selectedColumnIds);
    const columns = (table.columns ?? []).filter(
      (column) =>
        !optionalColumnIds.has(column.id) || selected.has(column.id)
    );
    const relativeBarColumns = columns.filter(
      (column) => column.cellKind === "relative_bar"
    );
    return {
      ...table,
      columns,
      defaultSort:
        relativeBarColumns.length === 1
          ? { columnId: relativeBarColumns[0].id, direction: "desc" }
          : table.defaultSort,
    };
  }, [config, selectedColumnIds, table]);

  return {
    config,
    selectedColumnIds,
    toggleColumn: (columnId) =>
      setSelectedColumnIds((current) =>
        config?.kind === "single_select"
          ? [columnId]
          : toggleOption(current, columnId, config?.options)
      ),
    filteredTable,
  };
}
