const VARIANT_CLASSES = {
  primary:
    "border-emerald-300/40 bg-emerald-400 text-slate-950 shadow-[0_18px_40px_-24px_rgba(16,185,129,0.95)] hover:brightness-110",
  secondary: "border-white/10 bg-slate-950/45 text-slate-100 hover:border-white/20 hover:bg-white/[0.05]",
  accent: "border-emerald-400/35 bg-emerald-400/10 text-emerald-100 hover:border-emerald-300/55 hover:bg-emerald-400/15",
};

const SIZE_CLASSES = {
  sm: "px-3 py-2 text-xs",
  md: "px-4 py-2.5 text-sm",
};

export function Button({
  type = "button",
  variant = "secondary",
  size = "md",
  fullWidth = false,
  className,
  children,
  ...props
}) {
  const classes = [
    "inline-flex items-center justify-center gap-2 rounded-lg border font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40 disabled:cursor-not-allowed disabled:opacity-60",
    VARIANT_CLASSES[variant] || VARIANT_CLASSES.secondary,
    SIZE_CLASSES[size] || SIZE_CLASSES.md,
    fullWidth ? "w-full" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} {...props}>
      {children}
    </button>
  );
}
