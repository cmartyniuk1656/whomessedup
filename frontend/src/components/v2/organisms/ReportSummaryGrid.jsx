import { SummaryMetricCard } from "../molecules/SummaryMetricCard";

export function ReportSummaryGrid({ metrics }) {
  if (!metrics?.length) {
    return null;
  }

  return (
    <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(190px,1fr))]">
      {metrics.map((metric) => (
        <SummaryMetricCard key={metric.id} metric={metric} />
      ))}
    </div>
  );
}
