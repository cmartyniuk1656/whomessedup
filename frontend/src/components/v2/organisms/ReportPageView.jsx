import { useEffect, useMemo, useState } from "react";
import { useDamageTableFilters } from "../../../hooks/useDamageTableFilters";
import { useTableColumnFilters } from "../../../hooks/useTableColumnFilters";
import { useTableRowFilters } from "../../../hooks/useTableRowFilters";
import { useTableSorting } from "../../../hooks/useTableSorting";
import { DamageTableFilters } from "./DamageTableFilters";
import { ReportPageHeader } from "../molecules/ReportPageHeader";
import { ReportUpdateNotification } from "../molecules/ReportUpdateNotification";
import { SpecAnalysisCallout } from "../molecules/SpecAnalysisCallout";
import { ThemedSelectMenu } from "../molecules/ThemedSelectMenu";
import { ReportSummaryGrid } from "./ReportSummaryGrid";
import { ReportTable } from "./ReportTable";
import { SpecAnalysisModal } from "./SpecAnalysisModal";
import { TableColumnFilters } from "./TableColumnFilters";
import { TableRowFilters } from "./TableRowFilters";

function ReportTableViewSelector({ control, value, onChange }) {
  if (!control?.options?.length) {
    return null;
  }

  return (
    <div className="min-w-56">
      <ThemedSelectMenu
        id={control.id}
        label={control.label}
        options={control.options.map((option) => ({
          id: option.value,
          label: option.label,
        }))}
        value={value}
        onChange={onChange}
      />
    </div>
  );
}

function ReportPageSelector({ control, value, onChange }) {
  if (!control?.options?.length) {
    return null;
  }
  return (
    <div className="max-w-md">
      <ThemedSelectMenu
        id={control.id}
        label={control.label}
        options={control.options.map((option) => ({
          id: option.value,
          label: option.label,
        }))}
        value={value}
        onChange={onChange}
      />
    </div>
  );
}

export function ReportPageView({ page, shareUrl, realtime }) {
  const reportControl = page?.reportControl;
  const defaultReportView = reportControl?.defaultValue;
  const [selectedReportView, setSelectedReportView] = useState(defaultReportView);

  useEffect(() => {
    setSelectedReportView(defaultReportView);
  }, [defaultReportView, page?.reportCode, page?.reportId]);

  useEffect(() => {
    if (!reportControl?.options?.length) {
      return;
    }
    const hasSelectedReport = reportControl.options.some(
      (option) => option.value === selectedReportView
    );
    if (!hasSelectedReport) {
      setSelectedReportView(defaultReportView);
    }
  }, [defaultReportView, reportControl, selectedReportView]);

  const selectedPage = reportControl
    ? page?.reportsByView?.[selectedReportView] ??
      page?.reportsByView?.[defaultReportView]
    : page;
  if (!selectedPage) {
    return null;
  }

  return (
    <div className="space-y-7">
      <ReportPageSelector
        control={reportControl}
        value={selectedReportView}
        onChange={setSelectedReportView}
      />
      <SingleReportPageView
        key={selectedReportView || selectedPage.reportId}
        page={selectedPage}
        shareUrl={shareUrl}
        realtime={realtime}
      />
    </div>
  );
}

