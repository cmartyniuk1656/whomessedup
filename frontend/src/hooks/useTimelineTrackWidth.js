/** Measure timeline tracks so crowded markers regroup on resize and zoom. */
import { useEffect, useRef, useState } from "react";

export function useTimelineTrackWidth() {
  const track = useRef(null);
  const [width, setWidth] = useState(1000);
  useEffect(() => {
    if (!globalThis.ResizeObserver) return;
    const observer = new ResizeObserver(([entry]) =>
      setWidth(entry.contentRect.width || 1000),
    );
    observer.observe(track.current);
    return () => observer.disconnect();
  }, []);
  return { track, width };
}
