import { createPortal } from "react-dom";
import { Button } from "../atoms/Button";

function UpdateIcon() {
  return (
    <svg
      aria-hidden="true"
      className="h-5 w-5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path
        d="m5 12 4 4L19 6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg
      aria-hidden="true"
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="m6 6 12 12M18 6 6 18" strokeLinecap="round" />
    </svg>
  );
}

export function ReportUpdateNotification({ notice, onDismiss, onViewPull }) {
  if (!notice || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div
      className="fixed bottom-4 left-4 right-4 z-[70] sm:left-auto sm:w-full sm:max-w-sm"
      role="status"
      aria-live="polite"
    >
      <div className="overflow-hidden rounded-xl border border-emerald-300/25 bg-slate-950/95 shadow-2xl shadow-black/40 backdrop-blur-xl">
        <div className="h-1 bg-gradient-to-r from-emerald-500 to-cyan-400" />
        <div className="flex gap-3 p-4">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300">
            <UpdateIcon />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-slate-100">
              {notice.title || (notice.viewId ? "New pull available" : "Report updated")}
            </p>
            <p className="mt-1 text-sm text-slate-300">{notice.message}</p>
            {onViewPull ? (
              <Button
                type="button"
                variant="accent"
                size="sm"
                className="mt-3"
                onClick={onViewPull}
              >
                View pull
              </Button>
            ) : null}
          </div>
          <button
            type="button"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-white/[0.06] hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40"
            aria-label="Dismiss notification"
            title="Dismiss"
            onClick={onDismiss}
          >
            <CloseIcon />
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
