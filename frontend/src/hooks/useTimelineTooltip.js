/** Position rich timeline tooltips in the viewport, outside clipped scroll tracks. */
import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { timelineTooltipPosition } from "../utils/timelineTooltip";

export function useTimelineTooltip() {
  const id = useId();
  const anchor = useRef(null);
  const popup = useRef(null);
  const timer = useRef(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ left: 8, top: 8 });
  const cancelHide = () => clearTimeout(timer.current);
  const show = () => { cancelHide(); setOpen(true); };
  const hide = () => { cancelHide(); setOpen(false); };
  const leave = () => {
    cancelHide();
    timer.current = setTimeout(() => setOpen(false), 160);
  };
  useEffect(() => () => clearTimeout(timer.current), []);
  useLayoutEffect(() => {
    if (!open || !anchor.current || !popup.current) return;
    const positionPopup = () => {
      if (!anchor.current || !popup.current) return;
      const rect = anchor.current.getBoundingClientRect();
      const box = popup.current.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) { setOpen(false); return; }
      setPosition(timelineTooltipPosition(rect,
        { width: box.width, height: popup.current.scrollHeight + 2 },
        { width: window.innerWidth, height: window.innerHeight }));
    };
    positionPopup();
    const dismiss = () => setOpen(false);
    const escape = (event) => { if (event.key === "Escape") dismiss(); };
    // Focusing an off-screen marker can scroll it into view. Keep its tooltip
    // open and reposition it, rather than immediately dismissing keyboard help.
    const scroll = (event) => {
      if (!(event.target instanceof window.Node) || !popup.current?.contains(event.target)) positionPopup();
    };
    window.addEventListener("resize", positionPopup);
    window.addEventListener("scroll", scroll, true);
    document.addEventListener("keydown", escape);
    return () => {
      window.removeEventListener("resize", positionPopup);
      window.removeEventListener("scroll", scroll, true);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);
  return {
    id, anchor, popup, open, position, hide,
    triggerProps: { onPointerEnter: show, onPointerLeave: leave, onFocus: show, onBlur: hide,
      "aria-describedby": open ? id : undefined },
    popupProps: { onPointerEnter: show, onPointerLeave: leave },
  };
}
