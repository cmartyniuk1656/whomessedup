import { formatFloat, formatInt } from "./numberFormat";

export function formatReportTableCellValue({ value, display, column }) {
  if (display != null && display !== "") {
    return display;
  }
  if (value == null) {
    return "";
  }
  if (column?.format === "integer") {
    return formatInt(value);
  }
  if (column?.format === "decimal") {
    return formatFloat(value, column?.precision ?? 3);
  }
  return value;
}

export function formatReportSummaryMetric(metric) {
  if (metric.display != null && metric.display !== "") {
    return metric.display;
  }
  if (metric.format === "integer") {
    return formatInt(metric.value);
  }
  if (metric.format === "decimal") {
    return formatFloat(metric.value, metric.precision ?? 3);
  }
  return metric.value;
}

function escapeCsv(value) {
  if (value == null) {
    return "";
  }
  const stringValue = String(value);
  if (/[",\n]/.test(stringValue)) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  return stringValue;
}

export function buildReportTableCsv(page, rows, tableOverride) {
  const table = tableOverride ?? page?.content?.table;
  const columns = table?.columns ?? [];
  const lines = [columns.map((column) => escapeCsv(column.label)).join(",")];

  rows.forEach((row) => {
    const values = columns.map((column) => {
      const cell = row?.cells?.[column.id];
      return formatReportTableCellValue({
        value: cell?.value,
        display: cell?.display,
        column,
      });
    });
    lines.push(values.map(escapeCsv).join(","));
  });

  return `\ufeff${lines.join("\n")}`;
}

export function downloadReportTableCsv(page, rows, tableOverride) {
  const csv = buildReportTableCsv(page, rows, tableOverride);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const safeReport = String(page?.reportCode || "report").replace(/[^a-zA-Z0-9-_]/g, "_");
  const safeId = String(page?.reportId || "report").replace(/[^a-zA-Z0-9-_]/g, "_");

  link.href = url;
  link.download = `${safeReport}_${safeId}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
