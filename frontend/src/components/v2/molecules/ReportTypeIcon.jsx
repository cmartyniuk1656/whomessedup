import { getReportType, REPORT_TYPES } from "../../../config/reportTypes";

const ICON_TONES = {
  [REPORT_TYPES.AGGREGATE]: "text-emerald-300",
  [REPORT_TYPES.MECHANICS]: "text-cyan-300",
  [REPORT_TYPES.DEATHS]: "text-rose-300",
  [REPORT_TYPES.AVOIDABLE_DAMAGE]: "text-amber-300",
  [REPORT_TYPES.DAMAGE]: "text-orange-300",
  [REPORT_TYPES.COOLDOWNS]: "text-violet-300",
  [REPORT_TYPES.DISPELS]: "text-sky-300",
  [REPORT_TYPES.GENERIC]: "text-slate-300",
};

function IconPaths({ type }) {
  switch (type) {
    case REPORT_TYPES.AGGREGATE:
      return (
        <>
          <rect x="3.5" y="3.5" width="6.5" height="6.5" rx="1.25" />
          <rect x="14" y="3.5" width="6.5" height="6.5" rx="1.25" />
          <rect x="3.5" y="14" width="6.5" height="6.5" rx="1.25" />
          <path d="M17.25 14v6.5M14 17.25h6.5" />
        </>
      );
    case REPORT_TYPES.MECHANICS:
      return (
        <>
          <path d="M14.1 6.4a4.3 4.3 0 0 0-5.35 5.35L3.8 16.7a2.45 2.45 0 1 0 3.5 3.5l4.95-4.95a4.3 4.3 0 0 0 5.35-5.35l-2.45 2.45-3.5-3.5 2.45-2.45Z" />
          <circle cx="5.55" cy="18.45" r=".7" fill="currentColor" stroke="none" />
        </>
      );
    case REPORT_TYPES.DEATHS:
      return (
        <>
          <path d="M5.25 10.25a6.75 6.75 0 1 1 13.5 0c0 2.5-1.35 4.4-3.3 5.45v3.55H8.55V15.7c-1.95-1.05-3.3-2.95-3.3-5.45Z" />
          <circle cx="9.5" cy="10.25" r="1" />
          <circle cx="14.5" cy="10.25" r="1" />
          <path d="m12 12.25-1 1.75h2l-1-1.75ZM10.2 19.25v-2.1M13.8 19.25v-2.1" />
        </>
      );
    case REPORT_TYPES.AVOIDABLE_DAMAGE:
      return (
        <>
          <path d="M12 3 21 20H3L12 3Z" />
          <path d="M12 8.5v5.25" />
          <circle cx="12" cy="17" r=".75" fill="currentColor" stroke="none" />
        </>
      );
    case REPORT_TYPES.DAMAGE:
      return (
        <>
          <path d="m14.5 4.25 5.25 5.25-9.9 9.9-5.25-5.25 9.9-9.9Z" />
          <path d="m12.25 6.5 5.25 5.25M7 16.5l-3.25 3.25M15.25 3.5l5.25 5.25" />
        </>
      );
    case REPORT_TYPES.COOLDOWNS:
      return (
        <>
          <circle cx="12" cy="12.5" r="8.25" />
          <path d="M12 8v4.75l3.25 2M9.5 2.75h5" />
        </>
      );
    case REPORT_TYPES.DISPELS:
      return (
        <>
          <path d="m12 3 1.35 4.2L17.5 8.5l-4.15 1.3L12 14l-1.35-4.2L6.5 8.5l4.15-1.3L12 3Z" />
          <path d="m18.25 14 .7 2.05 2.05.7-2.05.7-.7 2.05-.7-2.05-2.05-.7 2.05-.7.7-2.05ZM5.25 14.5l.5 1.5 1.5.5-1.5.5-.5 1.5-.5-1.5-1.5-.5 1.5-.5.5-1.5Z" />
        </>
      );
    default:
      return (
        <>
          <path d="M6 3.5h8l4 4v13H6v-17Z" />
          <path d="M14 3.5v4h4M9 12h6M9 16h6" />
        </>
      );
  }
}

export function ReportTypeIcon({ report }) {
  const type = getReportType(report);
  return (
    <span
      aria-hidden="true"
      className={`inline-flex h-9 w-9 shrink-0 items-center justify-center ${ICON_TONES[type]}`}
    >
      <svg
        viewBox="0 0 24 24"
        className="h-7 w-7"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <IconPaths type={type} />
      </svg>
    </span>
  );
}
