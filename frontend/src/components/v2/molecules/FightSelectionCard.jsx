import GlassCard from "../../ui/GlassCard";
import { StatusPill } from "../atoms/StatusPill";

function getAvailabilityLabel(reportCount) {
  if (reportCount === 1) {
    return "1 report available";
  }

  if (reportCount > 1) {
    return `${reportCount} reports available`;
  }

  return "No reports yet";
}

export function FightSelectionCard({ fight, isSelected, reportCount, onSelect }) {
  const availabilityLabel = getAvailabilityLabel(reportCount);
  const buttonClasses = [
    "group h-full w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300 focus-visible:ring-offset-2 ring-offset-surface",
  ].join(" ");
  const cardClasses = [
    "h-full",
    isSelected ? "ring-1 ring-emerald-400/60 shadow-[0_30px_80px_-40px_rgba(16,185,129,0.55)]" : null,
  ]
    .filter(Boolean)
    .join(" ");
  const artCardClasses = [
    "relative h-full min-h-[160px] overflow-hidden rounded-[26px]",
    "bg-[linear-gradient(160deg,rgba(18,31,48,0.98)_0%,rgba(12,20,35,0.97)_62%,rgba(7,12,23,1)_100%)]",
    "ring-1 ring-white/5 transition-all duration-300 ease-out will-change-transform",
    "group-hover:-translate-y-1 group-hover:ring-white/10 group-hover:shadow-[0_30px_80px_-40px_rgba(16,185,129,0.55)]",
    "group-focus-visible:ring-white/15",
    isSelected ? "ring-emerald-400/60 shadow-[0_30px_80px_-40px_rgba(16,185,129,0.55)]" : null,
  ]
    .filter(Boolean)
    .join(" ");

  const buttonLabel = `${fight.title}, ${availabilityLabel}${isSelected ? ", selected" : ""}`;

  if (fight.art) {
    return (
      <button
        type="button"
        onClick={() => onSelect(fight.id)}
        className={buttonClasses}
        aria-pressed={isSelected}
        aria-label={buttonLabel}
      >
        <div className={artCardClasses}>
          <div className="pointer-events-none absolute inset-y-0 right-0 w-3/5 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.18),transparent_58%)]" />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-[linear-gradient(180deg,transparent_0%,rgba(5,9,18,0.55)_100%)]" />

          <div className="absolute right-5 top-5 z-10 max-w-[10.5rem] text-right">
            <h3
              className={[
                "text-xl font-semibold leading-tight text-slate-50 drop-shadow-[0_6px_16px_rgba(0,0,0,0.6)]",
                isSelected ? "text-emerald-50" : null,
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {fight.title}
            </h3>
          </div>

          <div className="pointer-events-none absolute -bottom-2 left-0 z-[1] flex h-[84%] w-[72%] items-end justify-start pl-2">
            <img
              src={fight.art}
              alt=""
              className="max-h-full w-auto object-contain object-left-bottom mix-blend-lighten drop-shadow-[0_20px_30px_rgba(0,0,0,0.55)]"
              loading="lazy"
            />
          </div>
        </div>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onSelect(fight.id)}
      className={buttonClasses}
      aria-pressed={isSelected}
      aria-label={buttonLabel}
    >
      <GlassCard className={cardClasses} title={fight.title}>
        <div className="flex h-full flex-col gap-4 text-content">
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill tone={isSelected ? "accent" : "neutral"}>{isSelected ? "Selected" : "Available"}</StatusPill>
            <StatusPill tone={reportCount > 0 ? "accent" : "warning"}>{availabilityLabel}</StatusPill>
          </div>
          <p className="text-sm text-muted">
            {reportCount > 0
              ? "Reports are ready to browse for this boss and difficulty."
              : "No reports are available for this boss and difficulty yet."}
          </p>
          <div className="mt-auto inline-flex items-center gap-2 text-sm font-medium text-primary">
            {isSelected ? "Browsing reports" : "Select boss"}
          </div>
        </div>
      </GlassCard>
    </button>
  );
}

export default FightSelectionCard;
