import { Button } from "../atoms/Button";
import { StatusPill } from "../atoms/StatusPill";
import { ReportFieldControl } from "../molecules/ReportFieldControl";
import { ReportRunCard } from "../molecules/ReportRunCard";

const GLOBAL_CONFIGURATION_FIELD_IDS = new Set([
  "ignore_after_deaths",
  "ignore_unavoidable_after_healer_deaths",
  "kill_only",
  "omit_dead_players",
  "fresh_run",
]);

function splitFields(fields) {
  return fields.reduce(
    (sections, field) => {
      if (GLOBAL_CONFIGURATION_FIELD_IDS.has(field.id)) {
        sections.globalFields.push(field);
      } else {
        sections.primaryFields.push(field);
      }
      return sections;
    },
    { primaryFields: [], globalFields: [] },
  );
}

function GlobalConfigurationSection({ children, compact = false }) {
  return (
    <section className={compact ? "rounded-lg border border-white/10 bg-slate-950/30 p-3.5" : "rounded-xl border border-white/10 bg-slate-950/25 p-4"}>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Global Configuration</p>
        <p className="mt-1 text-xs leading-5 text-slate-500">These settings apply across the full report.</p>
      </div>
      <div className={compact ? "mt-3 space-y-2.5" : "mt-4 space-y-3"}>{children}</div>
    </section>
  );
}

export function ReportRequestForm({
  report,
  values,
  isSubmitting,
  pendingJob,
  onSubmit,
  onCancel,
  onValueChange,
  onMultiTextChange,
  onAddMultiTextRow,
  onRemoveMultiTextRow,
  layout = "sidebar",
}) {
  const fields = report?.requestSchema?.fields ?? [];
  const notes = report?.footnotes ?? [];
  const statusLabel = pendingJob ? (pendingJob.status === "running" ? "Running" : "Queued") : "Ready";
  const statusTone = pendingJob ? (pendingJob.status === "running" ? "accent" : "warning") : "neutral";
  const { primaryFields, globalFields } = splitFields(fields);

  const renderField = (field, density) => (
    <ReportFieldControl
      key={field.id}
      field={field}
      value={values?.[field.id]}
      onValueChange={onValueChange}
      onMultiTextChange={onMultiTextChange}
      onAddMultiTextRow={onAddMultiTextRow}
      onRemoveMultiTextRow={onRemoveMultiTextRow}
      density={density}
    />
  );

  if (layout === "modal") {
    return (
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <div className="max-h-[min(58vh,30rem)] space-y-3.5 overflow-y-auto pr-1">
          {primaryFields.map((field) => renderField(field, "compact"))}

          {globalFields.length ? (
            <GlobalConfigurationSection compact>{globalFields.map((field) => renderField(field, "compact"))}</GlobalConfigurationSection>
          ) : null}

          {notes.length ? (
            <div className="rounded-lg border border-white/10 bg-slate-950/30 p-3.5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Notes</p>
              <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs leading-5 text-slate-300 marker:text-slate-500">
                {notes.map((note, index) => (
                  <li key={`${report?.id || "report"}-note-${index}`}>{note}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        <div className="flex flex-col gap-3 border-t border-white/10 pt-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <StatusPill tone={statusTone}>{statusLabel}</StatusPill>
            </div>
            {pendingJob ? (
              <p className="break-all text-xs text-slate-500">
                {typeof pendingJob.position === "number" && pendingJob.position > 0
                  ? `Position in queue: ${pendingJob.position} | `
                  : ""}
                Job ID: {pendingJob.id}
              </p>
            ) : null}
          </div>

          <div className="flex gap-3 sm:justify-end">
            <Button type="button" variant="secondary" size="sm" onClick={onCancel} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
              {isSubmitting ? "Running..." : "Run report"}
            </Button>
          </div>
        </div>
      </form>
    );
  }

  return (
    <form
      className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_18rem]"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="space-y-5">
        {primaryFields.map((field) => renderField(field, "default"))}
        {globalFields.length ? <GlobalConfigurationSection>{globalFields.map((field) => renderField(field, "default"))}</GlobalConfigurationSection> : null}
      </div>

      <aside className="border-t border-white/10 pt-6 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
        <ReportRunCard report={report} isSubmitting={isSubmitting} pendingJob={pendingJob} />
      </aside>
    </form>
  );
}
