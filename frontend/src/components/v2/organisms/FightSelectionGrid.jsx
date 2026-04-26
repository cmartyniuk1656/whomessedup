import { FightSelectionCard } from "../molecules/FightSelectionCard";

export function FightSelectionGrid({ fights, selectedFightId, onSelectFight, reportCountsByFightId }) {
  return (
    <div className="flex flex-wrap justify-center gap-5">
      {fights.map((fight) => {
        return (
          <div
            key={fight.id}
            className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(33.333%-0.875rem)] xl:w-[calc(20%-1rem)]"
          >
            <FightSelectionCard
              fight={fight}
              isSelected={fight.id === selectedFightId}
              reportCount={reportCountsByFightId?.[fight.id] ?? 0}
              onSelect={onSelectFight}
            />
          </div>
        );
      })}
    </div>
  );
}

export default FightSelectionGrid;
