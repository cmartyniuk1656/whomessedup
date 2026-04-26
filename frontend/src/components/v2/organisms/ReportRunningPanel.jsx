import { Button } from "../atoms/Button";
import { PanelMessage } from "../atoms/PanelMessage";
import { StatusPill } from "../atoms/StatusPill";
import { SurfacePanel } from "../atoms/SurfacePanel";

function jobStatusLabel(pendingJob, isSubmitting) {
  if (pendingJob?.status === "running") {
    return "Running";
  }
  if (pendingJob) {
    return "Queued";
  }
  if (isSubmitting) {
    return "Starting";
  }
  return "Ready";
}

export function ReportRunningPanel({
  selectedDifficultyLabel,
  selectedFight,
  selectedReport,
  pendingJob,
  isSubmitting,
  jobError,
  page,
  onOpenConfiguration,
  onOpenResults,
}) {
  const statusLabel = jobStatusLabel(pendingJob, isSubmitting);
  const statusTone = pendingJob?.status === "running" || isSubmitting ? "accent" : "warning";
  const isProcessing = Boolean(isSubmitting || pendingJob);

  return (
    <SurfacePanel className="p-6" tone="muted">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_16rem] lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Run Status</p>
            <StatusPill tone={statusTone}>{statusLabel}</StatusPill>
          </div>
          <h2 className="mt-3 text-2xl font-semibold text-white">{selectedReport?.title || "Report"}</h2>
          <p className="mt-2 text-sm text-slate-400">
            {[selectedDifficultyLabel, selectedFight?.title].filter(Boolean).join(" - ")}
          </p>

          {isProcessing ? (
            <div className="mt-6 rounded-xl border border-emerald-300/15 bg-emerald-400/[0.06] p-4">
              <div className="flex items-center gap-4">
                <div className="relative h-12 w-12 shrink-0">
                  <div className="absolute inset-0 rounded-full border border-emerald-300/15 bg-slate-950/30" />
                  <div className="absolute inset-1 rounded-full border-2 border-transparent border-t-emerald-300 border-r-cyan-300 motion-safe:animate-spin" />
                  <div className="absolute inset-[1.05rem] rounded-full bg-emerald-300 shadow-[0_0_20px_rgba(110,231,183,0.55)] motion-safe:animate-pulse" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-emerald-50">
                    <span>{pendingJob?.status === "running" ? "Processing report" : "Preparing report"}</span>
                    <span aria-hidden className="flex items-center gap-1">
                      <span className="h-1 w-1 rounded-full bg-emerald-200 motion-safe:animate-bounce" />
                      <span className="h-1 w-1 rounded-full bg-emerald-200 motion-safe:animate-bounce [animation-delay:120ms]" />
                      <span className="h-1 w-1 rounded-full bg-emerald-200 motion-safe:animate-bounce [animation-delay:240ms]" />
                    </span>
                  </div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-950/60">
                    <div className="running-progress-sweep h-full w-1/3 rounded-full bg-gradient-to-r from-emerald-300 via-cyan-300 to-fuchsia-300" />
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {pendingJob ? (
            <div className="mt-5 space-y-2 rounded-lg border border-white/10 bg-slate-950/35 p-4 text-sm text-slate-300">
              {typeof pendingJob.position === "number" ? (
                <p>{pendingJob.position === 0 ? "In progress" : `Position in queue: ${pendingJob.position}`}</p>
              ) : null}
              <p className="break-all text-xs text-slate-500">Job ID: {pendingJob.id}</p>
            </div>
          ) : null}

          {isSubmitting && !pendingJob ? (
            <div className="mt-5 rounded-lg border border-emerald-300/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">
              Preparing report run...
            </div>
          ) : null}

          {jobError ? (
            <div className="mt-5">
              <PanelMessage tone="danger">{jobError}</PanelMessage>
            </div>
          ) : null}
        </div>

        <div className="space-y-3">
          <Button type="button" variant="secondary" fullWidth onClick={onOpenConfiguration}>
            Configure
          </Button>
          <Button type="button" variant="accent" fullWidth onClick={onOpenResults} disabled={!page}>
            View results
          </Button>
        </div>
      </div>
    </SurfacePanel>
  );
}
