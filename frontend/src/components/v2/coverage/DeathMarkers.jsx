/** A compact raid-wide death track stays visible when pressure is hidden. */
import { useTimelineTrackWidth } from "../../../hooks/useTimelineTrackWidth";
import { useTimelineTooltip } from "../../../hooks/useTimelineTooltip";
import { createPortal } from "react-dom";
import { DeathRecap } from "./DeathRecap";
import {
  clusterTimelineEvents,
  preciseCoverageTime,
} from "../../../utils/coverageTimeline";

function DeathMarker({ group, duration, onInspect }) {
  const tooltip = useTimelineTooltip();
  const first = group[0].event;
  const label = group.map(({ event }) => `${event.player} died at ${preciseCoverageTime(event.time)}`).join("\n");
  return <>
    <button ref={tooltip.anchor} {...tooltip.triggerProps} type="button"
      className="coverage-death-marker"
      style={{ left: `clamp(10px, ${(first.time / duration) * 100}%, calc(100% - 10px))` }}
      aria-label={label}
      onClick={() => { tooltip.hide(); onInspect({ deaths: group.map(({ event }) => event) }); }}>
      <svg aria-hidden="true" width="13" height="13" viewBox="0 0 16 16" fill="none">
        <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      {group.length > 1 && <small>{group.length}</small>}
    </button>
    {tooltip.open && createPortal(
      <div ref={tooltip.popup} {...tooltip.popupProps} id={tooltip.id} role="tooltip"
        className="coverage-death-tooltip" style={tooltip.position}>
        <DeathRecap death={first} compact />
        {group.length > 1 && <p className="coverage-death-cluster-note">
          Also: {group.slice(1, 4).map(({ event }) => event.player).join(", ")}
          {group.length > 4 ? ` +${group.length - 4} more` : ""}
        </p>}
        <p className="coverage-death-tooltip-hint">Click to inspect {group.length > 1 ? "all deaths" : "the full recap"}</p>
      </div>, document.body,
    )}
  </>;
}

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
        {groups.map((group) => <DeathMarker key={`${group[0].event.playerId}:${group[0].event.time}`}
          group={group} duration={duration} onInspect={onInspect} />)}
      </div>
    </div>
  );
}
