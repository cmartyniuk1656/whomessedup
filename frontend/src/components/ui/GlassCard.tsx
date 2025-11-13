import { PropsWithChildren } from "react";

type GlassCardProps = PropsWithChildren<{ title?: string; className?: string }>;

export function GlassCard({ title, children, className }: GlassCardProps) {
  const cardClasses = [
    "relative overflow-hidden rounded-xl2 border border-white/10 bg-white/5 backdrop-blur-2xl shadow-[0_25px_60px_-30px_rgba(16,185,129,0.65)]",
    "before:absolute before:inset-px before:rounded-[inherit] before:bg-gradient-to-b before:from-white/20 before:via-white/5 before:to-transparent before:opacity-70 before:pointer-events-none",
    "after:pointer-events-none after:absolute after:inset-0 after:bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.35),_transparent_55%)] after:opacity-30",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cardClasses}>
      {title ? (
        <div className="flex items-center justify-between border-b border-white/5 p-5">
          <h3 className="font-medium tracking-tight">{title}</h3>
          <span className="inline-flex h-2 w-2 rounded-full bg-primary shadow-[0_0_15px_hsl(var(--primary)/0.7)]" />
        </div>
      ) : null}
      <div className="p-5 text-muted">{children}</div>
    </div>
  );
}

export default GlassCard;
