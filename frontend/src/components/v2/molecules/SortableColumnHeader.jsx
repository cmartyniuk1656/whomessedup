function SortIcon({ active, direction }) {
  const symbol = active ? (direction === "asc" ? "\u25B2" : "\u25BC") : "\u2195";

  return (
    <span
      aria-hidden="true"
      className={`inline-flex w-3 justify-center text-[11px] leading-none ${
        active ? "text-emerald-300" : "text-slate-500"
      }`}
    >
      {symbol}
    </span>
  );
}

export function SortableColumnHeader({ column, sortConfig, onSort }) {
  const isActive = sortConfig?.columnId === column.id;
  const alignClass = column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left";
  const justifyClass = column.align === "right" ? "justify-end" : column.align === "center" ? "justify-center" : "justify-start";

  if (!column.sortable) {
    return <span className={alignClass}>{column.label}</span>;
  }

  return (
    <button
      type="button"
      className={`flex w-full items-center gap-2 ${justifyClass} ${alignClass} transition hover:text-slate-200`}
      onClick={() => onSort(column)}
    >
      {column.align === "right" ? (
        <>
          <SortIcon active={isActive} direction={sortConfig?.direction} />
          {column.label}
        </>
      ) : (
        <>
          {column.label}
          <SortIcon active={isActive} direction={sortConfig?.direction} />
        </>
      )}
    </button>
  );
}
