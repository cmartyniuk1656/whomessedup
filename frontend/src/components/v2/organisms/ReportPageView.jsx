import { useEffect, useMemo, useState } from "react";
import { useDamageTableFilters } from "../../../hooks/useDamageTableFilters";
import { useTableSorting } from "../../../hooks/useTableSorting";
import { SelectInput } from "../atoms/SelectInput";
import { DamageTableFilters } from "./DamageTableFilters";
import { ReportPageHeader } from "../molecules/ReportPageHeader";
import { ReportSummaryGrid } from "./ReportSummaryGrid";
import { ReportTable } from "./ReportTable";
import { SpecAnalysisModal } from "./SpecAnalysisModal";

function ReportTableViewSelector({ control, value, onChange }) {
  if (!control?.options?.length) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="min-w-56">
        <label className="text-sm font-medium text-slate-100" htmlFor={control.id}>
          {control.label}
        </label>
        <SelectInput id={control.id} value={value} onChange={(event) => onChange(event.target.value)}>
          {control.options.map((option) => (
            <option key={`${control.id}-${option.value}`} value={option.value}>
              {option.label}
            </option>
          ))}
        </SelectInput>
      </div>
    </div>
  );
}

export function ReportPageView({ page, shareUrl }) {
  const [isSpecAnalysisOpen, setIsSpecAnalysisOpen] = useState(false);
  const baseTable = page?.content?.table;
  const viewControl = baseTable?.viewControl;
  const defaultTableView = viewControl?.defaultValue ?? "aggregate";
  const [selectedTableView, setSelectedTableView] = useState(defaultTableView);
  const tableForView = useMemo(() => {
    if (!baseTable) {
      return null;
    }
    if (!viewControl) {
      return baseTable;
    }
    const rows = baseTable.rowsByView?.[selectedTableView] ?? baseTable.rowsByView?.[defaultTableView] ?? baseTable.rows;
    return {
      ...baseTable,
      rows,
    };
  }, [baseTable, defaultTableView, selectedTableView, viewControl]);
  const { config, selectedTargets, selectedMetrics, toggleTarget, toggleMetric, filteredTable } =
    useDamageTableFilters(tableForView);
  const table = filteredTable;
  const { sortConfig, sortedRows, handleSort } = useTableSorting(table);

  useEffect(() => {
    setIsSpecAnalysisOpen(false);
  }, [page?.reportId, page?.reportCode]);

  useEffect(() => {
    setSelectedTableView(defaultTableView);
  }, [defaultTableView, page?.reportCode, page?.reportId]);

  useEffect(() => {
    if (!viewControl?.options?.length) {
      return;
    }
    const hasSelectedView = viewControl.options.some((option) => option.value === selectedTableView);
    if (!hasSelectedView) {
      setSelectedTableView(defaultTableView);
    }
  }, [defaultTableView, selectedTableView, viewControl]);

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
      <ReportPageHeader
        page={displayPage}
        rows={sortedRows}
        shareUrl={shareUrl}
        onOpenSpecAnalysis={() => setIsSpecAnalysisOpen(true)}
      />
      <ReportSummaryGrid metrics={page.summary} />
      <ReportTableViewSelector control={viewControl} value={selectedTableView} onChange={setSelectedTableView} />
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
        pageKey={`${page.reportId}:${page.reportCode}:${selectedTableView}`}
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
      {isSpecAnalysisOpen && page.specAnalysis ? (
        <SpecAnalysisModal analysis={page.specAnalysis} onClose={() => setIsSpecAnalysisOpen(false)} />
      ) : null}
    </section>
  );
}
