const TONE_CLASSES = {
  neutral: "border-white/10 bg-white/[0.05] text-slate-300",
  accent: "border-emerald-400/35 bg-emerald-400/10 text-emerald-100",
  warning: "border-amber-400/35 bg-amber-400/10 text-amber-100",
  danger: "border-rose-400/35 bg-rose-400/10 text-rose-100",
};

export function StatusPill({ tone = "neutral", className, children }) {
  if (!children) {
    return null;
  }

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium tracking-[0.02em]",
        TONE_CLASSES[tone] || TONE_CLASSES.neutral,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </span>
  );
}
