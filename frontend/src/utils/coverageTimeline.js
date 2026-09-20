/** Shared time/geometry helpers for the pull-relative coverage view. */
export function coverageTime(value) {
  const seconds = Math.max(0, Math.round(value || 0));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export function preciseCoverageTime(value) {
  const seconds = Math.max(0, value || 0);
  return `${Math.floor(seconds / 60)}:${(seconds % 60).toFixed(3).padStart(6, "0")}`;
}

export function pressurePath(points, duration, maximum, field = "total") {
  if (!points.length || !maximum) return "";
  const coordinates = points.map((point) => {
    const value =
      field === "total" ? point.damage + point.healAbsorbs : point[field];
    return `${(point.time / duration) * 1000},${100 - (value / maximum) * 94}`;
  });
  return `M0,100 L${coordinates.join(" L")} L1000,100 Z`;
}

export function timelineTicks(duration) {
  const interval =
    duration > 600 ? 60 : duration > 240 ? 30 : duration > 90 ? 15 : 5;
  return Array.from(
    { length: Math.floor(duration / interval) + 1 },
    (_, i) => i * interval,
  );
}

/** Coverage uses the whole raid, independent of lane visibility filters. */
export function coverageSegments(pull, binSeconds) {
  const windows = [];
  const bursts = [];
  const edges = new Set([0, pull.duration]);
  for (let time = binSeconds; time < pull.duration; time += binSeconds)
    edges.add(time);
  for (const lane of pull.lanes.filter((entry) => entry.kind === "healer")) {
    for (const event of lane.events) {
      if (event.label === "Store") continue;
      const cast = { lane, event };
      if (event.end != null && event.end > event.time) {
        windows.push(cast);
        edges.add(event.time);
        edges.add(event.end);
      } else bursts.push(cast);
    }
  }
  for (const point of pull.pressure) edges.add(point.time);
  const levels = pull.pressure
    .map((p) => p.damage + p.healAbsorbs)
    .filter((p) => p > 0)
    .sort((a, b) => a - b);
  const highThreshold = levels.length
    ? levels[Math.floor((levels.length - 1) * 0.75)]
    : Infinity;
  const times = [...edges]
    .filter((time) => time >= 0 && time <= pull.duration)
    .sort((a, b) => a - b);
  return times.slice(0, -1).map((start, index) => {
    const end = times[index + 1];
    const point =
      pull.pressure[
        Math.min(pull.pressure.length - 1, Math.floor(start / binSeconds))
      ];
    const pressure = (point?.damage || 0) + (point?.healAbsorbs || 0);
    const active = windows.filter(
      ({ event }) => event.time < end && event.end > start,
    );
    const nearby = bursts.filter(
      ({ event }) =>
        Math.floor(event.time / binSeconds) === Math.floor(start / binSeconds),
    );
    return {
      start,
      end,
      active,
      bursts: nearby,
      pressure,
      highPressure: pressure > 0 && pressure >= highThreshold,
      potentialGap:
        pressure > 0 &&
        pressure >= highThreshold &&
        !active.length &&
        !nearby.length,
    };
  });
}

/** Cluster crowded boss icons without moving or changing recorded timestamps. */
export function clusterBossCasts(lanes, duration, trackWidth) {
  const casts = lanes
    .flatMap((lane) => lane.events.map((event) => ({ lane, event })))
    .sort((a, b) => a.event.time - b.event.time);
  const groups = [];
  const spacing = (28 * duration) / Math.max(1, trackWidth);
  for (const cast of casts) {
    const last = groups[groups.length - 1];
    if (last && cast.event.time - last[0].event.time < spacing) last.push(cast);
    else groups.push([cast]);
  }
  return groups;
}

export function compactCoverageNumber(value) {
  return new Intl.NumberFormat("en", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value || 0);
}
