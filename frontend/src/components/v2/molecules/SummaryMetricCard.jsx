import { MetricCard } from "../atoms/MetricCard";
import { formatReportSummaryMetric } from "../../../utils/reportTablePresentation";

export function SummaryMetricCard({ metric }) {
  return <MetricCard label={metric.label} value={formatReportSummaryMetric(metric)} />;
}
