import { PropsWithChildren } from "react";

export function GlassCard({ title, children }: PropsWithChildren<{ title?: string }>) {
  return (
    <div className="rounded-xl2 border border-border/60 bg-glass-gradient backdrop-blur-md shadow-glass">
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