function SingleReportPageView({ page, shareUrl, realtime }) {
  const [isSpecAnalysisOpen, setIsSpecAnalysisOpen] = useState(false);
  const baseTable = page?.content?.table;
  const viewControl = baseTable?.viewControl;
  const secondaryViewControl = baseTable?.secondaryViewControl;
  const defaultTableView = viewControl?.defaultValue ?? "aggregate";
  const defaultSecondaryTableView = secondaryViewControl?.defaultValue;
  const [selectedTableView, setSelectedTableView] = useState(defaultTableView);
  const [selectedSecondaryTableView, setSelectedSecondaryTableView] = useState(
    defaultSecondaryTableView
  );
  const subViewControl =
    baseTable?.subViewControlByView?.[selectedSecondaryTableView];
  const defaultSubTableView = subViewControl?.defaultValue;
  const [selectedSubTableView, setSelectedSubTableView] = useState(
    defaultSubTableView
  );
  const activeSubTableView = subViewControl?.options?.some(
    (option) => option.value === selectedSubTableView
  )
    ? selectedSubTableView
    : defaultSubTableView;
  const tableForView = useMemo(() => {
    if (!baseTable) {
      return null;
    }
    if (!viewControl && !secondaryViewControl) {
      return baseTable;
    }
    const combinedViewId = secondaryViewControl
      ? activeSubTableView
        ? `${selectedTableView}::${selectedSecondaryTableView}::${activeSubTableView}`
        : `${selectedTableView}::${selectedSecondaryTableView}`
      : null;
    const columnViewId = activeSubTableView ?? selectedSecondaryTableView;
    const rows =
      (combinedViewId ? baseTable.rowsByCombinedView?.[combinedViewId] : null) ??
      baseTable.rowsByView?.[selectedTableView] ??
      baseTable.rowsByView?.[defaultTableView] ??
      baseTable.rows;
    return {
      ...baseTable,
      defaultSort:
        baseTable.defaultSortByView?.[columnViewId] ?? baseTable.defaultSort,
      columns:
        baseTable.columnsByView?.[columnViewId] ??
        baseTable.columns,
      emptyState:
        baseTable.emptyStateByView?.[columnViewId] ??
        baseTable.emptyState,
      columnFilter:
        baseTable.columnFilterByView?.[columnViewId] ??
        baseTable.columnFilter,
      rowFilter:
        baseTable.rowFilterByView?.[columnViewId] ?? baseTable.rowFilter,
      damageFilterConfig:
        baseTable.damageFilterConfigByView?.[columnViewId] ??
        baseTable.damageFilterConfig,
      rows,
    };
  }, [
    baseTable,
    activeSubTableView,
    defaultTableView,
    secondaryViewControl,
    selectedSecondaryTableView,
    selectedTableView,
    viewControl,
  ]);
  const {
    config: rowFilterConfig,
    selectedRowValues,
    toggleRowValue,
    filteredTable: rowFilteredTable,
  } = useTableRowFilters(tableForView);
  const {
    config: columnFilterConfig,
    selectedColumnIds,
    toggleColumn,
    filteredTable: columnFilteredTable,
  } = useTableColumnFilters(rowFilteredTable);
  const {
    config,
    selectedTargets,
    selectedMetrics,
    toggleTarget,
    toggleMetric,
    filteredTable,
  } = useDamageTableFilters(columnFilteredTable);
  const table = filteredTable;
  const combinedSummaryViewId = secondaryViewControl
    ? `${selectedTableView}::${selectedSecondaryTableView}`
    : null;
  const summary =
    (combinedSummaryViewId
      ? page?.summaryByCombinedView?.[combinedSummaryViewId]
      : null) ??
    page?.summaryByView?.[selectedTableView] ??
    page?.summary;
  const { sortConfig, sortedRows, handleSort } = useTableSorting(table);

  useEffect(() => {
    setIsSpecAnalysisOpen(false);
  }, [page?.reportId, page?.reportCode]);

  useEffect(() => {
    setSelectedTableView(defaultTableView);
  }, [defaultTableView, page?.reportCode, page?.reportId]);

  useEffect(() => {
    setSelectedSecondaryTableView(defaultSecondaryTableView);
  }, [defaultSecondaryTableView, page?.reportCode, page?.reportId]);

  useEffect(() => {
    setSelectedSubTableView(defaultSubTableView);
  }, [
    defaultSubTableView,
    page?.reportCode,
    page?.reportId,
    selectedSecondaryTableView,
  ]);

  useEffect(() => {
    if (!viewControl?.options?.length) {
      return;
    }
    const hasSelectedView = viewControl.options.some((option) => option.value === selectedTableView);
    if (!hasSelectedView) {
      setSelectedTableView(defaultTableView);
    }
  }, [defaultTableView, selectedTableView, viewControl]);

  useEffect(() => {
    if (!secondaryViewControl?.options?.length) {
      return;
    }
    const hasSelectedView = secondaryViewControl.options.some(
      (option) => option.value === selectedSecondaryTableView
    );
    if (!hasSelectedView) {
      setSelectedSecondaryTableView(defaultSecondaryTableView);
    }
  }, [
    defaultSecondaryTableView,
    secondaryViewControl,
    selectedSecondaryTableView,
  ]);

  useEffect(() => {
    if (!subViewControl?.options?.length) {
      return;
    }
    const hasSelectedView = subViewControl.options.some(
      (option) => option.value === selectedSubTableView
    );
    if (!hasSelectedView) {
      setSelectedSubTableView(defaultSubTableView);
    }
  }, [defaultSubTableView, selectedSubTableView, subViewControl]);

  if (!page || !table) {
    return null;
  }

  const displayPage = {
    ...page,
    content: {
      ...page.content,
      table,
    },
    summary,
  };

  return (
    <section className="space-y-7">
      <ReportPageHeader
        page={displayPage}
        rows={sortedRows}
        shareUrl={shareUrl}
      />
      <ReportUpdateNotification
        notice={realtime?.notice}
        onDismiss={realtime?.clearNotice}
        onViewPull={
          realtime?.notice?.viewId &&
          viewControl?.options?.some(
            (option) => option.value === realtime.notice.viewId
          )
            ? () => {
                setSelectedTableView(realtime.notice.viewId);
                realtime.clearNotice();
              }
            : null
        }
      />
      <SpecAnalysisCallout
        analysis={selectedTableView === defaultTableView ? page.specAnalysis : null}
        onOpen={() => setIsSpecAnalysisOpen(true)}
      />
      <ReportSummaryGrid metrics={summary} />
      <div className="flex flex-wrap items-end gap-3">
        <ReportTableViewSelector
          control={viewControl}
          value={selectedTableView}
          onChange={setSelectedTableView}
        />
        <ReportTableViewSelector
          control={secondaryViewControl}
          value={selectedSecondaryTableView}
          onChange={setSelectedSecondaryTableView}
        />
        <ReportTableViewSelector
          control={subViewControl}
          value={activeSubTableView}
          onChange={setSelectedSubTableView}
        />
      </div>
      <DamageTableFilters
        config={config}
        selectedTargets={selectedTargets}
        selectedMetrics={selectedMetrics}
        onToggleTarget={toggleTarget}
        onToggleMetric={toggleMetric}
      />
      <TableRowFilters
        config={rowFilterConfig}
        selectedRowValues={selectedRowValues}
        onToggleRowValue={toggleRowValue}
      />
      <TableColumnFilters
        config={columnFilterConfig}
        selectedColumnIds={selectedColumnIds}
        onToggleColumn={toggleColumn}
      />
      <ReportTable
        table={table}
        rows={sortedRows}
        sortConfig={sortConfig}
        onSort={handleSort}
        pageKey={`${page.reportId}:${page.reportCode}:${selectedTableView}:${selectedSecondaryTableView || ""}:${activeSubTableView || ""}`}
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
