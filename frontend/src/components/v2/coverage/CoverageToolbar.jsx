/** Presentation-only controls for timeline state. */
export function CoverageToolbar({ state }) {
  return (
    <div className="coverage-controls">
      <label>
        <input
          type="checkbox"
          checked={state.overlay}
          onChange={(event) => state.setOverlay(event.target.checked)}
        />
        Damage + heal absorbs
      </label>
      <label>
        <input
          type="checkbox"
          checked={state.showReady}
          onChange={(event) => state.setShowReady(event.target.checked)}
        />
        Estimated readiness
      </label>
      <label>
        Healer{" "}
        <select
          value={state.healer}
          onChange={(event) => state.setHealer(event.target.value)}
        >
          <option value="all">Everyone</option>
          {state.healers.map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
      </label>
      <label>
        Zoom{" "}
        <input
          aria-label="Timeline zoom"
          type="range"
          min="1"
          max="4"
          step="0.5"
          value={state.zoom}
          onChange={(event) => state.setZoom(Number(event.target.value))}
        />
        {state.zoom}×
      </label>
    </div>
  );
}
