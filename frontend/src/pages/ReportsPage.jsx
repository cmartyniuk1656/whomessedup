import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { PanelMessage } from "../components/v2/atoms/PanelMessage";
import { DifficultyToggle } from "../components/v2/molecules/DifficultyToggle";
import { WizardBreadcrumbs } from "../components/v2/molecules/WizardBreadcrumbs";
import { FightSelectionGrid } from "../components/v2/organisms/FightSelectionGrid";
import { ReportCatalog } from "../components/v2/organisms/ReportCatalog";
import { ReportConfigurationModal } from "../components/v2/organisms/ReportConfigurationModal";
import { ReportResultsPanel } from "../components/v2/organisms/ReportResultsPanel";
import { ReportRunningPanel } from "../components/v2/organisms/ReportRunningPanel";
import { ReportWizardStepFrame } from "../components/v2/organisms/ReportWizardStepFrame";
import { useReportBrowserState } from "../hooks/useReportBrowserState";
import { useReportDefinitions } from "../hooks/useReportDefinitions";
import { useReportJob } from "../hooks/useReportJob";
import { buildCachedReportUrl, clearCachedReportParams, parseCachedReportParams } from "../utils/reportShareLink";

const WIZARD_STEPS = {
  BOSS: "boss",
  REPORT: "report",
  RUNNING: "running",
  RESULTS: "results",
};

