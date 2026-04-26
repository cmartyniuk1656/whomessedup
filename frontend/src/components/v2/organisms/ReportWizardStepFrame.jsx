import { useEffect, useRef } from "react";

export function ReportWizardStepFrame({ stepKey, title, eyebrow, description, children, phase = "enter" }) {
  const sectionRef = useRef(null);
  const headingRef = useRef(null);
  const hasTitle = Boolean(title);
  const hasHeading = Boolean(title || eyebrow || description);

  useEffect(() => {
    (headingRef.current ?? sectionRef.current)?.focus({ preventScroll: true });
  }, [stepKey]);

  return (
    <section
      key={stepKey}
      ref={sectionRef}
      className={`wizard-step-${phase} space-y-6 focus:outline-none`}
      aria-labelledby={hasTitle ? `${stepKey}-wizard-heading` : undefined}
      tabIndex={hasTitle ? undefined : -1}
    >
      {hasHeading ? (
        <div>
          {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-300">{eyebrow}</p> : null}
          {hasTitle ? (
            <h1
              id={`${stepKey}-wizard-heading`}
              ref={headingRef}
              tabIndex={-1}
              className="mt-2 text-3xl font-semibold leading-tight text-white focus:outline-none sm:text-4xl"
            >
              {title}
            </h1>
          ) : null}
          {description ? <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">{description}</p> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
