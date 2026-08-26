import { Button } from "../atoms/Button";

export function SpecAnalysisCallout({ analysis, onOpen }) {
  if (!analysis?.series?.length) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-emerald-300/25 bg-gradient-to-r from-emerald-400/[0.12] via-emerald-400/[0.06] to-transparent px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-4">
        <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-emerald-300/25 bg-emerald-400/10 text-emerald-200">
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M4 15.5V11m6 4.5V5m6 10.5V8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <path d="M2.75 17.25h14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-emerald-300">Spec analysis</p>
          <h3 className="mt-1 text-base font-semibold text-slate-50">{analysis.title}</h3>
          {analysis.subtitle ? <p className="mt-1 text-sm text-slate-400">{analysis.subtitle}</p> : null}
        </div>
      </div>
      <Button type="button" variant="primary" size="md" className="shrink-0" onClick={onOpen}>
        View Spec Analysis
        <svg className="h-4 w-4" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="m7.5 5 5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </Button>
    </div>
  );
}
