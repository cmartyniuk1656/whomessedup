import { CLASS_COLORS, DEFAULT_PLAYER_COLOR } from "../../../config/presentation";
import { formatFloat } from "../../../utils/numberFormat";

const METRIC_STYLES = {
  boss: {
    barClassName: "border-sky-300/70 bg-sky-400/85 shadow-[0_10px_24px_-14px_rgba(56,189,248,0.9)]",
    chipClassName: "border-sky-300/30 bg-sky-400/10 text-sky-200",
  },
  priority: {
    barClassName: "border-emerald-300/70 bg-emerald-400/85 shadow-[0_10px_24px_-14px_rgba(52,211,153,0.95)]",
    chipClassName: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
  },
  pad: {
    barClassName: "border-amber-300/70 bg-amber-300/85 shadow-[0_10px_24px_-14px_rgba(252,211,77,0.95)]",
    chipClassName: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  },
};

const AXIS_STEPS = [1, 0.75, 0.5, 0.25, 0];

function formatMetricValue(value) {
  if (typeof value !== "number") {
    return String(value ?? "0");
  }
  return formatFloat(value, 3);
}

function formatPercentRatio(value) {
  return `${Math.round(value * 100)}%`;
}

export function SpecAnalysisChart({ analysis, series }) {
  const metrics = analysis?.metrics ?? [];
  const chartSeries = series ?? [];
  const metricMaxById = Object.fromEntries(
    metrics.map((metric) => [
      metric.id,
      Math.max(0, ...chartSeries.map((entry) => Number(entry?.values?.[metric.id] ?? 0))),
    ])
  );
  const normalizedValues = chartSeries.flatMap((entry) =>
    metrics.map((metric) => {
      const value = Number(entry?.values?.[metric.id] ?? 0);
      const metricMax = Number(metricMaxById[metric.id] ?? 0);
      return metricMax > 0 ? Math.min(Math.max(value / metricMax, 0), 1) : 0;
    })
  );
  const nonZeroNormalizedValues = normalizedValues.filter((value) => value > 0);
  let lowerBoundRatio = 0;
  if (nonZeroNormalizedValues.length) {
    lowerBoundRatio = Math.max(0, Math.min(...nonZeroNormalizedValues) - 0.05);
    lowerBoundRatio = Math.floor(lowerBoundRatio / 0.05) * 0.05;
    if (1 - lowerBoundRatio < 0.15) {
      lowerBoundRatio = 0.85;
    }
  }
  const visibleSpan = Math.max(1 - lowerBoundRatio, 0.15);

  if (!metrics.length || !chartSeries.length) {
    return (
      <div className="rounded-xl border border-white/10 bg-slate-950/35 px-4 py-10 text-center text-sm text-slate-400">
        No specialization data was available for this report.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          {metrics.map((metric) => {
            const styles = METRIC_STYLES[metric.id] || METRIC_STYLES.boss;
            return (
              <span
                key={metric.id}
                className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${styles.chipClassName}`}
              >
                {metric.label}
              </span>
            );
          })}
        </div>
        <p className="text-xs text-slate-400">Each color is scaled against the top spec for that metric, and the y-axis is cropped to the visible range.</p>
      </div>

      <div className="overflow-x-auto pb-2">
        <div className="min-w-max space-y-4">
          <div className="relative pl-11">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex flex-col justify-between text-[10px] font-medium text-slate-500">
              {AXIS_STEPS.map((step) => (
                <span key={step}>{formatPercentRatio(lowerBoundRatio + step * visibleSpan)}</span>
              ))}
            </div>

            <div className="relative h-64 min-w-max border-b border-white/10">
              {AXIS_STEPS.map((step) => (
                <div
                  key={`grid-${step}`}
                  className="pointer-events-none absolute inset-x-0 border-t border-dashed border-white/8"
                  style={{ bottom: `${step * 100}%` }}
                />
              ))}

              <div className="relative flex h-full items-end gap-4 pr-3">
                {chartSeries.map((entry) => {
                  return (
                    <div key={entry.id} className="flex h-full w-[104px] shrink-0 items-end justify-center gap-2">
                      {metrics.map((metric) => {
                        const styles = METRIC_STYLES[metric.id] || METRIC_STYLES.boss;
                        const value = Number(entry?.values?.[metric.id] ?? 0);
                        const metricMax = Number(metricMaxById[metric.id] ?? 0);
                        const normalizedRatio = metricMax > 0 ? Math.min(Math.max(value / metricMax, 0), 1) : 0;
                        const visibleRatioRaw =
                          normalizedRatio > lowerBoundRatio ? (normalizedRatio - lowerBoundRatio) / visibleSpan : 0;
                        const visibleRatio = Math.min(Math.max(visibleRatioRaw, 0), 1);
                        const barStyle =
                          value > 0
                            ? {
                                height: `${visibleRatio * 100}%`,
                                minHeight: "4px",
                              }
                            : { height: "0%" };

                        return (
                          <div
                            key={`${entry.id}-${metric.id}`}
                            className="flex h-full w-6 items-end"
                            title={`${entry.specName} - ${metric.label}: ${formatMetricValue(value)}`}
                          >
                            <div
                              className={`w-full rounded-t-md border transition hover:brightness-110 ${styles.barClassName}`}
                              style={barStyle}
                            />
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="pl-11">
            <div className="flex gap-4 pr-3">
              {chartSeries.map((entry) => {
                const color = CLASS_COLORS[String(entry?.colorToken || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;

                return (
                  <div key={`${entry.id}-label`} className="w-[104px] shrink-0 space-y-1 text-center">
                    <p className="text-sm font-semibold tracking-tight" style={{ color }}>
                      {entry.specName}
                    </p>
                    <p className="text-[11px] text-slate-400">{entry.className || "Unknown"}</p>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
                      {entry.playerCount} {entry.playerCount === 1 ? "Player" : "Players"}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
