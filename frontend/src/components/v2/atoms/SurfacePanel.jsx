const TONE_CLASSES = {
  default: "border-white/10 bg-[color:rgba(15,23,42,0.72)] shadow-[0_35px_90px_-55px_rgba(16,185,129,0.28)]",
  muted: "border-white/10 bg-[color:rgba(15,23,42,0.58)] shadow-[0_28px_70px_-55px_rgba(8,145,178,0.3)]",
};

export function SurfacePanel({ as: Component = "section", tone = "default", className, children }) {
  const classes = [
    "relative overflow-hidden rounded-[24px] border backdrop-blur-xl",
    "before:pointer-events-none before:absolute before:inset-px before:rounded-[inherit] before:bg-gradient-to-b before:from-white/6 before:via-white/[0.03] before:to-transparent",
    "after:pointer-events-none after:absolute after:inset-0 after:bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.07),_transparent_55%)] after:opacity-45",
    TONE_CLASSES[tone] || TONE_CLASSES.default,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Component className={classes}>
      <div className="relative z-10">{children}</div>
    </Component>
  );
}
