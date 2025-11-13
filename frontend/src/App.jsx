import { useEffect, useMemo, useState } from "react";
import {
  CLASS_COLORS,
  DEFAULT_PLAYER_COLOR,
  DEFAULT_SORT_DIRECTIONS,
  ROLE_BADGE_STYLES,
  ROLE_PRIORITY,
  TILES,
} from "./config/constants";
import { useTileRunner } from "./hooks/useTileRunner";
import { useCsvExporter } from "./hooks/useCsvExporter";
import { ReportControls } from "./components/ReportControls";
import { TileCatalog } from "./components/TileCatalog";
import { ConfigDrawer } from "./components/ConfigDrawer";
import { ResultHeader } from "./components/ResultHeader";
import { ResultsTable } from "./components/ResultsTable";
import { formatFloat, formatInt } from "./utils/numberFormat";

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

const getAdditionalReportsTag = (raw) => {
  if (typeof raw !== "string") {
    return null;
  }
  const list = raw
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
  if (!list.length) {
    return null;
  }
  return list.length === 1 ? "Merged 1 additional report" : `Merged ${list.length} additional reports`;
};

function App() {
  const [reportInput, setReportInput] = useState("");
  const [fightOverride, setFightOverride] = useState(TILES[0]?.defaultFight ?? "");
  const [ignoreAfterDeaths, setIgnoreAfterDeaths] = useState("");
  const [ignoreFinalSeconds, setIgnoreFinalSeconds] = useState("");
  const [activeTile, setActiveTile] = useState(TILES[0]?.id ?? null);
  const [sortConfig, setSortConfig] = useState(TILES[0]?.defaultSort ?? { key: "role", direction: "asc" });
  const [pendingTile, setPendingTile] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [configValues, setConfigValues] = useState({});
  const [savedConfigs, setSavedConfigs] = useState({});
  const [mobileViewMode, setMobileViewMode] = useState("table");

  const { result, error, setError, loadingId, pendingJob, runTile: runTileRequest } = useTileRunner();
  const { downloadCsv } = useCsvExporter(setError);

  const currentTile = useMemo(() => TILES.find((tile) => tile.id === activeTile) ?? TILES[0], [activeTile]);
  const isBusy = Boolean(loadingId) || Boolean(pendingJob);

  useEffect(() => {
    if (!result?.ghost_events?.length) {
      return;
    }
    const label = `[Ghost Debug] ${result.report ?? "report"} - ${result.ghost_events.length} events`;
    console.groupCollapsed(label);
    result.ghost_events.forEach((event) => {
      const offsetSeconds = Number.isFinite(event.offset_ms) ? event.offset_ms / 1000 : null;
      console.log(
        `Pull ${event.pull}: ${event.player} at ${offsetSeconds !== null ? offsetSeconds.toFixed(2) : "?"}s (ts ${event.timestamp})`
      );
    });
    console.groupEnd();
  }, [result]);

  const phaseLabels = result?.phase_labels ?? {};
  const phaseOrder = result?.phases ?? [];
  const abilityIds = result?.ability_ids ?? {};
  const filters = result?.filters ?? {};
  const metricColumns = result?.metrics ?? [];
  const metricTotals = result?.metric_totals ?? {};
  const playerEvents = result?.player_events ?? {};

  const rows = useMemo(() => {
    if (!result) {
      return [];
    }
    if (currentTile?.mode === "phase-damage") {
      return (result.entries ?? []).map((entry) => {
        const className = result.player_classes?.[entry.player] ?? null;
        const color = CLASS_COLORS[(className || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
        const phaseTotals = {};
        const phaseAverages = {};
        (entry.metrics ?? []).forEach((metric) => {
          phaseTotals[metric.phase_id] = metric.total_amount ?? 0;
          phaseAverages[metric.phase_id] = metric.average_per_pull ?? 0;
        });
        return {
          player: entry.player,
          role: entry.role ?? "Unknown",
          className,
          pulls: entry.pulls ?? result.pull_count ?? 0,
          phaseTotals,
          phaseAverages,
          combinedAverage: (entry.metrics ?? []).reduce((sum, metric) => sum + (metric.average_per_pull ?? 0), 0),
          color,
        };
      });
    }
    if (currentTile?.mode === "add-damage") {
      return (result.entries ?? []).map((entry) => {
        const className = result.player_classes?.[entry.player] ?? null;
        const color = CLASS_COLORS[(className || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
        return {
          player: entry.player,
          role: entry.role ?? "Unknown",
          className,
          pulls: entry.pulls ?? result.pull_count ?? 0,
          addTotalDamage: entry.total_damage ?? 0,
          addAverageDamage: entry.average_damage ?? 0,
          color,
        };
      });
    }
    if (currentTile?.mode === "dimensius-phase1") {
      return (result.entries ?? []).map((entry) => {
        const className = result.player_classes?.[entry.player] ?? null;
        const color = CLASS_COLORS[(className || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
        const metricTotalsMap = {};
        Object.entries(entry.metrics ?? {}).forEach(([metricId, values]) => {
          if (!values) {
            return;
          }
          metricTotalsMap[metricId] = values.total ?? 0;
        });
        return {
          player: entry.player,
          role: entry.role ?? "Unknown",
          className,
          pulls: entry.pulls ?? result.pull_count ?? 0,
          metricTotals: metricTotalsMap,
          fuckupRate: entry.fuckup_rate ?? 0,
          color,
        };
      });
    }
    if (currentTile?.mode === "dimensius-deaths") {
      return (result.entries ?? []).map((entry) => {
        const className = result.player_classes?.[entry.player] ?? null;
        const color = CLASS_COLORS[(className || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
        return {
          player: entry.player,
          role: entry.role ?? "Unknown",
          className,
          pulls: entry.pulls ?? result.pull_count ?? 0,
          deaths: entry.deaths ?? 0,
          deathRate: entry.death_rate ?? 0,
          color,
        };
      });
    }
    return (result.entries ?? []).map((entry) => {
      const className = result.player_classes?.[entry.player] ?? null;
      const color = CLASS_COLORS[(className || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
      return {
        player: entry.player,
        role: entry.role ?? "Unknown",
        className,
        pulls: entry.pulls ?? result.pull_count ?? 0,
        besiegeHits: entry.besiege_hits ?? entry.hits ?? 0,
        besiegePerPull: entry.besiege_per_pull ?? entry.hits_per_pull ?? 0,
        ghostMisses: entry.ghost_misses ?? 0,
        ghostPerPull: entry.ghost_per_pull ?? 0,
        fuckupRate: entry.fuckup_rate ?? 0,
        color,
      };
    });
  }, [result, currentTile]);

  const sortedRows = useMemo(() => {
    const arr = [...rows];
    const { key, direction } = sortConfig;
    const dir = direction === "asc" ? 1 : -1;

    if (currentTile?.mode === "phase-damage") {
      arr.sort((a, b) => {
        if (key === "role") {
          const aPriority = ROLE_PRIORITY[a.role] ?? ROLE_PRIORITY.Unknown;
          const bPriority = ROLE_PRIORITY[b.role] ?? ROLE_PRIORITY.Unknown;
          if (aPriority !== bPriority) {
            return (aPriority - bPriority) * dir;
          }
          const pullDiff = (b.pulls ?? 0) - (a.pulls ?? 0);
          if (pullDiff !== 0) {
            return dir === 1 ? pullDiff : -pullDiff;
          }
          return a.player.localeCompare(b.player) * dir;
        }
        if (key === "player") {
          return a.player.localeCompare(b.player) * dir;
        }
        if (key === "pulls") {
          if (a.pulls !== b.pulls) {
            return (a.pulls - b.pulls) * dir;
          }
          return a.player.localeCompare(b.player);
        }
        if (key === "combinedAverage") {
          if (a.combinedAverage !== b.combinedAverage) {
            return (a.combinedAverage - b.combinedAverage) * dir;
          }
          return a.player.localeCompare(b.player) * dir;
        }
        if (key.startsWith("total_phase_")) {
          const phaseId = key.replace("total_phase_", "");
          const aVal = a.phaseTotals?.[phaseId] ?? 0;
          const bVal = b.phaseTotals?.[phaseId] ?? 0;
          if (aVal !== bVal) {
            return (aVal - bVal) * dir;
          }
          return a.player.localeCompare(b.player);
        }
        if (key.startsWith("avg_phase_")) {
          const phaseId = key.replace("avg_phase_", "");
          const aVal = a.phaseAverages?.[phaseId] ?? 0;
          const bVal = b.phaseAverages?.[phaseId] ?? 0;
          if (aVal !== bVal) {
            return (aVal - bVal) * dir;
          }
          return a.player.localeCompare(b.player);
        }
        return 0;
      });
      return arr;
    }

    if (currentTile?.mode === "add-damage") {
      arr.sort((a, b) => {
        if (key === "role") {
          const aPriority = ROLE_PRIORITY[a.role] ?? ROLE_PRIORITY.Unknown;
          const bPriority = ROLE_PRIORITY[b.role] ?? ROLE_PRIORITY.Unknown;
          if (aPriority !== bPriority) {
            return (aPriority - bPriority) * dir;
          }
          const totalDiff = (b.addTotalDamage ?? 0) - (a.addTotalDamage ?? 0);
          if (totalDiff !== 0) {
            return dir === 1 ? totalDiff : -totalDiff;
          }
          return a.player.localeCompare(b.player) * dir;
        }
        if (key === "player") {
          return a.player.localeCompare(b.player) * dir;
        }
        if (key === "pulls") {
          if (a.pulls !== b.pulls) {
            return (a.pulls - b.pulls) * dir;
          }
          return a.player.localeCompare(b.player);
        }
        if (key === "addTotalDamage") {
          if (a.addTotalDamage !== b.addTotalDamage) {
            return (a.addTotalDamage - b.addTotalDamage) * dir;
          }
          return a.player.localeCompare(b.player);
        }
        if (key === "addAverageDamage") {
          if (a.addAverageDamage !== b.addAverageDamage) {
            return (a.addAverageDamage - b.addAverageDamage) * dir;
          }
          return a.player.localeCompare(b.player);
        }
        return 0;
      });
      return arr;
    }

    arr.sort((a, b) => {
      if (key === "role") {
        const aPriority = ROLE_PRIORITY[a.role] ?? ROLE_PRIORITY.Unknown;
        const bPriority = ROLE_PRIORITY[b.role] ?? ROLE_PRIORITY.Unknown;
        if (aPriority !== bPriority) {
          return (aPriority - bPriority) * dir;
        }
        const rateDiff = (b.fuckupRate ?? 0) - (a.fuckupRate ?? 0);
        if (rateDiff !== 0) {
          return dir === 1 ? rateDiff : -rateDiff;
        }
        const pullDiff = (b.pulls ?? 0) - (a.pulls ?? 0);
        if (pullDiff !== 0) {
          return dir === 1 ? pullDiff : -pullDiff;
        }
        return a.player.localeCompare(b.player) * dir;
      }
      if (key === "player") {
        return a.player.localeCompare(b.player) * dir;
      }
      if (key === "pulls") {
        if (a.pulls !== b.pulls) {
          return (a.pulls - b.pulls) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key.startsWith("metric_total_")) {
        const metricId = key.replace("metric_total_", "");
        const aVal = a.metricTotals?.[metricId] ?? 0;
        const bVal = b.metricTotals?.[metricId] ?? 0;
        if (aVal !== bVal) {
          return (aVal - bVal) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "ghostMisses") {
        if (a.ghostMisses !== b.ghostMisses) {
          return (a.ghostMisses - b.ghostMisses) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "ghostPerPull") {
        if (a.ghostPerPull !== b.ghostPerPull) {
          return (a.ghostPerPull - b.ghostPerPull) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "besiegeHits") {
        if (a.besiegeHits !== b.besiegeHits) {
          return (a.besiegeHits - b.besiegeHits) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "besiegePerPull") {
        if (a.besiegePerPull !== b.besiegePerPull) {
          return (a.besiegePerPull - b.besiegePerPull) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "fuckupRate") {
        if (a.fuckupRate !== b.fuckupRate) {
          return (a.fuckupRate - b.fuckupRate) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "deaths") {
        if ((a.deaths ?? 0) !== (b.deaths ?? 0)) {
          return ((a.deaths ?? 0) - (b.deaths ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      if (key === "deathRate") {
        if ((a.deathRate ?? 0) !== (b.deathRate ?? 0)) {
          return ((a.deathRate ?? 0) - (b.deathRate ?? 0)) * dir;
        }
        return a.player.localeCompare(b.player);
      }
      return 0;
    });

    return arr;
  }, [rows, sortConfig, currentTile]);

  const pullCount = result?.pull_count ?? 0;
  const totals = result?.totals ?? {};
  const totalBesieges = totals.total_besieges ?? 0;
  const totalGhosts = totals.total_ghosts ?? 0;
  const avgBesiegePerPull = totals.avg_besieges_per_pull ?? 0;
  const avgGhostPerPull = totals.avg_ghosts_per_pull ?? 0;
  const combinedPerPull = totals.combined_per_pull ?? 0;
  const hitFilters = result?.hit_filters ?? {};

  let summaryMetrics = [];
  if (currentTile?.mode === "phase-damage") {
    summaryMetrics = [];
  } else if (currentTile?.mode === "add-damage") {
    summaryMetrics = [
      { label: "Pulls counted", value: formatInt(pullCount) },
      { label: "Combined add damage", value: formatInt(totals.total_damage ?? 0) },
      { label: "Avg add damage / Pull", value: formatFloat(totals.avg_damage_per_pull ?? 0, 3) },
    ];
  } else if (currentTile?.mode === "dimensius-phase1") {
    summaryMetrics = [{ label: "Pulls counted", value: formatInt(pullCount) }];
    metricColumns.forEach((metric) => {
      const metricSummary = metricTotals?.[metric.id];
      if (!metricSummary) {
        return;
      }
      summaryMetrics.push({ label: metric.label, value: formatInt(metricSummary.total ?? 0) });
      summaryMetrics.push({
        label: metric.per_pull_label || `${metric.label} / Pull`,
        value: formatFloat(metricSummary.per_pull ?? 0, 3),
      });
    });
    summaryMetrics.push({
      label: "Fuck-up rate / Pull",
      value: formatFloat(result?.totals?.combined_per_pull ?? result?.combined_per_pull ?? 0, 3),
    });
  } else if (currentTile?.mode === "dimensius-deaths") {
    summaryMetrics = [
      { label: "Pulls counted", value: formatInt(pullCount) },
      { label: "Total deaths", value: formatInt(result?.totals?.total_deaths ?? 0) },
      { label: "Avg deaths / Pull", value: formatFloat(result?.totals?.avg_deaths_per_pull ?? 0, 3) },
    ];
  } else if (currentTile?.mode === "dimensius-deaths") {
    if (filters.ignore_after_deaths) {
      const deaths = Number(filters.ignore_after_deaths);
      if (!Number.isNaN(deaths) && deaths > 0) {
        filterTags.push(`Stop after ${formatInt(deaths)} deaths`);
      }
    }
  } else {
    summaryMetrics = [
      { label: "Pulls counted", value: formatInt(pullCount) },
      { label: "Total Besieges", value: formatInt(totalBesieges) },
      { label: "Total Ghost Misses", value: formatInt(totalGhosts) },
      { label: "Avg Besieges / Pull", value: formatFloat(avgBesiegePerPull, 3) },
      { label: "Avg Ghosts / Pull", value: formatFloat(avgGhostPerPull, 3) },
      { label: "Fuck-up rate / Pull", value: formatFloat(combinedPerPull, 3) },
    ];
  }

  const filterTags = [];
  if (currentTile?.mode === "phase-damage") {
    if (hitFilters.ignore_after_deaths) {
      filterTags.push(`Stop after ${formatInt(hitFilters.ignore_after_deaths)} deaths`);
    }
    if (hitFilters.ignore_final_seconds) {
      filterTags.push(`Ignore final ${formatFloat(hitFilters.ignore_final_seconds, 1)}s`);
    }
    if (typeof hitFilters.first_hit_only === "boolean") {
      filterTags.push(hitFilters.first_hit_only ? "First Besiege per pull" : "All Besiege hits");
    }
    const ghostMode = hitFilters.ghost_miss_mode;
    if (ghostMode === "first_per_set") {
      filterTags.push("First Ghost per set");
    } else if (ghostMode === "first_per_pull") {
      filterTags.push("First Ghost per pull");
    } else if (ghostMode === "all") {
      filterTags.push("All Ghost misses");
    }
    if (phaseOrder.length) {
      filterTags.unshift(`Phases: ${phaseOrder.map((id) => phaseLabels[id] ?? id).join(", ")}`);
    }
    const additionalTag = getAdditionalReportsTag(filters.additional_reports);
    if (additionalTag) {
      filterTags.push(additionalTag);
    }
  } else if (currentTile?.mode === "add-damage") {
    if (filters.ignore_first_add_set === "true") {
      filterTags.push("Ignoring first Living Mass set");
    }
    const additionalTag = getAdditionalReportsTag(filters.additional_reports);
    if (additionalTag) {
      filterTags.push(additionalTag);
    }
  } else if (currentTile?.mode === "dimensius-phase1") {
    if (filters.reverse_gravity_excess_mass === "true") {
      filterTags.push("Reverse Gravity + Excess Mass overlap");
    }
    if (filters.early_mass_before_rg === "true") {
      filterTags.push("Excess Mass < 1s before Reverse Gravity");
    }
    if (filters.dark_energy_hits === "true") {
      filterTags.push("Dark Energy hits");
    }
    if (filters.ignore_after_deaths) {
      const deaths = Number(filters.ignore_after_deaths);
      if (!Number.isNaN(deaths) && deaths > 0) {
        filterTags.push(`Stop after ${formatInt(deaths)} deaths`);
      }
    }
  } else {
    if (hitFilters.ignore_after_deaths) {
      filterTags.push(`Stop after ${formatInt(hitFilters.ignore_after_deaths)} deaths`);
    }
    if (hitFilters.ignore_final_seconds) {
      filterTags.push(`Ignore final ${formatFloat(hitFilters.ignore_final_seconds, 1)}s`);
    }
  }

  const handleSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      const defaultDirection =
        DEFAULT_SORT_DIRECTIONS[key] ||
        (key.startsWith("total_phase_") || key.startsWith("avg_phase_") || key.startsWith("metric_total_") ? "desc" : "asc");
      return { key, direction: defaultDirection };
    });
  };

  const renderSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <span className="ml-2 text-slate-500">↕</span>;
    }
    return <span className="ml-2 text-emerald-300">{sortConfig.direction === "asc" ? "▲" : "▼"}</span>;
  };

  const runTile = (tile, overrides = {}) => {
    if (!tile) return;
    const code = extractReportCode(reportInput);
    if (!code) {
      setError("Enter a Warcraft Logs report URL or code first.");
      return;
    }

    let effectiveFight = fightOverride;
    if (tile.defaultFight) {
      effectiveFight = tile.defaultFight;
      if (fightOverride !== tile.defaultFight) {
        setFightOverride(tile.defaultFight);
      }
    }

    setActiveTile(tile.id);
    setSortConfig(tile.defaultSort ?? { key: "role", direction: "asc" });

    runTileRequest({
      tile,
      reportCode: code,
      fightName: effectiveFight,
      ignoreAfterDeaths,
      ignoreFinalSeconds,
      configOverrides: overrides,
    });
  };

  const handleTileClick = (tile) => {
    if (isBusy) return;
    if (tile.configOptions?.length) {
      const saved = savedConfigs[tile.id] ?? {};
      const initial = {};
      tile.configOptions.forEach((opt) => {
        const optionType = opt.type ?? "checkbox";
        const savedValue = saved[opt.id];
        if (optionType === "select") {
          if (typeof savedValue === "string") {
            initial[opt.id] = savedValue;
          } else if (typeof opt.default === "string") {
            initial[opt.id] = opt.default;
          } else if (Array.isArray(opt.options) && opt.options.length > 0) {
            initial[opt.id] = String(opt.options[0].value);
          } else {
            initial[opt.id] = "";
          }
        } else if (optionType === "multi-text") {
          if (Array.isArray(savedValue)) {
            initial[opt.id] = savedValue.map((entry) => (entry == null ? "" : String(entry)));
          } else if (Array.isArray(opt.default)) {
            initial[opt.id] = opt.default.map((entry) => (entry == null ? "" : String(entry)));
          } else {
            initial[opt.id] = [typeof savedValue === "string" && savedValue.trim() ? savedValue : ""];
          }
        } else {
          if (typeof savedValue === "boolean") {
            initial[opt.id] = savedValue;
          } else if (typeof opt.default === "boolean") {
            initial[opt.id] = opt.default;
          } else {
            initial[opt.id] = false;
          }
        }
      });
      setConfigValues(initial);
      setPendingTile(tile);
      setShowConfig(true);
    } else {
      runTile(tile);
    }
  };

  const handleConfigOptionChange = (id, value) => {
    setConfigValues((prev) => ({ ...prev, [id]: value }));
  };

  const handleMultiTextChange = (id, index, value) => {
    setConfigValues((prev) => {
      const current = Array.isArray(prev[id]) ? [...prev[id]] : [];
      while (current.length <= index) {
        current.push("");
      }
      current[index] = value;
      return { ...prev, [id]: current };
    });
  };

  const handleMultiTextAdd = (id) => {
    setConfigValues((prev) => {
      const current = Array.isArray(prev[id]) ? [...prev[id]] : [""];
      current.push("");
      return { ...prev, [id]: current };
    });
  };

  const handleMultiTextRemove = (id, index) => {
    setConfigValues((prev) => {
      let current = Array.isArray(prev[id]) ? [...prev[id]] : [""];
      if (current.length <= 1) {
        current = [""];
      } else {
        current.splice(index, 1);
        if (!current.length) {
          current = [""];
        }
      }
      return { ...prev, [id]: current };
    });
  };

  const handleConfigCancel = () => {
    setShowConfig(false);
    setPendingTile(null);
  };

  const handleConfigConfirm = () => {
    if (!pendingTile) return;
    const overrides = Object.entries(configValues).reduce((acc, [key, value]) => {
      acc[key] = Array.isArray(value) ? value.map((entry) => (entry == null ? "" : String(entry))) : value;
      return acc;
    }, {});
    setSavedConfigs((prev) => ({ ...prev, [pendingTile.id]: overrides }));
    setShowConfig(false);
    const tileToRun = pendingTile;
    setPendingTile(null);
    runTile(tileToRun, overrides);
  };

  const handleDownloadCsv = () => {
    if (!result || !currentTile) {
      return;
    }
    downloadCsv({
      tile: currentTile,
      result,
      rows: sortedRows,
      phases: phaseOrder,
      labels: phaseLabels,
      metrics: metricColumns,
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <ReportControls
        reportInput={reportInput}
        onReportInputChange={setReportInput}
        fightOverride={fightOverride}
        onFightOverrideChange={setFightOverride}
        ignoreAfterDeaths={ignoreAfterDeaths}
        onIgnoreAfterDeathsChange={setIgnoreAfterDeaths}
        ignoreFinalSeconds={ignoreFinalSeconds}
        onIgnoreFinalSecondsChange={setIgnoreFinalSeconds}
        isBusy={isBusy}
      />

      <main className="mx-auto max-w-6xl px-6 pb-16">
        <TileCatalog
          tiles={TILES}
          loadingId={loadingId}
          pendingJob={pendingJob}
          isBusy={isBusy}
          onTileClick={handleTileClick}
        />

        <section className="mt-12">
          {error && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div>
          )}

          {!error && loadingId && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-5 text-sm text-slate-300">
              {pendingJob ? (
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-emerald-300">
                    <span className="h-2 w-2 animate-ping rounded-full bg-emerald-300" />
                    {pendingJob.status === "running" ? "Report is running..." : `Waiting to start ${currentTile?.title || "analysis"}...`}
                  </div>
                  {typeof pendingJob.position === "number" ? (
                    <div className="text-xs text-slate-400">
                      {pendingJob.position === 0 ? "Currently executing." : `Position in queue: ${pendingJob.position}`}
                    </div>
                  ) : null}
                  <div className="text-xs text-slate-500">Job ID: {pendingJob.id}</div>
                </div>
              ) : (
                <>Running {currentTile?.title || "analysis"}...</>
              )}
            </div>
          )}

          {!error && !loadingId && result && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-lg shadow-emerald-500/10">
              <ResultHeader
                title={result.tileTitle || currentTile?.title}
                reportCode={result.report}
                filters={filters}
                filterTags={filterTags}
                abilityIds={abilityIds}
                onDownloadCsv={handleDownloadCsv}
                disableDownload={isBusy}
                summaryMetrics={summaryMetrics}
              />
              <ResultsTable
                mode={currentTile?.mode}
                rows={sortedRows}
                phaseOrder={phaseOrder}
                phaseLabels={phaseLabels}
                metricColumns={metricColumns}
                playerEvents={playerEvents}
                mobileViewMode={mobileViewMode}
                onMobileViewModeChange={setMobileViewMode}
                handleSort={handleSort}
                renderSortIcon={renderSortIcon}
              />
            </div>
          )}
        </section>
      </main>

      <ConfigDrawer
        visible={showConfig}
        tile={pendingTile}
        configValues={configValues}
        onOptionChange={handleConfigOptionChange}
        onMultiTextChange={handleMultiTextChange}
        onMultiTextAdd={handleMultiTextAdd}
        onMultiTextRemove={handleMultiTextRemove}
        onCancel={handleConfigCancel}
        onConfirm={handleConfigConfirm}
        isBusy={isBusy}
      />
    </div>
  );
}

export default App;
