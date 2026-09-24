/** Prepare graph geometry and cast lanes once per data/filter change, not UI interaction. */
import { useMemo } from "react";
import { damageScale, defensiveCasts, displayDamagePoints, incomingDamage, pressureReview } from "../utils/defensiveUsage";
import { filterDamagePoints } from "../utils/defensiveChartLayers";

export function useDefensivePullData({ pull, player, layers, allMitigation, fullRange, hiddenPlayerIds }) {
  return useMemo(() => {
    const displayPoints = (raw) => filterDamagePoints(displayDamagePoints(raw, allMitigation), layers);
    const hidden = new Set(hiddenPlayerIds);
    const shownPlayers = pull.players.filter((entry) => !hidden.has(entry.id));
    const hiddenPlayers = pull.players.filter((entry) => hidden.has(entry.id));
    const sourcePoints = displayDamagePoints(player ? player.pressure : pull.pressure, allMitigation);
    const points = filterDamagePoints(sourcePoints, layers);
    const scale = damageScale(points, fullRange);
    const rows = player
      ? player.lanes.map((lane) => ({ player, lane, casts: defensiveCasts({ ...player, lanes: [lane] }, pull) }))
      : shownPlayers.map((entry) => ({ player: entry, casts: defensiveCasts(entry, pull), points: displayPoints(entry.pressure) }));
    const everyoneDamage = player ? null : damageScale(rows.flatMap((row) => row.points), fullRange);
    const potionRows = player ? rows.filter((row) => row.lane.category === "consumable" && /potion/i.test(row.lane.name)) : [];
    const visibleRows = rows.filter((row) => !potionRows.includes(row));
    // Potion variants stay distinguishable on casts without several empty item rows.
    if (potionRows.length) visibleRows.push({ player,
      lane: { ...potionRows[0].lane, id: "health-potions", name: "Health potions", description: potionRows.map((row) => row.lane.name).join(" · ") },
      casts: potionRows.flatMap((row) => row.casts).sort((a, b) => a.event.time - b.event.time),
    });
    return { ...scale, sourcePoints, points, shownPlayers, hiddenPlayers, everyoneDamage,
      everyoneScale: everyoneDamage?.maximum ?? scale.maximum, visibleRows,
      review: player ? pressureReview(player, pull) : [],
      shading: points.map((point) => ({ time: point.time, damage: Math.min(scale.maximum, incomingDamage(point)), healAbsorbs: 0 })),
    };
  }, [pull, player, layers, allMitigation, fullRange, hiddenPlayerIds]);
}
