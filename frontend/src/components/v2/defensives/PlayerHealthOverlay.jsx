/** Overlay recorded health on a fixed percentage axis, never the damage scale. */
import { memo } from "react";
export const PlayerHealthOverlay = memo(function PlayerHealthOverlay({ points = [], duration }) {
  if (!points.length) return null;
  const path = points.map((point, index) => `${!index || point.breakBefore ? "M" : "L"}${point.time / duration * 1000},${99 - point.percent * .98}`).join(" ");
  return <div className="defensive-health-overlay">
    <svg viewBox="0 0 1000 100" preserveAspectRatio="none" role="img" aria-label="Player health: 100% at the top, 0% at the bottom">
      <path d={path} fill="none" stroke="#0c1622" strokeWidth="2.5" strokeOpacity=".35" vectorEffect="non-scaling-stroke" />
      <path data-health-line="true" d={path} fill="none" stroke="#ff6374" strokeWidth="1.4" strokeOpacity=".6" vectorEffect="non-scaling-stroke" />
    </svg>
    <span className="defensive-health-max">100%</span><span className="defensive-health-min">0%</span>
  </div>;
});

