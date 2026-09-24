/** Subtle vertical bands preserve time alignment without duplicating the graph. */
import { memo } from "react";
export const PressureShading = memo(function PressureShading({ points, duration, maximum, binSeconds }) {
  if (!maximum) return null;
  return (
    <svg
      className="coverage-pressure-shading"
      viewBox="0 0 1000 1"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      {points.map((point) => (
        <rect
          key={point.time}
          x={(point.time / duration) * 1000}
          y="0"
          width={
            (Math.min(binSeconds, duration - point.time) / duration) * 1000
          }
          height="1"
          fill="#fb923c"
          opacity={
            Math.pow((point.damage + point.healAbsorbs) / maximum, 1.5) * 0.16
          }
        />
      ))}
    </svg>
  );
});
