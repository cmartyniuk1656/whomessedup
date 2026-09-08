import { useEffect, useState } from "react";
import { Button } from "../atoms/Button";
import { ThemedSelectMenu } from "./ThemedSelectMenu";

function reportLabel(report) {
  const date = report.end_time ? new Date(report.end_time).toLocaleDateString() : "Unknown date";
  return `${date} — ${report.title}${report.zone_name ? ` (${report.zone_name})` : ""}`;
}

export function RecentGuildReports({ guild, reports, isLoading, error, onSelectReport }) {
  const [selectedCode, setSelectedCode] = useState("");
  const [copyLabel, setCopyLabel] = useState("Copy code");

  useEffect(() => {
    setSelectedCode(reports[0]?.code || "");
  }, [reports]);

  if (!guild && !isLoading && !error) {
    return null;
  }

  const handleSelection = (code) => {
    setSelectedCode(code);
    setCopyLabel("Copy code");
    if (code) onSelectReport(code);
  };

  const copyCode = async () => {
    if (!selectedCode) return;
    try {
      await navigator.clipboard.writeText(selectedCode);
      setCopyLabel("Copied!");
    } catch {
      setCopyLabel("Copy failed");
    }
  };

  return (
    <section className="rounded-lg border border-emerald-300/20 bg-emerald-300/[0.06] p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-200">Recent guild reports</p>
          <p className="mt-1 text-xs text-slate-400">{guild ? `${guild.name} — ${guild.server_name}` : "Loading saved guild..."}</p>
        </div>
      </div>
      {isLoading ? <p className="mt-3 text-sm text-slate-400">Loading reports...</p> : null}
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      {!isLoading && guild && reports.length ? (
        <div className="mt-3 space-y-2">
          <ThemedSelectMenu
            id="recent-guild-report"
            ariaLabel="Recent Warcraft Logs report"
            options={reports.map((report) => ({
              id: report.code,
              label: reportLabel(report),
            }))}
            value={selectedCode}
            onChange={handleSelection}
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="accent" onClick={() => onSelectReport(selectedCode)}>Use report</Button>
            <Button size="sm" variant="secondary" onClick={copyCode}>{copyLabel}</Button>
            <a className="inline-flex items-center rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-white/20 hover:bg-white/5" href={`https://www.warcraftlogs.com/reports/${selectedCode}`} target="_blank" rel="noreferrer">Open log</a>
          </div>
        </div>
      ) : null}
      {!isLoading && guild && !reports.length && !error ? <p className="mt-3 text-sm text-slate-400">No public reports were found for this guild.</p> : null}
    </section>
  );
}
