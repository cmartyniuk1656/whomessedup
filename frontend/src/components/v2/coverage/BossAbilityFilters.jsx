/** Icon toggles preserve the boss catalogue descriptions on hover and focus. */
export function BossAbilityFilters({
  lanes,
  selectedIds,
  onToggle,
  onSelectAll,
  onClear,
}) {
  return (
    <div
      className="coverage-boss-filters"
      role="group"
      aria-label="Boss ability filters"
    >
      <span>Boss abilities</span>
      {lanes.map((lane) => (
        <div className="coverage-boss-filter" key={lane.id}>
          <button
            type="button"
            aria-label={`Toggle ${lane.name}`}
            aria-pressed={selectedIds.includes(lane.id)}
            aria-describedby={`boss-tooltip-${lane.spellId}`}
            onClick={() => onToggle(lane.id)}
          >
            <img src={lane.icon} alt="" width="32" height="32" />
            <small>{lane.events.length}</small>
          </button>
          <span
            role="tooltip"
            id={`boss-tooltip-${lane.spellId}`}
            className="coverage-ability-tooltip"
          >
            <strong>{lane.name}</strong>
            {lane.description}
          </span>
        </div>
      ))}
      <button type="button" onClick={onSelectAll}>
        All
      </button>
      <button type="button" onClick={onClear}>
        None
      </button>
      <small>
        {selectedIds.length} / {lanes.length} shown
      </small>
    </div>
  );
}
