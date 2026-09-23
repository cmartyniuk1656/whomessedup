/** A compact raid-wide death track stays visible when pressure is hidden. */
import { useTimelineTrackWidth } from "../../../hooks/useTimelineTrackWidth";
import {
  clusterTimelineEvents,
  preciseCoverageTime,
} from "../../../utils/coverageTimeline";

export function DeathMarkers({ deaths, duration, onInspect }) {
  const { track, width } = useTimelineTrackWidth();
  const groups = clusterTimelineEvents(
    deaths.map((event) => ({ event })),
    duration,
    width,
    22,
  );
  return (
    <div className="coverage-row coverage-death-row">
      <div className="coverage-lane-label">
        <span>
          <strong>Deaths</strong>
        </span>
        <small>{deaths.length}</small>
      </div>
      <div ref={track} className="coverage-lane-track">
        {!deaths.length && (
          <span className="coverage-no-deaths">No player deaths</span>
        )}
        {groups.map((group) => {
          const first = group[0].event;
          const title = group
            .map(
              ({ event }) =>
                `${event.player} died at ${preciseCoverageTime(event.time)}`,
            )
            .join("\n");
          return (
            <button
              key={`${first.playerId}:${first.time}`}
              type="button"
              className="coverage-death-marker"
              style={{
                left: `clamp(10px, ${(first.time / duration) * 100}%, calc(100% - 10px))`,
              }}
              title={title}
              aria-label={title}
              onClick={() =>
                onInspect({ deaths: group.map(({ event }) => event) })
              }
            >
              <svg
                aria-hidden="true"
                width="13"
                height="13"
                viewBox="0 0 16 16"
                fill="none"
              >
                <path
                  d="M4 4l8 8M12 4l-8 8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              {group.length > 1 && <small>{group.length}</small>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
