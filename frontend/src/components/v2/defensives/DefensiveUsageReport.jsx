/** Orchestrate player/pull selection while retaining identity across attempts. */
import { useState } from "react";
import { ReportPageHeader } from "../molecules/ReportPageHeader";
import { DefensivePull } from "./DefensivePull";
import { DefensiveAggregate } from "./DefensiveAggregate";
import { DefensiveInspector } from "./DefensiveInspector";
import { defensiveCasts, isPersonalUse, playerPulls } from "../../../utils/defensiveUsage";
import "../coverage/coverage.css";
import "./defensives.css";

export function DefensiveUsageReport({ page, shareUrl }) {
  const timeline = page.content.timeline;
  const [pullId, setPullId] = useState(timeline.pulls[0]?.id);
  const [playerId, setPlayerId] = useState(timeline.pulls[0]?.players[0]?.id || "all");
  const [mode, setMode] = useState("pull");
  const [selection, setSelection] = useState(null);
  const [showReady, setShowReady] = useState(true);
  const [allMitigation, setAllMitigation] = useState(false);
  const [spellId, setSpellId] = useState("");
  const [occurrence, setOccurrence] = useState(1);
  const [bossSelection, setBossSelection] = useState(null);
  const [hiddenPlayerIds, setHiddenPlayerIds] = useState([]);
  const pull = timeline.pulls.find((p) => p.id === pullId) || timeline.pulls[0];
  const players = [...new Map(timeline.pulls.flatMap((p) => p.players).map((p) => [p.id, p])).values()].sort((a, b) => a.name.localeCompare(b.name));
  const player = pull?.players.find((p) => p.id === playerId) || players.find((p) => p.id === playerId);
  const entries = player ? playerPulls(timeline, player.id) : [];
  const mechanics = [...new Map(timeline.pulls.flatMap((p) => p.bossLanes).map((l) => [l.spellId, l])).values()];
  const bossIds = bossSelection ?? mechanics.filter((lane) => lane.shownByDefault).map((lane) => lane.spellId);
  const casts = mode === "aggregate" ? entries.flatMap(({ player: p, pull: f }) => defensiveCasts(p, f))
    : (player ? (pull?.players || []).filter((p) => p.id === player.id) : pull?.players || []).flatMap((p) => defensiveCasts(p, pull));
  const deaths = mode === "aggregate" ? entries.reduce((sum, e) => sum + e.player.deaths.length, 0)
    : player ? pull?.players.find((p) => p.id === player.id)?.deaths.length || 0 : pull?.deaths.length || 0;
  const selectPlayer = (id) => { setPlayerId(id); setSelection(null); };
  const changeMode = (next) => { setMode(next); setSelection(null); if (next === "aggregate" && playerId === "all") setPlayerId(pull?.players[0]?.id || players[0]?.id); };
  return <section className="coverage-report defensive-report">
    <ReportPageHeader page={page} shareUrl={shareUrl} rows={[]} />
    <div className="defensive-heading"><div><span className="defensive-eyebrow">DEFENSIVE USAGE</span><h2>Protection in context</h2><p>See who pressed what, what damage followed, and how usage changes between attempts.</p></div><div className="defensive-view-tabs" role="group" aria-label="Defensive report view">
      <button aria-pressed={mode === "pull"} onClick={() => changeMode("pull")}>This pull</button><button aria-pressed={mode === "aggregate"} onClick={() => changeMode("aggregate")}>Across pulls</button>
    </div></div>
    <div className="coverage-pull-bar">
      <label>Player <select aria-label="Defensive player" value={playerId} onChange={(e) => selectPlayer(e.target.value)}>{mode === "pull" && <option value="all">Everyone</option>}{players.map((p) => <option value={p.id} key={p.id}>{p.name} · {p.spec}{new Set(timeline.pulls.map((f) => f.reportCode)).size > 1 ? ` · ${p.id.split(":")[0]}` : ""}</option>)}</select></label>
      {mode === "pull" ? <label>Pull <select aria-label="Defensive pull" value={pull?.id || ""} onChange={(e) => { setPullId(e.target.value); setSelection(null); }}>{timeline.pulls.map((p) => <option value={p.id} key={p.id}>{p.label}</option>)}</select></label>
        : <label>Align to <select aria-label="Aggregate alignment" value={spellId} onChange={(e) => { setSpellId(e.target.value); setOccurrence(1); setSelection(null); }}><option value="">Pull start</option>{mechanics.map((m) => <option value={m.spellId} key={m.spellId}>{m.name}</option>)}</select></label>}
      {mode === "aggregate" && spellId && <label>Occurrence <input aria-label="Mechanic occurrence" type="number" min="1" max="100" value={occurrence} onChange={(e) => setOccurrence(Math.max(1, Number(e.target.value) || 1))} /></label>}
      <span>{timeline.pulls.length} pulls · {timeline.boss}</span>
    </div>
    <div className="coverage-overview"><div><span>Personal defensive uses</span><strong>{casts.filter((c) => isPersonalUse(c) && c.lane.category !== "consumable").length}</strong></div><div><span>Healthstones & health potions</span><strong>{casts.filter((c) => c.lane.category === "consumable").length}</strong></div><div><span>Raid / group / external casts</span><strong>{casts.filter((c) => !isPersonalUse(c)).length}</strong></div><div><span>Recorded deaths</span><strong>{deaths}</strong></div></div>
    <label className="defensive-mitigation-toggle"><input type="checkbox" checked={allMitigation} onChange={(e) => setAllMitigation(e.target.checked)} /> Show all mitigation (includes armor and passives)</label>
    {pull ? mode === "aggregate" ? <DefensiveAggregate bossIds={bossIds} onBossIds={setBossSelection} showReady={showReady} onShowReady={setShowReady} allMitigation={allMitigation} entries={entries} spellId={spellId} occurrence={occurrence} onInspect={setSelection} onOpenPull={(id) => { setPullId(id); setMode("pull"); setSelection(null); }} />
      : player && !pull.players.some((p) => p.id === player.id) ? <p className="coverage-empty">{player.name} did not participate in this pull. Select another pull or choose Across pulls.</p>
      : <DefensivePull hiddenPlayerIds={hiddenPlayerIds} onHiddenPlayerIds={setHiddenPlayerIds} bossIds={bossIds} onBossIds={setBossSelection} showReady={showReady} onShowReady={setShowReady} allMitigation={allMitigation} key={`${pull.id}:${playerId}`} pull={pull} playerId={playerId} onSelectPlayer={selectPlayer} onInspect={setSelection} /> : <p>No matching pulls were found.</p>}
    {!player && <p className="defensive-muted">Select a player to see personal incoming damage, pressure to review and all-pull usage.</p>}
    <details className="coverage-notes"><summary>How to read this report · research and interpretation</summary><p>Midnight {timeline.patch} research · {timeline.catalogueDate}</p>{page.footnotes.map((note) => <p key={note}>{note}</p>)}</details>
    <DefensiveInspector selection={selection} onInspect={setSelection} />
  </section>;
}
