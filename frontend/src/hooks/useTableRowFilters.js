import { useReportViewState } from "./useReportViewState";
import { useMemo } from "react";

function defaultSelectedIds(filter) {
  return (filter?.options ?? [])
    .filter((option) => option.defaultSelected !== false)
    .map((option) => option.id);
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

export function useTableRowFilters(table, viewKey = "") {
  const config = table?.rowFilter ?? null;
  const [selectedRowValues, setSelectedRowValues] = useReportViewState("rows", () => defaultSelectedIds(config), { resetKey: viewKey, validate: (ids) => ids.every((id) => config?.options?.some((option) => option.id === id)) });

  const filteredTable = useMemo(() => {
    if (!table || !config) {
      return table ?? null;
    }

    const selected = new Set(selectedRowValues);
    return {
      ...table,
      rows: (table.rows ?? []).filter((row) =>
        selected.has(String(row?.cells?.[config.id]?.value ?? ""))
      ),
    };
  }, [config, selectedRowValues, table]);

  return {
    config,
    selectedRowValues,
    toggleRowValue: (value) =>
      setSelectedRowValues((current) =>
        toggleOption(current, value, config?.options)
      ),
    filteredTable,
  };
}
