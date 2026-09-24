/** Cursor movement updates only this readout, leaving all SVG tracks untouched. */
import { forwardRef, useImperativeHandle } from "react";
import { useReportViewState } from "../../../hooks/useReportViewState";
import { healthAtTime } from "../../../utils/playerHealth";
import { coverageTime, compactCoverageNumber as compact } from "../../../utils/coverageTimeline";

export const DefensiveTimeReadout = forwardRef(function DefensiveTimeReadout({ pull, player, playerId, sourcePoints, allMitigation, showHealth }, ref) {
  const [cursor, setCursor] = useReportViewState("cursor", 0, { resetKey: `${pull.id}:${playerId}`, validate: (value) => value >= 0 && value <= pull.duration });
  useImperativeHandle(ref, () => ({ setCursor }), [setCursor]);
  const healthAtCursor = healthAtTime(player?.health, cursor);
  const bucket = sourcePoints[Math.min(sourcePoints.length - 1, Math.floor(cursor / 2))];
  return (
    <div className="coverage-pressure-readout">{showHealth && player && <span className="defensive-health-readout">{healthAtCursor !== null ? `Health ≈ ${healthAtCursor.toFixed(1)}%` : "No health snapshot near this time"}</span>}<label>Inspect time <input aria-label="Inspect defensive timeline time" type="range" min="0" max={pull.duration} step="1" value={cursor} onChange={(e) => setCursor(Number(e.target.value))} /><b>{coverageTime(cursor)}</b></label>
      <span><span className="damage-taken">{compact(bucket?.damage)}/s taken</span> · <span className="damage-absorbed">{allMitigation ? `${compact(bucket?.absorbed)}/s absorbed` : `${compact(bucket?.cooldownAbsorbed)}/s CD shields`}</span>{!allMitigation && <span className="damage-other"> · {compact((bucket?.absorbed || 0) - (bucket?.cooldownAbsorbed || 0))}/s other shields</span>} · <span className="damage-mitigated">{compact(bucket?.mitigated)}/s {allMitigation ? "all mitigation" : "estimated CD reduction"}</span>{bucket?.immuneEvents > 0 && <span className="damage-immune"> · {bucket.immuneEvents} immune hits (amount unknown)</span>}{bucket?.healAbsorbs > 0 && <span> · {compact(bucket.healAbsorbs)}/s healing absorbed separately</span>}</span>
      <div className="coverage-sources">{bucket?.sources.map((s) => <span key={s.name}>{s.name} <b>{allMitigation ? `${compact(s.amount)}/s` : ""}{s.immuneEvents > 0 ? ` · ${s.immuneEvents} immune` : ""}</b></span>)}</div>
      {!allMitigation && bucket?.cooldownSources?.length > 0 && <div className="coverage-sources">Protection: {bucket.cooldownSources.map((name) => <span key={name}>{name}</span>)}</div>}
    </div>
  );
});
