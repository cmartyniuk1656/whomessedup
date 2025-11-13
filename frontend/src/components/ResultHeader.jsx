const formatKey = (key) =>
  key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

export function ResultHeader({
  title,
  reportCode,
  filters,
  filterTags,
  abilityIds,
  onDownloadCsv,
  disableDownload,
  summaryMetrics,
}) {
  const abilityTags = [];
  if (abilityIds && typeof abilityIds === "object") {
    Object.entries(abilityIds).forEach(([key, value]) => {
      if (value == null) {
        return;
      }
      if (typeof value === "object") {
        const label = value.label || formatKey(key);
        if (value.id != null) {
          abilityTags.push(`${label} ${value.id}`);
        }
      } else {
        const label = key === "besiege" ? "Besiege" : key === "ghost" ? "Ghost" : formatKey(key);
        abilityTags.push(`${label} ${value}`);
      }
    });
  }

  const detailParts = [];
  if (filters?.fight_name) {
    detailParts.push(`Fight filter: ${filters.fight_name}`);
  }
  if (abilityTags.length) {
    detailParts.push(abilityTags.join(", "));
  }
  if (filterTags?.length) {
    detailParts.push(filterTags.join(" - "));
  }

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-xs uppercase tracking-widest text-emerald-400">Results</p>
        <h3 className="mt-1 text-2xl font-semibold text-white">{title}</h3>
        <p className="mt-1 text-sm text-slate-400">
          Report {reportCode}
          {detailParts.length ? ` - ${detailParts.join(" - ")}` : ""}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2 text-right text-sm text-slate-300">
        <button
          type="button"
          onClick={onDownloadCsv}
          className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/50 px-3 py-1.5 text-xs font-semibold text-emerald-200 transition hover:border-emerald-400 hover:text-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={disableDownload}
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
        {summaryMetrics?.map((metric) => (
          <p key={metric.label}>
            {metric.label}: {metric.value}
          </p>
        ))}
      </div>
    </div>
  );
}
