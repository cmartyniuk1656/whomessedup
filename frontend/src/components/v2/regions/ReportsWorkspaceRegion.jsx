import { PanelMessage } from "../atoms/PanelMessage";
import { ReportCatalog } from "../organisms/ReportCatalog";
import { ReportConfigurationPanel } from "../organisms/ReportConfigurationPanel";
import { ReportConfigurationModal } from "../organisms/ReportConfigurationModal";
import { ReportResultsPanel } from "../organisms/ReportResultsPanel";

export function ReportsWorkspaceRegion({
  definitionsLoading,
  definitionsError,
  selectedDifficultyLabel,
  selectedFight,
  reports,
  selectedReportId,
  onSelectReport,
  isConfigurationOpen,
  onOpenConfiguration,
  onCloseConfiguration,
  isSubmitting,
  selectedReport,
  formValues,
  pendingJob,
  onSubmitReport,
  onValueChange,
  onMultiTextChange,
  onAddMultiTextRow,
  onRemoveMultiTextRow,
  jobError,
  page,
}) {
  return (
    <div className="mt-10 space-y-10">
      {definitionsLoading ? <PanelMessage>Loading report definitions...</PanelMessage> : null}
      {definitionsError ? <PanelMessage tone="danger">{definitionsError}</PanelMessage> : null}

      {!definitionsLoading && !definitionsError && !selectedFight ? (
        <PanelMessage>Select a fight to browse available reports for that difficulty.</PanelMessage>
      ) : null}

      {!definitionsLoading && !definitionsError && selectedFight ? (
        <ReportCatalog
          reports={reports}
          selectedReportId={selectedReportId}
          onSelectReport={onSelectReport}
          isBusy={isSubmitting}
          title={`Choose a report for ${selectedFight.title}`}
          description={`Showing ${selectedDifficultyLabel.toLowerCase()} reports available for ${selectedFight.title}.`}
          emptyMessage={`No ${selectedDifficultyLabel.toLowerCase()} reports are available for ${selectedFight.title} yet.`}
        />
      ) : null}

      {!definitionsLoading && !definitionsError && selectedFight && reports.length > 0 && !selectedReport ? (
        <PanelMessage>Choose a report to load its configuration.</PanelMessage>
      ) : null}

      {!definitionsLoading && !definitionsError && selectedReport ? (
        <ReportConfigurationPanel
          report={selectedReport}
          isSubmitting={isSubmitting}
          pendingJob={pendingJob}
          onOpen={onOpenConfiguration}
        />
      ) : null}

      {jobError ? <PanelMessage tone="danger">{jobError}</PanelMessage> : null}
      <ReportResultsPanel page={page} />

      {!definitionsLoading && !definitionsError && selectedReport && isConfigurationOpen ? (
        <ReportConfigurationModal
          report={selectedReport}
          values={formValues}
          isSubmitting={isSubmitting}
          pendingJob={pendingJob}
          onClose={onCloseConfiguration}
          onSubmit={onSubmitReport}
          onValueChange={onValueChange}
          onMultiTextChange={onMultiTextChange}
          onAddMultiTextRow={onAddMultiTextRow}
          onRemoveMultiTextRow={onRemoveMultiTextRow}
        />
      ) : null}
    </div>
  );
}
