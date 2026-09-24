/** Share references to recorded events, never copies of log data or descriptions. */
import { useCallback, useMemo } from "react";
import { useReportViewState } from "./useReportViewState";

const eventIndex = (events, event) => events.indexOf(event);

function reference(selection, pulls) {
  if (!selection) return null;
  if (selection.coverage) return { type: "coverage", time: selection.coverage.start };
  if (selection.bossGroup) return { type: "bossGroup", events: selection.bossGroup.map((cast) => reference(cast, pulls)) };
  const deathPull = selection.deaths && pulls.find((pull) => selection.deaths.every((death) =>
    pull.deaths.includes(death) || pull.players?.some((player) => player.deaths.includes(death))));
  for (const pull of deathPull ? [deathPull] : pulls) {
    const deathIndex = (death) => pull.deaths.findIndex((item) => item === death || (item.time === death.time && item.playerId === death.playerId && item.player === death.player));
    if (selection.deaths && selection.deaths.every((death) => deathIndex(death) >= 0)) {
      return { type: "deaths", pull: pull.id, indices: selection.deaths.map(deathIndex) };
    }
    const cast = selection.defensive;
    const review = selection.review;
    if (cast?.pull.id === pull.id) return { type: "defensive", pull: pull.id, player: cast.player.id, lane: cast.lane.id, event: eventIndex(cast.lane.events, cast.event), time: cast.event.time, target: cast.event.targetId };
    if (review?.pull.id === pull.id) return { type: "review", pull: pull.id, player: review.player.id, time: review.point.time };
    const lane = (pull.lanes || pull.bossLanes || []).find((item) => item.id === selection.lane?.id && item.events.includes(selection.event));
    if (lane) return { type: "event", pull: pull.id, lane: lane.id, event: eventIndex(lane.events, selection.event), time: selection.event.time };
  }
  return null;
}

function resolve(ref, pulls, segments) {
  if (!ref || typeof ref !== "object") return null;
  if (ref.type === "coverage") {
    const coverage = segments?.find((segment) => segment.start === ref.time);
    return coverage ? { coverage } : null;
  }
  if (ref.type === "bossGroup") {
    // Groups contain event references only, so hostile fragments cannot recurse.
    const bossGroup = Array.isArray(ref.events) ? ref.events.filter((item) => item?.type === "event").map((item) => resolve(item, pulls)).filter(Boolean) : [];
    return bossGroup.length ? { bossGroup } : null;
  }
  const pull = pulls.find((item) => item.id === ref.pull);
  if (!pull) return null;
  if (ref.type === "deaths") {
    const deaths = Array.isArray(ref.indices) ? ref.indices.filter(Number.isInteger).map((index) => pull.deaths[index]).filter(Boolean) : [];
    return deaths.length ? { deaths } : null;
  }
  const player = pull.players?.find((item) => item.id === ref.player);
  if (ref.type === "review") {
    const point = player?.pressure.find((item) => item.time === ref.time);
    return point ? { review: { point, player, pull } } : null;
  }
  const lane = (ref.type === "defensive" ? player?.lanes : pull.lanes || pull.bossLanes)?.find((item) => item.id === ref.lane);
  const indexed = Number.isInteger(ref.event) ? lane?.events[ref.event] : null;
  const matches = (event) => event && event.time === ref.time && (ref.target === undefined || event.targetId === ref.target);
  const event = ref.time === undefined || matches(indexed) ? indexed : lane?.events.find(matches);
  if (!event) return null;
  return ref.type === "defensive" ? { defensive: { lane, event, player, pull } } : { lane, event };
}

export function useTimelineSelection(pulls, segments, resetKey = "") {
  const [ref, setRef] = useReportViewState("selection", null, { resetKey });
  const selection = useMemo(() => resolve(ref, pulls, segments), [ref, pulls, segments]);
  const inspect = useCallback((next) => setRef(reference(next, pulls)), [pulls, setRef]);
  return [selection, inspect];
}
