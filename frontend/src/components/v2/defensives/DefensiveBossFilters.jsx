/** Share boss icon controls across defensive views while preserving selected spell IDs. */
import { BossAbilityFilters } from "../coverage/BossAbilityFilters";
import { mergeBossAbilityLanes } from "../../../utils/defensiveUsage";

export function DefensiveBossFilters({ pulls, selectedIds, onChange }) {
  const lanes = mergeBossAbilityLanes(pulls);
  return <BossAbilityFilters lanes={lanes}
    selectedIds={lanes.filter((lane) => selectedIds.includes(lane.spellId)).map((lane) => lane.id)}
    onToggle={(id) => onChange(selectedIds.includes(id) ? selectedIds.filter((value) => value !== id) : [...selectedIds, id])}
    onSelectAll={() => onChange([...new Set([...selectedIds, ...lanes.map((lane) => lane.id)])])}
    onClear={() => onChange([])} />;
}
