/** Show the direct-healing split; shields have no comparable overheal measure. */
import { compactCoverageNumber as compact } from "../../../utils/coverageTimeline";

export function CastEffectiveness({ event }) {
  const data = event.effectiveness;
  if (!data || data.status !== "measured")
    return (
      <p className="coverage-measurement-note">
        {data?.note ||
          "Run a fresh report to load healing measurements for this cast."}
      </p>
    );

  const total = data.healthRestored + data.overhealing;
  const effectivePercent =
    total > 0 ? (100 * data.healthRestored) / total : null;
  const percent = (value) => `${value.toFixed(1)}%`;
  return (
    <section className="coverage-effectiveness" aria-label="Cast effectiveness">
      <div className="coverage-efficiency-heading">
        <span>Healing efficiency</span>
        <strong>
          {effectivePercent == null ? "—" : percent(effectivePercent)}
        </strong>
        <small>
          {effectivePercent == null
            ? "No direct healing recorded"
            : "of direct healing was effective"}
        </small>
      </div>
      <div
        className="coverage-healing-bar"
        role="img"
        aria-label={
          effectivePercent == null
            ? "No direct healing recorded"
            : `${percent(effectivePercent)} effective healing, ${percent(100 - effectivePercent)} overhealing`
        }
      >
        {effectivePercent != null && (
          <>
            <span
              className="coverage-healing-effective"
              style={{ width: `${effectivePercent}%` }}
            />
            <span
              className="coverage-healing-overheal"
              style={{ width: `${100 - effectivePercent}%` }}
            />
          </>
        )}
      </div>
      <div className="coverage-healing-totals">
        <div>
          <span>
            <i className="coverage-healing-effective" />
            Effective healing
          </span>
          <strong>{compact(data.healthRestored)}</strong>
        </div>
        <div>
          <span>
            <i className="coverage-healing-overheal" />
            Overhealing
          </span>
          <strong>{compact(data.overhealing)}</strong>
          <small>
            {effectivePercent == null ? "" : percent(100 - effectivePercent)}
          </small>
        </div>
      </div>
      {data.shieldsConsumed > 0 && (
        <p className="coverage-shield-note">
          + {compact(data.shieldsConsumed)} shield absorption, measured
          separately.
        </p>
      )}
      <p className="coverage-measurement-note">
        Healer + pet output during this window, including other spells.
      </p>
    </section>
  );
}
