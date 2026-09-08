import { TableMultiSelectFilter } from "../molecules/TableMultiSelectFilter";

export function TableColumnFilters({
  config,
  selectedColumnIds,
  onToggleColumn,
}) {
  if (!config) {
    return null;
  }

  return (
    <div className="border-y border-white/10 py-4">
      <TableMultiSelectFilter
        filter={config}
        selectedIds={selectedColumnIds}
        onToggle={onToggleColumn}
      />
    </div>
  );
}
