/** A modeless drawer keeps selected cast measurements beside the timeline. */
import { useEffect, useRef } from "react";
import {
  preciseCoverageTime,
  compactCoverageNumber as compact,
} from "../../../utils/coverageTimeline";
import { CastEffectiveness } from "./CastEffectiveness";
import { DeathRecap } from "./DeathRecap";

function CastChoices({ casts, onInspect }) {
  return (
    <div className="coverage-cast-choices">
      {casts.map(({ lane, event }, index) => (
        <button
          key={`${lane.id}:${event.time}:${index}`}
          onClick={() => onInspect({ lane, event })}
        >
          <img src={lane.icon} alt="" width="28" height="28" />
          <span>
            <strong>
              {lane.player || "Boss"} · {lane.name}
            </strong>
            <small>{preciseCoverageTime(event.time)}</small>
          </span>
        </button>
      ))}
    </div>
  );
}

export function CoverageInspector({ selection, onInspect, onClose }) {
  const drawer = useRef(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    if (!selection) return;
    const previousFocus = document.activeElement;
    drawer.current?.focus({ preventScroll: true });
    const escape = (event) => {
      if (event.key === "Escape") close.current();
    };
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("keydown", escape);
      if (previousFocus?.isConnected)
        previousFocus.focus({ preventScroll: true });
    };
  }, [selection]);
  if (!selection)
    return (
      <div className="coverage-inspector coverage-inspector-empty">
        Select a healer cast to inspect its effectiveness, or select the
        coverage strip to review an interval.
      </div>
    );
  const { lane, event, bossGroup, coverage, deaths } = selection;
  return (
    <aside
      ref={drawer}
      tabIndex={-1}
      className="coverage-inspector coverage-inspector-drawer"
      aria-label="Ability details"
    >
      <button
        className="coverage-close"
        onClick={onClose}
        aria-label="Close ability details"
      >
        ×
      </button>
      {deaths && (
        <>
          <h3>
            {deaths.length === 1
              ? "Player death"
              : `${deaths.length} player deaths`}
          </h3>
          <div className="coverage-death-recaps">
            {deaths.map((death, index) => deaths.length === 1
              ? <DeathRecap key={`${death.playerId}:${death.time}`} death={death} />
              : <details key={`${death.playerId}:${death.time}`} open={index === 0}>
                  <summary>{death.player}<time>{preciseCoverageTime(death.time)}</time></summary>
                  <DeathRecap death={death} />
                </details>)}
          </div>
        </>
      )}
      {bossGroup && (
        <>
          <h3>Boss casts close together</h3>
          <p>
            Each cast retains its exact logged time. Select one for its
            description.
          </p>
          <CastChoices casts={bossGroup} onInspect={onInspect} />
        </>
      )}
      {coverage && (
        <>
          <h3>
            Raid coverage · {preciseCoverageTime(coverage.start)}–
            {preciseCoverageTime(coverage.end)}
          </h3>
          <p>{compact(coverage.pressure)} raid pressure / sec</p>
          <p className={coverage.potentialGap ? "coverage-warning" : ""}>
            {coverage.potentialGap
              ? "Review this gap: pressure is in the pull’s highest quarter of non-zero intervals, with no tracked cooldown window or instant cast in this interval."
              : `${coverage.active.length} sustained cooldown window${coverage.active.length === 1 ? "" : "s"} active.`}
          </p>
          <CastChoices
            casts={[...coverage.active, ...coverage.bursts]}
            onInspect={onInspect}
          />
          <p className="coverage-measurement-note">
            Coverage includes every healer, regardless of the lane filter.
            Instant and unknown-duration casts mark a use, not sustained
            protection. Active windows do not measure raid-wide reach or
            effectiveness.
          </p>
        </>
      )}
      {lane && (
        <>
          <div className="coverage-inspector-title">
            <img src={lane.icon} alt="" width="36" height="36" />
            <div>
              <strong>{lane.name}</strong>
              <p>
                {lane.player || "Boss ability"}
                {event && (
                  <>
                    {" "}
                    · {preciseCoverageTime(event.time)}
                    {event.label ? ` · ${event.label}` : ""}
                  </>
                )}
              </p>
            </div>
          </div>
          {lane.kind === "healer" ? (
            <>
              {event && <CastEffectiveness event={event} />}
              {!event && <p>{lane.description}</p>}
            </>
          ) : (
            <>
              <p>{lane.description}</p>
              <a
                href={`https://www.wowhead.com/spell=${lane.spellId}`}
                target="_blank"
                rel="noreferrer"
              >
                Spell details ↗
              </a>
            </>
          )}
        </>
      )}
    </aside>
  );
}
