export const CLASS_COLORS = {
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

export const DEFAULT_PLAYER_COLOR = "#e2e8f0";

export const ROLE_PRIORITY = {
  Tank: 0,
  Healer: 1,
  Melee: 2,
  Ranged: 3,
  Unknown: 4,
};

export const ROLE_BADGE_STYLES = {
  Tank: "border border-amber-500/40 bg-amber-500/10 text-amber-200",
  Healer: "border border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
  Melee: "border border-rose-500/40 bg-rose-500/10 text-rose-200",
  Ranged: "border border-sky-500/40 bg-sky-500/10 text-sky-200",
  Unknown: "border border-slate-600/40 bg-slate-700/30 text-slate-200",
};

export const BOSS_OPTIONS = [
  "Plexus Sentinel",
  "Loom'ithar",
  "Soulbinder Naazindhri",
  "Forgeweaver Araz",
  "The Soul Hunters",
  "Fractillus",
  "Nexus-King Salhadaar",
  "Dimensius, the All-Devouring",
];

export const DEFAULT_SORT_DIRECTIONS = {
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

export const TILES = [
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
