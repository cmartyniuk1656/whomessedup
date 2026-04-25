import { FightSelectionCard } from "../molecules/FightSelectionCard";

export function FightSelectionGrid({ fights, selectedFightId, onSelectFight, reportCountsByFightId }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {fights.map((fight) => {
        return (
          <FightSelectionCard
            key={fight.id}
            fight={fight}
            isSelected={fight.id === selectedFightId}
            reportCount={reportCountsByFightId?.[fight.id] ?? 0}
            onSelect={onSelectFight}
          />
        );
      })}
    </div>
  );
}

export default FightSelectionGrid;
