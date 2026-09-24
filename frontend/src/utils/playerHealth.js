/** Read the health line at a time; never interpolate over missing observations. */
export function healthAtTime(points = [], time) {
  let low = 0;
  let high = points.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (points[middle].time <= time) low = middle + 1;
    else high = middle;
  }
  const next = points[low];
  const previous = points[low - 1];
  if (previous?.time === time) return previous.percent;
  if (!previous || !next || next.breakBefore) return null;
  return previous.percent + (next.percent - previous.percent) * (time - previous.time) / (next.time - previous.time);
}
