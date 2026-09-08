import { Button } from "../atoms/Button";

const STATUS_LABELS = {
  checking: "Checking…",
  error: "Retrying…",
  paused: "Paused",
  updating: "Updating…",
  watching: "Watching",
};

function RefreshIcon({ spinning = false }) {
  return (
    <svg
      aria-hidden="true"
      className={`h-4 w-4 ${spinning ? "animate-spin" : ""}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
    >
      <path d="M19.5 7.5V3.75m0 0h-3.75m3.75 0-3.1 3.1a7 7 0 1 0 1.55 7.55" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function RealtimeReportControl({ realtime }) {
  if (!realtime?.isVisible) {
    return null;
  }

  const statusLabel = realtime.enabled ? STATUS_LABELS[realtime.status] || "Watching" : "Real-time mode";
  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={realtime.refresh}
          disabled={realtime.isBusy}
          title="Refresh this report with the latest Warcraft Logs data."
        >
          <RefreshIcon spinning={realtime.isRefreshing} />
          {realtime.isRefreshing ? "Refreshing..." : "Refresh"}
        </Button>
        <Button
          type="button"
          variant={realtime.enabled ? "accent" : "secondary"}
          size="sm"
          onClick={realtime.toggle}
          disabled={!realtime.isAvailable || realtime.isBusy}
          aria-pressed={realtime.enabled}
          title={realtime.unavailableReason || "Check Warcraft Logs for newly completed pulls."}
        >
          <span
            aria-hidden
            className={`h-2 w-2 rounded-full ${
              realtime.enabled
                ? realtime.status === "error"
                  ? "bg-rose-300"
                  : realtime.status === "paused"
                    ? "bg-amber-300"
                    : "bg-emerald-300 shadow-[0_0_8px_rgba(110,231,183,0.8)]"
                : "bg-slate-500"
            }`}
          />
          {statusLabel}
        </Button>
      </div>
      {!realtime.isAvailable && realtime.unavailableReason ? (
        <span className="max-w-64 text-right text-[11px] text-amber-200" role="status">
          {realtime.unavailableReason}
        </span>
      ) : realtime.error ? (
        <span className="max-w-64 text-right text-[11px] text-rose-300" role="status">
          {realtime.error}
        </span>
      ) : null}
    </div>
  );
}
