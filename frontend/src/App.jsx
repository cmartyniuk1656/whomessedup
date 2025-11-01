import { useMemo, useState } from "react";

const CLASS_COLORS = {
  deathknight: "#C41E3A",
  demonhunter: "#A330C9",
  druid: "#FF7C0A",
  evoker: "#33937F",
  hunter: "#AAD372",
  mage: "#3FC7EB",
  monk: "#00FF98",
  paladin: "#F48CBA",
  priest: "#FFFFFF",
  rogue: "#FFF468",
  shaman: "#0070DD",
  warlock: "#8788EE",
  warrior: "#C69B6D",
};

const DEFAULT_PLAYER_COLOR = "#e2e8f0";

const ROLE_PRIORITY = {
  Tank: 0,
  Healer: 1,
  Melee: 2,
  Ranged: 3,
  Unknown: 4,
};

const DEFAULT_SORT_DIRECTIONS = {
  role: "asc",
  player: "asc",
  hits: "desc",
  damage: "desc",
  hitsPerPull: "desc",
  pulls: "desc",
  ghostMisses: "desc",
  ghostPerPull: "desc",
};

const ROLE_BADGE_STYLES = {
  Tank: "border border-amber-500/40 bg-amber-500/10 text-amber-200",
  Healer: "border border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
  Melee: "border border-rose-500/40 bg-rose-500/10 text-rose-200",
  Ranged: "border border-sky-500/40 bg-sky-500/10 text-sky-200",
  Unknown: "border border-slate-600/40 bg-slate-700/30 text-slate-200",
};

