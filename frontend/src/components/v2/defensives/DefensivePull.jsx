/** One real pull: raid overview or one player's personal damage and ability lanes. */
import { useDefensivePullData } from "../../../hooks/useDefensivePullData";
import { memo, useCallback, useRef } from "react";
import { DefensiveTimeReadout } from "./DefensiveTimeReadout";
import { useReportViewState, useReportViewScroll } from "../../../hooks/useReportViewState";
import { DefensiveBossFilters } from "./DefensiveBossFilters";
import { BossAbilityLane } from "../coverage/BossAbilityLane";
import { DamageLegend } from "./DamageLegend";
import { TimelineLegend } from "./TimelineLegend";
import { PlayerHealthOverlay } from "./PlayerHealthOverlay";
import { PersonalDamageGraph } from "./PersonalDamageGraph";
import { PressureShading } from "../coverage/PressureShading";
import { DeathMarkers } from "../coverage/DeathMarkers";
import { DefensiveTrack } from "./DefensiveTrack";
import { DefensivePlayerControls, DefensivePlayerLabel, HiddenDefensivePlayers } from "./DefensivePlayerVisibility";
import { timelineTicks, coverageTime, compactCoverageNumber as compact } from "../../../utils/coverageTimeline";

export const DefensivePull = memo(function DefensivePull({ layers, onLayerChange, pull, playerId, onSelectPlayer, onInspect, allMitigation, bossIds, onBossIds, hiddenPlayerIds, onHiddenPlayerIds }) {
  const scrollRef = useReportViewScroll(`${pull.id}:${playerId}`);
  const { health: showHealth } = layers;
  const player = pull.players.find((p) => p.id === playerId);
  const [fullRange, setFullRange] = useReportViewState("fullRange", false, { resetKey: `${pull.id}:${playerId}` });
  const [zoom, setZoom] = useReportViewState("zoom", 1, { resetKey: `${pull.id}:${playerId}`, validate: (value) => value >= 1 && value <= 4 });
  const readout = useRef(null);
  const setCursor = useCallback((time) => readout.current?.setCursor(time), []);
  const { shownPlayers, hiddenPlayers, sourcePoints, points, maximum, peak, clipped,
    everyoneDamage, everyoneScale, visibleRows, review, shading } = useDefensivePullData({
    pull, player, layers, allMitigation, fullRange, hiddenPlayerIds,
  });
  return <>
    <div className="coverage-controls">
      <label>Damage scale <select aria-label="Damage graph scale" value={fullRange ? "full" : "readable"} onChange={(e) => setFullRange(e.target.value === "full")}><option value="readable">Auto · readable peaks</option><option value="full">Full range</option></select></label>
      {clipped > 0 && <span className="defensive-muted">↑ {clipped} spikes above scale · hover for exact values</span>}
      <label>Zoom <input type="range" min="1" max="4" step=".5" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} /></label>
    </div>
    <DefensiveBossFilters pulls={[pull]} selectedIds={bossIds} onChange={onBossIds} />
    {!player && <DefensivePlayerControls players={pull.players} hiddenIds={hiddenPlayerIds} onChange={onHiddenPlayerIds} />}
    {review.length > 0 && <div className="defensive-review"><div><strong>Pressure to review</strong><span>Largest damage spikes without a tracked personal window · availability not inferred</span></div>
      {review.map((point) => <button key={point.time} onClick={() => { setCursor(point.time); onInspect({ review: { point, player, pull } }); }}>
        {coverageTime(point.time)} <b>{compact(point.damage)}/s</b>
      </button>)}</div>}
    <div ref={scrollRef} className="coverage-scroll" tabIndex="0" role="region" aria-label="Defensive usage timeline">
      <div className="coverage-canvas" style={{ width: `${zoom * 100}%`, minWidth: 850 * zoom, "--defensive-key-width": `${100 / zoom}%` }}>
        <div className="coverage-axis"><div className="coverage-axis-label">{player ? player.name : "RAID DEFENSIVES"}</div><div className="coverage-axis-track">
          {timelineTicks(pull.duration).map((t) => <span key={t} style={{ left: `${t / pull.duration * 100}%` }}>{coverageTime(t)}</span>)}
        </div></div>
        <div className="coverage-pressure-row"><div className="coverage-pressure-label"><strong>{player ? `${player.name} · incoming damage` : "Raid incoming damage"}</strong><span>{compact(maximum)}/s scale{clipped > 0 ? ` · ${compact(peak)}/s peak ↑` : ""}</span><small>Selected damage layers · 2s bins</small></div><div className="coverage-graph-track"><PersonalDamageGraph visibility={layers} points={points} maximum={maximum} duration={pull.duration} onTime={setCursor} scope={player ? "Personal" : "Raid"} />{showHealth && player && <PlayerHealthOverlay points={player.health} duration={pull.duration} />}</div></div>
        <DamageLegend extraPeaks={everyoneDamage?.clipped > 0} layers={layers} onLayerChange={onLayerChange} health={player ? player.health?.length > 0 : shownPlayers.some((p) => p.health?.length)} healthInLanes={!player} points={sourcePoints} visiblePoints={points} maximum={maximum} allMitigation={allMitigation} />
        <DeathMarkers deaths={player ? player.deaths : pull.deaths} duration={pull.duration} onInspect={onInspect} />
        <BossAbilityLane lanes={pull.bossLanes.filter((l) => bossIds.includes(l.spellId))} duration={pull.duration} onInspect={onInspect} />
        <TimelineLegend showReady casts={visibleRows.flatMap((row) => row.casts)} deaths={player ? player.deaths : pull.deaths} />
        {visibleRows.map(({ player: rowPlayer, lane, casts, points: rowPoints }) => <div className="coverage-row defensive-row" key={lane?.id || rowPlayer.id}>
          {!player ? <DefensivePlayerLabel player={rowPlayer} casts={casts.length}
            onHide={() => onHiddenPlayerIds([...hiddenPlayerIds, rowPlayer.id])} onInspect={() => onSelectPlayer(rowPlayer.id)} />
          : <button className="coverage-lane-label" onClick={() => onSelectPlayer(rowPlayer.id)} title={lane ? `${lane.description}${lane.readiness ? `\n${lane.readiness.note}` : ""}` : `Inspect ${rowPlayer.name}`}>
            {lane && <img src={lane.icon} width="27" height="27" alt="" />}<span><strong>{lane?.name || rowPlayer.name}</strong><span>{lane ? lane.category.replaceAll("_", " ") : rowPlayer.spec}</span></span><small>{casts.length}</small>
          </button>}
          <div className="defensive-row-content">
            {!player && <div className="defensive-mini-pressure"><PersonalDamageGraph visibility={layers} points={rowPoints} duration={pull.duration} maximum={everyoneScale} /></div>}
            {!player && showHealth && <PlayerHealthOverlay points={rowPlayer.health} duration={pull.duration} />}
            {player && <PressureShading points={shading} duration={pull.duration} maximum={maximum} binSeconds={2} />}
            <DefensiveTrack showReady casts={casts} duration={pull.duration} onInspect={onInspect} />
          </div>
        </div>)}
        {!player && !shownPlayers.length && <p className="coverage-empty">No players enabled. Select players below to compare their defensives.</p>}
        {!player && <HiddenDefensivePlayers players={hiddenPlayers} onEnable={(id) => onHiddenPlayerIds(hiddenPlayerIds.filter((hidden) => hidden !== id))} />}
      </div>
    </div>
    <DefensiveTimeReadout ref={readout} pull={pull} player={player} playerId={playerId} sourcePoints={sourcePoints} allMitigation={allMitigation} showHealth={showHealth} />
  </>;
});
