/** Keep the key beside its graph and include only outcomes present in that graph. */
import { incomingDamage } from "../../../utils/defensiveUsage";
import { DEFAULT_DEFENSIVE_LAYERS } from "../../../config/defensiveChartLayers";

function LegendItem({ label, detail, marker, checked, onChange }) {
  const Tag = onChange ? "label" : "span";
  return <Tag className={`defensive-graph-key-item${onChange ? " is-filter" : ""}${checked === false ? " is-off" : ""}`}>
    {onChange && <input type="checkbox" aria-label={label} checked={checked} onChange={(event) => onChange(event.target.checked)} />}
    {marker}<span><strong>{label}</strong><small>{detail}</small></span>
  </Tag>;
}

export function DamageLegend({ points, visiblePoints = points, maximum, extraPeaks = false, allMitigation = false, health = false, healthInLanes = false, layers = DEFAULT_DEFENSIVE_LAYERS, onLayerChange }) {
  const has = (value) => points.some((point) => value(point) > 0);
  const change = (key) => onLayerChange ? (checked) => onLayerChange(key, checked) : undefined;
  const items = [
    { key: "damage", show: has((p) => p.damage), color: "taken", label: "Damage to health", detail: "Actually taken" },
    { key: allMitigation ? "shields" : "cooldownShields", show: has((p) => allMitigation ? p.absorbed : p.cooldownAbsorbed), color: "absorbed",
      label: allMitigation ? "Absorbed by all shields" : "Absorbed by cooldowns", detail: "Measured in the log" },
    { key: "otherShields", show: !allMitigation && has((p) => (p.absorbed || 0) - (p.cooldownAbsorbed || 0)), color: "other",
      label: "Absorbed by other shields", detail: "Not credited to tracked cooldowns" },
    { key: "reduction", show: has((p) => p.mitigated), color: "mitigated",
      label: allMitigation ? "All damage reduction" : "Prevented by cooldowns",
      detail: allMitigation ? "Includes armor and passives" : "Estimated · supported effects only" },
  ].filter((item) => item.show);
  return <div className="defensive-graph-key" role="group" aria-label="Damage graph legend">
    <div className="defensive-graph-key-items">
      {health && <LegendItem label="Player health" detail={`${healthInLanes ? "Player lanes · " : ""}100% top, 0% bottom`}
        marker={<i className="defensive-health-swatch" aria-hidden="true" />} checked={layers.health} onChange={change("health")} />}
      {items.map(({ key, color, label, detail }) => <LegendItem key={key} label={label} detail={detail}
        marker={<i className={`defensive-graph-swatch damage-${color}`} aria-hidden="true" />}
        checked={layers[key]} onChange={change(key)} />)}
      {has((p) => p.immuneEvents) && <LegendItem label="Immune hit" detail="Prevented amount unknown"
        marker={<b className="damage-immune" aria-hidden="true">╹</b>} checked={layers.immune} onChange={change("immune")} />}
      {(extraPeaks || visiblePoints.some((p) => incomingDamage(p) > maximum)) && <LegendItem label="Peak above scale" detail="Full height is clipped"
        marker={<b aria-hidden="true">⌃</b>} checked={layers.peaks} onChange={change("peaks")} />}
    </div>
    <p>{items.length ? "Colours stack from bottom to top · damage per second in 2-second intervals." : "No damage recorded in this graph."}</p>
  </div>;
}
