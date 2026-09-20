/** Compose the aligned pressure, coverage, boss and healer tracks. */
import { useCoverageTimeline } from "../../../hooks/useCoverageTimeline";
import {
  coverageTime,
  compactCoverageNumber as compact,
} from "../../../utils/coverageTimeline";
import { BossAbilityFilters } from "./BossAbilityFilters";
import { BossAbilityLane } from "./BossAbilityLane";
import { CoverageLane } from "./CoverageLane";
import { CoverageInspector } from "./CoverageInspector";
import { CoverageToolbar } from "./CoverageToolbar";
import { PressureGraph } from "./PressureGraph";
import { PressureShading } from "./PressureShading";
import { RaidCoverageStrip } from "./RaidCoverageStrip";

export function PullTimeline({ pull, binSeconds }) {
  const state = useCoverageTimeline(pull, binSeconds);
  const {
    overlay,
    showReady,
    zoom,
    cursor,
    ticks,
    maximum,
    bucket,
    selection,
    inspect,
  } = state;
  return (
    <>
      <div className="coverage-overview">
        <div>
          <span>Pull length</span>
          <strong>{coverageTime(pull.duration)}</strong>
        </div>
        <div>
          <span>Healers with tracked cooldowns</span>
          <strong>{state.healers.length}</strong>
        </div>
        <div>
          <span>Cooldown uses · excludes Stasis stores</span>
          <strong>{state.casts}</strong>
        </div>
        <div>
          <span>Peak raid pressure / sec</span>
          <strong>{compact(maximum)}</strong>
        </div>
      </div>
      <CoverageToolbar state={state} />
      <BossAbilityFilters
        lanes={state.bossLanes}
        selectedIds={state.bossIds}
        onToggle={state.toggleBoss}
        onSelectAll={() =>
          state.setBossIds(state.bossLanes.map((lane) => lane.id))
        }
        onClear={() => state.setBossIds([])}
      />
      <div className="coverage-legend">
        <span className="coverage-key-window">━ Tracked window</span>
        <span>┄ Recovery estimate</span>
        <span>◇ Estimated ready</span>
        <span className="coverage-key-pressure">━ Damage + heal absorbs</span>
        <span className="coverage-key-absorbs">━ Heal absorbs consumed</span>
      </div>
      <p className="coverage-strip-help">
        <span className="coverage-key-window">■ Sustained coverage</span> ·{" "}
        <span className="coverage-key-absorbs">
          ▧ Instant / unknown duration
        </span>{" "}
        ·{" "}
        <span className="coverage-key-pressure">
          ■ High pressure without a tracked window
        </span>
        . Click the strip to inspect. More windows do not necessarily mean
        better coverage.
      </p>
      {pull.warnings.map((warning) => (
        <p className="coverage-warning" key={warning}>
          {warning}
        </p>
      ))}
      <div
        className="coverage-scroll"
        tabIndex="0"
        role="region"
        aria-label="Cooldown coverage timeline, scroll horizontally when zoomed"
      >
        <div
          className="coverage-canvas"
          style={{ width: `${zoom * 100}%`, minWidth: `${850 * zoom}px` }}
          onPointerMove={state.updateCursor}
        >
          <div className="coverage-axis">
            <div className="coverage-axis-label">PULL TIMELINE</div>
            <div className="coverage-axis-track">
              {ticks.map((tick) => (
                <span
                  key={tick}
                  style={{ left: `${(tick / pull.duration) * 100}%` }}
                >
                  {coverageTime(tick)}
                </span>
              ))}
            </div>
          </div>
          {overlay && (
            <div className="coverage-pressure-row">
              <div className="coverage-pressure-label">
                <strong>Raid pressure</strong>
                <span>{compact(maximum)} / sec peak</span>
                <small>{binSeconds}-second intervals</small>
              </div>
              <div className="coverage-graph-track">
                <PressureGraph
                  points={pull.pressure}
                  duration={pull.duration}
                  maximum={maximum}
                />
              </div>
            </div>
          )}
          <RaidCoverageStrip
            segments={state.segments}
            duration={pull.duration}
            onInspect={inspect}
          />
          <div className="coverage-lanes">
            {overlay && (
              <div className="coverage-lanes-backdrop">
                <PressureShading
                  points={pull.pressure}
                  duration={pull.duration}
                  maximum={maximum}
                  binSeconds={binSeconds}
                />
              </div>
            )}
            <div className="coverage-gridlines">
              {ticks.map((tick) => (
                <i
                  key={tick}
                  style={{ left: `${(tick / pull.duration) * 100}%` }}
                />
              ))}
            </div>
            <BossAbilityLane
              lanes={state.visibleBossLanes}
              duration={pull.duration}
              onInspect={inspect}
            />
            {state.healerLanes.map((lane) => (
              <CoverageLane
                key={lane.id}
                lane={lane}
                duration={pull.duration}
                showReady={showReady}
                onInspect={inspect}
                selectedEvent={
                  selection?.lane?.id === lane.id ? selection.event : null
                }
              />
            ))}
            {!state.healerLanes.length && (
              <p className="coverage-empty">
                No tracked healer cooldowns for this selection.
              </p>
            )}
          </div>
          <div className="coverage-cursor-track">
            <div
              className="coverage-cursor"
              style={{ left: `${(cursor / pull.duration) * 100}%` }}
            >
              <span>{coverageTime(cursor)}</span>
            </div>
          </div>
        </div>
      </div>
      {overlay && (
        <div className="coverage-pressure-readout">
          <label>
            Inspect time{" "}
            <input
              aria-label="Inspect timeline time"
              type="range"
              min="0"
              max={pull.duration}
              step="1"
              value={cursor}
              onChange={(event) => state.setCursor(Number(event.target.value))}
            />
            <b>{coverageTime(cursor)}</b>
          </label>
          <span className="coverage-key-pressure">
            Damage {compact(bucket?.damage)}/s
          </span>
          <span className="coverage-key-absorbs">
            Heal absorbs {compact(bucket?.healAbsorbs)}/s
          </span>
          <div className="coverage-sources">
            {bucket?.sources.map((source) => (
              <span key={source.name}>
                {source.name} <b>{compact(source.amount)}/s</b>
              </span>
            ))}
          </div>
        </div>
      )}
      <CoverageInspector
        selection={selection}
        onInspect={inspect}
        onClose={() => inspect(null)}
      />
    </>
  );
}
