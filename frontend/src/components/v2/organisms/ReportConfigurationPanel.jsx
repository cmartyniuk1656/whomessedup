import { Button } from "../atoms/Button";
import { StatusPill } from "../atoms/StatusPill";
import { KeyValuePill } from "../atoms/KeyValuePill";
import { SurfacePanel } from "../atoms/SurfacePanel";

export function ReportConfigurationPanel({
  report,
  isSubmitting,
  pendingJob,
  onOpen,
}) {
  if (!report) {
    return null;
  }

  const statusLabel = pendingJob ? (pendingJob.status === "running" ? "Running" : "Queued") : "Ready";
  const statusTone = pendingJob ? (pendingJob.status === "running" ? "accent" : "warning") : "neutral";

  return (
    <SurfacePanel className="p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Configuration</p>
            <StatusPill tone={statusTone}>{statusLabel}</StatusPill>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">{report.title}</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">{report.description}</p>
          {report.footnotes?.[0] ? <p className="mt-3 text-xs text-slate-500">{report.footnotes[0]}</p> : null}
        </div>
        <div className="flex flex-col items-start gap-3 lg:items-end">
          {report.defaultFight ? <KeyValuePill label="Default fight" value={report.defaultFight} /> : null}
          <Button onClick={onOpen} disabled={isSubmitting}>
            {isSubmitting ? "Running..." : "Open configuration"}
          </Button>
        </div>
      </div>
    </SurfacePanel>
  );
}
