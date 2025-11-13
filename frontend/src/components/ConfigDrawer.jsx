import { Fragment } from "react";

export function ConfigDrawer({
  visible,
  tile,
  configValues,
  onOptionChange,
  onMultiTextChange,
  onMultiTextAdd,
  onMultiTextRemove,
  onCancel,
  onConfirm,
  isBusy,
}) {
  if (!visible || !tile) {
    return null;
  }

  const inputClasses =
    "w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-content placeholder:text-muted/70 focus:border-primary focus:ring focus:ring-primary/40 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60";
  const selectClasses = `${inputClasses} [&>option]:text-bg`;
  const secondaryButtonClasses =
    "inline-flex items-center rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-content hover:bg-white/10 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface disabled:cursor-not-allowed disabled:opacity-60";
  const primaryButtonClasses =
    "inline-flex items-center rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring focus-visible:ring-offset-2 ring-offset-surface disabled:cursor-not-allowed disabled:opacity-60";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/80 px-4 py-6 backdrop-blur">
      <div className="w-full max-w-lg rounded-xl2 border border-border/60 bg-glass-gradient p-6 shadow-glass backdrop-blur-md">
        <h2 className="text-lg font-semibold text-content">Report Configuration</h2>
        <p className="mt-1 text-sm text-muted">
          Adjust settings before running <span className="font-medium text-content">{tile.title}</span>.
        </p>
        <div className="mt-4 space-y-3 text-content">
          {tile.configOptions?.map((option) => {
            const optionType = option.type ?? "checkbox";
            if (optionType === "multi-text") {
              const rawValues = Array.isArray(configValues[option.id])
                ? configValues[option.id]
                : Array.isArray(option.default)
                ? option.default
                : [""];
              const values = rawValues.length ? rawValues : [""];
              return (
                <div key={option.id} className="flex flex-col gap-2 text-sm">
                  <span>{option.label}</span>
                  <div className="space-y-2">
                    {values.map((entryValue, index) => (
                      <div key={`${option.id}-${index}`} className="flex items-center gap-2">
                        <input
                          type="text"
                          className={`${inputClasses} flex-1`}
                          value={entryValue ?? ""}
                          placeholder={option.placeholder ?? "Report code or URL"}
                          onChange={(event) => onMultiTextChange(option.id, index, event.target.value)}
                          disabled={isBusy}
                        />
                        <button
                          type="button"
                          onClick={() => onMultiTextRemove(option.id, index)}
                          className={secondaryButtonClasses}
                          disabled={isBusy || values.length <= 1}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={() => onMultiTextAdd(option.id)}
                    className={`${secondaryButtonClasses} border-dashed px-4`}
                    disabled={isBusy}
                  >
                    + Add another
                  </button>
                </div>
              );
            }
            if (optionType === "select") {
              const selectValue =
                typeof configValues[option.id] === "string"
                  ? configValues[option.id]
                  : typeof option.default === "string"
                  ? option.default
                  : "";
              return (
                <label key={option.id} className="flex flex-col gap-2 text-sm">
                  <span>{option.label}</span>
                  <select
                    className={selectClasses}
                    style={{ colorScheme: "dark" }}
                    value={selectValue}
                    onChange={(event) => onOptionChange(option.id, event.target.value)}
                    disabled={isBusy}
                  >
                    {(option.options ?? []).map((optChoice) => (
                      <option key={optChoice.value} value={optChoice.value}>
                        {optChoice.label ?? optChoice.value}
                      </option>
                    ))}
                  </select>
                </label>
              );
            }
            return (
              <label key={option.id} className="flex items-start gap-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary"
                  checked={
                    typeof configValues[option.id] === "boolean"
                      ? configValues[option.id]
                      : typeof option.default === "boolean"
                      ? option.default
                      : false
                  }
                  onChange={(event) => onOptionChange(option.id, event.target.checked)}
                  disabled={isBusy}
                />
                <span>{option.label}</span>
              </label>
            );
          })}
        </div>
        {tile.footnotes?.length ? (
          <div className="mt-4 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">Notes</p>
            <ul className="mt-2 space-y-1 text-xs text-muted">
              {tile.footnotes.map((note) => (
                <li key={note}>* {note}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onCancel} className={`${secondaryButtonClasses} px-5 py-2 text-sm`} disabled={isBusy}>
            Cancel
          </button>
          <button type="button" onClick={onConfirm} className={primaryButtonClasses} disabled={isBusy}>
            Run Report
          </button>
        </div>
      </div>
    </div>
  );
}
