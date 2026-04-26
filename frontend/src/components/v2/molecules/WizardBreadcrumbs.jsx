export function WizardBreadcrumbs({ steps, activeStep, onSelectStep }) {
  return (
    <nav aria-label="Report workflow" className="overflow-x-auto">
      <ol className="flex min-w-max items-center gap-3 px-1 py-1">
        {steps.map((step, index) => {
          const isActive = step.id === activeStep;
          const isEnabled = Boolean(step.enabled);
          const isComplete = Boolean(step.complete);
          const stepClasses = isActive
            ? "text-emerald-100 after:scale-x-100 after:bg-emerald-300"
            : isComplete
              ? "text-cyan-100 hover:text-cyan-50 after:bg-cyan-300/70"
              : "text-slate-500";
          const dotClasses = isActive
            ? "bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,0.55)]"
            : isComplete
              ? "bg-cyan-300/80"
              : "bg-slate-600/70";

          return (
            <li key={step.id} className="flex items-center gap-3">
              {index > 0 ? <span aria-hidden className="h-px w-7 bg-white/12" /> : null}
              <button
                type="button"
                aria-current={isActive ? "step" : undefined}
                disabled={!isEnabled}
                onClick={() => onSelectStep(step.id)}
                className={[
                  "relative inline-flex items-center gap-2 px-0.5 py-2 text-[0.7rem] font-semibold uppercase tracking-[0.18em]",
                  "transition after:absolute after:inset-x-0 after:bottom-0 after:h-px after:origin-left after:scale-x-0 after:transition-transform",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/35 focus-visible:ring-offset-4 focus-visible:ring-offset-transparent",
                  "enabled:hover:after:scale-x-100 disabled:cursor-not-allowed disabled:opacity-55",
                  stepClasses,
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <span aria-hidden className={["h-1.5 w-1.5 rounded-full transition", dotClasses].join(" ")} />
                <span>{step.label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
