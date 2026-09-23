/** Own timeline filters and selection; coverage always considers every healer. */
import { useMemo, useState } from "react";
import { coverageSegments, timelineTicks } from "../utils/coverageTimeline";

export function useCoverageTimeline(pull, binSeconds) {
  const [overlay, setOverlay] = useState(true);
  const [showReady, setShowReady] = useState(true);
  const [healer, setHealer] = useState("all");
  const [zoom, setZoom] = useState(1);
  const [cursor, setCursor] = useState(0);
  const [selection, setSelection] = useState(null);
  const bossLanes = pull.lanes.filter((lane) => lane.kind === "boss");
  const [bossIds, setBossIds] = useState(() =>
    bossLanes.filter((lane) => lane.shownByDefault).map((lane) => lane.id),
  );
  const healerLanes = pull.lanes.filter((lane) => lane.kind === "healer");
  const segments = useMemo(
    () => coverageSegments(pull, binSeconds),
    [pull, binSeconds],
  );
  const inspect = (next) => {
    setSelection(next);
    if (next?.event) setCursor(next.event.time);
    if (next?.coverage) setCursor(next.coverage.start);
    if (next?.deaths?.length) setCursor(next.deaths[0].time);
  };
  const toggleBoss = (id) =>
    setBossIds((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : [...current, id],
    );
  const updateCursor = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setCursor(
      Math.max(
        0,
        Math.min(
          pull.duration,
          ((event.clientX - rect.left - 232) / (rect.width - 232)) *
            pull.duration,
        ),
      ),
    );
  };
  return {
    overlay,
    setOverlay,
    showReady,
    setShowReady,
    healer,
    setHealer,
    zoom,
    setZoom,
    cursor,
    setCursor,
    selection,
    inspect,
    bossLanes,
    bossIds,
    setBossIds,
    toggleBoss,
    segments,
    visibleBossLanes: bossLanes.filter((lane) => bossIds.includes(lane.id)),
    healerLanes: healerLanes.filter(
      (lane) => healer === "all" || lane.player === healer,
    ),
    healers: [...new Set(healerLanes.map((lane) => lane.player))].sort(),
    maximum: Math.max(0, ...pull.pressure.map((p) => p.damage + p.healAbsorbs)),
    casts: healerLanes.reduce(
      (sum, lane) =>
        sum + lane.events.filter((event) => event.label !== "Store").length,
      0,
    ),
    bucket:
      pull.pressure[
        Math.min(pull.pressure.length - 1, Math.floor(cursor / binSeconds))
      ],
    ticks: timelineTicks(pull.duration),
    updateCursor,
  };
}
