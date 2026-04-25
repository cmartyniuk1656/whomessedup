export function TextInput({ className, ...props }) {
  const classes = [
    "mt-2 w-full rounded-lg border border-white/10 bg-slate-950/40 px-3 py-2.5 text-sm text-slate-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] placeholder:text-slate-500 transition hover:border-white/15 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/30",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <input className={classes} {...props} />;
}
