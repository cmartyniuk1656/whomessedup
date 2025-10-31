import { useMemo, useState } from "react";

const CLASS_COLORS = {
  "Death Knight": "#C41E3A",
  "Demon Hunter": "#A330C9",
  Druid: "#FF7C0A",
  Evoker: "#33937F",
  Hunter: "#AAD372",
  Mage: "#3FC7EB",
  Monk: "#00FF98",
  Paladin: "#F48CBA",
  Priest: "#FFFFFF",
  Rogue: "#FFF468",
  Shaman: "#0070DD",
  Warlock: "#8788EE",
  Warrior: "#C69B6D",
};

const DEFAULT_PLAYER_COLOR = "#e2e8f0";

const TILES = [
  {
    id: "besiege-hits",
    title: "Besiege Hits – Nexus-King Salhadaar",
    description:
      "Count how many times each player was struck by Besiege (1227472) during Nexus-King Salhadaar pulls across the raid.",
    dataType: "DamageTaken",
    abilityId: 1227472,
    defaultFight: "Nexus-King",
  },
];

function extractReportCode(input) {
  if (!input) return "";
  const trimmed = input.trim();
  try {
    const url = new URL(trimmed);
    if (url.pathname.includes("/reports/")) {
      const segments = url.pathname.split("/").filter(Boolean);
      const idx = segments.indexOf("reports");
      if (idx !== -1 && segments[idx + 1]) {
        return segments[idx + 1];
      }
    }
    return trimmed;
  } catch (_err) {
    return trimmed;
  }
}

