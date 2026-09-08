export const REPORT_TYPES = {
  AGGREGATE: "aggregate",
  MECHANICS: "mechanics",
  DEATHS: "deaths",
  AVOIDABLE_DAMAGE: "avoidable_damage",
  DAMAGE: "damage",
  COOLDOWNS: "cooldowns",
  DISPELS: "dispels",
  GENERIC: "generic",
};

export function getReportType(report) {
  const searchable = `${report?.id || ""} ${report?.title || ""}`.toLowerCase();
  if (searchable.includes("aggregate")) return REPORT_TYPES.AGGREGATE;
  if (searchable.includes("mechanic")) return REPORT_TYPES.MECHANICS;
  if (searchable.includes("death")) return REPORT_TYPES.DEATHS;
  if (searchable.includes("avoidable") && searchable.includes("damage")) {
    return REPORT_TYPES.AVOIDABLE_DAMAGE;
  }
  if (searchable.includes("cooldown")) return REPORT_TYPES.COOLDOWNS;
  if (searchable.includes("dispel")) return REPORT_TYPES.DISPELS;
  if (searchable.includes("damage")) return REPORT_TYPES.DAMAGE;
  return REPORT_TYPES.GENERIC;
}

export function orderReportCatalog(reports) {
  const priority = {
    [REPORT_TYPES.AGGREGATE]: 0,
    [REPORT_TYPES.MECHANICS]: 1,
  };
  return (reports ?? [])
    .map((report, index) => ({ report, index }))
    .sort((left, right) => {
      const leftPriority = priority[getReportType(left.report)] ?? 2;
      const rightPriority = priority[getReportType(right.report)] ?? 2;
      return leftPriority - rightPriority || left.index - right.index;
    })
    .map(({ report }) => report);
}
