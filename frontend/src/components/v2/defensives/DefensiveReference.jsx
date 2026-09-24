/** Transparent mechanic-aligned top-log observations, never an efficiency score. */
import { referenceComparison } from "../../../utils/defensiveUsage";

export function DefensiveReference({ entries, reference, spellId, occurrence, mechanicName, spec }) {
  if (!reference) return <p className="defensive-muted">Top-log comparison was not requested. Enable “Include top-log observations from Lorrgs” when running this report.</p>;
  if (reference.status !== "available") return <p className="defensive-muted">{reference.note}</p>;
  const matching = entries.filter(({ player }) => player.specId === reference.specId);
  const rows = referenceComparison(matching, reference, spellId, occurrence);
  return <section className="defensive-reference">
    <header><div><span className="defensive-eyebrow">LORRGS · {reference.metric?.toUpperCase()} TOP PARSES</span><h3>Common usage around {mechanicName} #{occurrence}</h3><p>{spec} · {reference.difficulty} · {reference.samples.length} player-log samples</p></div><a href={reference.sourceUrl} target="_blank" rel="noreferrer">Open Lorrgs ↗</a></header>
    <p className="defensive-muted">{rows[0]?.referenceTotal || 0} of {reference.samples.length} samples have this recorded mechanic and its full window. Observed from 5s before to 10s after in each log. Your comparison includes the same specialization.</p>
    <div className="defensive-reference-table"><table><thead><tr><th>Defensive</th><th>Your pulls</th><th>Top-log observations</th><th>Typical timing</th></tr></thead><tbody>
      {rows.map((row) => <tr key={row.lane.spellId}><td><img src={row.lane.icon} width="24" height="24" alt="" />{row.lane.name}</td>
        <td>{row.ownUses}/{row.ownTotal}</td><td>{row.tracked && row.referenceTotal ? <><span className="defensive-reference-meter"><i style={{ width: `${row.referenceUses / row.referenceTotal * 100}%` }} /></span>{row.referenceUses}/{row.referenceTotal} ({Math.round(row.referenceUses / row.referenceTotal * 100)}%)</> : row.tracked ? "No matching mechanic samples" : "Not tracked by Lorrgs"}</td>
        <td>{row.medianOffset == null ? "—" : <a href={row.sampleUrl} target="_blank" rel="noreferrer">{Math.abs(row.medianOffset).toFixed(1)}s {row.medianOffset < 0 ? "before" : "after"} ↗</a>}</td></tr>)}
    </tbody></table></div>
    <p className="defensive-muted">{reference.note} Sample fetched {new Date(reference.retrievedAt).toLocaleString()}.</p>
  </section>;
}
