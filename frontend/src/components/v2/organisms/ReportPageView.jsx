import { useDamageTableFilters } from "../../../hooks/useDamageTableFilters";
import { useTableSorting } from "../../../hooks/useTableSorting";
import { DamageTableFilters } from "./DamageTableFilters";
import { ReportPageHeader } from "../molecules/ReportPageHeader";
import { ReportSummaryGrid } from "./ReportSummaryGrid";
import { ReportTable } from "./ReportTable";

export function ReportPageView({ page }) {
  const baseTable = page?.content?.table;
  const { config, selectedTargets, selectedMetrics, toggleTarget, toggleMetric, filteredTable } =
    useDamageTableFilters(baseTable);
  const table = filteredTable;
  const { sortConfig, sortedRows, handleSort } = useTableSorting(table);

  if (!page || !table) {
    return null;
  }

  const displayPage = {
    ...page,
    content: {
      ...page.content,
      table,
    },
  };

  return (
    <section className="space-y-7">
      <ReportPageHeader page={displayPage} rows={sortedRows} />
      <ReportSummaryGrid metrics={page.summary} />
      <DamageTableFilters
        config={config}
        selectedTargets={selectedTargets}
        selectedMetrics={selectedMetrics}
        onToggleTarget={toggleTarget}
        onToggleMetric={toggleMetric}
      />
      <ReportTable
        table={table}
        rows={sortedRows}
        sortConfig={sortConfig}
        onSort={handleSort}
        pageKey={`${page.reportId}:${page.reportCode}`}
      />
      {page.footnotes?.length ? (
        <div className="border-t border-white/10 pt-5 text-sm text-slate-400">
          <p className="mb-3 text-[11px] uppercase tracking-[0.18em] text-slate-500">Notes</p>
          {page.footnotes.map((footnote, index) => (
            <p key={`footnote-${index}`} className={index === 0 ? "" : "mt-2"}>
              {footnote}
            </p>
          ))}
        </div>
      ) : null}
    </section>
  );
}
