import { TableMultiSelectFilter } from "../molecules/TableMultiSelectFilter";

export function TableRowFilters({
  config,
  selectedRowValues,
  onToggleRowValue,
}) {
  if (!config) {
    return null;
  }

  return (
    <div className="border-y border-white/10 py-4">
      <TableMultiSelectFilter
        filter={config}
        selectedIds={selectedRowValues}
        onToggle={onToggleRowValue}
      />
    </div>
  );
}
