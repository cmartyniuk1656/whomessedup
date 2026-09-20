/** One boss lane. Crowded casts open a chooser with their exact timestamps. */
import { useEffect, useRef, useState } from "react";
import {
  clusterBossCasts,
  preciseCoverageTime,
} from "../../../utils/coverageTimeline";

export function BossAbilityLane({ lanes, duration, onInspect }) {
  const track = useRef(null);
  const [width, setWidth] = useState(1000);
  useEffect(() => {
    if (!globalThis.ResizeObserver) return;
    const observer = new ResizeObserver(([entry]) =>
      setWidth(entry.contentRect.width || 1000),
    );
    observer.observe(track.current);
    return () => observer.disconnect();
  }, []);
  const groups = clusterBossCasts(lanes, duration, width);
  return (
    <div className="coverage-row coverage-row-boss">
      <div className="coverage-lane-label">
        <span>
          <strong>Boss abilities</strong>
          <span>
            Recorded casts · {groups.reduce((n, group) => n + group.length, 0)}{" "}
            events
          </span>
        </span>
      </div>
      <div className="coverage-lane-track" ref={track}>
        {!groups.length && (
          <span className="coverage-unused">
            No boss abilities selected or recorded
          </span>
        )}
        {groups.map((group, index) => {
          const { lane, event } = group[0];
          const label =
            group.length === 1
              ? `Boss · ${lane.name} at ${preciseCoverageTime(event.time)}`
              : `${group.length} boss casts near ${preciseCoverageTime(event.time)}`;
          return (
            <button
              key={index}
              className="coverage-cast coverage-boss-cast"
              aria-label={label}
              title={group
                .map(
                  ({ lane: ability, event: cast }) =>
                    `${ability.name} at ${preciseCoverageTime(cast.time)} — ${ability.description}`,
                )
                .join("\n")}
              style={{ left: `${(event.time / duration) * 100}%` }}
              onClick={() =>
                onInspect(group.length === 1 ? group[0] : { bossGroup: group })
              }
            >
              <img src={lane.icon} alt="" width="22" height="22" />
              {group.length > 1 && (
                <span className="coverage-cluster-count">{group.length}</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
