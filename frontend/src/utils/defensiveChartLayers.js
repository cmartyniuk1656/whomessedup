/** Filter presentation data without changing recorded evidence or cast details. */
import { DEFAULT_DEFENSIVE_LAYERS } from "../config/defensiveChartLayers.js";

export function filterDamagePoints(points, layers = DEFAULT_DEFENSIVE_LAYERS) {
  return points.map((point) => {
    const matched = Math.min(point.absorbed || 0, point.cooldownAbsorbed || 0);
    const cooldownAbsorbed = layers.cooldownShields ? matched : 0;
    const otherAbsorbed = layers.otherShields ? Math.max(0, (point.absorbed || 0) - matched) : 0;
    return { ...point, damage: layers.damage ? point.damage : 0,
      absorbed: point.cooldownMode ? cooldownAbsorbed + otherAbsorbed : layers.shields ? point.absorbed : 0,
      cooldownAbsorbed: point.cooldownMode ? cooldownAbsorbed : layers.shields ? matched : 0,
      mitigated: layers.reduction ? point.mitigated : 0,
      immuneEvents: layers.immune ? point.immuneEvents : 0 };
  });
}
