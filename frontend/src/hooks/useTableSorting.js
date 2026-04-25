import { useEffect, useMemo, useState } from "react";

const isNumber = (value) => typeof value === "number" && Number.isFinite(value);

const normalizeForSort = (value) => {
  if (value == null) {
    return null;
  }
  if (typeof value === "boolean") {
    return value ? 1 : 0;
  }
  return value;
};

const compareValues = (left, right) => {
  const a = normalizeForSort(left);
  const b = normalizeForSort(right);

  if (a == null && b == null) {
    return 0;
  }
  if (a == null) {
    return 1;
  }
  if (b == null) {
    return -1;
  }

  if (isNumber(a) && isNumber(b)) {
    return a - b;
  }

  return String(a).localeCompare(String(b), undefined, {
    numeric: true,
    sensitivity: "base",
  });
};

const resolveSortConfig = (table, preferredSort) => {
  const columns = Array.isArray(table?.columns) ? table.columns : [];
  if (!columns.length) {
    return null;
  }

  const columnIds = new Set(columns.map((column) => column.id));
  if (preferredSort?.columnId && columnIds.has(preferredSort.columnId)) {
    return preferredSort;
  }

  if (table?.defaultSort?.columnId && columnIds.has(table.defaultSort.columnId)) {
    return table.defaultSort;
  }

  const firstSortable = columns.find((column) => column.sortable);
  if (!firstSortable) {
    return null;
  }

  return {
    columnId: firstSortable.id,
    direction: "asc",
  };
};

export function useTableSorting(table) {
  const [sortConfig, setSortConfig] = useState(table?.defaultSort ?? null);

  useEffect(() => {
    setSortConfig((current) => resolveSortConfig(table, current));
  }, [table]);

  const sortedRows = useMemo(() => {
    const rows = Array.isArray(table?.rows) ? [...table.rows] : [];
    const activeSort = resolveSortConfig(table, sortConfig);
    if (!activeSort?.columnId) {
      return rows;
    }

    const direction = activeSort.direction === "desc" ? -1 : 1;
    const columnId = activeSort.columnId;

    rows.sort((leftRow, rightRow) => {
      const leftCell = leftRow?.cells?.[columnId];
      const rightCell = rightRow?.cells?.[columnId];
      const leftValue = leftCell?.sortValue ?? leftCell?.value ?? null;
      const rightValue = rightCell?.sortValue ?? rightCell?.value ?? null;
      const diff = compareValues(leftValue, rightValue);
      if (diff !== 0) {
        return diff * direction;
      }
      return String(leftRow?.id ?? "").localeCompare(String(rightRow?.id ?? ""), undefined, {
        numeric: true,
        sensitivity: "base",
      });
    });

    return rows;
  }, [sortConfig, table]);

  const handleSort = (column) => {
    if (!column?.sortable) {
      return;
    }
    setSortConfig((previous) => {
      if (previous?.columnId === column.id) {
        return {
          columnId: column.id,
          direction: previous.direction === "asc" ? "desc" : "asc",
        };
      }
      return {
        columnId: column.id,
        direction: table?.defaultSort?.columnId === column.id ? table.defaultSort.direction : "asc",
      };
    });
  };

  return {
    sortConfig,
    sortedRows,
    handleSort,
  };
}
