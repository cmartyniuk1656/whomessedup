import { CLASS_COLORS, DEFAULT_PLAYER_COLOR, ROLE_BADGE_STYLES } from "../../../config/presentation";
import { formatReportTableCellValue } from "../../../utils/reportTablePresentation";
import { colorWithAlpha } from "../../../utils/colorPresentation";
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
  ejected: "text-violet-300 drop-shadow-[0_0_6px_rgba(196,181,253,0.4)]",
  warning: "text-amber-300 drop-shadow-[0_0_6px_rgba(252,211,77,0.35)]",
  success: "text-emerald-300 drop-shadow-[0_0_6px_rgba(52,211,153,0.35)]",
  info: "text-sky-300 drop-shadow-[0_0_6px_rgba(125,211,252,0.35)]",
};

const PLAYER_LIST_TONES = {
  danger: "bg-rose-400/10 ring-1 ring-inset ring-rose-300/35",
  ejected: "bg-violet-400/10 ring-1 ring-inset ring-violet-300/35",
  warning: "bg-amber-400/10 ring-1 ring-inset ring-amber-300/30",
  default: "bg-white/[0.035]",
};

function PlayerStatusIndicator({ indicator }) {
  const tone = String(indicator?.tone || "danger").toLowerCase();
  const label = indicator?.label || "Player status";
  const isSkull = indicator?.icon === "skull";

  return (
    <Tooltip content={label} placement="top" triggerClassName="align-middle">
      <span
        className={`inline-flex h-4 w-4 shrink-0 items-center justify-center ${INDICATOR_TONES[tone] || INDICATOR_TONES.danger}`}
        role="img"
        aria-label={label}
      >
        {isSkull ? (
          <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true" focusable="false">
            <path
              d="M5.5 10.1a6.5 6.5 0 1 1 13 0c0 2.35-1.25 4.15-3.15 5.2V19h-2.1v-2.35h-2.5V19h-2.1v-3.7C6.75 14.25 5.5 12.45 5.5 10.1Z"
              fill="currentColor"
              fillOpacity="0.2"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinejoin="round"
            />
            <circle cx="9.4" cy="10.2" r="1.25" fill="currentColor" />
            <circle cx="14.6" cy="10.2" r="1.25" fill="currentColor" />
            <path d="m12 12.2-1 1.7h2l-1-1.7Z" fill="currentColor" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true" focusable="false">
            <circle cx="12" cy="12" r="8.75" fill="currentColor" fillOpacity="0.13" stroke="currentColor" strokeWidth="1.7" />
            <path d="M12 16.5v-9m0 0L8.7 10.8M12 7.5l3.3 3.3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </span>
    </Tooltip>
  );
}

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

  if (column.cellKind === "relative_bar") {
    const value = Number(cell?.value ?? 0);
    const maximum = Number(cell?.maxValue ?? 0);
    const ratio = maximum > 0 ? Math.min(Math.max(value / maximum, 0), 1) : 0;
    const percent = Math.round(ratio * 100);
    const color =
      CLASS_COLORS[String(cell?.colorToken || "").toLowerCase()] ?? DEFAULT_PLAYER_COLOR;
    const label = cell?.label || "Damage";
    const unitLabel = cell?.unitLabel || "damage";

    return (
      <div className="grid min-w-[36rem] grid-cols-[10rem_minmax(20rem,1fr)] items-center gap-3">
        <span
          className="truncate text-right text-sm font-semibold tracking-tight"
          style={{ color }}
        >
          {label}
        </span>
        <div className="relative h-7 overflow-hidden rounded-md border border-white/10 bg-slate-950/45">
          <div
            className="flex h-full items-center justify-end rounded-r-md border-r px-2.5 text-xs font-semibold tabular-nums text-white transition-[width] duration-300"
            style={{
              width: `${ratio * 100}%`,
              minWidth: value > 0 ? "8.5rem" : 0,
              borderRightColor: colorWithAlpha(color, 0.72),
              background: `linear-gradient(90deg, ${colorWithAlpha(color, 0.52)}, ${colorWithAlpha(color, 0.88)})`,
              boxShadow: `0 0 18px -8px ${colorWithAlpha(color, 0.9)}`,
            }}
            role="progressbar"
            aria-label={`${label}: ${content} ${unitLabel}, ${percent}% of the highest value`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
            title={`${label}: ${content} ${unitLabel} (${percent}%)`}
          >
            {value > 0 ? <span>{content} · {percent}%</span> : null}
          </div>
          {value <= 0 ? (
            <span className="absolute inset-y-0 right-2.5 flex items-center text-xs font-semibold tabular-nums text-slate-400">
              {content} · 0%
            </span>
          ) : null}
        </div>
      </div>
    );
  }

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

  if (column.cellKind === "player_list") {
    if (!cell?.players?.length) {
      return <span className="text-slate-400">{content}</span>;
    }
    return (
      <span className="flex min-w-72 flex-wrap gap-x-3 gap-y-1.5">
        {cell?.players?.map((player) => {
          const color =
            CLASS_COLORS[String(player?.colorToken || "").toLowerCase()] ??
            DEFAULT_PLAYER_COLOR;
          const playerName = player?.segments?.length ? (
            <span className="font-medium tracking-tight">
              {player.segments.map((segment, index) => {
                const segmentColor = segment?.colorToken
                  ? CLASS_COLORS[String(segment.colorToken).toLowerCase()] ??
                    DEFAULT_PLAYER_COLOR
                  : null;
                return (
                  <span
                    key={`${player.name}-segment-${index}`}
                    className={segmentColor ? undefined : "text-slate-400"}
                    style={segmentColor ? { color: segmentColor } : undefined}
                  >
                    {segment.text}
                  </span>
                );
              })}
            </span>
          ) : (
            <span className="font-medium tracking-tight" style={{ color }}>
              {player.name}
            </span>
          );
          return (
            <span
              key={player.name}
              className={[
                "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5",
                PLAYER_LIST_TONES[player?.tone] || PLAYER_LIST_TONES.default,
              ].join(" ")}
            >
              {player?.tooltip ? (
                <Tooltip
                  content={player.tooltip}
                  placement="top"
                  triggerClassName="align-middle"
                >
                  {playerName}
                </Tooltip>
              ) : (
                playerName
              )}
              {player?.indicators?.map((indicator) => (
                <PlayerStatusIndicator
                  key={`${player.name}-${indicator.id}`}
                  indicator={indicator}
                />
              ))}
            </span>
          );
        })}
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
