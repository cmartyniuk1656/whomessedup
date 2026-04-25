import { Button } from "../atoms/Button";
import { FieldHint } from "../atoms/FieldHint";
import { StatusPill } from "../atoms/StatusPill";

export function ReportRunCard({ report, isSubmitting, pendingJob }) {
  const statusLabel = pendingJob ? (pendingJob.status === "running" ? "Running" : "Queued") : "Ready";
  const statusTone = pendingJob ? (pendingJob.status === "running" ? "accent" : "warning") : "neutral";

  return (
    <div className="space-y-4 xl:sticky xl:top-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium text-slate-100">Run {report?.title}</p>
          <StatusPill tone={statusTone}>{statusLabel}</StatusPill>
        </div>
        <FieldHint>{report?.description}</FieldHint>
      </div>
      <Button
        type="submit"
        variant="primary"
        fullWidth
        disabled={isSubmitting}
      >
        {isSubmitting ? "Running..." : "Run report"}
      </Button>
      {pendingJob ? (
        <div className="space-y-1 border-t border-white/10 pt-4 text-xs text-slate-400">
          {typeof pendingJob.position === "number" ? (
            <p>{pendingJob.position === 0 ? "Currently executing." : `Position in queue: ${pendingJob.position}`}</p>
          ) : null}
          <p className="break-all">Job ID: {pendingJob.id}</p>
        </div>
      ) : (
        <p className="border-t border-white/10 pt-4 text-xs text-slate-500">The result is rendered directly from the backend view model.</p>
      )}
    </div>
  );
}
