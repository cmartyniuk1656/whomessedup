/** Stack recorded damage outcomes; immunity counts never invent damage amounts. */
import { coverageTime } from "../../../utils/coverageTimeline";

import { incomingDamage } from "../../../utils/defensiveUsage";

const exact = (value) => (value || 0).toLocaleString("en-US", { maximumFractionDigits: 2 });

export function PersonalDamageGraph({ points, duration, maximum, onTime, scope = "Personal" }) {
  const cooldownMode = points[0]?.cooldownMode;
  const layers = [
    { field: "mitigated", color: "#6ee7a0", value: incomingDamage },
    { field: "absorbed", color: cooldownMode ? "#718096" : "#67d6f4", value: (p) => p.damage + (p.absorbed || 0) },
    ...(cooldownMode ? [{ field: "cooldownAbsorbed", color: "#67d6f4", value: (p) => p.damage + (p.cooldownAbsorbed || 0) }] : []),
    { field: "damage", color: "#fb923c", value: (p) => p.damage },
  ];
  const path = (value) => `M0,100 ${points.map((p) => {
    const y = 100 - Math.min(1, value(p) / maximum) * 94;
    return `L${p.time / duration * 1000},${y} L${Math.min(duration, p.time + 2) / duration * 1000},${y}`;
  }).join(" ")} L1000,100 Z`;
  return <svg className="coverage-pressure-graph defensive-damage-graph" viewBox="0 0 1000 100" preserveAspectRatio="none"
    role="img" aria-label={`${scope} damage taken, absorbed and mitigated; immune hits marked separately`}
    onPointerMove={onTime ? (e) => { const rect = e.currentTarget.getBoundingClientRect(); onTime(Math.max(0, Math.min(duration, (e.clientX - rect.left) / rect.width * duration))); } : undefined}>
    {layers.map(({ field, color, value }) => <path key={field} data-damage-layer={field} d={path(value)} fill={color} fillOpacity=".32" stroke={color} strokeWidth="1" vectorEffect="non-scaling-stroke" />)}
    {points.filter((p) => incomingDamage(p) > maximum).map((p) => {
      const x = (p.time + Math.min(2, duration - p.time) / 2) / duration * 1000;
      return <path className="defensive-overflow" key={p.time} d={`M${x - 3},7 L${x},1 L${x + 3},7`} fill="none" stroke="#f8fafc" strokeWidth="2" vectorEffect="non-scaling-stroke" />;
    })}
    {points.filter((p) => p.immuneEvents > 0).map((p) => <line key={p.time} x1={(p.time + Math.min(2, duration - p.time) / 2) / duration * 1000} x2={(p.time + Math.min(2, duration - p.time) / 2) / duration * 1000} y1="2" y2="9" stroke="#d8b4fe" strokeWidth="3" vectorEffect="non-scaling-stroke"><title>{coverageTime(p.time)}: {p.immuneEvents} immune hits · prevented amount unknown</title></line>)}
    {points.map((p) => <rect key={p.time} x={p.time / duration * 1000} y="0" width={Math.min(2, duration - p.time) / duration * 1000} height="100" fill="transparent"><title>{coverageTime(p.time)} · {exact(p.damage)}/s taken · {cooldownMode ? `${exact(p.cooldownAbsorbed)}/s matched CD shields · ${exact(p.absorbed - (p.cooldownAbsorbed || 0))}/s other shields` : `${exact(p.absorbed)}/s absorbed`} · {exact(p.mitigated)}/s {cooldownMode ? "estimated cooldown reduction" : "total mitigation"}{incomingDamage(p) > maximum ? ` · Above display scale: ${exact(incomingDamage(p))}/s total` : ""}{cooldownMode && p.cooldownSources?.length ? ` | Cooldowns: ${p.cooldownSources.join(", ")}` : ""}{p.immuneEvents ? ` · ${p.immuneEvents} immune hits (amount unknown)` : ""}</title></rect>)}
  </svg>;
}