export function ReportsPage() {
  const [activeWizardStep, setActiveWizardStep] = useState(WIZARD_STEPS.BOSS);
  const [wizardTransitionPhase, setWizardTransitionPhase] = useState("enter");
  const [isConfigurationOpen, setIsConfigurationOpen] = useState(false);
  const [hasRunAttempt, setHasRunAttempt] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const transitionTimerRef = useRef(null);
  const cachedLinkAttemptedRef = useRef(false);
  const { reports, error: definitionsError, loading: definitionsLoading } = useReportDefinitions();
  const {
    page,
    error: jobError,
    isSubmitting,
    pendingJob,
    loadCachedReport,
    runReport,
    clearReportState,
    setError: setJobError,
  } = useReportJob();
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
    setReportFormValues,
    handleValueChange,
    handleMultiTextChange,
    handleAddMultiTextRow,
    handleRemoveMultiTextRow,
  } = useReportBrowserState(reports);

  const canSelectReport = Boolean(selectedFight);
  const canViewRunning = Boolean(selectedReport && (hasRunAttempt || pendingJob || isSubmitting || jobError));
  const canViewResults = Boolean(page);

  const breadcrumbSteps = useMemo(
    () => [
      { id: WIZARD_STEPS.BOSS, label: "Boss", enabled: true, complete: Boolean(selectedFight) },
      { id: WIZARD_STEPS.REPORT, label: "Report", enabled: canSelectReport, complete: Boolean(selectedReport) },
      { id: WIZARD_STEPS.RUNNING, label: "Running", enabled: canViewRunning, complete: canViewResults },
      { id: WIZARD_STEPS.RESULTS, label: "Results", enabled: canViewResults, complete: canViewResults },
    ],
    [canSelectReport, canViewResults, canViewRunning, selectedFight, selectedReport]
  );

  useEffect(() => {
    return () => {
      if (transitionTimerRef.current) {
        window.clearTimeout(transitionTimerRef.current);
      }
    };
  }, []);

  const goToWizardStep = useCallback(
    (stepId) => {
      if (stepId === activeWizardStep) {
        if (transitionTimerRef.current) {
          window.clearTimeout(transitionTimerRef.current);
          transitionTimerRef.current = null;
        }
        setWizardTransitionPhase("enter");
        return;
      }

      if (transitionTimerRef.current) {
        window.clearTimeout(transitionTimerRef.current);
      }

      setWizardTransitionPhase("exit");
      transitionTimerRef.current = window.setTimeout(() => {
        setActiveWizardStep(stepId);
        setWizardTransitionPhase("enter");
        transitionTimerRef.current = null;
      }, 180);
    },
    [activeWizardStep]
  );

  useEffect(() => {
    if (page && activeWizardStep === WIZARD_STEPS.RUNNING) {
      goToWizardStep(WIZARD_STEPS.RESULTS);
    }
  }, [activeWizardStep, goToWizardStep, page]);

  useEffect(() => {
    if (cachedLinkAttemptedRef.current || definitionsLoading || !reports.length) {
      return;
    }

    let cachedParams = null;
    try {
      cachedParams = parseCachedReportParams(window.location.search);
    } catch (err) {
      cachedLinkAttemptedRef.current = true;
      setHasRunAttempt(true);
      setJobError(err.message || "Cached report link is invalid.");
      goToWizardStep(WIZARD_STEPS.RUNNING);
      return;
    }

    if (!cachedParams) {
      return;
    }

    cachedLinkAttemptedRef.current = true;
    const report = reports.find((candidate) => candidate.id === cachedParams.reportId);
    if (!report) {
      setHasRunAttempt(true);
      setJobError("Cached report link references an unknown report.");
      goToWizardStep(WIZARD_STEPS.RUNNING);
      return;
    }

    setSelectedDifficulty(report.difficulty || selectedDifficulty);
    setSelectedFightId(report.fightId || "");
    setReportFormValues(report.id, cachedParams.values);
    setHasRunAttempt(true);
    setIsConfigurationOpen(false);
    goToWizardStep(WIZARD_STEPS.RUNNING);
    loadCachedReport({ reportId: report.id, values: cachedParams.values });
  }, [
    definitionsLoading,
    goToWizardStep,
    loadCachedReport,
    reports,
    selectedDifficulty,
    setJobError,
    setReportFormValues,
    setSelectedDifficulty,
    setSelectedFightId,
  ]);

  useEffect(() => {
    if (!page || !selectedReportId || !Object.keys(formValues ?? {}).length) {
      return;
    }
    const nextShareUrl = buildCachedReportUrl({ reportId: selectedReportId, values: formValues });
    setShareUrl(nextShareUrl);
    const nextUrl = new URL(nextShareUrl);
    const nextPath = `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`;
    const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (nextPath !== currentPath) {
      window.history.replaceState(null, "", nextPath);
    }
  }, [formValues, page, selectedReportId]);

  const resetRunState = () => {
    setHasRunAttempt(false);
    setShareUrl("");
    clearReportState();
    if (window.location.search.includes("reportId=") || window.location.search.includes("values=")) {
      window.history.replaceState(null, "", clearCachedReportParams());
    }
  };

  const handleSelectDifficulty = (difficultyId) => {
    setSelectedDifficulty(difficultyId);
    setSelectedFightId("");
    setSelectedReportId("");
    setIsConfigurationOpen(false);
    resetRunState();
    goToWizardStep(WIZARD_STEPS.BOSS);
  };

  const handleSelectFight = (fightId) => {
    setSelectedFightId(fightId);
    setSelectedReportId("");
    setIsConfigurationOpen(false);
    resetRunState();
    goToWizardStep(WIZARD_STEPS.REPORT);
  };

  const handleSelectReport = (reportId) => {
    setSelectedReportId(reportId);
    setIsConfigurationOpen(true);
    resetRunState();
    goToWizardStep(WIZARD_STEPS.REPORT);
  };

  const handleSelectBreadcrumb = (stepId) => {
    const step = breadcrumbSteps.find((candidate) => candidate.id === stepId);
    if (!step?.enabled) {
      return;
    }
    if (stepId !== WIZARD_STEPS.REPORT) {
      setIsConfigurationOpen(false);
    }
    goToWizardStep(stepId);
  };

  const handleSubmitReport = async () => {
    if (!selectedReport) {
      return false;
    }
    setHasRunAttempt(true);
    setIsConfigurationOpen(false);
    goToWizardStep(WIZARD_STEPS.RUNNING);
    return runReport({ reportId: selectedReport.id, values: formValues });
  };

  const handleOpenConfigurationFromRunning = () => {
    goToWizardStep(WIZARD_STEPS.REPORT);
    setIsConfigurationOpen(true);
  };

  const renderBossStep = () => (
    <ReportWizardStepFrame
      stepKey={WIZARD_STEPS.BOSS}
      phase={wizardTransitionPhase}
    >
      <div className="space-y-8">
        <div className="flex justify-center">
          <DifficultyToggle
            options={difficultyOptions}
            selectedId={selectedDifficulty}
            onSelect={handleSelectDifficulty}
          />
        </div>
        {definitionsLoading ? <PanelMessage>Loading report definitions...</PanelMessage> : null}
        {definitionsError ? <PanelMessage tone="danger">{definitionsError}</PanelMessage> : null}
        <div className="mx-auto w-full max-w-5xl">
          <FightSelectionGrid
            fights={fightOptions}
            selectedFightId={selectedFightId}
            onSelectFight={handleSelectFight}
            reportCountsByFightId={reportCountsByFightId}
          />
        </div>
      </div>
    </ReportWizardStepFrame>
  );

  const renderReportStep = () => (
    <ReportWizardStepFrame
      stepKey={WIZARD_STEPS.REPORT}
      phase={wizardTransitionPhase}
      eyebrow="Report"
      title={selectedFight ? `Choose a report for ${selectedDifficultyLabel} ${selectedFight.title}` : "Choose a report"}
      description={
        selectedFight
          ? "Select a report, then adjust its configuration before running."
          : "Select a boss before choosing a report."
      }
    >
      {definitionsLoading ? <PanelMessage>Loading report definitions...</PanelMessage> : null}
      {definitionsError ? <PanelMessage tone="danger">{definitionsError}</PanelMessage> : null}
      {!definitionsLoading && !definitionsError && selectedFight ? (
        <ReportCatalog
          reports={availableReports}
          selectedReportId={selectedReportId}
          onSelectReport={handleSelectReport}
          isBusy={isSubmitting}
          title="Available reports"
          description=""
          emptyMessage={`No ${selectedDifficultyLabel.toLowerCase()} reports are available for ${selectedFight.title} yet.`}
        />
      ) : null}
    </ReportWizardStepFrame>
  );

  const renderRunningStep = () => (
    <ReportWizardStepFrame
      stepKey={WIZARD_STEPS.RUNNING}
      phase={wizardTransitionPhase}
      eyebrow="Running"
      title="Report is running"
      description="The results will appear when processing completes."
    >
      <ReportRunningPanel
        selectedDifficultyLabel={selectedDifficultyLabel}
        selectedFight={selectedFight}
        selectedReport={selectedReport}
        pendingJob={pendingJob}
        isSubmitting={isSubmitting}
        jobError={jobError}
        page={page}
        onOpenConfiguration={handleOpenConfigurationFromRunning}
        onOpenResults={() => goToWizardStep(WIZARD_STEPS.RESULTS)}
      />
    </ReportWizardStepFrame>
  );

  const renderResultsStep = () => (
    <ReportWizardStepFrame
      stepKey={WIZARD_STEPS.RESULTS}
      phase={wizardTransitionPhase}
      eyebrow="Results"
      title={page?.title || "Report results"}
      description="Review the completed report."
    >
      {page ? <ReportResultsPanel page={page} shareUrl={shareUrl} /> : <PanelMessage>Run a report to view results.</PanelMessage>}
    </ReportWizardStepFrame>
  );

  const renderActiveStep = () => {
    switch (activeWizardStep) {
      case WIZARD_STEPS.REPORT:
        return renderReportStep();
      case WIZARD_STEPS.RUNNING:
        return renderRunningStep();
      case WIZARD_STEPS.RESULTS:
        return renderResultsStep();
      case WIZARD_STEPS.BOSS:
      default:
        return renderBossStep();
    }
  };

  return (
    <div className="liquid-bg min-h-dvh text-content relative overflow-hidden" style={{ isolation: "isolate" }}>
      <div aria-hidden className="liquid-glow liquid-glow--top -z-30" />
      <div aria-hidden className="liquid-glow liquid-glow--bottom -z-30" />
      <div aria-hidden className="liquid-blob liquid-blob--emerald -z-20 opacity-70" />
      <div aria-hidden className="liquid-blob liquid-blob--cyan -z-20 opacity-65" />
      <div aria-hidden className="liquid-blob liquid-blob--magenta -z-20 opacity-55" />
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 mix-blend-overlay opacity-25 [background-image:var(--noise)]" />

      <main className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-8">
        <header className="relative isolate overflow-hidden border-b border-white/10 pb-10 pt-3 sm:pb-12">
          <div className="mx-auto mt-8 flex max-w-6xl flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.35em] text-slate-300 shadow-[0_0_40px_rgba(255,255,255,0.05)]">
              <span>Log Analysis</span>
              <span aria-hidden>&middot;</span>
              <span>Mythic Raid Tools</span>
            </div>
            <h1 className="mt-8 text-5xl font-semibold leading-none tracking-tight text-white sm:text-6xl lg:text-7xl">
              <span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-fuchsia-300 bg-clip-text text-transparent">
                HK Logs
              </span>
            </h1>
          </div>
        </header>

        <div className="mt-6">
          <WizardBreadcrumbs
            steps={breadcrumbSteps}
            activeStep={activeWizardStep}
            onSelectStep={handleSelectBreadcrumb}
          />
        </div>

        <div className={selectedFight ? "mt-8" : "mt-10"}>{renderActiveStep()}</div>

        {selectedReport && isConfigurationOpen ? (
          <ReportConfigurationModal
            report={selectedReport}
            values={formValues}
            isSubmitting={isSubmitting}
            pendingJob={pendingJob}
            onClose={() => setIsConfigurationOpen(false)}
            onSubmit={handleSubmitReport}
            onValueChange={handleValueChange}
            onMultiTextChange={handleMultiTextChange}
            onAddMultiTextRow={handleAddMultiTextRow}
            onRemoveMultiTextRow={handleRemoveMultiTextRow}
          />
        ) : null}
      </main>
    </div>
  );
}
