/** Orchestrate player/pull selection while retaining identity across attempts. */
import { ReportUpdateNotification } from "../molecules/ReportUpdateNotification";
import { useCallback, useMemo } from "react";
import { useReportViewState } from "../../../hooks/useReportViewState";
import { useTimelineSelection } from "../../../hooks/useTimelineSelection";
import { DEFAULT_DEFENSIVE_LAYERS } from "../../../config/defensiveChartLayers";
import { ReportPageHeader } from "../molecules/ReportPageHeader";
import { DefensivePull } from "./DefensivePull";
import { DefensiveAggregate } from "./DefensiveAggregate";
import { DefensiveInspector } from "./DefensiveInspector";
import { defensiveCasts, isPersonalUse, playerPulls } from "../../../utils/defensiveUsage";
import "../coverage/coverage.css";
import "./defensives.css";

export function DefensiveUsageReport({ page, shareUrl, realtime }) {
  const timeline = page.content.timeline;
  const [pullId, setPullId] = useReportViewState("pullId", timeline.pulls[0]?.id, { validate: (id) => timeline.pulls.some((pull) => pull.id === id) });
  const [playerId, setPlayerId] = useReportViewState("playerId", timeline.pulls[0]?.players[0]?.id || "all", { validate: (id) => id === "all" || timeline.pulls.some((pull) => pull.players.some((player) => player.id === id)) });
  const [mode, setMode] = useReportViewState("mode", "pull", { validate: (value) => ["pull", "aggregate"].includes(value) });
  const [selection, setSelection] = useTimelineSelection(timeline.pulls);
  const [layers, setLayers] = useReportViewState("layers", DEFAULT_DEFENSIVE_LAYERS);
  const setLayer = useCallback((key, checked) => setLayers((current) => ({ ...current, [key]: checked })), [setLayers]);
  const [allMitigation, setAllMitigation] = useReportViewState("allMitigation", false);
  const [spellId, setSpellId] = useReportViewState("spellId", "", { validate: (id) => id === "" || timeline.pulls.some((pull) => pull.bossLanes.some((lane) => String(lane.spellId) === id)) });
  const [occurrence, setOccurrence] = useReportViewState("occurrence", 1, { validate: (value) => Number.isInteger(value) && value >= 1 && value <= 100 });
  const [bossSelection, setBossSelection] = useReportViewState("bossSelection", null, { validate: (ids) => ids === null || (Array.isArray(ids) && ids.every(Number.isFinite)) });
  const [hiddenPlayerIds, setHiddenPlayerIds] = useReportViewState("hiddenPlayerIds", []);
  const pull = timeline.pulls.find((p) => p.id === pullId) || timeline.pulls[0];
  const players = useMemo(() => [...new Map(timeline.pulls.flatMap((p) => p.players).map((p) => [p.id, p])).values()].sort((a, b) => a.name.localeCompare(b.name)), [timeline]);
  const player = pull?.players.find((p) => p.id === playerId) || players.find((p) => p.id === playerId);
  const entries = useMemo(() => player ? playerPulls(timeline, player.id) : [], [timeline, player]);
  const mechanics = useMemo(() => [...new Map(timeline.pulls.flatMap((p) => p.bossLanes).map((l) => [l.spellId, l])).values()], [timeline]);
  const bossIds = useMemo(() => bossSelection ?? mechanics.filter((lane) => lane.shownByDefault).map((lane) => lane.spellId), [bossSelection, mechanics]);
  const casts = useMemo(() => mode === "aggregate" ? entries.flatMap(({ player: p, pull: f }) => defensiveCasts(p, f))
    : (player ? (pull?.players || []).filter((p) => p.id === player.id) : pull?.players || []).flatMap((p) => defensiveCasts(p, pull)), [mode, entries, player, pull]);
  const deaths = mode === "aggregate" ? entries.reduce((sum, e) => sum + e.player.deaths.length, 0)
    : player ? pull?.players.find((p) => p.id === player.id)?.deaths.length || 0 : pull?.deaths.length || 0;
  const selectPlayer = useCallback((id) => { setPlayerId(id); setSelection(null); }, [setPlayerId, setSelection]);
  const openPull = useCallback((id) => { setPullId(id); setMode("pull"); setSelection(null); }, [setPullId, setMode, setSelection]);
  const changeMode = (next) => { setMode(next); setSelection(null); if (next === "aggregate" && playerId === "all") setPlayerId(pull?.players[0]?.id || players[0]?.id); };
  return <section className="coverage-report defensive-report">
    <ReportPageHeader page={page} shareUrl={shareUrl} rows={[]} />
      <ReportUpdateNotification notice={realtime?.notice} onDismiss={realtime?.clearNotice}
        onViewPull={timeline.pulls.some((entry) => entry.id === realtime?.notice?.viewId)
          ? () => { openPull(realtime.notice.viewId); realtime.clearNotice(); } : null} />
    <div className="defensive-heading"><div><span className="defensive-eyebrow">DEFENSIVE USAGE</span><h2>Protection in context</h2><p>See who pressed what, what damage followed, and how usage changes between attempts.</p></div><div className="defensive-view-tabs" role="group" aria-label="Defensive report view">
      <button aria-pressed={mode === "pull"} onClick={() => changeMode("pull")}>This pull</button><button aria-pressed={mode === "aggregate"} onClick={() => changeMode("aggregate")}>Across pulls</button>
    </div></div>
    <div className="coverage-pull-bar">
      <label>Player <select aria-label="Defensive player" value={playerId} onChange={(e) => selectPlayer(e.target.value)}>{mode === "pull" && <option value="all">Everyone</option>}{players.map((p) => <option value={p.id} key={p.id}>{p.name} · {p.spec}{new Set(timeline.pulls.map((f) => f.reportCode)).size > 1 ? ` · ${p.id.split(":")[0]}` : ""}</option>)}</select></label>
      {mode === "pull" ? <label>Pull <select aria-label="Defensive pull" value={pull?.id || ""} onChange={(e) => { setPullId(e.target.value); setSelection(null); }}>{timeline.pulls.map((p) => <option value={p.id} key={p.id}>{p.label}</option>)}</select></label>
        : <label>Align to <select aria-label="Aggregate alignment" value={spellId} onChange={(e) => { setSpellId(e.target.value); setOccurrence(1); setSelection(null); }}><option value="">Pull start</option>{mechanics.map((m) => <option value={m.spellId} key={m.spellId}>{m.name}</option>)}</select></label>}
      {mode === "aggregate" && spellId && <label>Occurrence <input aria-label="Mechanic occurrence" type="number" min="1" max="100" value={occurrence} onChange={(e) => setOccurrence(Math.min(100, Math.max(1, Number(e.target.value) || 1)))} /></label>}
      <span>{timeline.pulls.length} pulls · {timeline.boss}</span>
    </div>
    <div className="coverage-overview"><div><span>Personal defensive uses</span><strong>{casts.filter((c) => isPersonalUse(c) && c.lane.category !== "consumable").length}</strong></div><div><span>Healthstones & health potions</span><strong>{casts.filter((c) => c.lane.category === "consumable").length}</strong></div><div><span>Raid / group / external casts</span><strong>{casts.filter((c) => !isPersonalUse(c)).length}</strong></div><div><span>Recorded deaths</span><strong>{deaths}</strong></div></div>
    <label className="defensive-mitigation-toggle"><input type="checkbox" checked={allMitigation} onChange={(e) => setAllMitigation(e.target.checked)} /> Show all mitigation (includes armor and passives)</label>
    {pull ? mode === "aggregate" ? <DefensiveAggregate layers={layers} onLayerChange={setLayer} bossIds={bossIds} onBossIds={setBossSelection} allMitigation={allMitigation} entries={entries} spellId={spellId} occurrence={occurrence} onInspect={setSelection} onOpenPull={openPull} />
      : player && !pull.players.some((p) => p.id === player.id) ? <p className="coverage-empty">{player.name} did not participate in this pull. Select another pull or choose Across pulls.</p>
      : <DefensivePull layers={layers} onLayerChange={setLayer} hiddenPlayerIds={hiddenPlayerIds} onHiddenPlayerIds={setHiddenPlayerIds} bossIds={bossIds} onBossIds={setBossSelection} allMitigation={allMitigation} key={`${pull.id}:${playerId}`} pull={pull} playerId={playerId} onSelectPlayer={selectPlayer} onInspect={setSelection} /> : <p>No matching pulls were found.</p>}
    {!player && <p className="defensive-muted">Select a player to see personal incoming damage, pressure to review and all-pull usage.</p>}
    <details className="coverage-notes"><summary>How to read this report · research and interpretation</summary><p>Midnight {timeline.patch} research · {timeline.catalogueDate}</p>{page.footnotes.map((note) => <p key={note}>{note}</p>)}</details>
    <DefensiveInspector selection={selection} onInspect={setSelection} />
  </section>;
}
