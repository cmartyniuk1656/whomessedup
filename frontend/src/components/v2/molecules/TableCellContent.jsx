import { CLASS_COLORS, DEFAULT_PLAYER_COLOR, ROLE_BADGE_STYLES } from "../../../config/presentation";
import { formatReportTableCellValue } from "../../../utils/reportTablePresentation";

const BADGE_TONES = {
  tank: ROLE_BADGE_STYLES.Tank,
  healer: ROLE_BADGE_STYLES.Healer,
  melee: ROLE_BADGE_STYLES.Melee,
  ranged: ROLE_BADGE_STYLES.Ranged,
  unknown: ROLE_BADGE_STYLES.Unknown,
};

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

    if (cell?.href) {
      return (
        <a
          href={cell.href}
          target="_blank"
          rel="noreferrer"
          className="underline decoration-dotted underline-offset-2 hover:opacity-90"
        >
          {text}
        </a>
      );
    }

    return text;
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
