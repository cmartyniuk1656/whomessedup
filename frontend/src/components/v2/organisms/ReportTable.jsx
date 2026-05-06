import { Fragment, useEffect, useRef, useState } from "react";
import { EventGroupList } from "../molecules/EventGroupList";
import { SortableColumnHeader } from "../molecules/SortableColumnHeader";
import { TableCellContent } from "../molecules/TableCellContent";

const DETAIL_ANIMATION_MS = 220;

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

  return (
    <div className="overflow-x-auto rounded-xl border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.015))] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <table className="min-w-full divide-y divide-white/10 text-sm">
        <thead className="bg-slate-950/55 text-xs uppercase tracking-[0.16em] text-slate-400">
          <tr>
            {table.columns.map((column) => {
              const alignClass =
                column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left";
              return (
                <th key={column.id} className={`px-4 py-3.5 ${alignClass}`}>
                  <SortableColumnHeader column={column} sortConfig={sortConfig} onSort={onSort} />
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/10 text-slate-100">
          {rows.length ? (
            rows.map((row) => {
              const hasDetails = Boolean(row?.details?.groups?.length);
              const isExpanded = Boolean(expandedRows[row.id]);
              const shouldRenderDetails = hasDetails && Boolean(mountedDetailRows[row.id]);

              return (
                <Fragment key={row.id}>
                  <tr
                    className={`transition ${hasDetails ? "cursor-pointer hover:bg-white/[0.05]" : "hover:bg-white/[0.03]"}`}
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
                        <td key={`${row.id}-${column.id}`} className={`px-4 py-3.5 ${alignClass}`}>
                          <div>
                            <TableCellContent column={column} cell={row.cells?.[column.id]} />
                            {index === 0 && hasDetails ? (
                              <button
                                type="button"
                                className="mt-1 block text-xs font-medium text-emerald-300 transition hover:text-emerald-200"
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
                    <tr className={isExpanded ? "bg-slate-950/25" : "bg-slate-950/10"}>
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
            })
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
