/** One ability lane, with accessible cast buttons and estimated recovery marks. */
import {
  coverageTime,
  preciseCoverageTime,
} from "../../../utils/coverageTimeline";

export function CoverageLane({
  lane,
  duration,
  showReady,
  onInspect,
  selectedEvent,
}) {
  const percent = (time) =>
    `${(100 * Math.min(duration, Math.max(0, time))) / duration}%`;
  return (
    <div className={`coverage-row coverage-row-${lane.kind}`}>
      <button
        className="coverage-lane-label"
        onClick={() => onInspect({ lane })}
        title={lane.description}
      >
        <img src={lane.icon} alt="" width="28" height="28" />
        <span>
          <strong>{lane.player || "Boss"}</strong>
          <span>{lane.name}</span>
        </span>
        <small>{lane.events.length}</small>
      </button>
      <div className="coverage-lane-track">
        {!lane.events.length && (
          <span className="coverage-unused">Talented · not used this pull</span>
        )}
        {lane.events.map((event, index) => {
          const end = event.end ?? event.time;
          const ready = event.ready;
          const title = `${lane.player || "Boss"} · ${lane.name}${event.label ? ` (${event.label})` : ""} at ${preciseCoverageTime(event.time)}${lane.kind === "healer" ? ` · ${event.durationBasis} window${ready != null ? ` · estimated ready ${coverageTime(ready)}` : ""}` : ""}`;
          return (
            <span key={`${event.time}:${index}`}>
              {showReady && ready != null && ready > end && (
                <span
                  className="coverage-recovery"
                  style={{
                    left: percent(end),
                    width: percent(Math.min(ready, duration) - end),
                  }}
                />
              )}
              {showReady && ready != null && ready <= duration && (
                <button
                  className="coverage-ready"
                  style={{ left: percent(ready) }}
                  title={`${event.readyBasis || "Estimated ready"} ${coverageTime(ready)}`}
                  aria-label={`${lane.name}: ${event.readyBasis || "estimated ready"} ${coverageTime(ready)}`}
                  onClick={() => onInspect({ lane, event })}
                >
                  ◇
                </button>
              )}
              <button
                className={`coverage-cast ${selectedEvent === event ? "coverage-cast-selected" : ""}`}
                style={{
                  left: percent(event.time),
                  width: percent(end - event.time),
                }}
                title={title}
                aria-label={title}
                aria-pressed={selectedEvent === event}
                onClick={() => onInspect({ lane, event })}
              >
                <img src={lane.icon} alt="" width="22" height="22" />
                {event.label && (
                  <span className="coverage-event-label">
                    {event.label === "Release" ? "R" : "S"}
                  </span>
                )}
              </button>
            </span>
          );
        })}
      </div>
    </div>
  );
}
