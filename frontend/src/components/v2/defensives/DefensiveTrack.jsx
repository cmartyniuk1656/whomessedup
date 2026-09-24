/** Shared compact cast track for raid overview, individual abilities and pull rows. */
import { memo } from "react";
import { Fragment } from "react";
import { defensiveRecovery } from "../../../utils/defensiveUsage";
import { useTimelineTrackWidth } from "../../../hooks/useTimelineTrackWidth";
import { preciseCoverageTime } from "../../../utils/coverageTimeline";

export const DefensiveTrack = memo(function DefensiveTrack({ casts, duration, onInspect, offset = 0, start = 0, end = duration, showReady = false }) {
  const { track, width } = useTimelineTrackWidth();
  const span = Math.max(.001, end - start);
  const positions = [];
  const placed = casts.map((cast) => {
    const position = (cast.event.time - offset - start) / span;
    const pixel = position * width;
    const recovery = showReady ? defensiveRecovery(cast) : null;
    let row = positions.findIndex((right) => right + 3 <= pixel);
    if (row < 0) row = positions.length;
    positions[row] = pixel + Math.max(24, ((Math.max(cast.event.end, recovery?.end || 0) - cast.event.time) / span) * width + (recovery?.marker ? 8 : 0));
    return { cast, position, row, recovery };
  });
  return <div ref={track} className="defensive-track" style={{ minHeight: Math.max(48, positions.length * 27 + 12) }}>
    {!casts.length && <span className="coverage-unused">No recorded uses</span>}
    {placed.map(({ cast, position, row, recovery }, i) => <Fragment key={`${cast.lane.id}:${cast.event.time}:${i}`}>
      {recovery && recovery.end > recovery.start && <span className="coverage-recovery defensive-recovery" aria-hidden="true"
        style={{ left: `${(recovery.start - offset - start) / span * 100}%`, width: `${(recovery.end - recovery.start) / span * 100}%`, top: 18 + row * 27 }} />}
      {recovery?.marker && <button className="coverage-ready defensive-ready"
        style={{ left: `clamp(6px, ${(cast.event.ready - offset - start) / span * 100}%, calc(100% - 6px))`, top: 6 + row * 27 }}
        title={`${cast.lane.name} · ${cast.event.readyBasis} ${preciseCoverageTime(cast.event.ready)}\n${cast.event.readyNote}`}
        aria-label={`${cast.player.name}: ${cast.lane.name} · ${cast.event.readyBasis} ${preciseCoverageTime(cast.event.ready)}`}
        onClick={() => onInspect({ defensive: cast })}>◇</button>}
      <button
      className={`defensive-cast is-${cast.lane.category} ${cast.event.durationBasis === "nominal" ? "is-nominal" : ""}`}
      style={{ left: `clamp(0px, ${position * 100}%, calc(100% - 24px))`, top: 6 + row * 27,
        width: `${Math.max(0, (cast.event.end - cast.event.time) / span) * 100}%` }}
      onClick={() => onInspect({ defensive: cast })}
      aria-label={`${cast.player.name}: ${cast.lane.name} at ${preciseCoverageTime(cast.event.time)}`}
      title={`${cast.lane.name} · ${preciseCoverageTime(cast.event.time)} · ${cast.event.durationBasis}${!cast.event.selfUse ? ` · on ${cast.event.target}` : ""}\n${cast.lane.description}${showReady && cast.event.readyNote ? `\n${cast.event.ready != null ? `${cast.event.readyBasis} ${preciseCoverageTime(cast.event.ready)} · ` : ""}${cast.event.readyNote}` : ""}`}>
      <img src={cast.lane.icon} alt="" width="22" height="22" />
      {!cast.event.selfUse && cast.event.targetId != null && !["raid", "group"].includes(cast.lane.category) && <span className="defensive-external-mark">↗</span>}
    </button></Fragment>)}
  </div>;
});
