import { FieldHint } from "./FieldHint";
import { Tooltip } from "./Tooltip";

function FieldTooltipContent({ tooltip }) {
  if (!tooltip?.description && !tooltip?.tags?.length) {
    return null;
  }

  return (
    <span className="block max-w-80 space-y-2">
      {tooltip.description ? <span className="block text-slate-100">{tooltip.description}</span> : null}
      {tooltip.tags?.length ? (
        <span className="flex flex-wrap gap-1.5">
          {tooltip.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-100"
            >
              {tag}
            </span>
          ))}
        </span>
      ) : null}
    </span>
  );
}

export function CheckboxField({ id, label, description, tooltip, checked, onChange, compact = false }) {
  const wrapperClasses = compact
    ? "flex items-start gap-2.5 px-1 py-0 text-sm text-slate-200"
    : "flex items-start gap-3 rounded-lg border border-white/10 bg-slate-950/35 px-4 py-3.5 text-sm text-slate-200 transition hover:border-white/15 hover:bg-white/[0.03]";
  const labelContent = tooltip ? (
    <Tooltip content={<FieldTooltipContent tooltip={tooltip} />} placement="right" triggerClassName="align-middle">
      <span className="font-medium text-slate-100 underline decoration-dotted underline-offset-2">{label}</span>
    </Tooltip>
  ) : (
    <span className="font-medium text-slate-100">{label}</span>
  );

  return (
    <label className={wrapperClasses}>
      <input
        id={id}
        type="checkbox"
        checked={Boolean(checked)}
        onChange={onChange}
        className="mt-0.5 h-4 w-4 rounded border-white/20 bg-transparent text-emerald-400 focus:ring-emerald-400"
      />
      <span>
        {labelContent}
        <FieldHint>{description}</FieldHint>
      </span>
    </label>
  );
}
