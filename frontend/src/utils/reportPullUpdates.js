/** Normalize table and timeline pulls to report-qualified identities for live updates. */
export function reportPulls(page) {
  const pulls = new Map();
  const pending = page ? [page] : [];
  const visited = new Set();
  while (pending.length) {
    const candidate = pending.shift();
    if (!candidate || visited.has(candidate)) continue;
    visited.add(candidate);
    for (const pull of candidate.content?.timeline?.pulls || []) {
      pulls.set(`${pull.reportCode}:${pull.fightId}`, { value: pull.id, label: pull.label });
    }
    for (const option of candidate.content?.table?.viewControl?.options || []) {
      const match = /^pull:([^:]+):(\d+)$/.exec(option.value || "");
      if (match) pulls.set(`${match[1]}:${Number(match[2])}`, option);
    }
    pending.push(...Object.values(candidate.reportsByView || {}));
  }
  return pulls;
}

export function watchedPulls(snapshot) {
  return (snapshot.fights || []).map((fight) => ({
    ...fight, key: `${fight.report_code || snapshot.report_code}:${Number(fight.id)}`,
  }));
}

export function watchRevision(snapshot) {
  return snapshot.revisions ? JSON.stringify(snapshot.revisions) : snapshot.revision;
}
