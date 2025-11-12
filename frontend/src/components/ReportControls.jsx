import { BOSS_OPTIONS } from "../config/constants";

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
  return (
    <header className="border-b border-slate-800 bg-slate-950/40">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <p className="text-sm uppercase tracking-widest text-slate-400">Who Messed Up</p>
        <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">Raid Analysis Dashboard</h1>
        <p className="mt-4 max-w-3xl text-base text-slate-300">
          Pick a tool, paste a Warcraft Logs report URL or code, and review the culprits in seconds. Tiles run a curated
          query against the report and return a player-by-player summary.
        </p>
        <div className="mt-8 flex flex-col gap-4 sm:flex-row">
          <label className="flex w-full flex-col text-sm font-medium text-slate-300 sm:max-w-md">
            Report URL or code
            <input
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
              placeholder="https://www.warcraftlogs.com/reports/..."
              value={reportInput}
              onChange={(event) => onReportInputChange(event.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="flex w-full flex-col text-sm font-medium text-slate-300 sm:max-w-xs">
            Fight filter (optional)
            <select
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
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
            <span className="mt-1 text-xs text-slate-400">Use this to restrict the report to a specific boss.</span>
          </label>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex w-full flex-col text-sm font-medium text-slate-300">
            Ignore hits after total deaths (per pull)
            <input
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
              placeholder="e.g. 3"
              value={ignoreAfterDeaths}
              onChange={(event) => onIgnoreAfterDeathsChange(event.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="flex w-full flex-col text-sm font-medium text-slate-300">
            Ignore final seconds of each pull
            <input
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
              placeholder="e.g. 10"
              value={ignoreFinalSeconds}
              onChange={(event) => onIgnoreFinalSecondsChange(event.target.value)}
              disabled={isBusy}
            />
          </label>
        </div>
      </div>
    </header>
  );
}
