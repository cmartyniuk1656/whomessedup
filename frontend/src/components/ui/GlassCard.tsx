import { PropsWithChildren } from "react";

type GlassCardProps = PropsWithChildren<{ title?: string; className?: string; bodyClassName?: string }>;

export function GlassCard({ title, children, className, bodyClassName }: GlassCardProps) {
  const cardClasses = [
    "relative overflow-hidden rounded-[26px] bg-[color:rgba(21,36,53,0.92)] backdrop-blur-xl ring-1 ring-white/5",
    "transition-all duration-300 ease-out will-change-transform",
    "group-hover:-translate-y-1 group-hover:bg-[color:rgba(25,42,62,0.98)] group-hover:ring-white/10",
    "group-hover:shadow-[0_30px_80px_-40px_rgba(16,185,129,0.55)] group-focus-visible:ring-white/15",
    "before:absolute before:inset-px before:rounded-[inherit] before:bg-gradient-to-b before:from-white/6 before:via-white/1 before:to-transparent before:opacity-25 before:pointer-events-none",
    "after:pointer-events-none after:absolute after:inset-0 after:bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.04),_transparent_55%)] after:opacity-6",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const bodyClasses = ["p-5 text-muted", bodyClassName].filter(Boolean).join(" ");

  return (
    <div className={cardClasses}>
      {title ? (
        <div className="flex items-center justify-between border-b border-white/5 p-5">
          <h3 className="font-medium tracking-tight">{title}</h3>
          <span className="inline-flex h-2 w-2 rounded-full bg-primary shadow-[0_0_15px_hsl(var(--primary)/0.7)]" />
        </div>
      ) : null}
      <div className={bodyClasses}>{children}</div>
    </div>
  );
}

export default GlassCard;
