/** Each attempt keeps its own damage and mechanic timings on a shared axis. */
import { memo, useMemo } from "react";
import { useReportViewState, useReportViewScroll } from "../../../hooks/useReportViewState";
import { aggregateRows, alignedTicks } from "../../../utils/defensiveUsage";
import { coverageTime } from "../../../utils/coverageTimeline";
import { damageScale, displayDamagePoints } from "../../../utils/defensiveUsage";
import { DamageLegend } from "./DamageLegend";
import { TimelineLegend } from "./TimelineLegend";
import { PlayerHealthOverlay } from "./PlayerHealthOverlay";
import { filterDamagePoints } from "../../../utils/defensiveChartLayers";
import { PersonalDamageGraph } from "./PersonalDamageGraph";
import { DefensiveTrack } from "./DefensiveTrack";
import { DefensiveBossFilters } from "./DefensiveBossFilters";

export const DefensiveAggregate = memo(function DefensiveAggregate({ layers, onLayerChange, entries, spellId, occurrence, onInspect, onOpenPull, allMitigation, bossIds, onBossIds }) {
  const scrollRef = useReportViewScroll("aggregate");
  const { health: showHealth } = layers;
  const [fullRange, setFullRange] = useReportViewState("aggregateScale", false);
  const rows = useMemo(() => aggregateRows(entries, spellId, occurrence), [entries, spellId, occurrence]);
  const rowPoints = useMemo(() => new Map(rows.map((row) => [row.pull.id, filterDamagePoints(displayDamagePoints(row.player.pressure, allMitigation), layers)])), [rows, allMitigation, layers]);
  const start = Math.min(0, ...rows.map((r) => -r.anchor));
  const end = Math.max(1, ...rows.map((r) => r.pull.duration - r.anchor));
  const duration = end - start;
  const sourcePoints = useMemo(() => displayDamagePoints(rows.flatMap((r) => r.player.pressure), allMitigation), [rows, allMitigation]);
  const points = useMemo(() => [...rowPoints.values()].flat(), [rowPoints]);
  const { maximum: peak, clipped } = damageScale(points, fullRange);
  const counts = new Map();
  entries.forEach(({ player }) => player.lanes.forEach((lane) => {
    const current = counts.get(lane.spellId) || { lane, uses: 0, pulls: 0 };
    current.uses += lane.events.length;
    current.pulls += Number(lane.events.length > 0);
    counts.set(lane.spellId, current);
  }));
  return <>
    <div className="coverage-controls"><label>Damage scale <select aria-label="Damage graph scale" value={fullRange ? "full" : "readable"} onChange={(e) => setFullRange(e.target.value === "full")}><option value="readable">Auto · readable peaks</option><option value="full">Full range</option></select></label>{clipped > 0 && <span className="defensive-muted">↑ {clipped} spikes above the shared scale · open a pull for exact values</span>}</div>
    <DefensiveBossFilters pulls={rows.map((row) => row.pull)} selectedIds={bossIds} onChange={onBossIds} />
    <div className="defensive-aggregate-intro"><strong>Every attempt, one player</strong><span>{rows.length} of {entries.length} pulls shown{entries.length !== rows.length ? ` · ${entries.length - rows.length} did not record this mechanic occurrence` : ""}. Personal damage, absorbs and mitigation use the same scale across pulls.</span></div>
    <div ref={scrollRef} className="coverage-scroll" tabIndex="0" role="region" aria-label="Defensive usage across pulls">
      <div className="coverage-canvas" style={{ minWidth: 1000 }}>
        <div className="coverage-axis"><div className="coverage-axis-label">{spellId ? "RELATIVE TO MECHANIC" : "TIME SINCE PULL"}</div><div className="coverage-axis-track">
          {alignedTicks(start, end).map((t) => <span key={t} style={{ left: `${(t - start) / duration * 100}%` }}>{t < 0 ? "−" : ""}{coverageTime(Math.abs(t))}</span>)}
        </div></div>
        {rows.length > 0 && <DamageLegend layers={layers} onLayerChange={onLayerChange} health={rows.some((row) => row.player.health?.length)} points={sourcePoints} visiblePoints={points} maximum={peak} allMitigation={allMitigation} />}
        <TimelineLegend showReady casts={rows.flatMap((row) => row.casts)} deaths={rows.flatMap((row) => row.player.deaths)} />
        {rows.map(({ pull, player, casts, anchor }) => <div className="coverage-row defensive-aggregate-row" key={pull.id}>
          <button className="coverage-lane-label" onClick={() => onOpenPull(pull.id)}><span><strong>{pull.label.split(" · ").slice(0, 3).join(" · ")}</strong><span>{casts.length} uses · {player.deaths.length} deaths{spellId ? ` · anchor ${coverageTime(anchor)}` : ""}</span></span><span>↗</span></button>
          <div className="defensive-aggregate-track">
            <div className="defensive-mini-pressure" style={{ left: `${(-anchor - start) / duration * 100}%`, width: `${pull.duration / duration * 100}%` }}><PersonalDamageGraph visibility={layers} points={rowPoints.get(pull.id)} duration={pull.duration} maximum={peak} /></div>
            {showHealth && <div className="defensive-health-aligned" style={{ left: `${(-anchor - start) / duration * 100}%`, width: `${pull.duration / duration * 100}%` }}><PlayerHealthOverlay points={player.health} duration={pull.duration} /></div>}
            <div className="defensive-pull-end" style={{ left: `${(pull.duration - anchor - start) / duration * 100}%` }} />
            {spellId && <div className="defensive-anchor-line" style={{ left: `${-start / duration * 100}%` }} />}
            <div className="defensive-mini-bosses">{pull.bossLanes.filter((l) => bossIds.includes(l.spellId)).flatMap((lane) => lane.events.map((event, i) => <button key={`${lane.id}:${i}`} style={{ left: `clamp(0px, ${(event.time - anchor - start) / duration * 100}%, calc(100% - 14px))` }} onClick={() => onInspect({ lane, event })} title={`${lane.name} #${i + 1} · ${coverageTime(event.time)}`} aria-label={`${pull.label}: ${lane.name} at ${coverageTime(event.time)}`}><img src={lane.icon} width="14" height="14" alt="" /></button>))}</div>
            <DefensiveTrack showReady casts={casts} duration={pull.duration} offset={anchor} start={start} end={end} onInspect={onInspect} />
            <div className="defensive-mini-deaths">{player.deaths.map((death, i) => <button key={i} style={{ left: `clamp(0px, ${(death.time - anchor - start) / duration * 100}%, calc(100% - 14px))` }} onClick={() => onInspect({ deaths: [death] })} title={`${player.name} died at ${coverageTime(death.time)}`} aria-label={`Death in ${pull.label} at ${coverageTime(death.time)}`}>×</button>)}</div>
          </div>
        </div>)}
        {!rows.length && <p className="coverage-empty">No pulls recorded this mechanic occurrence. Choose another occurrence or align to pull start.</p>}
      </div>
    </div>
    <div className="defensive-summary-grid">{[...counts.values()].sort((a, b) => b.uses - a.uses).map(({ lane, uses, pulls }) => <div key={lane.spellId} title={lane.description}>
      <img src={lane.icon} alt="" width="28" height="28" /><span><strong>{lane.name}</strong><small>{pulls}/{entries.length} pulls with a recorded use</small></span><b>{uses}</b>
    </div>)}</div>
  </>;
});
