import { PropsWithChildren } from "react";

type GlassCardProps = PropsWithChildren<{ title?: string; className?: string }>;

export function GlassCard({ title, children, className }: GlassCardProps) {
  const cardClasses = [
    "relative overflow-hidden rounded-[26px] bg-[#152435] backdrop-blur-xl ring-1 ring-white/5",
    "before:absolute before:inset-px before:rounded-[inherit] before:bg-gradient-to-b before:from-white/6 before:via-white/1 before:to-transparent before:opacity-25 before:pointer-events-none",
    "after:pointer-events-none after:absolute after:inset-0 after:bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.04),_transparent_55%)] after:opacity-6",
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
