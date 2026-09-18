// A part-to-whole bar with explicit counts, including zero and unresolved outcomes.
const TONES = {
  success: { bar: "bg-emerald-400", text: "text-emerald-300" },
  danger: { bar: "bg-rose-400", text: "text-rose-300" },
  neutral: { bar: "bg-slate-400", text: "text-slate-300" },
};

export function OutcomeBar({ cell, compact = false }) {
  const outcomes = cell?.outcomes ?? [];
  const total = outcomes.reduce((sum, outcome) => sum + outcome.value, 0);
  const description = outcomes.map((outcome) => `${outcome.value} ${outcome.label.toLowerCase()}`).join(", ");

  return (
    <div className={`${compact ? "min-w-0" : "min-w-72"} max-w-xl space-y-2`}>
      <div
        className="flex h-5 overflow-hidden rounded-md bg-slate-950/50 ring-1 ring-white/10"
        role="img"
        aria-label={`${cell?.label || "Outcomes"}: ${description}; ${total} total`}
      >
        {outcomes.filter((outcome) => outcome.value > 0).map((outcome) => (
          <div
            key={outcome.id}
            className={`${(TONES[outcome.tone] || TONES.neutral).bar} border-r border-slate-950/25 last:border-0`}
            style={{ width: `${(outcome.value / total) * 100}%` }}
            title={`${outcome.label}: ${outcome.value} / ${total}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
        {outcomes.map((outcome) => (
          <span key={outcome.id} className={`inline-flex items-center gap-1.5 ${(TONES[outcome.tone] || TONES.neutral).text}`}>
            <span className={`h-2 w-2 rounded-sm ${(TONES[outcome.tone] || TONES.neutral).bar}`} aria-hidden="true" />
            <strong className="tabular-nums">{outcome.value}</strong> {outcome.label}
          </span>
        ))}
      </div>
      {!total ? <p className="text-xs text-slate-400">No outcomes observed</p> : null}
    </div>
  );
}
