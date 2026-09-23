/** Shared compact hover preview and expanded five-second death recap. */
import { compactCoverageNumber as compact, preciseCoverageTime } from "../../../utils/coverageTimeline";

const KINDS = {
  damage: { label: "Damage", sign: "−", symbol: "↓" },
  heal: { label: "Effective healing", sign: "+", symbol: "+" },
  absorbed: { label: "Shield absorbed", sign: "", symbol: "◇" },
  healabsorbed: { label: "Healing absorbed", sign: "", symbol: "×" },
};

export function DeathRecap({ death, compact: preview = false }) {
  const recap = death.recap;
  const all = recap?.events || [];
  const events = preview ? all.slice(-6) : all;
  const killingBlow = all.findLast((event) => event.killingBlow);
  const omitted = Math.max(0, (recap?.totalEvents || 0) - events.length);
  return (
    <section className={`coverage-death-recap ${preview ? "is-preview" : ""}`} aria-label={`${death.player} death recap`}>
      <header className="coverage-death-heading">
        <div><span className="coverage-death-eyebrow">DEATH RECAP</span><strong>{death.player}</strong></div>
        <time>{preciseCoverageTime(death.time)}</time>
      </header>
      <p className="coverage-death-window">Last {recap?.windowSeconds ?? 5} seconds before death</p>
      {killingBlow && (
        <div className="coverage-killing-blow"><span>Killing blow</span><strong>{killingBlow.name}</strong></div>
      )}
      {recap?.totalEvents > 0 ? (
        <>
          <div className="coverage-death-totals">
            <div><span>Damage taken</span><strong>{compact(recap.damageTaken)}</strong></div>
            <div><span>Effective healing</span><strong>{compact(recap.healingReceived)}</strong></div>
          </div>
          {(recap.healingAbsorbed > 0 || recap.damageAbsorbed > 0) && (
            <p className="coverage-death-absorbs">
              {recap.healingAbsorbed > 0 && <span>{compact(recap.healingAbsorbed)} healing absorbed</span>}
              {recap.damageAbsorbed > 0 && <span>{compact(recap.damageAbsorbed)} damage shielded</span>}
            </p>
          )}
          <p className="coverage-death-events-label">{preview ? "Final events" : "Events before death"}</p>
          <ol className="coverage-death-events" aria-label="Events before death">
            {events.map((event, index) => {
              const kind = KINDS[event.kind];
              return (
                <li key={index} className={`coverage-death-event is-${event.kind} ${event.killingBlow ? "is-lethal" : ""}`}>
                  <time>{event.offset < 0 ? "−" : ""}{Math.abs(event.offset).toFixed(2)}s</time>
                  <span className="coverage-death-event-symbol" aria-label={kind.label}>{kind.symbol}</span>
                  <div className="coverage-death-event-name"><strong>{event.name}</strong>
                    <small>{event.source}{event.killingBlow ? " · Killing blow" : ""}</small>
                  </div>
                  <div className="coverage-death-event-amount"><strong>{kind.sign}{compact(event.amount)}</strong>
                    {event.overkill > 0 ? <small>{compact(event.overkill)} overkill</small>
                      : event.absorbed > 0 ? <small>{compact(event.absorbed)} shielded</small> : null}
                  </div>
                </li>
              );
            })}
          </ol>
          {omitted > 0 && <p className="coverage-death-note">Showing {events.length} of {recap.totalEvents} events; totals cover the full window.</p>}
          {!killingBlow && <p className="coverage-death-note">Killing blow not confirmed in these events.</p>}
        </>
      ) : <p className="coverage-death-note">No damage or effective healing events recorded in this window.</p>}
    </section>
  );
}
