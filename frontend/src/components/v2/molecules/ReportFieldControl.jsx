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
        type={field.kind === "number" ? "number" : "text"}
        value={value ?? ""}
        placeholder={field.placeholder || ""}
        onChange={(event) => onValueChange(field.id, event.target.value)}
        className={compact ? "mt-1.5 py-2" : undefined}
      />
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
