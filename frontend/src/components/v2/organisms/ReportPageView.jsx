import { ReportViewScope } from "./ReportViewProvider";
import { useReportViewState } from "../../../hooks/useReportViewState";
import { useEffect, useMemo } from "react";
import { useDamageTableFilters } from "../../../hooks/useDamageTableFilters";
import { useTableColumnFilters } from "../../../hooks/useTableColumnFilters";
import { useTableRowFilters } from "../../../hooks/useTableRowFilters";
import { useTableSorting } from "../../../hooks/useTableSorting";
import { resolveReportRows } from "../../../utils/reportRows";
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
import { CooldownCoverageReport } from "../coverage/CooldownCoverageReport";
import { DefensiveUsageReport } from "../defensives/DefensiveUsageReport";

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
  const [selectedReportView, setSelectedReportView] = useReportViewState("report", defaultReportView);


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
  }, [defaultReportView, reportControl, selectedReportView, setSelectedReportView]);

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
      <ReportViewScope name={selectedReportView || selectedPage.reportId}>
      {selectedPage.content?.variant === "defensive_timeline" ? (
        <DefensiveUsageReport key={`${selectedPage.reportId}:${selectedPage.reportCode}`} page={selectedPage} shareUrl={shareUrl} realtime={realtime} />
      ) : selectedPage.content?.variant === "timeline" ? (
        <CooldownCoverageReport
          key={`${selectedPage.reportId}:${selectedPage.reportCode}`}
          page={selectedPage}
          shareUrl={shareUrl}
          realtime={realtime}
        />
      ) : (
        <SingleReportPageView
          key={selectedReportView || selectedPage.reportId}
          page={selectedPage}
          shareUrl={shareUrl}
          realtime={realtime}
        />
      )}
      </ReportViewScope>
    </div>
  );
}

function SingleReportPageView({ page, shareUrl, realtime }) {
  const [isSpecAnalysisOpen, setIsSpecAnalysisOpen] = useReportViewState("specAnalysis", false);
  const baseTable = page?.content?.table;
  const viewControl = baseTable?.viewControl;
  const secondaryViewControl = baseTable?.secondaryViewControl;
  const defaultTableView = viewControl?.defaultValue ?? "aggregate";
  const defaultSecondaryTableView = secondaryViewControl?.defaultValue;
  const [selectedTableView, setSelectedTableView] = useReportViewState("tableView", defaultTableView);
  const [selectedSecondaryTableView, setSelectedSecondaryTableView] = useReportViewState("secondaryView", defaultSecondaryTableView);
  const subViewControl =
    baseTable?.subViewControlByView?.[selectedSecondaryTableView];
  const defaultSubTableView = subViewControl?.defaultValue;
  const [selectedSubTableView, setSelectedSubTableView] = useReportViewState("subView", defaultSubTableView, { resetKey: selectedSecondaryTableView });
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
      return { ...baseTable, rows: resolveReportRows(baseTable) };
    }
    const combinedViewId = secondaryViewControl
      ? activeSubTableView
        ? `${selectedTableView}::${selectedSecondaryTableView}::${activeSubTableView}`
        : `${selectedTableView}::${selectedSecondaryTableView}`
      : null;
    const columnViewId = activeSubTableView ?? selectedSecondaryTableView;
    const rows = resolveReportRows(
      baseTable, selectedTableView, combinedViewId, defaultTableView
    );
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
  const filterScope = `${selectedTableView}:${selectedSecondaryTableView || ""}:${activeSubTableView || ""}`;
  const {
    config: rowFilterConfig,
    selectedRowValues,
    toggleRowValue,
    filteredTable: rowFilteredTable,
  } = useTableRowFilters(tableForView, filterScope);
  const {
    config: columnFilterConfig,
    selectedColumnIds,
    toggleColumn,
    filteredTable: columnFilteredTable,
  } = useTableColumnFilters(rowFilteredTable, filterScope);
  const {
    config,
    selectedTargets,
    selectedMetrics,
    toggleTarget,
    toggleMetric,
    filteredTable,
  } = useDamageTableFilters(columnFilteredTable, filterScope);
  const table = filteredTable;
  const combinedSummaryViewId = secondaryViewControl
    ? `${selectedTableView}::${selectedSecondaryTableView}`
    : null;
  const subSummaryViewId = combinedSummaryViewId && activeSubTableView
    ? `${combinedSummaryViewId}::${activeSubTableView}`
    : null;
  const summary =
    (subSummaryViewId ? page?.summaryByCombinedView?.[subSummaryViewId] : null) ??
    (combinedSummaryViewId
      ? page?.summaryByCombinedView?.[combinedSummaryViewId]
      : null) ??
    page?.summaryByView?.[selectedTableView] ??
    page?.summary;
  const { sortConfig, sortedRows, handleSort } = useTableSorting(table, filterScope);

  useEffect(() => {
    if (!viewControl?.options?.length) {
      return;
    }
    const hasSelectedView = viewControl.options.some((option) => option.value === selectedTableView);
    if (!hasSelectedView) {
      setSelectedTableView(defaultTableView);
    }
  }, [defaultTableView, selectedTableView, viewControl, setSelectedTableView]);

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
    setSelectedSecondaryTableView,
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
  }, [defaultSubTableView, selectedSubTableView, subViewControl, setSelectedSubTableView]);

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
