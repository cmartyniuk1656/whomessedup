import { FieldHint } from "./FieldHint";

export function CheckboxField({ id, label, description, checked, onChange, compact = false }) {
  const wrapperClasses = compact
    ? "flex items-start gap-2.5 px-1 py-0 text-sm text-slate-200"
    : "flex items-start gap-3 rounded-lg border border-white/10 bg-slate-950/35 px-4 py-3.5 text-sm text-slate-200 transition hover:border-white/15 hover:bg-white/[0.03]";

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
        <span className="font-medium text-slate-100">{label}</span>
        <FieldHint>{description}</FieldHint>
      </span>
    </label>
  );
}
