import { TableMultiSelectFilter } from "../molecules/TableMultiSelectFilter";

export function DamageTableFilters({
  config,
  selectedTargets,
  selectedMetrics,
  onToggleTarget,
  onToggleMetric,
}) {
  if (!config) {
    return null;
  }

  return (
    <div className="grid gap-4 border-y border-white/10 py-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)] lg:gap-6">
      <TableMultiSelectFilter
        filter={config.targetFilter}
        selectedIds={selectedTargets}
        onToggle={onToggleTarget}
      />
      <TableMultiSelectFilter
        filter={config.metricFilter}
        selectedIds={selectedMetrics}
        onToggle={onToggleMetric}
      />
    </div>
  );
}
