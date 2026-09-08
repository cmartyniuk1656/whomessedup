import { CLASS_COLORS, DEFAULT_PLAYER_COLOR } from "../../../config/presentation";
import { colorWithAlpha } from "../../../utils/colorPresentation";

export function RelativeBarChart({ chart, standalone = false }) {
  const bars = chart?.bars ?? [];
  const maximum = Math.max(0, ...bars.map((bar) => Number(bar?.value ?? 0)));

  return (
    <section className={standalone ? "" : "mt-4 border-t border-white/10 pt-4"}>
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">
          {chart?.title}
        </h4>
        {chart?.subtitle ? <p className="mt-1 text-xs text-slate-400">{chart.subtitle}</p> : null}
      </div>

      {bars.length ? (
        <div className="mt-3 overflow-x-auto pb-1">
          <div className="min-w-[34rem] space-y-2.5" role="list">
            {bars.map((bar) => {
              const value = Number(bar?.value ?? 0);
              const ratio = maximum > 0 ? Math.min(Math.max(value / maximum, 0), 1) : 0;
              const percent = Math.round(ratio * 100);
              const color =
                CLASS_COLORS[String(bar?.colorToken || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;

              return (
                <div
                  key={bar.id}
                  className="grid grid-cols-[10rem_minmax(20rem,1fr)] items-center gap-3"
                  role="listitem"
                >
                  <span className="truncate text-right text-sm font-semibold tracking-tight" style={{ color }}>
                    {bar.label}
                  </span>
                  <div className="h-7 overflow-hidden rounded-md border border-white/10 bg-slate-950/45">
                    <div
                      className="flex h-full min-w-[8.5rem] items-center justify-end rounded-r-md border-r px-2.5 text-xs font-semibold tabular-nums text-white transition-[width] duration-300"
                      style={{
                        width: `${ratio * 100}%`,
                        borderRightColor: colorWithAlpha(color, 0.72),
                        background: `linear-gradient(90deg, ${colorWithAlpha(color, 0.52)}, ${colorWithAlpha(color, 0.88)})`,
                        boxShadow: `0 0 18px -8px ${colorWithAlpha(color, 0.9)}`,
                      }}
                      role="progressbar"
                      aria-label={`${bar.label}: ${bar.display} damage, ${percent}% of the highest contributor`}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={percent}
                      title={`${bar.label}: ${bar.display} damage (${percent}%)`}
                    >
                      <span>{bar.display} · {percent}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-400">No Drowned Echo damage was recorded for this set.</p>
      )}
    </section>
  );
}
