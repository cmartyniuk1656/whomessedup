/** Keep a rich tooltip inside the viewport without covering its own trigger. */
export function timelineTooltipPosition(anchor, popup, viewport) {
  const margin = 8;
  const gap = 10;
  const width = Math.min(popup.width, viewport.width - margin * 2);
  const height = Math.min(popup.height, viewport.height - margin * 2);
  const centered = Math.max(margin, Math.min(viewport.width - width - margin,
    anchor.left + anchor.width / 2 - width / 2));
  const above = anchor.top - margin - gap;
  const below = viewport.height - anchor.bottom - margin - gap;
  const full = { maxHeight: viewport.height - margin * 2 };
  if (height <= above) return { left: centered, top: anchor.top - gap - height, ...full };
  if (height <= below) return { left: centered, top: anchor.bottom + gap, ...full };
  const sideTop = Math.max(margin, Math.min(viewport.height - height - margin, anchor.top - height / 2));
  if (anchor.right + gap + width <= viewport.width - margin)
    return { left: anchor.right + gap, top: sideTop, ...full };
  if (anchor.left - gap - width >= margin)
    return { left: anchor.left - gap - width, top: sideTop, ...full };
  // Narrow screens use a shorter scrollable popup above/below the marker.
  return above >= below
    ? { left: centered, top: margin, maxHeight: Math.max(0, above) }
    : { left: centered, top: anchor.bottom + gap, maxHeight: Math.max(0, below) };
}
