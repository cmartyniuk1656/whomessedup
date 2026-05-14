import GlassCard from "../../ui/GlassCard";
import { PanelMessage } from "../atoms/PanelMessage";

function formatReportDifficulty(difficulty) {
  if (!difficulty) {
    return null;
  }
  return `${difficulty.charAt(0).toUpperCase()}${difficulty.slice(1)}`;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeTitlePart(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function getShortReportTitle(report) {
  let title = normalizeTitlePart(report?.title || "Report");
  const difficulty = normalizeTitlePart(formatReportDifficulty(report?.difficulty));
  const fightName = normalizeTitlePart(report?.fightName || report?.defaultFight);
  const shortFightName = normalizeTitlePart(fightName.split(",")[0]);
  const prefixes = [
    difficulty && fightName ? `${difficulty} ${fightName}` : null,
    difficulty && shortFightName ? `${difficulty} ${shortFightName}` : null,
    fightName,
    shortFightName,
    difficulty,
  ].filter(Boolean);

  prefixes.forEach((prefix) => {
    title = title.replace(new RegExp(`^${escapeRegExp(prefix)}\\s*(?:[-:])?\\s*`, "i"), "").trim();
  });

  return title || report?.title || "Report";
}

function getReportStatusLabel(report, isSelected) {
  return [formatReportDifficulty(report.difficulty), isSelected ? "Selected" : "Available"].filter(Boolean).join(" • ");
}

export function ReportCatalog({
  reports,
  selectedReportId,
  onSelectReport,
  isBusy,
  eyebrow = "Reports",
  title = "Choose a report",
  description = "",
  emptyMessage = "",
}) {
  const hasReports = Boolean(reports?.length);

  return (
    <section aria-label="Available reports" className="space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.22em] text-emerald-300">{eyebrow}</p>
        <h2 className="mt-2 text-2xl font-semibold text-white">{title}</h2>
        {description ? <p className="mt-2 text-sm text-slate-400">{description}</p> : null}
      </div>
      {hasReports ? (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {reports.map((report) => {
            const isSelected = report.id === selectedReportId;
            return (
              <button
                key={report.id}
                type="button"
                onClick={() => onSelectReport(report.id)}
                className="group h-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300 focus-visible:ring-offset-2 ring-offset-surface disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isBusy}
                aria-pressed={isSelected}
              >
                <GlassCard
                  title={getShortReportTitle(report)}
                  className={
                    isSelected
                      ? "h-full ring-1 ring-emerald-400/60 shadow-[0_30px_80px_-40px_rgba(16,185,129,0.55)]"
                      : "h-full"
                  }
                >
                  <div className="flex h-full flex-col gap-4 text-content">
                    <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                      {getReportStatusLabel(report, isSelected)}
                    </div>
                    <p className="text-sm text-muted">{report.description}</p>
                    <div className="mt-auto inline-flex items-center gap-2 text-sm font-medium text-primary">
                      {isSelected ? "Editing configuration" : "Open report"}
                    </div>
                  </div>
                </GlassCard>
              </button>
            );
          })}
        </div>
      ) : emptyMessage ? (
        <PanelMessage>{emptyMessage}</PanelMessage>
      ) : null}
    </section>
  );
}
