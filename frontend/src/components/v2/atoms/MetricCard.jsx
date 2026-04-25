export function MetricCard({ label, value, className }) {
  return (
    <div
      className={[
        "rounded-[18px] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.045),rgba(255,255,255,0.015))] px-4 py-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-3 text-[1.45rem] font-semibold leading-none tracking-tight text-slate-50">{value}</p>
    </div>
  );
}
