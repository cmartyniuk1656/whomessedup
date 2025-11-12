import { Fragment, useEffect, useMemo, useRef, useState } from "react";

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

const ROLE_BADGE_STYLES = {
  Tank: "border border-amber-500/40 bg-amber-500/10 text-amber-200",
  Healer: "border border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
  Melee: "border border-rose-500/40 bg-rose-500/10 text-rose-200",
  Ranged: "border border-sky-500/40 bg-sky-500/10 text-sky-200",
  Unknown: "border border-slate-600/40 bg-slate-700/30 text-slate-200",
};

const BOSS_OPTIONS = [
  "Plexus Sentinel",
  "Loom'ithar",
  "Soulbinder Naazindhri",
  "Forgeweaver Araz",
  "The Soul Hunters",
  "Fractillus",
  "Nexus-King Salhadaar",
  "Dimensius, the All-Devouring",
];

const DEFAULT_SORT_DIRECTIONS = {
  role: "asc",
  player: "asc",
  pulls: "desc",
  combinedAverage: "desc",
  addTotalDamage: "desc",
  addAverageDamage: "desc",
  ghostMisses: "desc",
  ghostPerPull: "desc",
  besiegeHits: "desc",
  besiegePerPull: "desc",
  fuckupRate: "desc",
};

const TILES = [
  {
    id: "nexus-phase1",
    title: "Nexus-King Phase 1 - Fuck Ups",
    description:
      "Combine Besiege hits and Oathbound ghost misses into a single per-player dashboard for Nexus-King Salhadaar pulls.",
    defaultFight: "Nexus-King Salhadaar",
    endpoint: "/api/nexus-phase1",
    params: {
      hit_ability_id: 1227472,
      ghost_ability_id: 1224737,
      data_type: "DamageTaken",
    },
    defaultSort: { key: "role", direction: "asc" },
    configOptions: [
      {
        id: "first_hit_only",
        type: "checkbox",
        label: "Only report the first Besiege hit per pull",
        default: true,
        param: "first_hit_only",
      },
      {
        id: "ghost_miss_mode",
        type: "select",
        label: "How should ghost misses be counted?",
        default: "first_per_set",
        param: "ghost_miss_mode",
        options: [
          { value: "first_per_set", label: "Count the first ghost miss of each set" },
          { value: "first_per_pull", label: "Count the first ghost miss of each pull" },
          { value: "all", label: "Count every ghost miss" },
        ],
      },
      {
        id: "fresh_run",
        type: "checkbox",
        label: "Force fresh run (skip cache)",
        default: false,
        param: "fresh",
      },
    ],
    footnotes: [
      "Filters out duplicate besiege ticks that happen when a single besiege hits a player multiple times.",
    ],
  },
  {
    id: "nexus-phase1-damage",
    title: "Nexus-King Phase Damage/Healing Report",
    description:
      "Summarize total damage or healing per phase across all Nexus-King Salhadaar pulls, with per-pull averages.",
    defaultFight: "Nexus-King Salhadaar",
    endpoint: "/api/nexus-phase-damage",
    params: {
      phase_profile: "nexus",
    },
    mode: "phase-damage",
    defaultSort: { key: "role", direction: "asc" },
    configOptions: [
      {
        id: "additional_reports",
        type: "multi-text",
        label: "Additional report codes or URLs (optional)",
        default: [""],
        param: "additional_report",
        placeholder: "https://www.warcraftlogs.com/reports/...",
      },
      {
        id: "phase_full",
        label: "Full Fight",
        default: true,
        param: "phase",
        value: "full",
      },
      {
        id: "phase_1",
        label: "Stage One: Oath Breakers",
        default: false,
        param: "phase",
        value: "1",
      },
      {
        id: "phase_2",
        label: "Stage Two: Rider's of the Dark",
        default: false,
        param: "phase",
        value: "2",
      },
      {
        id: "phase_3",
        label: "Intermission One: Nexus Descent",
        default: false,
        param: "phase",
        value: "3",
      },
      {
        id: "phase_4",
        label: "Intermission Two: King's Hunger",
        default: false,
        param: "phase",
        value: "4",
      },
      {
        id: "phase_5",
        label: "Stage Three: World in Twilight",
        default: false,
        param: "phase",
        value: "5",
      },
      {
        id: "fresh_run",
        label: "Force fresh run (skip cache)",
        default: false,
        param: "fresh",
      },
    ],
    footnotes: [
      "Tanks and DPS will show Damage done and Healers will show healing done.",
      "Single phase or full fight reports are recommended. Multi-phase reports will aggregate data and compute averages off the total pull count even if the player was dead during a phase, impacting their overall average.",
    ],
  },
  {
    id: "dimensius-phase-damage",
    title: "Dimensius Phase Damage/Healing Report",
    description:
      "Summarize total damage or healing per phase across all Dimensius, the All-Devouring pulls, with per-pull averages.",
    defaultFight: "Dimensius, the All-Devouring",
    endpoint: "/api/nexus-phase-damage",
    params: {
      phase_profile: "dimensius",
    },
    mode: "phase-damage",
    defaultSort: { key: "role", direction: "asc" },
    configOptions: [
      {
        id: "additional_reports_dimensius",
        type: "multi-text",
        label: "Additional report codes or URLs (optional)",
        default: [""],
        param: "additional_report",
        placeholder: "https://www.warcraftlogs.com/reports/...",
      },
      {
        id: "dim_phase_full",
        label: "Full Fight",
        default: true,
        param: "phase",
        value: "full",
      },
      {
        id: "dim_phase_1",
        label: "Stage One: Critical Mass",
        default: false,
        param: "phase",
        value: "1",
      },
      {
        id: "dim_phase_2",
        label: "Intermission: Event Horizon",
        default: false,
        param: "phase",
        value: "2",
      },
      {
        id: "dim_phase_3",
        label: "Stage Two: The Dark Heart",
        default: false,
        param: "phase",
        value: "3",
      },
      {
        id: "dim_phase_4",
        label: "Stage Three: Singularity",
        default: false,
        param: "phase",
        value: "4",
      },
      {
        id: "dim_fresh_run",
        label: "Force fresh run (skip cache)",
        default: false,
        param: "fresh",
      },
    ],
    footnotes: [
      "Tanks and DPS will show Damage done and Healers will show healing done.",
      "Single phase or full fight reports are recommended. Multi-phase reports will aggregate data and compute averages off the total pull count even if the player was dead during a phase, impacting their overall average.",
    ],
  },
  {
    id: "dimensius-add-damage",
    title: "Dimensius - Phase 1 Add Damage",
    description:
      "Average player damage into Living Mass adds during Stage One: Critical Mass for Dimensius, the All-Devouring.",
    defaultFight: "Dimensius, the All-Devouring",
    endpoint: "/api/dimensius-add-damage",
    mode: "add-damage",
    defaultSort: { key: "role", direction: "asc" },
    configOptions: [
      {
        id: "dim_additional_reports",
        type: "multi-text",
        label: "Additional report codes or URLs (optional)",
        default: [""],
        param: "additional_report",
        placeholder: "https://www.warcraftlogs.com/reports/...",
      },
      {
        id: "dim_ignore_first_add_set",
        type: "checkbox",
        label: "Ignore first add set",
        default: false,
        param: "ignore_first_add_set",
      },
      {
        id: "dim_add_fresh_run",
        label: "Force fresh run (skip cache)",
        default: false,
        param: "fresh",
      },
    ],
    footnotes: ["*Optional ignore first 6 adds that spawn instantly on pull"],
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
  const [fightOverride, setFightOverride] = useState(TILES[0]?.defaultFight ?? "");
  const [ignoreAfterDeaths, setIgnoreAfterDeaths] = useState("");
  const [ignoreFinalSeconds, setIgnoreFinalSeconds] = useState("");
  const [activeTile, setActiveTile] = useState(TILES[0]?.id ?? null);
  const [sortConfig, setSortConfig] = useState(TILES[0]?.defaultSort ?? { key: "role", direction: "asc" });
  const [loadingId, setLoadingId] = useState(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [pendingTile, setPendingTile] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [configValues, setConfigValues] = useState({});
  const [savedConfigs, setSavedConfigs] = useState({});
  const [mobileViewMode, setMobileViewMode] = useState("table");
  const [pendingJob, setPendingJob] = useState(null);
  const jobPollRef = useRef({ timer: null, id: null });

  useEffect(() => {
    return () => {
      if (jobPollRef.current.timer) {
        clearTimeout(jobPollRef.current.timer);
      }
      jobPollRef.current = { timer: null, id: null };
    };
  }, []);

  const stopJobPolling = () => {
    if (jobPollRef.current.timer) {
      clearTimeout(jobPollRef.current.timer);
    }
    jobPollRef.current = { timer: null, id: null };
  };

  const scheduleJobPoll = (jobId, tile) => {
    jobPollRef.current.timer = setTimeout(() => requestJobStatus(jobId, tile), 1500);
  };

  const requestJobStatus = async (jobId, tile) => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`);
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail?.detail || "Failed to fetch job status.");
      }
      const data = await response.json();
      if (jobPollRef.current.id !== jobId) {
        return;
      }

      if (data.status === "completed" && data.result) {
        stopJobPolling();
        setPendingJob(null);
        setLoadingId(null);
        setResult({
          ...data.result,
          abilityLabel: tile.title,
          tileTitle: tile.title,
        });
        return;
      }

      if (data.status === "failed") {
        stopJobPolling();
        setPendingJob(null);
        setLoadingId(null);
        setError(data.error || "Report generation failed.");
        return;
      }

      setPendingJob(data);
      scheduleJobPoll(jobId, tile);
    } catch (err) {
      if (jobPollRef.current.id !== jobId) {
        return;
      }
      stopJobPolling();
      setPendingJob(null);
      setLoadingId(null);
      setError(err.message || "Failed to poll job status.");
    }
  };

  const escapeCsv = (value) => {
    if (value === null || value === undefined) return "";
    const str = String(value);
    if (/[",\n]/.test(str)) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const buildCsvContent = (tile, data, tableRows, phases, labels) => {
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
        const values = [
          row.player,
          row.role,
          className,
          row.pulls ?? 0,
        ];
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

  const handleDownloadCsv = () => {
    if (!result || !currentTile) {
      return;
    }
    try {
      const csvContent = buildCsvContent(currentTile, result, sortedRows, phaseOrder, phaseLabels);
      const safeReport = (result.report || "report").replace(/[^a-zA-Z0-9-_]/g, "_");
      const filename = `${safeReport}_${currentTile.id}.csv`;
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
      setError("Failed to export CSV. Please try again.");
    }
  };
  const isBusy = loadingId !== null;

  const currentTile = useMemo(
    () => TILES.find((tile) => tile.id === activeTile) ?? TILES[0] ?? null,
    [activeTile]
  );

  const phaseOrder = result?.phases ?? [];
  const phaseLabels = result?.phase_labels ?? {};

  const rows = useMemo(() => {
    if (!result?.entries || !currentTile) return [];
    const playerClasses = result.player_classes ?? {};
    const playerRoles = result.player_roles ?? {};
    const selectedPhaseIds = result?.phases ?? [];

    if (currentTile.mode === "phase-damage") {
      return result.entries.map((entry) => {
        const playerClass = playerClasses[entry.player] ?? null;
        const normalizedClass = playerClass ? playerClass.replace(/\s+/g, "").toLowerCase() : null;
        const color = normalizedClass ? CLASS_COLORS[normalizedClass] ?? DEFAULT_PLAYER_COLOR : DEFAULT_PLAYER_COLOR;
        const role = entry.role ?? playerRoles[entry.player] ?? "Unknown";
        const phaseTotals = {};
        const phaseAverages = {};
        (entry.metrics ?? []).forEach((metric) => {
          phaseTotals[metric.phase_id] = metric.total_amount ?? 0;
          phaseAverages[metric.phase_id] = metric.average_per_pull ?? 0;
        });
        const totalAmount = selectedPhaseIds.reduce(
          (sum, phaseId) => sum + (phaseTotals[phaseId] ?? 0),
          0
        );
        const combinedAverage = entry.pulls ? totalAmount / entry.pulls : 0;
        return {
          player: entry.player,
          role,
          className: playerClass,
          color,
          pulls: entry.pulls ?? 0,
          phaseTotals,
          phaseAverages,
          combinedAverage,
        };
      });
    }

    if (currentTile.mode === "add-damage") {
      return result.entries.map((entry) => {
        const playerClass = entry.class_name ?? playerClasses[entry.player] ?? null;
        const normalizedClass = playerClass ? playerClass.replace(/\s+/g, "").toLowerCase() : null;
        const color = normalizedClass ? CLASS_COLORS[normalizedClass] ?? DEFAULT_PLAYER_COLOR : DEFAULT_PLAYER_COLOR;
        const role = entry.role ?? playerRoles[entry.player] ?? "Unknown";
        return {
          player: entry.player,
          role,
          className: playerClass,
          color,
          pulls: entry.pulls ?? 0,
          addTotalDamage: entry.total_damage ?? 0,
          addAverageDamage: entry.average_damage ?? 0,
        };
      });
    }

    return result.entries.map((entry) => {
      const playerClass = playerClasses[entry.player] ?? null;
      const normalizedClass = playerClass ? playerClass.replace(/\s+/g, "").toLowerCase() : null;
      const color = normalizedClass ? CLASS_COLORS[normalizedClass] ?? DEFAULT_PLAYER_COLOR : DEFAULT_PLAYER_COLOR;
      const role = entry.role ?? playerRoles[entry.player] ?? "Unknown";
      return {
        player: entry.player,
        role,
        className: playerClass,
        color,
        pulls: entry.pulls ?? 0,
        ghostMisses: entry.ghost_misses ?? 0,
        ghostPerPull: entry.ghost_per_pull ?? 0,
        besiegeHits: entry.besiege_hits ?? entry.hits ?? 0,
        besiegePerPull: entry.besiege_per_pull ?? entry.hits_per_pull ?? 0,
        fuckupRate: entry.fuckup_rate ?? 0,
      };
    });
  }, [result, currentTile]);

  useEffect(() => {
    if (!result?.ghost_events || !result.ghost_events.length) {
      return;
    }
    const groupLabel = `[Ghost Miss Debug] ${result.report || "Report"} - ${result.ghost_events.length} events`;
    console.groupCollapsed(groupLabel);
    const tableData = result.ghost_events.map((event) => {
      const offsetSeconds = Number.isFinite(event.offset_ms) ? event.offset_ms / 1000 : null;
      console.log(
        `Pull ${event.pull}: ${event.player} at ${offsetSeconds !== null ? offsetSeconds.toFixed(2) : "?"}s (ts ${event.timestamp})`
      );
      return {
        pull: event.pull,
        player: event.player,
        fight: event.fight_name ?? "",
        timestamp: event.timestamp,
        offset_seconds: offsetSeconds,
      };
    });
    console.table(tableData);
    console.groupEnd();
  }, [result]);

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
  const abilityIds = result?.ability_ids ?? {};
  const hitFilters = result?.hit_filters ?? {};

  const formatInt = (value) =>
    typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : value;
  const formatFloat = (value, digits = 3) =>
    typeof value === "number"
      ? value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
      : value;

  const filters = result?.filters ?? {};
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
    } else if (typeof hitFilters.first_ghost_only === "boolean") {
      filterTags.push(hitFilters.first_ghost_only ? "First Ghost per pull" : "All Ghost misses");
    }
    const additionalReportsFilter = filters.additional_reports;
    if (typeof additionalReportsFilter === "string" && additionalReportsFilter.trim()) {
      const reportList = additionalReportsFilter
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
      if (reportList.length === 1) {
        filterTags.push("Merged 1 additional report");
      } else if (reportList.length > 1) {
        filterTags.push(`Merged ${reportList.length} additional reports`);
      }
    }
    if (phaseOrder.length) {
      const phaseLabelString = phaseOrder.map((id) => phaseLabels[id] ?? id).join(", ");
      filterTags.unshift(`Phases: ${phaseLabelString}`);
    }
  } else if (currentTile?.mode === "add-damage") {
    if (filters.ignore_first_add_set === "true") {
      filterTags.push("Ignoring first Living Mass set");
    }
    const additionalReportsFilter = filters.additional_reports;
    if (typeof additionalReportsFilter === "string" && additionalReportsFilter.trim()) {
      const reportList = additionalReportsFilter
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
      if (reportList.length === 1) {
        filterTags.push("Merged 1 additional report");
      } else if (reportList.length > 1) {
        filterTags.push(`Merged ${reportList.length} additional reports`);
      }
    }
  } else {
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
    } else if (typeof hitFilters.first_ghost_only === "boolean") {
      filterTags.push(hitFilters.first_ghost_only ? "First Ghost per pull" : "All Ghost misses");
    }
    const additionalReportsFilter = filters.additional_reports;
    if (typeof additionalReportsFilter === "string" && additionalReportsFilter.trim()) {
      const reportList = additionalReportsFilter
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
      if (reportList.length === 1) {
        filterTags.push("Merged 1 additional report");
      } else if (reportList.length > 1) {
        filterTags.push(`Merged ${reportList.length} additional reports`);
      }
    }
  }

  let summaryMetrics = [];
  if (currentTile?.mode === "phase-damage") {
    summaryMetrics = [];
  } else if (currentTile?.mode === "add-damage") {
    const addTotals = result?.totals ?? {};
    summaryMetrics = [
      { label: "Pulls counted", value: formatInt(pullCount) },
      { label: "Combined add damage", value: formatInt(addTotals.total_damage ?? 0) },
      { label: "Avg add damage / Pull", value: formatFloat(addTotals.avg_damage_per_pull ?? 0, 3) },
    ];
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

  const handleSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      const defaultDirection =
        DEFAULT_SORT_DIRECTIONS[key] ||
        (key.startsWith("total_phase_") || key.startsWith("avg_phase_") ? "desc" : "asc");
      return { key, direction: defaultDirection };
    });
  };

  const renderSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <span className="ml-2 text-slate-500">↕</span>;
    }
    return <span className="ml-2 text-emerald-300">{sortConfig.direction === "asc" ? "▲" : "▼"}</span>;
  };

  const runTile = async (tile, overrides = {}) => {
    const code = extractReportCode(reportInput);
    if (!code) {
      setError("Enter a Warcraft Logs report URL or code first.");
      return;
    }

    stopJobPolling();
    setPendingJob(null);

    let effectiveFight = fightOverride;
    if (tile.defaultFight) {
      effectiveFight = tile.defaultFight;
      if (fightOverride !== tile.defaultFight) {
        setFightOverride(tile.defaultFight);
      }
    }

    const resolvedConfig = {};
    if (tile.configOptions?.length) {
      tile.configOptions.forEach((opt) => {
        const optionType = opt.type ?? "checkbox";
        let rawValue;
        if (Object.prototype.hasOwnProperty.call(overrides, opt.id)) {
          rawValue = overrides[opt.id];
        } else if (opt.default !== undefined) {
          rawValue = opt.default;
        } else if (optionType === "select" && Array.isArray(opt.options) && opt.options.length > 0) {
          rawValue = opt.options[0].value;
        } else if (optionType === "checkbox") {
          rawValue = false;
        }
        if (rawValue === undefined) {
          return;
        }
        if (optionType === "select") {
          resolvedConfig[opt.id] = String(rawValue);
        } else if (optionType === "multi-text") {
          if (Array.isArray(rawValue)) {
            resolvedConfig[opt.id] = rawValue.map((entry) => (entry == null ? "" : String(entry)));
          } else if (typeof rawValue === "string") {
            resolvedConfig[opt.id] = [rawValue];
          } else {
            resolvedConfig[opt.id] = [];
          }
        } else if (optionType === "checkbox") {
          if (typeof rawValue === "boolean") {
            resolvedConfig[opt.id] = rawValue;
          } else if (typeof rawValue === "string") {
            resolvedConfig[opt.id] = rawValue === "true" || rawValue === "1";
          } else if (typeof rawValue === "number") {
            resolvedConfig[opt.id] = rawValue === 1;
          } else {
            resolvedConfig[opt.id] = Boolean(rawValue);
          }
        } else {
          resolvedConfig[opt.id] = rawValue;
        }
      });
    }

    setError("");
    setResult(null);
    setActiveTile(tile.id);
    setSortConfig(tile.defaultSort ?? { key: "role", direction: "asc" });

    setLoadingId(tile.id);
    let jobQueued = false;
    try {
      const params = new URLSearchParams({ report: code });
      const fightName = (effectiveFight || "").trim();
      if (fightName) {
        params.set("fight", fightName);
      }
      if (tile.params) {
        Object.entries(tile.params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.set(key, String(value));
          }
        });
      }
      const deathsValue = ignoreAfterDeaths.trim();
      const deathsNum = deathsValue ? Number.parseInt(deathsValue, 10) : NaN;
      if (!Number.isNaN(deathsNum) && deathsNum > 0) {
        params.set("ignore_after_deaths", String(deathsNum));
      }
      const finalValue = ignoreFinalSeconds.trim();
      const finalNum = finalValue ? Number.parseFloat(finalValue) : NaN;
      if (!Number.isNaN(finalNum) && finalNum > 0) {
        params.set("ignore_final_seconds", String(finalNum));
      }
      if (tile.configOptions?.length) {
        tile.configOptions.forEach((opt) => {
          const optionType = opt.type ?? "checkbox";
          const value = resolvedConfig[opt.id];
          if (value === undefined || value === null) {
            return;
          }
          if (optionType === "select") {
            params.set(opt.param, String(value));
            return;
          }
          if (optionType === "multi-text") {
            const list = Array.isArray(value) ? value : [value];
            list
              .map((entry) => (entry == null ? "" : String(entry).trim()))
              .filter((entry) => entry.length > 0)
              .forEach((entry) => {
                params.append(opt.param, entry);
              });
            return;
          }
          const boolValue =
            typeof value === "boolean"
              ? value
              : typeof value === "string"
              ? value === "true" || value === "1"
              : Boolean(value);
          if (opt.value !== undefined) {
            if (boolValue) {
              params.append(opt.param, String(opt.value));
            }
          } else {
            params.set(opt.param, boolValue ? "true" : "false");
          }
        });
      }

      const response = await fetch(`${tile.endpoint}?${params.toString()}`);
      if (response.status === 202) {
        const payload = await response.json().catch(() => null);
        const job = payload?.job;
        if (!job?.id) {
          throw new Error("Unable to queue report job.");
        }
        jobQueued = true;
        setPendingJob(job);
        jobPollRef.current.id = job.id;
        requestJobStatus(job.id, tile);
        return;
      }
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail?.detail || "Request failed");
      }

      const data = await response.json();
      setResult({
        ...data,
        tileTitle: tile.title,
        abilityLabel: tile.title,
      });
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      if (!jobQueued) {
        setLoadingId(null);
      }
    }
  };

  const handleTileClick = (tile) => {
    if (isBusy) {
      return;
    }
    if (tile.configOptions?.length) {
      const saved = savedConfigs[tile.id] ?? {};
      const initial = {};
      tile.configOptions.forEach((opt) => {
        const savedValue = saved[opt.id];
        const optionType = opt.type ?? "checkbox";
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
          let values;
          if (Array.isArray(savedValue)) {
            values = savedValue.map((entry) => (entry == null ? "" : String(entry)));
          } else if (Array.isArray(opt.default)) {
            values = opt.default.map((entry) => (entry == null ? "" : String(entry)));
          } else if (typeof savedValue === "string" && savedValue.trim()) {
            values = [savedValue];
          } else {
            values = [""];
          }
          if (!values.length) {
            values = [""];
          }
          initial[opt.id] = values;
        } else {
          if (typeof savedValue === "boolean") {
            initial[opt.id] = savedValue;
          } else if (typeof opt.default === "boolean") {
            initial[opt.id] = opt.default;
          } else if (typeof savedValue === "string") {
            initial[opt.id] = savedValue === "true" || savedValue === "1";
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
    setConfigValues((prev) => ({
      ...prev,
      [id]: value,
    }));
  };

  const handleMultiTextChange = (id, index, value) => {
    setConfigValues((prev) => {
      const current = Array.isArray(prev[id]) ? [...prev[id]] : [];
      while (current.length <= index) {
        current.push("");
      }
      current[index] = value;
      return {
        ...prev,
        [id]: current,
      };
    });
  };

  const handleMultiTextAdd = (id) => {
    setConfigValues((prev) => {
      const current = Array.isArray(prev[id]) ? [...prev[id]] : [];
      current.push("");
      return {
        ...prev,
        [id]: current,
      };
    });
  };

  const handleMultiTextRemove = (id, index) => {
    setConfigValues((prev) => {
      let current = Array.isArray(prev[id]) ? [...prev[id]] : [];
      if (current.length <= 1) {
        current = [""];
      } else {
        current.splice(index, 1);
        if (!current.length) {
          current = [""];
        }
      }
      return {
        ...prev,
        [id]: current,
      };
    });
  };

  const handleConfigCancel = () => {
    setShowConfig(false);
    setPendingTile(null);
  };

  const handleConfigConfirm = () => {
    if (!pendingTile) {
      return;
    }
    const overrides = Object.entries(configValues).reduce((acc, [key, value]) => {
      if (Array.isArray(value)) {
        acc[key] = value.map((entry) => (entry == null ? "" : String(entry)));
      } else {
        acc[key] = value;
      }
      return acc;
    }, {});
    setSavedConfigs((prev) => ({
      ...prev,
      [pendingTile.id]: overrides,
    }));
    setShowConfig(false);
    const tileToRun = pendingTile;
    setPendingTile(null);
    runTile(tileToRun, overrides);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/40">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <p className="text-sm uppercase tracking-widest text-slate-400">Who Messed Up</p>
          <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">Raid Analysis Dashboard</h1>
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
                disabled={isBusy}
              />
            </label>
            <label className="flex w-full flex-col text-sm font-medium text-slate-300 sm:max-w-xs">
              Fight filter (optional)
              <select
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                value={fightOverride}
                onChange={(event) => setFightOverride(event.target.value)}
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
                onChange={(event) => setIgnoreAfterDeaths(event.target.value)}
                disabled={isBusy}
              />
            </label>
            <label className="flex w-full flex-col text-sm font-medium text-slate-300">
              Ignore final seconds of each pull
              <input
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                placeholder="e.g. 10"
                value={ignoreFinalSeconds}
                onChange={(event) => setIgnoreFinalSeconds(event.target.value)}
                disabled={isBusy}
              />
            </label>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16">
        <section aria-label="Tool tiles" className="mt-[30px]">
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {TILES.map((tile) => {
              const isLoading = loadingId === tile.id;
              const jobForTile = isLoading ? pendingJob : null;
              const tileBadge =
                tile.mode === "phase-damage"
                  ? "Damage/Healing Report"
                  : tile.mode === "add-damage"
                  ? "Add Damage Report"
                  : tile.mode === "ghost"
                  ? "Ghost Analysis"
                  : "Combined Failures";
              return (
                <button
                  key={tile.id}
                  type="button"
                  onClick={() => handleTileClick(tile)}
                  className="group flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-left shadow-lg shadow-emerald-500/5 transition hover:border-emerald-400 hover:shadow-emerald-500/20 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-slate-950"
                  disabled={isBusy}
                >
                  <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-emerald-400">
                    Raid Tool
                    <span className="h-1 w-1 rounded-full bg-emerald-400" />
                    {tileBadge}
                  </div>
                  <h2 className="mt-3 text-xl font-semibold text-white">{tile.title}</h2>
                  <p className="mt-3 text-sm text-slate-300">{tile.description}</p>
                  <div className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-emerald-300">
                    {isLoading ? (
                      <span className="flex flex-col text-left text-emerald-300">
                        <span className="flex items-center gap-2">
                          <span className="h-2 w-2 animate-ping rounded-full bg-emerald-300" />
                          {jobForTile?.status === "running" ? "Running report..." : "Queued..."}
                        </span>
                        {typeof jobForTile?.position === "number" ? (
                          <span className="mt-1 text-[11px] text-emerald-200">
                            {jobForTile.position === 0
                              ? "In progress"
                              : `Position in queue: ${jobForTile.position}`}
                          </span>
                        ) : null}
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
              {pendingJob ? (
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-emerald-300">
                    <span className="h-2 w-2 animate-ping rounded-full bg-emerald-300" />
                    {pendingJob.status === "running"
                      ? "Report is running..."
                      : `Waiting to start ${currentTile?.title || "analysis"}...`}
                  </div>
                  {typeof pendingJob.position === "number" ? (
                    <div className="text-xs text-slate-400">
                      {pendingJob.position === 0
                        ? "Currently executing."
                        : `Position in queue: ${pendingJob.position}`}
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
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-widest text-emerald-400">Results</p>
                  <h3 className="mt-1 text-2xl font-semibold text-white">{result.tileTitle || currentTile?.title}</h3>
                  <p className="mt-1 text-sm text-slate-400">
                    Report {result.report}
                    {result.filters?.fight_name ? ` · Fight filter: ${result.filters.fight_name}` : ""}
                    {abilityIds.besiege ? ` · Besiege ${abilityIds.besiege}` : ""}
                    {abilityIds.ghost ? ` · Ghost ${abilityIds.ghost}` : ""}
                    {filterTags.length ? ` · ${filterTags.join(" · ")}` : ""}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2 text-right text-sm text-slate-300">
                  <button
                    type="button"
                    onClick={handleDownloadCsv}
                    className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/50 px-3 py-1.5 text-xs font-semibold text-emerald-200 transition hover:border-emerald-400 hover:text-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={Boolean(loadingId) || Boolean(pendingJob)}
                  >
                    Download CSV
                    <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path
                        fillRule="evenodd"
                        d="M3 14.5a1 1 0 011-1h2.5a.5.5 0 010 1H4v2h12v-2h-2.5a.5.5 0 010-1H16a1 1 0 011 1v2.5a1 1 0 01-1 1H4a1 1 0 01-1-1v-2.5zm7-11a1 1 0 011 1v7.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4A1 1 0 015.293 9.793L7.586 12.086V4.5a1 1 0 011-1H10z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                  {summaryMetrics.map((metric) => (
                    <p key={metric.label}>
                      {metric.label}: {metric.value}
                    </p>
                  ))}
                </div>
              </div>

              <div className="sm:hidden mt-4">
                <label className="flex w-full flex-col text-sm font-medium text-slate-300">
                  Mobile layout
                  <select
                    className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-base text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                    value={mobileViewMode}
                    onChange={(event) => setMobileViewMode(event.target.value)}
                  >
                    <option value="table">Table</option>
                    <option value="cards">Cards</option>
                  </select>
                  <span className="mt-1 text-xs text-slate-400">Choose how results display on smaller screens.</span>
                </label>
              </div>

              <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/40">
                {currentTile?.mode === "phase-damage" ? (
                  <>
                    <div className="hidden sm:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-slate-800 text-sm">
                        <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
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
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("pulls")}
                              >
                                Pulls
                                {renderSortIcon("pulls")}
                              </button>
                            </th>
                            {phaseOrder.length > 1 ? (
                              <th className="px-4 py-3 text-right">
                                <button
                                  type="button"
                                  className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                  onClick={() => handleSort("combinedAverage")}
                                >
                                  Avg / Pull - Combined
                                  {renderSortIcon("combinedAverage")}
                                </button>
                              </th>
                            ) : null}
                            {phaseOrder.map((phaseId) => (
                              <Fragment key={`phase-header-${phaseId}`}>
                                <th className="px-4 py-3 text-right">
                                  <button
                                    type="button"
                                    className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                                    onClick={() => handleSort(`total_phase_${phaseId}`)}
                                  >
                                    Total - {phaseLabels[phaseId] || phaseId}
                                    {renderSortIcon(`total_phase_${phaseId}`)}
                                  </button>
                                </th>
                                <th className="px-4 py-3 text-right">
                                  <button
                                    type="button"
                                    className="inline-flex w-full items-center justify-end gap-1 text-right text-slate-300 hover:text-white"
                                    onClick={() => handleSort(`avg_phase_${phaseId}`)}
                                  >
                                    Avg / Pull - {phaseLabels[phaseId] || phaseId}
                                    {renderSortIcon(`avg_phase_${phaseId}`)}
                                  </button>
                                </th>
                              </Fragment>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                          {sortedRows.map((row) => (
                            <tr key={`${row.player}-${row.role}`}>
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
                            <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                            {phaseOrder.length > 1 ? (
                              <td className="px-4 py-3 text-right text-slate-200">
                                {formatFloat(row.combinedAverage ?? 0, 2)}
                              </td>
                            ) : null}
                            {phaseOrder.map((phaseId) => (
                              <Fragment key={`metric-${row.player}-${row.role}-${phaseId}`}>
                                <td className="px-4 py-3 text-right text-slate-200">
                                  {formatInt(row.phaseTotals?.[phaseId] ?? 0)}
                                </td>
                                  <td className="px-4 py-3 text-right text-slate-200">
                                    {formatFloat(row.phaseAverages?.[phaseId] ?? 0, 2)}
                                  </td>
                                </Fragment>
                              ))}
                            </tr>
                          ))}
                          {sortedRows.length === 0 && (
                            <tr>
                          <td
                            colSpan={3 + (phaseOrder.length > 1 ? 1 : 0) + phaseOrder.length * 2}
                            className="px-4 py-6 text-center text-slate-400"
                          >
                            No events matched the filters.
                          </td>
                        </tr>
                      )}
                        </tbody>
                      </table>
                    </div>
                    <div
                      className={`sm:hidden p-4 ${mobileViewMode === "cards" ? "space-y-4" : "overflow-x-auto"}`}
                    >
                      {sortedRows.length === 0 ? (
                        <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-400">
                          No events matched the filters.
                        </div>
                      ) : mobileViewMode === "cards" ? (
                        sortedRows.map((row) => (
                          <div
                            key={`${row.player}-${row.role}-phase-card`}
                            className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-base font-semibold" style={{ color: row.color }}>
                                {row.player}
                              </span>
                              <span
                                className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                                  ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                                }`}
                              >
                                {row.role}
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-slate-400">Pulls: {formatInt(row.pulls)}</p>
                            {phaseOrder.length > 1 ? (
                              <p className="text-xs text-emerald-200">
                                Avg / pull (combined): {formatFloat(row.combinedAverage ?? 0, 2)}
                              </p>
                            ) : null}
                            <div className="mt-3 space-y-2 text-sm text-slate-200">
                              {phaseOrder.map((phaseId) => (
                                <div
                                  key={`phase-card-${row.player}-${row.role}-${phaseId}`}
                                  className="rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2"
                                >
                                  <p className="text-xs uppercase tracking-widest text-slate-400">
                                    {phaseLabels[phaseId] || `Phase ${phaseId}`}
                                  </p>
                                  <div className="mt-1 flex justify-between text-xs">
                                    <span>Total</span>
                                    <span>{formatInt(row.phaseTotals?.[phaseId] ?? 0)}</span>
                                  </div>
                                  <div className="mt-1 flex justify-between text-xs">
                                    <span>Avg / Pull</span>
                                    <span>{formatFloat(row.phaseAverages?.[phaseId] ?? 0, 2)}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))
                      ) : (
                        <table className="min-w-full divide-y divide-slate-800 text-xs">
                          <thead className="bg-slate-900/80 text-[11px] uppercase tracking-widest text-slate-400">
                            <tr>
                              <th className="px-3 py-2 text-left">Player</th>
                              <th className="px-3 py-2 text-left">Role</th>
                              <th className="px-3 py-2 text-right">Pulls</th>
                              {phaseOrder.length > 1 ? (
                                <th className="px-3 py-2 text-right">Avg / Pull (Combined)</th>
                              ) : null}
                              {phaseOrder.map((phaseId) => (
                                <Fragment key={`mobile-phase-header-${phaseId}`}>
                                  <th className="px-3 py-2 text-right">Total {phaseLabels[phaseId] || phaseId}</th>
                                  <th className="px-3 py-2 text-right">Avg {phaseLabels[phaseId] || phaseId}</th>
                                </Fragment>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                            {sortedRows.map((row) => (
                              <tr key={`${row.player}-${row.role}-mobile-table`}>
                                <td className="px-3 py-2 font-medium" style={{ color: row.color }}>
                                  {row.player}
                                </td>
                                <td className="px-3 py-2">
                                  <span
                                    className={`inline-flex rounded-full px-2 py-1 text-[11px] font-medium ${
                                      ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                                    }`}
                                  >
                                    {row.role}
                                  </span>
                                </td>
                                <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.pulls)}</td>
                                {phaseOrder.length > 1 ? (
                                  <td className="px-3 py-2 text-right text-slate-200">
                                    {formatFloat(row.combinedAverage ?? 0, 2)}
                                  </td>
                                ) : null}
                                {phaseOrder.map((phaseId) => (
                                  <Fragment key={`mobile-phase-metric-${row.player}-${row.role}-${phaseId}`}>
                                    <td className="px-3 py-2 text-right text-slate-200">
                                      {formatInt(row.phaseTotals?.[phaseId] ?? 0)}
                                    </td>
                                    <td className="px-3 py-2 text-right text-slate-200">
                                      {formatFloat(row.phaseAverages?.[phaseId] ?? 0, 2)}
                                    </td>
                                  </Fragment>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </>
                ) : currentTile?.mode === "add-damage" ? (
                  <>
                    <div className="hidden sm:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-slate-800 text-sm">
                        <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
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
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("pulls")}
                              >
                                Pulls
                                {renderSortIcon("pulls")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("addTotalDamage")}
                              >
                                Total Add Damage
                                {renderSortIcon("addTotalDamage")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("addAverageDamage")}
                              >
                                Avg Add Damage / Pull
                                {renderSortIcon("addAverageDamage")}
                              </button>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                          {sortedRows.map((row) => (
                            <tr key={`${row.player}-${row.role}-add`}>
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
                              <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                              <td className="px-4 py-3 text-right text-slate-200">
                                {formatInt(row.addTotalDamage)}
                              </td>
                              <td className="px-4 py-3 text-right text-slate-200">
                                {formatFloat(row.addAverageDamage, 3)}
                              </td>
                            </tr>
                          ))}
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
                    <div
                      className={`sm:hidden p-4 ${mobileViewMode === "cards" ? "space-y-4" : "overflow-x-auto"}`}
                    >
                      {sortedRows.length === 0 ? (
                        <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-400">
                          No events matched the filters.
                        </div>
                      ) : mobileViewMode === "cards" ? (
                        sortedRows.map((row) => (
                          <div
                            key={`${row.player}-${row.role}-add-card`}
                            className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-base font-semibold" style={{ color: row.color }}>
                                {row.player}
                              </span>
                              <span
                                className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                                  ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                                }`}
                              >
                                {row.role}
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-slate-400">Pulls: {formatInt(row.pulls)}</p>
                            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-200">
                              <div className="rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[11px] uppercase tracking-widest text-slate-400">Total Damage</p>
                                <p className="mt-1 text-sm font-semibold text-emerald-300">
                                  {formatInt(row.addTotalDamage)}
                                </p>
                              </div>
                              <div className="rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[11px] uppercase tracking-widest text-slate-400">
                                  Avg / Pull
                                </p>
                                <p className="mt-1 text-sm font-semibold text-emerald-300">
                                  {formatFloat(row.addAverageDamage, 3)}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <table className="min-w-full divide-y divide-slate-800 text-xs">
                          <thead className="bg-slate-900/80 text-[11px] uppercase tracking-widest text-slate-400">
                            <tr>
                              <th className="px-3 py-2 text-left">Player</th>
                              <th className="px-3 py-2 text-left">Role</th>
                              <th className="px-3 py-2 text-right">Pulls</th>
                              <th className="px-3 py-2 text-right">Add Damage</th>
                              <th className="px-3 py-2 text-right">Avg / Pull</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                            {sortedRows.map((row) => (
                              <tr key={`${row.player}-${row.role}-add-mobile`}>
                                <td className="px-3 py-2 font-medium" style={{ color: row.color }}>
                                  {row.player}
                                </td>
                                <td className="px-3 py-2">
                                  <span
                                    className={`inline-flex rounded-full px-2 py-1 text-[11px] font-medium ${
                                      ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                                    }`}
                                  >
                                    {row.role}
                                  </span>
                                </td>
                                <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.pulls)}</td>
                                <td className="px-3 py-2 text-right text-slate-200">
                                  {formatInt(row.addTotalDamage)}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-200">
                                  {formatFloat(row.addAverageDamage, 3)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <div className="hidden sm:block overflow-x-auto">
                      <table className="min-w-full divide-y divide-slate-800 text-sm">
                        <thead className="bg-slate-900/80 text-xs uppercase tracking-widest text-slate-400">
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
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("pulls")}
                              >
                                Pulls
                                {renderSortIcon("pulls")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("besiegeHits")}
                              >
                                Besiege Hits
                                {renderSortIcon("besiegeHits")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("besiegePerPull")}
                              >
                                Besiege / Pull
                                {renderSortIcon("besiegePerPull")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("ghostMisses")}
                              >
                                Ghost Misses
                                {renderSortIcon("ghostMisses")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("ghostPerPull")}
                              >
                                Ghosts / Pull
                                {renderSortIcon("ghostPerPull")}
                              </button>
                            </th>
                            <th className="px-4 py-3 text-right">
                              <button
                                type="button"
                                className="flex items-center gap-1 text-right text-slate-300 hover:text-white"
                                onClick={() => handleSort("fuckupRate")}
                              >
                                Fuck-up Rate
                                {renderSortIcon("fuckupRate")}
                              </button>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                          {sortedRows.map((row) => (
                            <tr key={`${row.player}-${row.role}`}>
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
                              <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.pulls)}</td>
                              <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.besiegeHits)}</td>
                              <td className="px-4 py-3 text-right text-slate-200">
                                {formatFloat(row.besiegePerPull, 3)}
                              </td>
                              <td className="px-4 py-3 text-right text-slate-200">{formatInt(row.ghostMisses)}</td>
                              <td className="px-4 py-3 text-right text-slate-200">
                                {formatFloat(row.ghostPerPull, 3)}
                              </td>
                              <td className="px-4 py-3 text-right text-slate-200">
                                {formatFloat(row.fuckupRate, 3)}
                              </td>
                            </tr>
                          ))}
                          {sortedRows.length === 0 && (
                            <tr>
                              <td colSpan={8} className="px-4 py-6 text-center text-slate-400">
                                No events matched the filters.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                    <div
                      className={`sm:hidden p-4 ${mobileViewMode === "cards" ? "space-y-4" : "overflow-x-auto"}`}
                    >
                      {sortedRows.length === 0 ? (
                        <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-400">
                          No events matched the filters.
                        </div>
                      ) : mobileViewMode === "cards" ? (
                        sortedRows.map((row) => (
                          <div
                            key={`${row.player}-${row.role}-combined-card`}
                            className="rounded-lg border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-emerald-500/5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-base font-semibold" style={{ color: row.color }}>
                                {row.player}
                              </span>
                              <span
                                className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                                  ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                                }`}
                              >
                                {row.role}
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-slate-400">Pulls: {formatInt(row.pulls)}</p>
                            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-200">
                              <div className="rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[11px] uppercase tracking-widest text-slate-400">Besiege Hits</p>
                                <p className="mt-1 text-sm font-semibold text-emerald-300">
                                  {formatInt(row.besiegeHits)}
                                </p>
                                <p className="text-[11px] text-slate-400">
                                  Per pull: {formatFloat(row.besiegePerPull, 3)}
                                </p>
                              </div>
                              <div className="rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[11px] uppercase tracking-widest text-slate-400">Ghost Misses</p>
                                <p className="mt-1 text-sm font-semibold text-emerald-300">
                                  {formatInt(row.ghostMisses)}
                                </p>
                                <p className="text-[11px] text-slate-400">
                                  Per pull: {formatFloat(row.ghostPerPull, 3)}
                                </p>
                              </div>
                              <div className="col-span-2 rounded-md border border-slate-800/70 bg-slate-900/60 px-3 py-2">
                                <p className="text-[11px] uppercase tracking-widest text-slate-400">Fuck-up Rate</p>
                                <p className="mt-1 text-sm font-semibold text-emerald-300">
                                  {formatFloat(row.fuckupRate, 3)}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <table className="min-w-full divide-y divide-slate-800 text-xs">
                          <thead className="bg-slate-900/80 text-[11px] uppercase tracking-widest text-slate-400">
                            <tr>
                              <th className="px-3 py-2 text-left">Player</th>
                              <th className="px-3 py-2 text-left">Role</th>
                              <th className="px-3 py-2 text-right">Pulls</th>
                              <th className="px-3 py-2 text-right">Besiege</th>
                              <th className="px-3 py-2 text-right">Besiege / Pull</th>
                              <th className="px-3 py-2 text-right">Ghosts</th>
                              <th className="px-3 py-2 text-right">Ghosts / Pull</th>
                              <th className="px-3 py-2 text-right">Fuck-up Rate</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800 bg-slate-900/40 text-slate-100">
                            {sortedRows.map((row) => (
                              <tr key={`${row.player}-${row.role}-mobile-combined`}>
                                <td className="px-3 py-2 font-medium" style={{ color: row.color }}>
                                  {row.player}
                                </td>
                                <td className="px-3 py-2">
                                  <span
                                    className={`inline-flex rounded-full px-2 py-1 text-[11px] font-medium ${
                                      ROLE_BADGE_STYLES[row.role] || ROLE_BADGE_STYLES.Unknown
                                    }`}
                                  >
                                    {row.role}
                                  </span>
                                </td>
                                <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.pulls)}</td>
                                <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.besiegeHits)}</td>
                                <td className="px-3 py-2 text-right text-slate-200">
                                  {formatFloat(row.besiegePerPull, 3)}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-200">{formatInt(row.ghostMisses)}</td>
                                <td className="px-3 py-2 text-right text-slate-200">
                                  {formatFloat(row.ghostPerPull, 3)}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-200">
                                  {formatFloat(row.fuckupRate, 3)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </section>
      </main>
      {showConfig && pendingTile ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 py-6">
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-emerald-500/10">
            <h2 className="text-lg font-semibold text-white">Report Configuration</h2>
            <p className="mt-1 text-sm text-slate-400">
              Adjust settings before running <span className="font-medium text-slate-200">{pendingTile.title}</span>.
            </p>
            <div className="mt-4 space-y-3">
              {pendingTile.configOptions?.map((option) => {
                const optionType = option.type ?? "checkbox";
                if (optionType === "multi-text") {
                  const rawValues = Array.isArray(configValues[option.id])
                    ? configValues[option.id]
                    : Array.isArray(option.default)
                    ? option.default
                    : [""];
                  const values = rawValues.length ? rawValues : [""];
                  return (
                    <div key={option.id} className="flex flex-col gap-2 text-sm text-slate-200">
                      <span>{option.label}</span>
                      <div className="space-y-2">
                        {values.map((entryValue, index) => (
                          <div key={`${option.id}-${index}`} className="flex items-center gap-2">
                            <input
                              type="text"
                              className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                              value={entryValue ?? ""}
                              placeholder={option.placeholder ?? "Report code or URL"}
                              onChange={(event) =>
                                handleMultiTextChange(option.id, index, event.target.value)
                              }
                              disabled={isBusy}
                            />
                            <button
                              type="button"
                              onClick={() => handleMultiTextRemove(option.id, index)}
                              className="rounded-lg border border-slate-600 px-2 py-1 text-xs font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800 disabled:opacity-40"
                              disabled={isBusy || values.length <= 1}
                            >
                              Remove
                            </button>
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleMultiTextAdd(option.id)}
                        className="self-start rounded-lg border border-dashed border-slate-600 px-3 py-1 text-xs font-medium text-slate-200 transition hover:border-emerald-500 hover:text-emerald-400 disabled:opacity-40"
                        disabled={isBusy}
                      >
                        + Add another
                      </button>
                    </div>
                  );
                }
                if (optionType === "select") {
                  const selectValue =
                    typeof configValues[option.id] === "string"
                      ? configValues[option.id]
                      : typeof option.default === "string"
                      ? option.default
                      : "";
                  return (
                    <label key={option.id} className="flex flex-col gap-2 text-sm text-slate-200">
                      <span>{option.label}</span>
                      <select
                        className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                        value={selectValue}
                        onChange={(event) => handleConfigOptionChange(option.id, event.target.value)}
                        disabled={isBusy}
                      >
                        {(option.options ?? []).map((optChoice) => (
                          <option key={optChoice.value} value={optChoice.value}>
                            {optChoice.label ?? optChoice.value}
                          </option>
                        ))}
                      </select>
                    </label>
                  );
                }
                return (
                  <label key={option.id} className="flex items-start gap-3 text-sm text-slate-200">
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-400"
                      checked={
                        typeof configValues[option.id] === "boolean"
                          ? configValues[option.id]
                          : typeof option.default === "boolean"
                          ? option.default
                          : false
                      }
                      onChange={(event) => handleConfigOptionChange(option.id, event.target.checked)}
                      disabled={isBusy}
                    />
                    <span>{option.label}</span>
                  </label>
                );
              })}
            </div>
            {pendingTile.footnotes?.length ? (
              <div className="mt-4 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-2">
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Notes</p>
                <ul className="mt-2 space-y-1 text-xs text-slate-400">
                  {pendingTile.footnotes.map((note) => (
                    <li key={note}>* {note}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleConfigCancel}
                className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800"
                disabled={isBusy}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfigConfirm}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                disabled={isBusy}
              >
                Run Report
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;