const TILES = [
  {
    id: "besiege-hits",
    title: "Besiege Hits – Nexus-King Salhadaar",
    description:
      "Count how many times each player was struck by Besiege (1227472) during Nexus-King Salhadaar pulls across the raid.",
    dataType: "DamageTaken",
    abilityId: 1227472,
    defaultFight: "Nexus-King",
    endpoint: "/api/hits",
    mode: "hits",
    defaultSort: { key: "role", direction: "asc" },
  },
  {
    id: "ghost-misses",
    title: "Ghost Misses – Nexus-King Salhadaar",
    description:
      "Track applications of Oathbound (1224737) after the first 15 seconds of each pull to identify missed Ghost triggers.",
    abilityId: 1224737,
    defaultFight: "Nexus-King",
    endpoint: "/api/ghosts",
    mode: "ghost",
    defaultSort: { key: "role", direction: "asc" },
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
  const [sortConfig, setSortConfig] = useState({ key: "role", direction: "asc" });

  const currentTile = useMemo(
    () => TILES.find((tile) => tile.id === activeTile) ?? null,
    [activeTile]
  );
  const isGhostMode = currentTile?.mode === "ghost";

  const rows = useMemo(() => {
    if (!result || !currentTile) return [];

    if (currentTile.mode === "ghost") {
      const playerClasses = result.player_classes ?? {};
      const playerRoles = result.player_roles ?? {};
      return (result.entries ?? []).map((entry) => {
        const playerClass = playerClasses[entry.player] ?? null;
        const normalizedClass = playerClass ? playerClass.replace(/\s+/g, "").toLowerCase() : null;
        const color = normalizedClass ? CLASS_COLORS[normalizedClass] ?? DEFAULT_PLAYER_COLOR : DEFAULT_PLAYER_COLOR;
        const role = playerRoles[entry.player] ?? entry.role ?? "Unknown";
        return {
          player: entry.player,
          pulls: entry.pulls,
          ghostMisses: entry.ghost_misses ?? entry.misses ?? 0,
          ghostPerPull: entry.ghost_per_pull ?? entry.misses_per_pull ?? 0,
          color,
          role,
        };
      });
    }

    const playerClasses = result.player_classes ?? {};
    const playerRoles = result.player_roles ?? {};
    return Object.entries(result.per_player ?? {}).map(([player, hits]) => {
      const damage = result.per_player_damage?.[player] ?? 0;
      const hitsPerPull = result.per_player_hits_per_pull?.[player] ?? 0;
      const playerClass = playerClasses[player] ?? null;
      const normalizedClass = playerClass ? playerClass.replace(/\s+/g, "").toLowerCase() : null;
      const color = normalizedClass ? CLASS_COLORS[normalizedClass] ?? DEFAULT_PLAYER_COLOR : DEFAULT_PLAYER_COLOR;
      const role = playerRoles[player] ?? "Unknown";
      return {
        player,
        hits,
        damage,
        hitsPerPull,
        color,
        role,
      };
    });
  }, [result, currentTile]);

  const sortedRows = useMemo(() => {
    const arr = [...rows];
    const { key, direction } = sortConfig;
    const dir = direction === "asc" ? 1 : -1;
    arr.sort((a, b) => {
      if (key === "role") {
        const aPriority = ROLE_PRIORITY[a.role] ?? ROLE_PRIORITY.Unknown;
        const bPriority = ROLE_PRIORITY[b.role] ?? ROLE_PRIORITY.Unknown;
        if (aPriority !== bPriority) {
          return (aPriority - bPriority) * dir;
        }
        if (isGhostMode) {
          if ((b.ghostMisses ?? 0) !== (a.ghostMisses ?? 0)) {
            return ((a.ghostMisses ?? 0) - (b.ghostMisses ?? 0)) * dir;
          }
          if ((b.pulls ?? 0) !== (a.pulls ?? 0)) {
            return ((a.pulls ?? 0) - (b.pulls ?? 0)) * dir;
          }
        } else if ((b.hits ?? 0) !== (a.hits ?? 0)) {
          return ((a.hits ?? 0) - (b.hits ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player) * dir;
      }
      if (key === "player") {
        return a.player.localeCompare(b.player) * dir;
      }
      if (key === "hits") {
        if ((a.hits ?? 0) !== (b.hits ?? 0)) {
          return ((a.hits ?? 0) - (b.hits ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "damage") {
        if ((a.damage ?? 0) !== (b.damage ?? 0)) {
          return ((a.damage ?? 0) - (b.damage ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "hitsPerPull") {
        if ((a.hitsPerPull ?? 0) !== (b.hitsPerPull ?? 0)) {
          return ((a.hitsPerPull ?? 0) - (b.hitsPerPull ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "pulls") {
        if ((a.pulls ?? 0) !== (b.pulls ?? 0)) {
          return ((a.pulls ?? 0) - (b.pulls ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "ghostMisses") {
        if ((a.ghostMisses ?? 0) !== (b.ghostMisses ?? 0)) {
          return ((a.ghostMisses ?? 0) - (b.ghostMisses ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "ghostPerPull") {
        if ((a.ghostPerPull ?? 0) !== (b.ghostPerPull ?? 0)) {
          return ((a.ghostPerPull ?? 0) - (b.ghostPerPull ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      return 0;
    });
    return arr;
  }, [rows, sortConfig, isGhostMode]);

  const pullCount = useMemo(() => {
    if (!result) return 0;
    if (isGhostMode) {
      return result.pull_count ?? (result.fights ? result.fights.length : 0);
    }
    return result.fights ? result.fights.length : 0;
  }, [result, isGhostMode]);

  const totalHits = useMemo(() => {
    if (isGhostMode || !result?.total_hits) return 0;
    return Object.values(result.total_hits).reduce((acc, value) => acc + value, 0);
  }, [result, isGhostMode]);

  const averageHitsPerPull = useMemo(() => {
    if (isGhostMode) return 0;
    return result?.average_hits_per_pull ?? 0;
  }, [result, isGhostMode]);

  const totalDamage = isGhostMode ? 0 : result?.total_damage ?? 0;

  const totalGhostMisses = useMemo(() => {
    if (!isGhostMode) return 0;
    return rows.reduce((sum, row) => sum + (row.ghostMisses ?? 0), 0);
  }, [rows, isGhostMode]);

  const averageGhostPerPull = pullCount ? totalGhostMisses / pullCount : 0;

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

  const summaryMetrics = isGhostMode
    ? [
        { label: "Pulls counted", value: formatInt(pullCount) },
        { label: "Total ghost misses", value: formatInt(totalGhostMisses) },
        { label: "Avg ghost per pull", value: formatFloat(averageGhostPerPull, 3) },
      ]
    : [
        { label: "Pulls counted", value: formatInt(pullCount) },
        { label: "Total hits", value: formatInt(totalHits) },
        { label: "Total damage", value: formatDamage(totalDamage) },
        { label: "Avg hits per pull", value: formatFloat(averageHitsPerPull, 2) },
      ];

  const handleSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: DEFAULT_SORT_DIRECTIONS[key] || "asc" };
    });
  };

  const renderSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <span className="ml-2 text-slate-500">↕</span>;
    }
    return (
      <span className="ml-2 text-emerald-300">
        {sortConfig.direction === "asc" ? "▲" : "▼"}
      </span>
    );
  };

  const handleTileClick = async (tile) => {
    setError("");
    setResult(null);
    setSortConfig(tile.defaultSort ?? { key: "role", direction: "asc" });

    const code = extractReportCode(reportInput);
    if (!code) {
      setError("Enter a Warcraft Logs report URL or code first.");
      return;
    }

    setLoadingId(tile.id);
    setActiveTile(tile.id);
    try {
      const endpoint = tile.endpoint ?? "/api/hits";
      const params = new URLSearchParams();
      params.set("report", code);

      const fightName = (fightOverride || tile.defaultFight || "").trim();
      if (fightName) {
        params.set("fight", fightName);
      }

      if (tile.dataType && endpoint === "/api/hits") {
        params.set("data_type", tile.dataType);
      }
      if (tile.abilityId) {
        params.set("ability_id", String(tile.abilityId));
      }

      const response = await fetch(`${endpoint}?${params.toString()}`);
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
                  {summaryMetrics.map(({ label, value }) => (
                    <p key={label}>
                      {label}: {value}
                    </p>
                  ))}
                </div>
              </div>

              <div className="mt-6 overflow-hidden rounded-xl border border-slate-800">
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
                    {isGhostMode ? (
                      <tr>
                        <th className="px-4 py-3 text-left">
                          <button
                            type="button"
                            className="flex items-center gap-1 text-left text-slate-300 hover:text-white"
                            onClick={() => handleSort("player")}
                          >
                            Player
                            {renderSortIcon("player")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-left">
                          <button
                            type="button"
                            className="flex items-center gap-1 text-left text-slate-300 hover:text-white"
                            onClick={() => handleSort("role")}
                          >
                            Role
                            {renderSortIcon("role")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                            onClick={() => handleSort("pulls")}
                          >
                            Pulls In
                            {renderSortIcon("pulls")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                            onClick={() => handleSort("ghostMisses")}
                          >
                            Ghost Misses
                            {renderSortIcon("ghostMisses")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                            onClick={() => handleSort("ghostPerPull")}
                          >
                            Ghost / Pull
                            {renderSortIcon("ghostPerPull")}
                          </button>
                        </th>
                      </tr>
                    ) : (
                      <tr>
                        <th className="px-4 py-3 text-left">
                          <button
                            type="button"
                            className="flex items-center gap-1 text-left text-slate-300 hover:text-white"
                            onClick={() => handleSort("player")}
                          >
                            Player
                            {renderSortIcon("player")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-left">
                          <button
                            type="button"
                            className="flex items-center gap-1 text-left text-slate-300 hover:text-white"
                            onClick={() => handleSort("role")}
                          >
                            Role
                            {renderSortIcon("role")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                            onClick={() => handleSort("hits")}
                          >
                            Hits
                            {renderSortIcon("hits")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                            onClick={() => handleSort("damage")}
                          >
                            Damage
                            {renderSortIcon("damage")}
                          </button>
                        </th>
                        <th className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                            onClick={() => handleSort("hitsPerPull")}
                          >
                            Hits / Pull
                            {renderSortIcon("hitsPerPull")}
                          </button>
                        </th>
                      </tr>
                    )}
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                    {sortedRows.map((row) =>
                      isGhostMode ? (
                        <tr key={row.player}>
                          <td className="px-4 py-3 font-medium">
                            <span style={{ color: row.color }}>{row.player}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                                ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                              }`}
                            >
                              {row.role}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls ?? 0)}</td>
                          <td className="px-4 py-3 text-right font-semibold text-emerald-300">
                            {formatInt(row.ghostMisses ?? 0)}
                          </td>
                          <td className="px-4 py-3 text-right text-slate-200">
                            {formatFloat(row.ghostPerPull ?? 0, 3)}
                          </td>
                        </tr>
                      ) : (
                        <tr key={row.player}>
                          <td className="px-4 py-3 font-medium">
                            <span style={{ color: row.color }}>{row.player}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                                ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                              }`}
                            >
                              {row.role}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-semibold text-emerald-300">{formatInt(row.hits ?? 0)}</td>
                          <td className="px-4 py-3 text-right text-slate-200">{formatDamage(row.damage ?? 0)}</td>
                          <td className="px-4 py-3 text-right text-slate-200">{formatFloat(row.hitsPerPull ?? 0, 2)}</td>
                        </tr>
                      )
                    )}
                    {sortedRows.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                          No events matched the filters.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {!isGhostMode && result.fight_totals?.length ? (
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

