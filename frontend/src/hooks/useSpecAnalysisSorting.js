import { useEffect, useMemo, useState } from "react";

function compareSeries(left, right) {
  const classDiff = String(left?.className ?? "").localeCompare(String(right?.className ?? ""), undefined, {
    sensitivity: "base",
  });
  if (classDiff !== 0) {
    return classDiff;
  }
  return String(left?.specName ?? "").localeCompare(String(right?.specName ?? ""), undefined, {
    sensitivity: "base",
  });
}

function metricMaxById(analysis) {
  const metrics = Array.isArray(analysis?.metrics) ? analysis.metrics : [];
  const series = Array.isArray(analysis?.series) ? analysis.series : [];
  return Object.fromEntries(
    metrics.map((metric) => [
      metric.id,
      Math.max(0, ...series.map((entry) => Number(entry?.values?.[metric.id] ?? 0))),
    ])
  );
}

function normalizedMetricAverage(entry, metricIds, maxByMetric) {
  if (!metricIds.length) {
    return 0;
  }
  const total = metricIds.reduce((sum, metricId) => {
    const value = Number(entry?.values?.[metricId] ?? 0);
    const maxValue = Number(maxByMetric?.[metricId] ?? 0);
    if (maxValue <= 0) {
      return sum;
    }
    return sum + value / maxValue;
  }, 0);
  return total / metricIds.length;
}

function overallScore(entry, analysis, maxByMetric) {
  const metrics = Array.isArray(analysis?.metrics) ? analysis.metrics : [];
  return normalizedMetricAverage(
    entry,
    metrics.map((metric) => metric.id),
    maxByMetric
  );
}

function bossPriorityScore(entry, maxByMetric) {
  return normalizedMetricAverage(entry, ["boss", "priority"], maxByMetric);
}

export function useSpecAnalysisSorting(analysis) {
  const defaultSort = analysis?.defaultSort || "overall";
  const [sortId, setSortId] = useState(defaultSort);

  useEffect(() => {
    setSortId(defaultSort);
  }, [defaultSort, analysis?.title]);

  const sortedSeries = useMemo(() => {
    const series = Array.isArray(analysis?.series) ? [...analysis.series] : [];
    const maxByMetric = metricMaxById(analysis);

    series.sort((left, right) => {
      if (sortId === "boss_priority") {
        const rightScore = bossPriorityScore(right, maxByMetric);
        const leftScore = bossPriorityScore(left, maxByMetric);
        if (rightScore !== leftScore) {
          return rightScore - leftScore;
        }
        return compareSeries(left, right);
      }

      if (sortId === "overall") {
        const rightScore = overallScore(right, analysis, maxByMetric);
        const leftScore = overallScore(left, analysis, maxByMetric);
        if (rightScore !== leftScore) {
          return rightScore - leftScore;
        }
        return compareSeries(left, right);
      }

      const rightValue = Number(right?.values?.[sortId] ?? 0);
      const leftValue = Number(left?.values?.[sortId] ?? 0);
      if (rightValue !== leftValue) {
        return rightValue - leftValue;
      }
      return compareSeries(left, right);
    });

    return series;
  }, [analysis, sortId]);

  return {
    sortId,
    setSortId,
    sortedSeries,
  };
}
