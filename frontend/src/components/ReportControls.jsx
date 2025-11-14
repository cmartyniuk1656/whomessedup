import { BOSS_OPTIONS } from "../config/constants";
import GlassCard from "./ui/GlassCard";

export function ReportControls({
  reportInput,
  onReportInputChange,
  fightOverride,
  onFightOverrideChange,
  ignoreAfterDeaths,
  onIgnoreAfterDeathsChange,
  ignoreFinalSeconds,
  onIgnoreFinalSecondsChange,
  isBusy,
}) {
  const fieldClasses =
    "mt-2 w-full rounded-lg border border-white/10 bg-white/10 px-4 py-2 text-base text-content placeholder:text-muted/70 focus:border-primary focus:ring focus:ring-primary/40 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60";
  const selectClasses = `${fieldClasses} themed-select`;

  return (
    <section className="px-6 pb-10">
      <GlassCard
        className="mx-auto max-w-6xl isolate rounded-[32px] shadow-[0_35px_80px_-40px_rgba(15,118,110,0.8)] z-10"
        bodyClassName="relative px-6 py-10 text-content sm:px-12"
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.25),_transparent_70%)] opacity-30" />
        <div className="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Report controls</p>
            <p className="mt-1 text-sm text-muted/90">Paste a Warcraft Logs report and optionally scope the fight.</p>
          </div>
          <span className="text-xs text-muted/70">All inputs optional except the report URL or code.</span>
        </div>
        <div className="relative mt-8 flex flex-col gap-4 sm:flex-row">
          <label className="flex w-full flex-col text-sm font-medium sm:max-w-md">
            Report URL or code
            <input
              className={fieldClasses}
              placeholder="https://www.warcraftlogs.com/reports/..."
              value={reportInput}
              onChange={(event) => onReportInputChange(event.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="flex w-full flex-col text-sm font-medium sm:max-w-xs">
            Fight filter (optional)
            <select
              className={selectClasses}
              style={{ colorScheme: "dark" }}
              value={fightOverride}
              onChange={(event) => onFightOverrideChange(event.target.value)}
              disabled={isBusy}
            >
              <option value="">All fights</option>
              {BOSS_OPTIONS.map((boss) => (
                <option key={boss} value={boss}>
                  {boss}
                </option>
              ))}
            </select>
            <span className="mt-1 text-xs text-muted">Use this to restrict the report to a specific boss.</span>
          </label>
        </div>
        <div className="relative mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex w-full flex-col text-sm font-medium">
            Ignore hits after total deaths (per pull)
            <input
              className={fieldClasses}
              placeholder="e.g. 3"
              value={ignoreAfterDeaths}
              onChange={(event) => onIgnoreAfterDeathsChange(event.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="flex w-full flex-col text-sm font-medium">
            Ignore final seconds of each pull
            <input
              className={fieldClasses}
              placeholder="e.g. 10"
              value={ignoreFinalSeconds}
              onChange={(event) => onIgnoreFinalSecondsChange(event.target.value)}
              disabled={isBusy}
            />
          </label>
        </div>
      </GlassCard>
    </section>
  );
}
