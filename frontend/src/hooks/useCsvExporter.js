import { useCallback } from "react";

const escapeCsv = (value) => {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
};

const buildCsvContent = (tile, data, tableRows, phases, labels, metrics = []) => {
  if (!tile) {
    throw new Error("No tile selected");
  }

  if (tile.mode === "phase-damage") {
    const headers = ["Player", "Role", "Class", "Pulls"];
    if (phases.length > 1) {
      headers.push("Avg / Pull (Combined)");
    }
    phases.forEach((phaseId) => {
      const label = labels[phaseId] || `Phase ${phaseId}`;
      headers.push(`Total ${label}`);
      headers.push(`Avg / Pull ${label}`);
    });
    const lines = [headers.map(escapeCsv).join(",")];
    tableRows.forEach((row) => {
      const className = row.className ?? data.player_classes?.[row.player] ?? "";
      const values = [row.player, row.role, className, row.pulls ?? 0];
      if (phases.length > 1) {
        values.push(row.combinedAverage ?? 0);
      }
      phases.forEach((phaseId) => {
        values.push(row.phaseTotals?.[phaseId] ?? 0);
        values.push(row.phaseAverages?.[phaseId] ?? 0);
      });
      lines.push(values.map(escapeCsv).join(","));
    });
    return `\ufeff${lines.join("\n")}`;
  }

  if (tile.mode === "add-damage") {
    const headers = ["Player", "Role", "Class", "Pulls", "Total Add Damage", "Avg Add Damage / Pull"];
    const lines = [headers.map(escapeCsv).join(",")];
    tableRows.forEach((row) => {
      const className = row.className ?? data.player_classes?.[row.player] ?? "";
      const values = [
        row.player,
        row.role,
        className,
        row.pulls ?? 0,
        row.addTotalDamage ?? 0,
        row.addAverageDamage ?? 0,
      ];
      lines.push(values.map(escapeCsv).join(","));
    });
    return `\ufeff${lines.join("\n")}`;
  }

  if (tile.mode === "dimensius-phase1") {
    const metricList = Array.isArray(metrics) ? metrics : [];
    const headers = ["Player", "Role", "Class", "Pulls"];
    metricList.forEach((metric) => {
      headers.push(metric.label || metric.id);
      headers.push(metric.per_pull_label || `${metric.label || metric.id} / Pull`);
    });
    headers.push("Fuck-up Rate");
    const lines = [headers.map(escapeCsv).join(",")];
    tableRows.forEach((row) => {
      const className = row.className ?? data.player_classes?.[row.player] ?? "";
      const values = [row.player, row.role, className, row.pulls ?? 0];
      metricList.forEach((metric) => {
        values.push(row.metricTotals?.[metric.id] ?? 0);
        values.push(row.metricPerPull?.[metric.id] ?? 0);
      });
      values.push(row.fuckupRate ?? 0);
      lines.push(values.map(escapeCsv).join(","));
    });
    return `\ufeff${lines.join("\n")}`;
  }

  const headers = [
    "Player",
    "Role",
    "Class",
    "Pulls",
    "Besiege Hits",
    "Besiege / Pull",
    "Ghost Misses",
    "Ghost / Pull",
    "Fuck-up Rate",
  ];
  const lines = [headers.map(escapeCsv).join(",")];
  tableRows.forEach((row) => {
    const className = row.className ?? data.player_classes?.[row.player] ?? "";
    const values = [
      row.player,
      row.role,
      className,
      row.pulls ?? 0,
      row.besiegeHits ?? 0,
      row.besiegePerPull ?? 0,
      row.ghostMisses ?? 0,
      row.ghostPerPull ?? 0,
      row.fuckupRate ?? 0,
    ];
    lines.push(values.map(escapeCsv).join(","));
  });
  return `\ufeff${lines.join("\n")}`;
};

export function useCsvExporter(setError) {
  const downloadCsv = useCallback(
    ({ tile, result, rows, phases, labels, metrics }) => {
      if (!tile || !result) {
        return;
      }
      try {
        const csvContent = buildCsvContent(tile, result, rows, phases, labels, metrics);
        const safeReport = (result.report || "report").replace(/[^a-zA-Z0-9-_]/g, "_");
        const filename = `${safeReport}_${tile.id}.csv`;
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error("CSV export failed:", err);
        if (setError) {
          setError("Failed to export CSV. Please try again.");
        }
      }
    },
    [setError]
  );

  return { downloadCsv };
}
