import { useId } from "react";

const PLACEMENT_CLASSES = {
  top: "bottom-full left-1/2 mb-2 -translate-x-1/2",
  right: "left-full top-1/2 ml-2 -translate-y-1/2",
  bottom: "left-1/2 top-full mt-2 -translate-x-1/2",
  left: "right-full top-1/2 mr-2 -translate-y-1/2",
};

const ARROW_CLASSES = {
  top: "left-1/2 top-full -translate-x-1/2 -translate-y-1/2",
  right: "right-full top-1/2 translate-x-1/2 -translate-y-1/2",
  bottom: "bottom-full left-1/2 -translate-x-1/2 translate-y-1/2",
  left: "left-full top-1/2 -translate-x-1/2 -translate-y-1/2",
};

export function Tooltip({
  content,
  placement = "top",
  className,
  triggerClassName,
  tooltipClassName,
  children,
}) {
  const tooltipId = useId();

  if (!content) {
    return children;
  }

  return (
    <span className={["group/tooltip relative inline-flex", className].filter(Boolean).join(" ")}>
      <span
        aria-describedby={tooltipId}
        tabIndex={0}
        className={[
          "inline-flex rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300/45 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950",
          triggerClassName,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {children}
      </span>
      <span
        id={tooltipId}
        role="tooltip"
        className={[
          "pointer-events-none absolute z-50 w-max max-w-72 rounded-lg border border-white/10 bg-slate-950/95 px-3 py-2 text-xs font-medium leading-snug text-slate-100 opacity-0 shadow-2xl shadow-black/40 backdrop-blur transition duration-150 group-hover/tooltip:opacity-100 group-focus-within/tooltip:opacity-100",
          PLACEMENT_CLASSES[placement] || PLACEMENT_CLASSES.top,
          tooltipClassName,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {content}
        <span
          className={[
            "absolute h-2 w-2 rotate-45 border-b border-r border-white/10 bg-slate-950/95",
            ARROW_CLASSES[placement] || ARROW_CLASSES.top,
          ]
            .filter(Boolean)
            .join(" ")}
          aria-hidden="true"
        />
      </span>
    </span>
  );
}
