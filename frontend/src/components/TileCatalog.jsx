export function TileCatalog({ tiles, loadingId, pendingJob, isBusy, onTileClick }) {
  return (
    <section aria-label="Tool tiles" className="mt-[30px]">
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {tiles.map((tile) => {
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
              onClick={() => onTileClick(tile)}
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
                        {jobForTile.position === 0 ? "In progress" : `Position in queue: ${jobForTile.position}`}
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
  );
}
