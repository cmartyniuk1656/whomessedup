import { useEffect, useMemo, useState } from "react";

function defaultSelectedIds(filter) {
  return (filter?.options ?? []).filter((option) => option.defaultSelected !== false).map((option) => option.id);
}

function toggleOption(current, optionId, options) {
  const selected = new Set(current);
  if (selected.has(optionId)) {
    selected.delete(optionId);
  } else {
    selected.add(optionId);
  }
  return (options ?? []).map((option) => option.id).filter((id) => selected.has(id));
}

function asNumber(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

export function useDamageTableFilters(table) {
  const config = table?.damageFilterConfig ?? null;
  const [selectedTargets, setSelectedTargets] = useState([]);
  const [selectedMetrics, setSelectedMetrics] = useState([]);

  useEffect(() => {
    if (!config) {
      setSelectedTargets([]);
      setSelectedMetrics([]);
      return;
    }
    setSelectedTargets(defaultSelectedIds(config.targetFilter));
    setSelectedMetrics(defaultSelectedIds(config.metricFilter));
  }, [config]);

  const filteredTable = useMemo(() => {
    if (!table || !config) {
      return table ?? null;
    }

    const selectedTargetIds = new Set(selectedTargets);
    const selectedMetricIds = new Set(selectedMetrics);
    const targetColumnGroups = config.targetColumns ?? [];
    const totalGroupByColumnId = new Map(targetColumnGroups.map((group) => [group.totalColumnId, group]));
    const averageGroupByColumnId = new Map(targetColumnGroups.map((group) => [group.averageColumnId, group]));
    const selectedTargetGroups = targetColumnGroups.filter((group) => selectedTargetIds.has(group.targetId));
    const showSelectedColumns = selectedTargetGroups.length !== 1;

    const columns = (table.columns ?? []).filter((column) => {
      if (column.id === config.selectedTotalColumnId) {
        return showSelectedColumns && selectedMetricIds.has("totals");
      }
      if (column.id === config.selectedAverageColumnId) {
        return showSelectedColumns && selectedMetricIds.has("averages");
      }
      const totalGroup = totalGroupByColumnId.get(column.id);
      if (totalGroup) {
        return selectedMetricIds.has("totals") && selectedTargetIds.has(totalGroup.targetId);
      }
      const averageGroup = averageGroupByColumnId.get(column.id);
      if (averageGroup) {
        return selectedMetricIds.has("averages") && selectedTargetIds.has(averageGroup.targetId);
      }
      return true;
    });

    const rows = (table.rows ?? []).map((row) => {
      const currentCells = row?.cells ?? {};
      const nextCells = { ...currentCells };

      if (config.selectedTotalColumnId && currentCells[config.selectedTotalColumnId]) {
        const nextTotal = selectedTargetGroups.reduce(
          (sum, group) => sum + asNumber(currentCells[group.totalColumnId]?.value),
          0
        );
        nextCells[config.selectedTotalColumnId] = {
          ...currentCells[config.selectedTotalColumnId],
          value: nextTotal,
          sortValue: nextTotal,
          display: undefined,
        };
      }

      if (config.selectedAverageColumnId && currentCells[config.selectedAverageColumnId]) {
        const nextAverage = selectedTargetGroups.reduce(
          (sum, group) => sum + asNumber(currentCells[group.averageColumnId]?.value),
          0
        );
        nextCells[config.selectedAverageColumnId] = {
          ...currentCells[config.selectedAverageColumnId],
          value: nextAverage,
          sortValue: nextAverage,
          display: undefined,
        };
      }

      return {
        ...row,
        cells: nextCells,
      };
    });

    return {
      ...table,
      columns,
      rows,
    };
  }, [config, selectedMetrics, selectedTargets, table]);

  return {
    config,
    selectedTargets,
    selectedMetrics,
    toggleTarget: (optionId) =>
      setSelectedTargets((current) => toggleOption(current, optionId, config?.targetFilter?.options)),
    toggleMetric: (optionId) =>
      setSelectedMetrics((current) => toggleOption(current, optionId, config?.metricFilter?.options)),
    filteredTable,
  };
}
