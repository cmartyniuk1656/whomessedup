/** Compact per-cast protection totals; no percentage without a meaningful denominator. */
import { compactCoverageNumber as compact } from "../../../utils/coverageTimeline";

export function CooldownContribution({ event }) {
  const evidence = event.attribution;
  const shield = evidence?.matchedAbsorbed ?? event.protection?.spellAbsorbed ?? 0;
  const reduction = evidence?.estimatedReduction;
  if (shield <= 0 && reduction == null) {
    return event.effectiveHealing > 0 || event.overhealing > 0 ? null
      : <p className="defensive-muted">Damage prevention unavailable.</p>;
  }
  return <div className="defensive-contribution">
    <div className="defensive-evidence">
      {shield > 0 && <span className="damage-absorbed">Damage absorbed<strong>{compact(shield)}</strong></span>}
      {reduction != null && <span className="damage-mitigated">Damage prevented<strong>≈ {compact(reduction)}</strong></span>}
    </div>
  </div>;
}
