/** Count tracked sustained windows; instant/unknown effects stay distinct. */
import { coverageTime } from "../../../utils/coverageTimeline";

export function RaidCoverageStrip({ segments, duration, onInspect }) {
  return (
    <div className="coverage-row coverage-strip-row">
      <div className="coverage-lane-label">
        <span>
          <strong>Raid coverage</strong>
          <span>All healers · tracked windows</span>
        </span>
      </div>
      <div className="coverage-strip-track" aria-label="Raid coverage strip">
        {segments.map((segment) => {
          const detail = segment.active.length
            ? `${segment.active.length} active windows`
            : segment.bursts.length
              ? "Instant or unknown-duration cast nearby"
              : "No sustained tracked window";
          const title = `${coverageTime(segment.start)}–${coverageTime(segment.end)} · ${detail}${segment.potentialGap ? " · high pressure: review this interval" : ""}`;
          return (
            <button
              key={segment.start}
              title={title}
              aria-label={title}
              className={`coverage-strip-segment ${segment.potentialGap ? "coverage-strip-gap" : segment.bursts.length && !segment.active.length ? "coverage-strip-burst" : ""}`}
              style={{
                left: `${(segment.start / duration) * 100}%`,
                width: `${((segment.end - segment.start) / duration) * 100}%`,
                backgroundColor: segment.active.length
                  ? `rgba(52,211,153,${Math.min(0.7, 0.2 + segment.active.length * 0.14)})`
                  : undefined,
              }}
              onClick={() => onInspect({ coverage: segment })}
            />
          );
        })}
      </div>
    </div>
  );
}
