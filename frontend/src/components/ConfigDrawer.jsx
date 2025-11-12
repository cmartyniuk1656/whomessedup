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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 py-6">
      <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-xl shadow-emerald-500/10">
        <h2 className="text-lg font-semibold text-white">Report Configuration</h2>
        <p className="mt-1 text-sm text-slate-400">
          Adjust settings before running <span className="font-medium text-slate-200">{tile.title}</span>.
        </p>
        <div className="mt-4 space-y-3">
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
                <div key={option.id} className="flex flex-col gap-2 text-sm text-slate-200">
                  <span>{option.label}</span>
                  <div className="space-y-2">
                    {values.map((entryValue, index) => (
                      <div key={`${option.id}-${index}`} className="flex items-center gap-2">
                        <input
                          type="text"
                          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                          value={entryValue ?? ""}
                          placeholder={option.placeholder ?? "Report code or URL"}
                          onChange={(event) => onMultiTextChange(option.id, index, event.target.value)}
                          disabled={isBusy}
                        />
                        <button
                          type="button"
                          onClick={() => onMultiTextRemove(option.id, index)}
                          className="rounded-lg border border-slate-600 px-2 py-1 text-xs font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800 disabled:opacity-40"
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
                    className="self-start rounded-lg border border-dashed border-slate-600 px-3 py-1 text-xs font-medium text-slate-200 transition hover:border-emerald-500 hover:text-emerald-400 disabled:opacity-40"
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
                <label key={option.id} className="flex flex-col gap-2 text-sm text-slate-200">
                  <span>{option.label}</span>
                  <select
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
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
              <label key={option.id} className="flex items-start gap-3 text-sm text-slate-200">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-400"
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
          <div className="mt-4 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-2">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Notes</p>
            <ul className="mt-2 space-y-1 text-xs text-slate-400">
              {tile.footnotes.map((note) => (
                <li key={note}>* {note}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800"
            disabled={isBusy}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
            disabled={isBusy}
          >
            Run Report
          </button>
        </div>
      </div>
    </div>
  );
}
