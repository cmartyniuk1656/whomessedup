import { Button } from "../atoms/Button";
import { DifficultyToggle } from "../molecules/DifficultyToggle";
import { FightSelectionGrid } from "../organisms/FightSelectionGrid";

export function ReportsHeroRegion({
  onSwitchToLegacy,
  fights,
  difficultyOptions,
  selectedDifficulty,
  onSelectDifficulty,
  selectedFightId,
  onSelectFight,
  reportCountsByFightId,
}) {
  return (
    <section className="relative isolate overflow-hidden border-b border-white/10 pb-10 pt-6 sm:pb-12 sm:pt-8">
      <div className="flex justify-end">
        <Button type="button" variant="secondary" onClick={onSwitchToLegacy}>
          Open legacy UI
        </Button>
      </div>

      <div className="mx-auto mt-8 flex max-w-6xl flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.35em] text-slate-300 shadow-[0_0_40px_rgba(255,255,255,0.05)]">
          <span>Log Analysis</span>
          <span aria-hidden>&middot;</span>
          <span>Mythic Raid Tools</span>
        </div>
        <h1 className="mt-8 text-5xl font-semibold leading-none tracking-tight text-white sm:text-6xl lg:text-7xl">
          <span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-fuchsia-300 bg-clip-text text-transparent">
            HK Logs
          </span>
        </h1>
        <DifficultyToggle
          options={difficultyOptions}
          selectedId={selectedDifficulty}
          onSelect={onSelectDifficulty}
          className="mt-8"
        />
        <div className="mt-8 w-full">
          <FightSelectionGrid
            fights={fights}
            selectedFightId={selectedFightId}
            onSelectFight={onSelectFight}
            reportCountsByFightId={reportCountsByFightId}
          />
        </div>
      </div>
    </section>
  );
}

export default ReportsHeroRegion;
