/** Pure selectors for observed usage and mechanic-relative comparisons. */
export function defensiveCasts(player, pull) {
  return (player?.lanes || []).flatMap((lane) => lane.events.map((event) => ({ lane, event, player, pull })))
    .sort((a, b) => a.event.time - b.event.time);
}

export function isPersonalUse({ lane, event }) {
  return lane.category === "personal" || lane.category === "consumable"
    || (lane.category === "external_or_self" && event.selfUse);
}

export function playerPulls(timeline, playerId) {
  return timeline.pulls.flatMap((pull) => {
    const player = pull.players.find((p) => p.id === playerId);
    return player ? [{ pull, player }] : [];
  });
}

export function mechanicTime(pull, spellId, occurrence = 1) {
  if (!spellId) return 0;
  return pull.bossLanes.find((lane) => lane.spellId === Number(spellId))?.events[occurrence - 1]?.time ?? null;
}

export function aggregateRows(entries, spellId, occurrence) {
  return entries.flatMap(({ pull, player }) => {
    const anchor = mechanicTime(pull, spellId, occurrence);
    return anchor == null ? [] : [{ pull, player, anchor, casts: defensiveCasts(player, pull) }];
  });
}

export function alignedTicks(start, end) {
  const interval = end - start > 600 ? 60 : end - start > 240 ? 30 : 15;
  const ticks = [];
  for (let t = Math.ceil(start / interval) * interval; t <= end; t += interval) ticks.push(t);
  return ticks;
}

export function pressureReview(player, pull) {
  const personal = defensiveCasts(player, pull).filter(isPersonalUse);
  const candidates = player.pressure.filter((p) => p.damage > 0 && !personal.some(({ event }) =>
    event.time < p.time + 2 && (event.end > p.time || (event.end === event.time && event.time >= p.time - 2))));
  const selected = [];
  for (const point of [...candidates].sort((a, b) => b.damage - a.damage)) {
    if (selected.every((p) => Math.abs(p.time - point.time) >= 8)) selected.push(point);
    if (selected.length === 3) break;
  }
  return selected;
}

/** Same mechanic occurrence, observed in each log; never align by fixed timers. */
export function referenceComparison(entries, reference, spellId, occurrence) {
  const samples = (reference?.samples || []).flatMap((sample) => {
    const anchor = sample.bossEvents.filter((e) => e.spellId === Number(spellId))
      .sort((a, b) => a.time - b.time)[occurrence - 1]?.time;
    return anchor != null && anchor >= 5 && sample.duration >= anchor + 10 ? [{ ...sample, anchor }] : [];
  });
  const own = aggregateRows(entries, spellId, occurrence).filter(({ pull, anchor }) => anchor >= 5 && pull.duration >= anchor + 10);
  const abilities = new Map(entries.flatMap(({ player }) => player.lanes).map((lane) => [lane.spellId, lane]));
  const rows = [...abilities.values()].filter((lane) => ["personal", "consumable"].includes(lane.category)).map((lane) => {
    const tracked = reference?.trackedSpellIds?.includes(lane.spellId);
    const matches = samples.flatMap((sample) => {
      const events = sample.events.filter((e) => e.spellId === lane.spellId && e.time >= sample.anchor - 5 && e.time <= sample.anchor + 10);
      return events.length ? [{ sample, offset: events[0].time - sample.anchor }] : [];
    });
    const offsets = matches.map((m) => m.offset).sort((a, b) => a - b);
    const medianOffset = offsets.length ? offsets[Math.floor(offsets.length / 2)] : null;
    const ownUses = own.filter(({ casts, anchor }) => casts.some(({ lane: l, event }) => l.spellId === lane.spellId
      && event.time >= anchor - 5 && event.time <= anchor + 10));
    return { lane, tracked, referenceUses: matches.length, referenceTotal: samples.length,
      ownUses: ownUses.length, ownTotal: own.length,
      medianOffset, sampleUrl: matches.find((match) => match.offset === medianOffset)?.sample.url };
  });
  return rows.sort((a, b) => b.referenceUses - a.referenceUses || b.ownUses - a.ownUses);
}

/** Recorded personal damage outcomes; heal absorbs and unknown immunity amounts stay separate. */
export const incomingDamage = (point) => (point?.damage || 0) + (point?.absorbed || 0) + (point?.mitigated || 0);

/** Default green is supported cooldown DR only; baseline mitigation is opt-in. */
export function displayDamagePoints(points, allMitigation = false) {
  return points.map((point) => ({ ...point, cooldownMode: !allMitigation,
    mitigated: allMitigation ? point.mitigated : (point.cooldownMitigated || 0) }));
}

/** Merge spec versions in summary cards only; casts retain their original spell and timing. */
export function defensiveUsageCounts(entries) {
  const counts = new Map();
  entries.forEach(({ player }) => {
    const used = new Set();
    player.lanes.forEach((lane) => {
      const key = lane.spellId === 403876 ? 498 : lane.spellId;
      const current = counts.get(key) || { lane, uses: 0, pulls: 0 };
      current.uses += lane.events.length;
      if (lane.events.length && !used.has(key)) { current.pulls++; used.add(key); }
      counts.set(key, current);
    });
  });
  return [...counts.values()].sort((a, b) => b.uses - a.uses);
}

/** One filter per spell, with counts from all displayed pulls and stable identity. */
export function mergeBossAbilityLanes(pulls) {
  const lanes = new Map();
  for (const pull of pulls) {
    for (const lane of pull.bossLanes) {
      if (!lanes.has(lane.spellId)) lanes.set(lane.spellId, { ...lane, id: lane.spellId, events: [] });
      lanes.get(lane.spellId).events.push(...lane.events);
    }
  }
  return [...lanes.values()];
}

/** Stop visual recovery at the caster's next death or pull end, without resetting cooldowns. */
export function defensiveRecovery({ event, player, pull }) {
  if (event.ready == null || event.ready < event.time) return null;
  const death = Math.min(...(player.deaths || []).filter((d) => d.time >= event.time).map((d) => d.time));
  const end = Math.min(event.ready, pull.duration, death);
  return { start: event.end ?? event.time, end, marker: event.ready <= pull.duration && event.ready < death };
}

/** Keep exceptional spikes visible without letting them flatten ordinary hits.
 * All compared rows must pass their points together to retain one shared scale.
 */
export function damageScale(points, fullRange = false) {
  const values = points.map(incomingDamage).filter((value) => value > 0).sort((a, b) => a - b);
  const peak = values.at(-1) || 0;
  const typical = values[Math.max(0, Math.ceil(values.length * .95) - 1)] || 0;
  const ceiling = !fullRange && values.length >= 10 && peak > typical * 2 ? typical * 1.25 : peak;
  return { maximum: Math.max(1, ceiling), peak, clipped: values.filter((value) => value > ceiling).length };
}
