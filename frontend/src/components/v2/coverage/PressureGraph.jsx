/** A shared scale aligns pressure with every lane below it. */
import { pressurePath } from "../../../utils/coverageTimeline";

export function PressureGraph({ points, duration, maximum }) {
  return (
    <svg
      className="coverage-pressure-graph"
      viewBox="0 0 1000 100"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d={pressurePath(points, duration, maximum)}
        fill="rgba(251,146,60,.20)"
        stroke="#fb923c"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
      <path
        d={pressurePath(points, duration, maximum, "healAbsorbs")}
        fill="rgba(192,132,252,.26)"
        stroke="#c084fc"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
