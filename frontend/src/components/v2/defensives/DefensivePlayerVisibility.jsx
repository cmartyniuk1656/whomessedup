/** Everyone-view lane toggles; hidden players remain available below the comparison. */
export function DefensivePlayerControls({ players, hiddenIds, onChange }) {
  const shown = players.filter((player) => !hiddenIds.includes(player.id)).length;
  return <div className="defensive-player-controls" role="group" aria-label="Player visibility">
    <strong>Player lanes <span>{shown} / {players.length} shown</span></strong>
    <button onClick={() => onChange(hiddenIds.filter((id) => !players.some((player) => player.id === id)))}>Show all players</button>
    <button onClick={() => onChange([...new Set([...hiddenIds, ...players.map((player) => player.id)])])}>Hide all players</button>
  </div>;
}

export function DefensivePlayerLabel({ player, casts, onHide, onInspect }) {
  return <div className="coverage-lane-label defensive-player-label">
    <input type="checkbox" aria-label={`Show ${player.name}`} checked onChange={onHide} />
    <button onClick={onInspect} title={`Inspect ${player.name}`}>
      <strong>{player.name}</strong><span>{player.spec}</span>
    </button>
    <small>{casts}</small>
  </div>;
}

export function HiddenDefensivePlayers({ players, onEnable }) {
  if (!players.length) return null;
  return <section className="defensive-hidden-players" aria-label="Hidden players">
    <h4>Hidden players <span>{players.length} · Select to re-enable</span></h4>
    <div>{players.map((player) => <label key={player.id}>
      <input type="checkbox" aria-label={`Show ${player.name}`} checked={false} onChange={() => onEnable(player.id)} />
      <span><strong>{player.name}</strong><small>{player.spec}</small></span>
    </label>)}</div>
  </section>;
}