function App() {
  const [reportInput, setReportInput] = useState("");
  const [fightOverride, setFightOverride] = useState("");
  const [loadingId, setLoadingId] = useState(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [activeTile, setActiveTile] = useState(null);

  const rows = useMemo(() => {
    if (!result?.per_player) return [];
    return Object.entries(result.per_player)
      .map(([player, hits]) => {
        const damage = result.per_player_damage?.[player] ?? 0;
        const hitsPerPull = result.per_player_hits_per_pull?.[player] ?? 0;
        const playerClass = result.player_classes?.[player] ?? null;
        const color = playerClass ? CLASS_COLORS[playerClass] ?? DEFAULT_PLAYER_COLOR : DEFAULT_PLAYER_COLOR;
        return {
          player,
          hits,
          damage,
          hitsPerPull,
          className: playerClass,
          color,
        };
      })
      .sort((a, b) => b.hits - a.hits);
  }, [result]);

  const totalHits = useMemo(() => {
    if (!result?.total_hits) return 0;
    return Object.values(result.total_hits).reduce((acc, value) => acc + value, 0);
  }, [result]);

  const pullCount = result?.pull_count ?? 0;
  const averageHitsPerPull = result?.average_hits_per_pull ?? 0;
  const totalDamage = result?.total_damage ?? 0;

  const formatInt = (value) =>
    typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : value;
  const formatDamage = (value) =>
    typeof value === "number"
      ? value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
      : value;
  const formatFloat = (value, digits = 2) =>
    typeof value === "number"
      ? value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
      : value;

  const handleTileClick = async (tile) => {
    setError("");
    setResult(null);

    const code = extractReportCode(reportInput);
    if (!code) {
      setError("Enter a Warcraft Logs report URL or code first.");
      return;
    }

    setLoadingId(tile.id);
    setActiveTile(tile.id);
    try {
      const params = new URLSearchParams({
        report: code,
        data_type: tile.dataType,
        ability_id: String(tile.abilityId),
      });
      const fightName = (fightOverride || tile.defaultFight || "").trim();
      if (fightName) {
        params.set("fight", fightName);
      }

      const response = await fetch(`/api/hits?${params.toString()}`);
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail?.detail || "Request failed");
      }

      const data = await response.json();
      setResult({
        ...data,
        abilityLabel: tile.title,
      });
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/40">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <p className="text-sm uppercase tracking-widest text-slate-400">Who Messed Up</p>
          <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">Raid Failure Dashboard</h1>
          <p className="mt-4 max-w-3xl text-base text-slate-300">
            Pick a tool, paste a Warcraft Logs report URL or code, and review the culprits in seconds. Tiles run a
            curated query against the report and return a player-by-player summary.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row">
            <label className="flex w-full flex-col text-sm font-medium text-slate-300 sm:max-w-md">
              Report URL or code
              <input
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                placeholder="https://www.warcraftlogs.com/reports/..."
                value={reportInput}
                onChange={(event) => setReportInput(event.target.value)}
              />
            </label>
            <label className="flex w-full flex-col text-sm font-medium text-slate-300 sm:max-w-xs">
              Fight filter (optional)
              <input
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                placeholder="Defaults per tile"
                value={fightOverride}
                onChange={(event) => setFightOverride(event.target.value)}
              />
            </label>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16">
        <section aria-label="Tool tiles">
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {TILES.map((tile) => {
              const isLoading = loadingId === tile.id;
              return (
                <button
                  key={tile.id}
                  type="button"
                  onClick={() => handleTileClick(tile)}
                  className="group flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-left shadow-lg shadow-emerald-500/5 transition hover:border-emerald-400 hover:shadow-emerald-500/20 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-slate-950"
                  disabled={isLoading}
                >
                  <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-emerald-400">
                    Raid Tool
                    <span className="h-1 w-1 rounded-full bg-emerald-400" />
                    Damage Taken
                  </div>
                  <h2 className="mt-3 text-xl font-semibold text-white">{tile.title}</h2>
                  <p className="mt-3 text-sm text-slate-300">{tile.description}</p>
                  <div className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-emerald-300">
                    {isLoading ? (
                      <span className="flex items-center gap-2">
                        <span className="h-2 w-2 animate-ping rounded-full bg-emerald-300" />
                        Loading...
                      </span>
                    ) : (
                      <>
                        Run analysis
                        <svg className="h-4 w-4 transition group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor">
                          <path
                            fillRule="evenodd"
                            d="M10.293 3.293a1 1 0 011.414 0l5 5a1 1 0 010 1.414l-5 5a1 1 0 11-1.414-1.414L13.586 11H4a1 1 0 110-2h9.586l-3.293-3.293a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        <section className="mt-12">
          {error && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div>
          )}

          {!error && loadingId && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-5 text-sm text-slate-300">
              Running {activeTile ? TILES.find((t) => t.id === activeTile)?.title : "analysis"}...
            </div>
          )}

          {!error && !loadingId && result && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-emerald-500/10">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-widest text-emerald-400">Results</p>
                  <h3 className="mt-1 text-2xl font-semibold text-white">{result.abilityLabel}</h3>
                  <p className="mt-1 text-sm text-slate-400">
                    Report {result.report} · Data type {result.data_type}
                    {result.filters?.fight_name ? ` · Fight filter: ${result.filters.fight_name}` : ""}
                  </p>
                </div>
                <div className="grid gap-1 text-right text-sm text-slate-300">
                  <p>Pulls counted: {formatInt(pullCount)}</p>
                  <p>Total hits: {formatInt(totalHits)}</p>
                  <p>Total damage: {formatDamage(totalDamage)}</p>
                  <p>Avg hits per pull: {formatFloat(averageHitsPerPull, 2)}</p>
                </div>
              </div>

              <div className="mt-6 overflow-hidden rounded-xl border border-slate-800">
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
                    <tr>
                      <th className="px-4 py-3 text-left">Player</th>
                      <th className="px-4 py-3 text-right">Hits</th>
                      <th className="px-4 py-3 text-right">Damage</th>
                      <th className="px-4 py-3 text-right">Hits / Pull</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                    {rows.map((row) => (
                      <tr key={row.player}>
                        <td className="px-4 py-3 font-medium">
                          <span style={{ color: row.color }}>
                            {row.player}
                            {row.className ? (
                              <span className="ml-2 text-xs text-slate-400">({row.className})</span>
                            ) : null}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-emerald-300">{formatInt(row.hits)}</td>
                        <td className="px-4 py-3 text-right text-slate-200">{formatDamage(row.damage)}</td>
                        <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.hitsPerPull, 2)}</td>
                      </tr>
                    ))}
                    {rows.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                          No events matched the filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {result.fight_totals?.length ? (
                <div className="mt-6 overflow-hidden rounded-xl border border-slate-800">
                  <div className="bg-slate-900/80 px-4 py-3 text-xs uppercase tracking-widest text-slate-400">
                    Per-pull totals
                  </div>
                  <ul className="divide-y divide-slate-800 bg-slate-900/40 text-sm text-slate-200">
                    {result.fight_totals.map((fight) => (
                      <li key={fight.id} className="flex items-center justify-between px-4 py-3">
                        <span className="font-medium">{fight.name} #{formatInt(fight.id)}</span>
                        <span className="space-x-4 text-xs text-slate-400">
                          <span>Hits: {formatInt(fight.hits)}</span>
                          <span>Damage: {formatDamage(fight.damage)}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
