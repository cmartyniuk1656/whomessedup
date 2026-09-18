// Small labeled values shared by compact table cells and expanded evidence.
import { formatReportTableCellValue } from "../../../utils/reportTablePresentation";

export function MetricList({ metrics = [], panel = false }) {
  return (
    <dl className={panel ? "grid grid-cols-2 gap-3 rounded-xl border border-white/10 bg-slate-950/25 p-3 sm:grid-cols-3" : "flex min-w-0 flex-wrap gap-x-4 gap-y-2"}>
      {metrics.map((metric) => (
        <div key={metric.id} className="min-w-0">
          <dt className="break-words text-xs text-slate-400">{metric.label}</dt>
          <dd className="mt-0.5 break-words font-semibold tabular-nums text-slate-100" title={metric.value == null ? undefined : String(metric.value)}>
            {formatReportTableCellValue({ value: metric.value, display: metric.display, column: metric })}
          </dd>
        </div>
      ))}
    </dl>
  );
}
