import GlassCard from "./ui/GlassCard";

export function TileCatalog({ tiles, loadingId, pendingJob, isBusy, onTileClick }) {
  return (
    <section aria-label="Tool tiles" id="tiles" className="mt-[30px]">
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
              : tile.mode === "priority-damage"
              ? "Damage Report"
              : "Combined Failures";
          return (
            <button
              key={tile.id}
              type="button"
              onClick={() => onTileClick(tile)}
              className="group h-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isBusy}
            >
              <GlassCard title={tile.title} className="h-full">
                <div className="flex h-full flex-col gap-4 text-content">
                  <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-primary">
                    Raid Tool
                    <span className="h-1 w-1 rounded-full bg-primary" />
                    {tileBadge}
                  </div>
                  <p className="text-sm text-muted">{tile.description}</p>
                  <div className="mt-auto inline-flex items-center gap-2 text-sm font-medium text-primary">
                    {isLoading ? (
                      <span className="flex flex-col text-left text-primary">
                        <span className="flex items-center gap-2">
                          <span className="h-2 w-2 animate-ping rounded-full bg-primary" />
                          {jobForTile?.status === "running" ? "Running report..." : "Queued..."}
                        </span>
                        {typeof jobForTile?.position === "number" ? (
                          <span className="mt-1 text-[11px] text-primary/80">
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
                </div>
              </GlassCard>
            </button>
          );
        })}
      </div>
    </section>
  );
}
