export function TableMultiSelectFilter({ filter, selectedIds, onToggle }) {
  if (!filter?.options?.length) {
    return null;
  }

  const selected = new Set(selectedIds ?? []);
  const isSingleSelect = filter.kind === "single_select";

  return (
    <div className="space-y-2.5">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{filter.label}</p>
      <div
        className="flex flex-wrap gap-2"
        role={isSingleSelect ? "radiogroup" : undefined}
        aria-label={isSingleSelect ? filter.label : undefined}
      >
        {filter.options.map((option) => {
          const isActive = selected.has(option.id);
          return (
            <button
              key={`${filter.id}-${option.id}`}
              type="button"
              role={isSingleSelect ? "radio" : undefined}
              aria-checked={isSingleSelect ? isActive : undefined}
              aria-pressed={isSingleSelect ? undefined : isActive}
              className={[
                "rounded-lg border px-3 py-1.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/40",
                isActive
                  ? "border-emerald-300/35 bg-emerald-400/10 text-emerald-100"
                  : "border-white/10 bg-slate-950/35 text-slate-300 hover:border-white/20 hover:bg-white/[0.04]",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onToggle(option.id)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
