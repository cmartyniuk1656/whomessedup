// A responsive comparison bar. Values sit outside the fill, so small/zero bars
// stay proportional and never need a minimum width to fit their labels.
import { CLASS_COLORS, DEFAULT_PLAYER_COLOR } from "../../../config/presentation";
import { colorWithAlpha } from "../../../utils/colorPresentation";

export function RelativeBar({ label, value, maximum, display, unitLabel, colorToken }) {
  const ratio = maximum > 0 ? Math.min(Math.max(value / maximum, 0), 1) : 0;
  const color = CLASS_COLORS[String(colorToken || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
  return (
    <div className="min-w-0 space-y-1.5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 text-sm">
        <span className="min-w-0 break-words font-medium [overflow-wrap:anywhere]" style={{ color }}>{label}</span>
        <span className="shrink-0 text-xs font-semibold tabular-nums text-slate-200" title={`${value.toLocaleString()} ${unitLabel}`}>{display}</span>
      </div>
      <div className="h-3 overflow-hidden rounded bg-slate-950/50 ring-1 ring-white/10"
        role="meter" aria-label={`${label}: ${display} ${unitLabel}`}
        aria-valuemin={0} aria-valuemax={maximum || 1} aria-valuenow={value}
        aria-valuetext={`${value.toLocaleString()} ${unitLabel}`}>
        <div className="h-full rounded-r" style={{ width: `${ratio * 100}%`, background: `linear-gradient(90deg, ${colorWithAlpha(color, 0.5)}, ${color})` }} />
      </div>
    </div>
  );
}
