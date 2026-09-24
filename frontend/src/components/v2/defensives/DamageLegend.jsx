/** Keep the key beside its graph and include only outcomes present in that graph. */
import { incomingDamage } from "../../../utils/defensiveUsage";

export function DamageLegend({ points, maximum, allMitigation = false }) {
  const has = (value) => points.some((point) => value(point) > 0);
  const items = [
    { show: has((p) => p.damage), color: "taken", label: "Damage to health", detail: "Actually taken" },
    { show: has((p) => allMitigation ? p.absorbed : p.cooldownAbsorbed), color: "absorbed",
      label: allMitigation ? "Absorbed by all shields" : "Absorbed by cooldowns", detail: "Measured in the log" },
    { show: !allMitigation && has((p) => (p.absorbed || 0) - (p.cooldownAbsorbed || 0)), color: "other",
      label: "Absorbed by other shields", detail: "Not credited to tracked cooldowns" },
    { show: has((p) => p.mitigated), color: "mitigated",
      label: allMitigation ? "All damage reduction" : "Prevented by cooldowns",
      detail: allMitigation ? "Includes armor and passives" : "Estimated · supported effects only" },
  ].filter((item) => item.show);
  return <div className="defensive-graph-key" role="group" aria-label="Damage graph legend">
    <div className="defensive-graph-key-items">
      {items.map(({ color, label, detail }) => <span className="defensive-graph-key-item" key={color}>
        <i className={`defensive-graph-swatch damage-${color}`} aria-hidden="true" />
        <span><strong>{label}</strong><small>{detail}</small></span>
      </span>)}
      {has((p) => p.immuneEvents) && <span className="defensive-graph-key-item"><b className="damage-immune" aria-hidden="true">╹</b><span><strong>Immune hit</strong><small>Prevented amount unknown</small></span></span>}
      {has((p) => incomingDamage(p) - maximum) && <span className="defensive-graph-key-item"><b aria-hidden="true">⌃</b><span><strong>Peak above scale</strong><small>Full height is clipped</small></span></span>}
    </div>
    <p>{items.length ? "Colours stack from bottom to top · damage per second in 2-second intervals." : "No damage recorded in this graph."}</p>
  </div>;
}
