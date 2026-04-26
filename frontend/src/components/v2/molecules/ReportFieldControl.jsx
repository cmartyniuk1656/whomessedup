import { Button } from "../atoms/Button";
import { CheckboxField } from "../atoms/CheckboxField";
import { FieldHint } from "../atoms/FieldHint";
import { SelectInput } from "../atoms/SelectInput";
import { TextInput } from "../atoms/TextInput";

function TextFieldControl({ field, value, onValueChange, density }) {
  const compact = density === "compact";

  return (
    <div className={compact ? "space-y-1.5" : undefined}>
      <label className="text-sm font-medium text-slate-100" htmlFor={field.id}>
        {field.label}
      </label>
      <FieldHint>{field.description}</FieldHint>
      <TextInput
        id={field.id}
        type="text"
        value={value ?? ""}
        placeholder={field.placeholder || ""}
        onChange={(event) => onValueChange(field.id, event.target.value)}
        className={compact ? "mt-1.5 py-2" : undefined}
      />
    </div>
  );
}

function NumberFieldControl({ field, value, onValueChange, density }) {
  const compact = density === "compact";
  const parsedValue = Number.parseInt(value ?? "", 10);
  const canDecrement = Number.isNaN(parsedValue) || parsedValue > 0;
  const buttonClasses =
    "flex h-full w-9 items-center justify-center text-emerald-100 transition hover:bg-emerald-300/12 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-emerald-300/60 disabled:cursor-not-allowed disabled:text-slate-600";

  const changeBy = (delta) => {
    const currentValue = Number.isNaN(parsedValue) ? 0 : parsedValue;
    const nextValue = Math.max(0, currentValue + delta);
    onValueChange(field.id, String(nextValue));
  };

  return (
    <div className={compact ? "space-y-1.5" : undefined}>
      <label className="text-sm font-medium text-slate-100" htmlFor={field.id}>
        {field.label}
      </label>
      <FieldHint>{field.description}</FieldHint>
      <div
        className={[
          "flex w-full overflow-hidden rounded-lg border border-white/10 bg-slate-950/40 text-sm text-slate-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] transition hover:border-white/15 focus-within:border-emerald-400 focus-within:ring-2 focus-within:ring-emerald-400/30",
          compact ? "mt-1.5" : "mt-2",
        ].join(" ")}
      >
        <input
          id={field.id}
          type="number"
          min="0"
          step="1"
          inputMode="numeric"
          value={value ?? ""}
          placeholder={field.placeholder || ""}
          onChange={(event) => onValueChange(field.id, event.target.value)}
          className={[
            "numeric-input min-w-0 flex-1 bg-transparent px-3 text-slate-100 placeholder:text-slate-500 focus:outline-none",
            compact ? "py-2" : "py-2.5",
          ].join(" ")}
        />
        <div className="grid w-9 shrink-0 grid-rows-[1fr_auto_1fr] border-l border-white/10 bg-slate-950/55">
          <button
            type="button"
            className={buttonClasses}
            aria-label={`Increase ${field.label}`}
            onClick={() => changeBy(1)}
          >
            <svg aria-hidden="true" className="h-3 w-3" viewBox="0 0 12 12" fill="none">
              <path d="M3 7.25 6 4.25l3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <span aria-hidden className="h-px bg-emerald-300/15" />
          <button
            type="button"
            className={buttonClasses}
            aria-label={`Decrease ${field.label}`}
            onClick={() => changeBy(-1)}
            disabled={!canDecrement}
          >
            <svg aria-hidden="true" className="h-3 w-3" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.75 6 7.75l3-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function SelectFieldControl({ field, value, onValueChange, density }) {
  const compact = density === "compact";

  return (
    <div className={compact ? "space-y-1.5" : undefined}>
      <label className="text-sm font-medium text-slate-100" htmlFor={field.id}>
        {field.label}
      </label>
      <FieldHint>{field.description}</FieldHint>
      <SelectInput
        id={field.id}
        value={value ?? ""}
        onChange={(event) => onValueChange(field.id, event.target.value)}
        className={compact ? "mt-1.5 py-2" : undefined}
      >
        {(field.options ?? []).map((option) => (
          <option key={`${field.id}-${option.value}`} value={option.value}>
            {option.label}
          </option>
          ))}
      </SelectInput>
    </div>
  );
}

function CheckboxControl({ field, value, onValueChange, density }) {
  return (
    <CheckboxField
      id={field.id}
      label={field.label}
      description={field.description}
      tooltip={field.tooltip}
      checked={value}
      onChange={(event) => onValueChange(field.id, event.target.checked)}
      compact={density === "compact"}
    />
  );
}

function MultiTextInput({
  field,
  value,
  onMultiTextChange,
  onAddMultiTextRow,
  onRemoveMultiTextRow,
  density,
}) {
  const items = Array.isArray(value) ? value : [""];
  const compact = density === "compact";

  return (
    <div className={compact ? "space-y-2.5" : "space-y-3"}>
      <div>
        <label className="text-sm font-medium text-slate-100">{field.label}</label>
        <FieldHint>{field.description}</FieldHint>
      </div>
      <div className={compact ? "space-y-1.5" : "space-y-2"}>
        {items.map((item, index) => (
          <div key={`${field.id}-${index}`} className="flex items-center gap-2">
            <TextInput
              type="text"
              value={item}
              placeholder={field.placeholder || ""}
              onChange={(event) => onMultiTextChange(field.id, index, event.target.value)}
              className={compact ? "mt-0 py-2" : "mt-0"}
            />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className={compact ? "min-w-[4.75rem] shrink-0 bg-white/[0.04]" : undefined}
              onClick={() => onRemoveMultiTextRow(field.id, index)}
              disabled={items.length <= 1}
            >
              Remove
            </Button>
          </div>
        ))}
      </div>
      <Button
        type="button"
        variant={compact ? "secondary" : "accent"}
        size="sm"
        fullWidth={compact}
        className={compact ? "justify-start border-dashed bg-white/[0.04] text-slate-100 hover:bg-white/[0.06]" : undefined}
        onClick={() => onAddMultiTextRow(field.id)}
      >
        + Add another
      </Button>
    </div>
  );
}

export function ReportFieldControl({
  field,
  value,
  onValueChange,
  onMultiTextChange,
  onAddMultiTextRow,
  onRemoveMultiTextRow,
  density = "default",
}) {
  if (field.kind === "checkbox") {
    return <CheckboxControl field={field} value={value} onValueChange={onValueChange} density={density} />;
  }

  if (field.kind === "multi_text") {
    return (
      <MultiTextInput
        field={field}
        value={value}
        onMultiTextChange={onMultiTextChange}
        onAddMultiTextRow={onAddMultiTextRow}
        onRemoveMultiTextRow={onRemoveMultiTextRow}
        density={density}
      />
    );
  }

  if (field.kind === "select") {
    return <SelectFieldControl field={field} value={value} onValueChange={onValueChange} density={density} />;
  }

  return <TextFieldControl field={field} value={value} onValueChange={onValueChange} density={density} />;
}
