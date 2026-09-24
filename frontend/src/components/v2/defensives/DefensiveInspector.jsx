/** Compact evidence drawer; recorded damage isn't a mitigation effectiveness score. */
import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { CooldownContribution } from "./CooldownContribution";
import { CoverageInspector } from "../coverage/CoverageInspector";
import { compactCoverageNumber as compact, coverageTime } from "../../../utils/coverageTimeline";

export function DefensiveInspector({ selection, onInspect }) {
  const drawer = useRef(null);
  useEffect(() => {
    if (!selection?.defensive && !selection?.review) return;
    const previousFocus = document.activeElement;
    drawer.current?.focus({ preventScroll: true });
    const key = (event) => { if (event.key === "Escape") onInspect(null); };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true });
    };
  }, [selection, onInspect]);
  const cast = selection?.defensive;
  const review = selection?.review;
  const protection = cast?.event.protection;
  if (!selection) return null;
  if (!cast && !review) return createPortal(<CoverageInspector selection={selection} onInspect={onInspect} onClose={() => onInspect(null)} />, document.body);
  const { player, pull } = cast || review;
  return createPortal(<aside ref={drawer} tabIndex={-1} className="coverage-inspector coverage-inspector-drawer defensive-inspector" aria-label="Defensive usage details">
    <button className="coverage-close" onClick={() => onInspect(null)} aria-label="Close defensive details">×</button>
    <p className="defensive-eyebrow">{player.name} · {player.spec}</p>
    {cast ? <>
      <h3><img src={cast.lane.icon} alt="" width="32" height="32" />{cast.lane.name}</h3>
      <p>{coverageTime(cast.event.time)} · {["raid", "group"].includes(cast.lane.category) ? "Raid / group cast" : cast.event.selfUse ? "Personal use" : `On ${cast.event.target}`}</p>
      <p>{cast.lane.description}</p>
      {cast.event.end > cast.event.time && <p className="defensive-muted">Duration: {cast.event.durationBasis === "observed aura" ? "" : "≈ "}{(cast.event.end - cast.event.time).toFixed(1)}s</p>}
      <CooldownContribution event={cast.event} />
      {cast.event.ready != null && <p className="defensive-muted">{cast.lane.readiness?.charges > 1 ? "Charge returns" : "Ready again"} · ≈ {coverageTime(cast.event.ready)}</p>}
      {protection?.immuneEvents > 0 && <p className="defensive-muted">{protection.immuneEvents} immune {protection.immuneEvents === 1 ? "hit" : "hits"} during this window</p>}
      {(cast.event.effectiveHealing > 0 || cast.event.overhealing > 0) && <>
        <div className="defensive-heal-bar" aria-label="Effective healing versus overhealing"><i style={{ width: `${100 * cast.event.effectiveHealing / (cast.event.effectiveHealing + cast.event.overhealing)}%` }} /></div>
        <p><span className="coverage-key-window">{compact(cast.event.effectiveHealing)} effective healing</span> · {compact(cast.event.overhealing)} overhealing</p>
      </>}
      {cast.event.nearbyBoss && <p className="defensive-boss-context">{Math.abs(cast.event.nearbyBoss.delta).toFixed(1)}s {cast.event.nearbyBoss.delta < 0 ? "before" : "after"} <strong>{cast.event.nearbyBoss.name}</strong></p>}

    </> : <>
      <h3>Pressure to review · {coverageTime(review.point.time)}</h3>
      <p>{compact(review.point.damage)}/s with no tracked personal defensive window.</p>
      <ul>{review.point.sources.map((source) => <li key={source.name}>{source.name} · {compact(source.amount)}/s</li>)}</ul>
      <p className="defensive-muted">A review prompt, not a missed-use verdict. Availability, damage school, assignments and external protection still matter.</p>
    </>}
    <a href={`${pull.url}&source=${player.actorId}`} target="_blank" rel="noreferrer">Inspect player in Warcraft Logs ↗</a>
  </aside>, document.body);
}
