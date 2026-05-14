import { CLASS_COLORS, DEFAULT_PLAYER_COLOR, ROLE_BADGE_STYLES } from "../../../config/presentation";
import { formatReportTableCellValue } from "../../../utils/reportTablePresentation";
import { Tooltip } from "../atoms/Tooltip";

const BADGE_TONES = {
  tank: ROLE_BADGE_STYLES.Tank,
  healer: ROLE_BADGE_STYLES.Healer,
  melee: ROLE_BADGE_STYLES.Melee,
  ranged: ROLE_BADGE_STYLES.Ranged,
  unknown: ROLE_BADGE_STYLES.Unknown,
};

const INDICATOR_TONES = {
  danger: "text-red-300 drop-shadow-[0_0_6px_rgba(248,113,113,0.45)]",
  warning: "text-amber-300 drop-shadow-[0_0_6px_rgba(252,211,77,0.35)]",
  success: "text-emerald-300 drop-shadow-[0_0_6px_rgba(52,211,153,0.35)]",
  info: "text-sky-300 drop-shadow-[0_0_6px_rgba(125,211,252,0.35)]",
};

function AttentionIndicator({ indicator }) {
  const tone = String(indicator?.tone || "danger").toLowerCase();
  const label = indicator?.label || "More information available";

  return (
    <Tooltip content={label} placement="right" triggerClassName="align-middle">
      <span
        className={`inline-flex h-4 w-4 shrink-0 items-center justify-center ${INDICATOR_TONES[tone] || INDICATOR_TONES.danger}`}
        role="img"
        aria-label={label}
      >
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true" focusable="false">
          <path
            d="M12 3.25 22 20.5H2L12 3.25Z"
            fill="currentColor"
            fillOpacity="0.16"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M12 8v6" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
          <circle cx="12" cy="17" r="1.25" fill="currentColor" />
        </svg>
      </span>
    </Tooltip>
  );
}

export function TableCellContent({ column, cell }) {
  const content = formatReportTableCellValue({
    value: cell?.value,
    display: cell?.display,
    column,
  });

  if (column.cellKind === "badge") {
    const tone = String(cell?.tone || "unknown").toLowerCase();
    return (
      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${BADGE_TONES[tone] || BADGE_TONES.unknown}`}>
        {content}
      </span>
    );
  }

  if (column.cellKind === "player") {
    const color = CLASS_COLORS[String(cell?.colorToken || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
    const text = (
      <span className="font-medium tracking-tight" style={{ color }}>
        {content}
      </span>
    );
    const name = cell?.href ? (
      <a
        href={cell.href}
        target="_blank"
        rel="noreferrer"
        className="underline decoration-dotted underline-offset-2 hover:opacity-90"
      >
        {text}
      </a>
    ) : (
      text
    );

    return (
      <span className="inline-flex min-w-0 items-center gap-1.5 align-middle">
        {name}
        {cell?.indicators?.map((indicator) => (
          <AttentionIndicator key={`${cell.value}-${indicator.id}`} indicator={indicator} />
        ))}
      </span>
    );
  }

  if (column.cellKind === "link" && cell?.href) {
    return (
      <a href={cell.href} target="_blank" rel="noreferrer" className="text-emerald-300 underline decoration-dotted underline-offset-2">
        {content}
      </a>
    );
  }

  return content;
}
