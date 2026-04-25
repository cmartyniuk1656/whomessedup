export function KeyValuePill({ label, value, className }) {
  if (!label && !value) {
    return null;
  }

  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1.5 text-xs text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {label ? <span className="text-slate-500">{label}:</span> : null}
      {value ? <span className="font-medium text-slate-100">{value}</span> : null}
    </span>
  );
}
