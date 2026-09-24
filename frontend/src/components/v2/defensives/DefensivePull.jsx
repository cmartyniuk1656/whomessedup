/** One real pull: raid overview or one player's personal damage and ability lanes. */
import { useState } from "react";
import { DefensiveBossFilters } from "./DefensiveBossFilters";
import { BossAbilityLane } from "../coverage/BossAbilityLane";
import { incomingDamage, damageScale, displayDamagePoints } from "../../../utils/defensiveUsage";
import { DamageLegend } from "./DamageLegend";
import { TimelineLegend } from "./TimelineLegend";
import { PersonalDamageGraph } from "./PersonalDamageGraph";
import { PressureShading } from "../coverage/PressureShading";
import { DeathMarkers } from "../coverage/DeathMarkers";
import { DefensiveTrack } from "./DefensiveTrack";
import { DefensivePlayerControls, DefensivePlayerLabel, HiddenDefensivePlayers } from "./DefensivePlayerVisibility";
import { defensiveCasts, pressureReview } from "../../../utils/defensiveUsage";
import { timelineTicks, coverageTime, compactCoverageNumber as compact } from "../../../utils/coverageTimeline";

export function DefensivePull({ pull, playerId, onSelectPlayer, onInspect, allMitigation, showReady, onShowReady, bossIds, onBossIds, hiddenPlayerIds, onHiddenPlayerIds }) {
  const player = pull.players.find((p) => p.id === playerId);
  const [shading, setShading] = useState(true);
  const [fullRange, setFullRange] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [cursor, setCursor] = useState(0);
  const shownPlayers = pull.players.filter((p) => !hiddenPlayerIds.includes(p.id));
  const hiddenPlayers = pull.players.filter((p) => hiddenPlayerIds.includes(p.id));
  const points = displayDamagePoints(player ? player.pressure : pull.pressure, allMitigation);
  const { maximum, peak, clipped } = damageScale(points, fullRange);
  const everyoneScale = player ? maximum : damageScale(displayDamagePoints(shownPlayers.flatMap((p) => p.pressure), allMitigation), fullRange).maximum;
  const bucket = points[Math.min(points.length - 1, Math.floor(cursor / 2))];
  const rows = player ? player.lanes.map((lane) => ({ player, lane, casts: defensiveCasts({ ...player, lanes: [lane] }, pull) }))
    : shownPlayers.map((p) => ({ player: p, casts: defensiveCasts(p, pull) }));
  // Keep potion variants distinguishable on casts without several empty item rows.
  const potionRows = player ? rows.filter((row) => row.lane.category === "consumable" && /potion/i.test(row.lane.name)) : [];
  const visibleRows = rows.filter((row) => !potionRows.includes(row));
  if (potionRows.length) visibleRows.push({ player, lane: { ...potionRows[0].lane, id: "health-potions", name: "Health potions",
    description: potionRows.map((row) => row.lane.name).join(" · ") }, casts: potionRows.flatMap((row) => row.casts).sort((a, b) => a.event.time - b.event.time) });
  const review = player ? pressureReview(player, pull) : [];
  return <>
    <div className="coverage-controls"><label><input type="checkbox" checked={showReady} onChange={(e) => onShowReady(e.target.checked)} />Estimated readiness</label>
      <label>Damage scale <select aria-label="Damage graph scale" value={fullRange ? "full" : "readable"} onChange={(e) => setFullRange(e.target.value === "full")}><option value="readable">Auto · readable peaks</option><option value="full">Full range</option></select></label>
      {clipped > 0 && <span className="defensive-muted">↑ {clipped} spikes above scale · hover for exact values</span>}
      <label><input type="checkbox" checked={shading} onChange={(e) => setShading(e.target.checked)} />Pressure shading</label>
      <label>Zoom <input type="range" min="1" max="4" step=".5" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} /></label>
    </div>
    <DefensiveBossFilters pulls={[pull]} selectedIds={bossIds} onChange={onBossIds} />
    {!player && <DefensivePlayerControls players={pull.players} hiddenIds={hiddenPlayerIds} onChange={onHiddenPlayerIds} />}
    {review.length > 0 && <div className="defensive-review"><div><strong>Pressure to review</strong><span>Largest damage spikes without a tracked personal window · availability not inferred</span></div>
      {review.map((point) => <button key={point.time} onClick={() => { setCursor(point.time); onInspect({ review: { point, player, pull } }); }}>
        {coverageTime(point.time)} <b>{compact(point.damage)}/s</b>
      </button>)}</div>}
    <div className="coverage-scroll" tabIndex="0" role="region" aria-label="Defensive usage timeline">
      <div className="coverage-canvas" style={{ width: `${zoom * 100}%`, minWidth: 850 * zoom, "--defensive-key-width": `${100 / zoom}%` }}>
        <div className="coverage-axis"><div className="coverage-axis-label">{player ? player.name : "RAID DEFENSIVES"}</div><div className="coverage-axis-track">
          {timelineTicks(pull.duration).map((t) => <span key={t} style={{ left: `${t / pull.duration * 100}%` }}>{coverageTime(t)}</span>)}
        </div></div>
        <div className="coverage-pressure-row"><div className="coverage-pressure-label"><strong>{player ? `${player.name} · incoming damage` : "Raid incoming damage"}</strong><span>{compact(maximum)}/s scale{clipped > 0 ? ` · ${compact(peak)}/s peak ↑` : ""}</span><small>{allMitigation ? "Taken + shields + all mitigation" : "Taken + shields + estimated CD reduction"} · 2s bins</small></div><div className="coverage-graph-track"><PersonalDamageGraph points={points} maximum={maximum} duration={pull.duration} onTime={setCursor} scope={player ? "Personal" : "Raid"} /></div></div>
        <DamageLegend points={points} maximum={maximum} allMitigation={allMitigation} />
        <DeathMarkers deaths={player ? player.deaths : pull.deaths} duration={pull.duration} onInspect={onInspect} />
        <BossAbilityLane lanes={pull.bossLanes.filter((l) => bossIds.includes(l.spellId))} duration={pull.duration} onInspect={onInspect} />
        <TimelineLegend showReady={showReady} casts={visibleRows.flatMap((row) => row.casts)} deaths={player ? player.deaths : pull.deaths} />
        {visibleRows.map(({ player: rowPlayer, lane, casts }) => <div className="coverage-row defensive-row" key={lane?.id || rowPlayer.id}>
          {!player ? <DefensivePlayerLabel player={rowPlayer} casts={casts.length}
            onHide={() => onHiddenPlayerIds([...hiddenPlayerIds, rowPlayer.id])} onInspect={() => onSelectPlayer(rowPlayer.id)} />
          : <button className="coverage-lane-label" onClick={() => onSelectPlayer(rowPlayer.id)} title={lane ? `${lane.description}${showReady && lane.readiness ? `\n${lane.readiness.note}` : ""}` : `Inspect ${rowPlayer.name}`}>
            {lane && <img src={lane.icon} width="27" height="27" alt="" />}<span><strong>{lane?.name || rowPlayer.name}</strong><span>{lane ? lane.category.replaceAll("_", " ") : rowPlayer.spec}</span></span><small>{casts.length}</small>
          </button>}
          <div className="defensive-row-content">
            {!player && shading && <div className="defensive-mini-pressure"><PersonalDamageGraph points={displayDamagePoints(rowPlayer.pressure, allMitigation)} duration={pull.duration} maximum={everyoneScale} /></div>}
            {shading && player && <PressureShading points={points.map((p) => ({ ...p, damage: Math.min(maximum, incomingDamage(p)), healAbsorbs: 0 }))} duration={pull.duration} maximum={maximum} binSeconds={2} />}
            <DefensiveTrack showReady={showReady} casts={casts} duration={pull.duration} onInspect={onInspect} />
          </div>
        </div>)}
        {!player && !shownPlayers.length && <p className="coverage-empty">No players enabled. Select players below to compare their defensives.</p>}
        {!player && <HiddenDefensivePlayers players={hiddenPlayers} onEnable={(id) => onHiddenPlayerIds(hiddenPlayerIds.filter((hidden) => hidden !== id))} />}
      </div>
    </div>
    <div className="coverage-pressure-readout"><label>Inspect time <input aria-label="Inspect defensive timeline time" type="range" min="0" max={pull.duration} step="1" value={cursor} onChange={(e) => setCursor(Number(e.target.value))} /><b>{coverageTime(cursor)}</b></label>
      <span><span className="damage-taken">{compact(bucket?.damage)}/s taken</span> · <span className="damage-absorbed">{allMitigation ? `${compact(bucket?.absorbed)}/s absorbed` : `${compact(bucket?.cooldownAbsorbed)}/s CD shields`}</span>{!allMitigation && <span className="damage-other"> · {compact((bucket?.absorbed || 0) - (bucket?.cooldownAbsorbed || 0))}/s other shields</span>} · <span className="damage-mitigated">{compact(bucket?.mitigated)}/s {allMitigation ? "all mitigation" : "estimated CD reduction"}</span>{bucket?.immuneEvents > 0 && <span className="damage-immune"> · {bucket.immuneEvents} immune hits (amount unknown)</span>}{bucket?.healAbsorbs > 0 && <span> · {compact(bucket.healAbsorbs)}/s healing absorbed separately</span>}</span>
      <div className="coverage-sources">{bucket?.sources.map((s) => <span key={s.name}>{s.name} <b>{allMitigation ? `${compact(s.amount)}/s` : ""}{s.immuneEvents > 0 ? ` · ${s.immuneEvents} immune` : ""}</b></span>)}</div>
      {!allMitigation && bucket?.cooldownSources?.length > 0 && <div className="coverage-sources">Protection: {bucket.cooldownSources.map((name) => <span key={name}>{name}</span>)}</div>}
    </div>
  </>;
}
