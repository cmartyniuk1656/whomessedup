import { Fragment, useEffect, useRef, useState } from "react";
import { EventGroupList } from "../molecules/EventGroupList";
import { SortableColumnHeader } from "../molecules/SortableColumnHeader";
import { TableCellContent } from "../molecules/TableCellContent";

const DETAIL_ANIMATION_MS = 220;

function groupRowsForDisplay(rows) {
  if (!rows.some((row) => row?.group?.id)) {
    return [{ id: "all-rows", group: null, rows }];
  }

  const sections = new Map();
  rows.forEach((row) => {
    const group = row?.group;
    const groupId = group?.id || `ungrouped-${row.id}`;
    if (!sections.has(groupId)) {
      sections.set(groupId, {
        id: groupId,
        group,
        rows: [],
        insertionOrder: sections.size,
      });
    }
    sections.get(groupId).rows.push(row);
  });

  return [...sections.values()].sort((left, right) => {
    const leftSort = left.group?.sortValue;
    const rightSort = right.group?.sortValue;
    if (typeof leftSort === "number" && typeof rightSort === "number") {
      return leftSort - rightSort;
    }
    return left.insertionOrder - right.insertionOrder;
  });
}

export function ReportTable({ table, rows, sortConfig, onSort, pageKey }) {
  const [expandedRows, setExpandedRows] = useState({});
  const [mountedDetailRows, setMountedDetailRows] = useState({});
  const closingTimersRef = useRef({});

  const clearClosingTimer = (rowId) => {
    const timer = closingTimersRef.current[rowId];
    if (timer) {
      window.clearTimeout(timer);
      delete closingTimersRef.current[rowId];
    }
  };

  useEffect(() => {
    Object.values(closingTimersRef.current).forEach((timer) => window.clearTimeout(timer));
    closingTimersRef.current = {};
    setExpandedRows({});
    setMountedDetailRows({});
  }, [pageKey]);

  useEffect(
    () => () => {
      Object.values(closingTimersRef.current).forEach((timer) => window.clearTimeout(timer));
    },
    []
  );

  if (!table) {
    return null;
  }

  const usesRelativeBars = table.columns.some(
    (column) => column.cellKind === "relative_bar"
  );

  const toggleRow = (rowId) => {
    if (expandedRows[rowId]) {
      setExpandedRows((current) => ({ ...current, [rowId]: false }));
      clearClosingTimer(rowId);
      closingTimersRef.current[rowId] = window.setTimeout(() => {
        setMountedDetailRows((current) => {
          const next = { ...current };
          delete next[rowId];
          return next;
        });
        delete closingTimersRef.current[rowId];
      }, DETAIL_ANIMATION_MS);
      return;
    }

    clearClosingTimer(rowId);
    setMountedDetailRows((current) => ({ ...current, [rowId]: true }));
    window.requestAnimationFrame(() => {
      setExpandedRows((current) => ({ ...current, [rowId]: true }));
    });
  };

  const rowSections = groupRowsForDisplay(rows);

  return (
    <div className="overflow-x-auto rounded-xl border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.015))] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <table className="min-w-full divide-y divide-white/10 text-sm">
        <thead className="bg-slate-950/55 text-xs uppercase tracking-[0.16em] text-slate-400">
          <tr>
            {table.columns.map((column) => {
              const alignClass =
                column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left";
              return (
                <th
                  key={column.id}
                  className={`${usesRelativeBars ? "px-3 py-3" : "px-4 py-3.5"} ${alignClass}`}
                >
                  <SortableColumnHeader column={column} sortConfig={sortConfig} onSort={onSort} />
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/10 text-slate-100">
          {rows.length ? (
            rowSections.map((section, groupIndex) => (
              <Fragment key={section.id}>
                {section.group ? (
                  <tr className="border-t-2 border-emerald-300/25 bg-[linear-gradient(90deg,rgba(16,185,129,0.13),rgba(14,165,233,0.06),rgba(15,23,42,0.2))]">
                    <td colSpan={table.columns.length} className="px-4 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                          {section.group.href ? (
                            <a
                              href={section.group.href}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sm font-bold tracking-wide text-emerald-200 underline decoration-emerald-300/40 underline-offset-4 hover:text-emerald-100"
                            >
                              {section.group.label}
                            </a>
                          ) : (
                            <span className="text-sm font-bold tracking-wide text-emerald-200">
                              {section.group.label}
                            </span>
                          )}
                          {section.group.subtitle ? (
                            <span className="text-xs text-slate-400">{section.group.subtitle}</span>
                          ) : null}
                        </div>
                        {section.group.href ? (
                          <a
                            href={section.group.href}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300/80 hover:text-emerald-200"
                          >
                            View pull ↗
                          </a>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ) : null}
                {section.rows.map((row) => {
                  const hasDetails = Boolean(
                    row?.details?.groups?.length || row?.details?.barChart
                  );
                  const isExpanded = Boolean(expandedRows[row.id]);
                  const shouldRenderDetails = hasDetails && Boolean(mountedDetailRows[row.id]);
                  const groupSurface = section.group
                    ? groupIndex % 2 === 0
                      ? "bg-emerald-950/[0.055]"
                      : "bg-sky-950/[0.07]"
                    : "";

                  return (
                    <Fragment key={row.id}>
                  <tr
                    className={`transition ${groupSurface} ${hasDetails ? "cursor-pointer hover:bg-white/[0.05]" : "hover:bg-white/[0.03]"}`}
                    onClick={() => {
                      if (hasDetails) {
                        toggleRow(row.id);
                      }
                    }}
                  >
                    {table.columns.map((column, index) => {
                      const alignClass =
                        column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left";
                      return (
                        <td
                          key={`${row.id}-${column.id}`}
                          className={`${usesRelativeBars ? "px-3 py-2" : "px-4 py-3.5"} ${alignClass}`}
                        >
                          <div>
                            <TableCellContent column={column} cell={row.cells?.[column.id]} />
                            {index === 0 && hasDetails ? (
                              <button
                                type="button"
                                className={
                                  usesRelativeBars
                                    ? "sr-only"
                                    : "mt-1 block text-xs font-medium text-emerald-300 transition hover:text-emerald-200"
                                }
                                onClick={(event) => {
                                  event.stopPropagation();
                                  toggleRow(row.id);
                                }}
                              >
                                {isExpanded ? "Hide details" : "Show details"}
                              </button>
                            ) : null}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                  {shouldRenderDetails ? (
                    <tr className={isExpanded ? "bg-slate-950/35" : "bg-slate-950/10"}>
                      <td
                        colSpan={table.columns.length}
                        className={[
                          "px-4 transition-[padding] duration-200 ease-out motion-reduce:transition-none",
                          isExpanded ? "py-4" : "py-0",
                        ].join(" ")}
                      >
                        <div
                          className={[
                            "grid transition-[grid-template-rows,opacity,transform] duration-200 ease-out motion-reduce:translate-y-0 motion-reduce:transition-none",
                            isExpanded ? "grid-rows-[1fr] translate-y-0 opacity-100" : "grid-rows-[0fr] -translate-y-1 opacity-0",
                          ].join(" ")}
                        >
                          <div className="overflow-hidden">
                            <EventGroupList details={row.details} />
                          </div>
                        </div>
                      </td>
                    </tr>
                  ) : null}
                    </Fragment>
                  );
                })}
              </Fragment>
            ))
          ) : (
            <tr>
              <td colSpan={table.columns.length} className="px-4 py-8 text-center text-slate-400">
                {table.emptyState}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
