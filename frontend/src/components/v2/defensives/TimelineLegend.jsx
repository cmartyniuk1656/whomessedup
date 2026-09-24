/** Secondary cast-marker help stays separate from damage outcome colours. */
export function TimelineLegend({ casts, deaths = [], showReady = false }) {
  return <div className="defensive-timeline-help">
    {showReady && <p className="defensive-readiness-key">{casts.some((c) => c.event.ready != null)
      ? "◇ Estimated ready / charge replenished · dashed line: recharge · hover a cast for its timing basis"
      : "Readiness is unknown for these uses · hover a cast for the reason"}</p>}
    <details className="defensive-timeline-key"><summary>Timeline markers · click a cast for details</summary>
    <div>
      {casts.some((c) => c.lane.category === "personal") && <span className="coverage-key-window">━ Personal defensive</span>}
      {casts.some((c) => c.lane.category === "consumable") && <span className="defensive-key-item">━ Healthstone / potion</span>}
      {casts.some((c) => ["external", "external_or_self", "group", "raid"].includes(c.lane.category)) && <span className="defensive-key-external">━ Group / external defensive</span>}
      {casts.some((c) => !c.event.selfUse && c.event.targetId != null && !["raid", "group"].includes(c.lane.category)) && <span>↗ Cast on another player</span>}
      {casts.some((c) => c.event.durationBasis === "nominal") && <span>Dashed border: estimated duration</span>}
      {deaths.length > 0 && <span>× Player death</span>}
    </div>
  </details></div>;
}
