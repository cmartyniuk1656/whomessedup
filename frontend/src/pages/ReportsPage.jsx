import { useEffect, useState } from "react";
import { ReportsHeroRegion } from "../components/v2/regions/ReportsHeroRegion";
import { ReportsWorkspaceRegion } from "../components/v2/regions/ReportsWorkspaceRegion";
import { useReportBrowserState } from "../hooks/useReportBrowserState";
import { useReportDefinitions } from "../hooks/useReportDefinitions";
import { useReportJob } from "../hooks/useReportJob";

export function ReportsPage({ onSwitchToLegacy }) {
  const [isConfigurationOpen, setIsConfigurationOpen] = useState(false);
  const { reports, error: definitionsError, loading: definitionsLoading } = useReportDefinitions();
  const { page, error: jobError, isSubmitting, pendingJob, runReport, clearReportState } = useReportJob();
  const {
    fightOptions,
    difficultyOptions,
    selectedDifficulty,
    selectedDifficultyLabel,
    setSelectedDifficulty,
    selectedFightId,
    selectedFight,
    setSelectedFightId,
    reportCountsByFightId,
    availableReports,
    selectedReportId,
    selectedReport,
    formValues,
    setSelectedReportId,
    handleValueChange,
    handleMultiTextChange,
    handleAddMultiTextRow,
    handleRemoveMultiTextRow,
  } = useReportBrowserState(reports);

  useEffect(() => {
    clearReportState();
  }, [selectedDifficulty, selectedFightId, selectedReportId, clearReportState]);

  useEffect(() => {
    setIsConfigurationOpen(Boolean(selectedReport));
  }, [selectedReport]);

  const handleSelectReport = (reportId) => {
    setSelectedReportId(reportId);
    setIsConfigurationOpen(true);
  };

  const handleSubmitReport = async () => {
    if (!selectedReport) {
      return false;
    }
    const succeeded = await runReport({ reportId: selectedReport.id, values: formValues });
    if (succeeded) {
      setIsConfigurationOpen(false);
    }
    return succeeded;
  };

  return (
    <div className="liquid-bg min-h-dvh text-content relative overflow-hidden" style={{ isolation: "isolate" }}>
      <div aria-hidden className="liquid-glow liquid-glow--top -z-30" />
      <div aria-hidden className="liquid-glow liquid-glow--bottom -z-30" />
      <div aria-hidden className="liquid-blob liquid-blob--emerald -z-20 opacity-70" />
      <div aria-hidden className="liquid-blob liquid-blob--cyan -z-20 opacity-65" />
      <div aria-hidden className="liquid-blob liquid-blob--magenta -z-20 opacity-55" />
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 mix-blend-overlay opacity-25 [background-image:var(--noise)]" />

      <main className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-10">
        <ReportsHeroRegion
          onSwitchToLegacy={onSwitchToLegacy}
          fights={fightOptions}
          difficultyOptions={difficultyOptions}
          selectedDifficulty={selectedDifficulty}
          onSelectDifficulty={setSelectedDifficulty}
          selectedFightId={selectedFightId}
          onSelectFight={setSelectedFightId}
          reportCountsByFightId={reportCountsByFightId}
        />
        <ReportsWorkspaceRegion
          definitionsLoading={definitionsLoading}
          definitionsError={definitionsError}
          selectedDifficultyLabel={selectedDifficultyLabel}
          selectedFight={selectedFight}
          reports={availableReports}
          selectedReportId={selectedReportId}
          onSelectReport={handleSelectReport}
          isConfigurationOpen={isConfigurationOpen}
          onOpenConfiguration={() => setIsConfigurationOpen(true)}
          onCloseConfiguration={() => setIsConfigurationOpen(false)}
          isSubmitting={isSubmitting}
          selectedReport={selectedReport}
          formValues={formValues}
          pendingJob={pendingJob}
          onSubmitReport={handleSubmitReport}
          onValueChange={handleValueChange}
          onMultiTextChange={handleMultiTextChange}
          onAddMultiTextRow={handleAddMultiTextRow}
          onRemoveMultiTextRow={handleRemoveMultiTextRow}
          jobError={jobError}
          page={page}
        />
      </main>
    </div>
  );
}
