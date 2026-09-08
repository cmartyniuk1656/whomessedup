import { useState } from "react";

const INCLUDE_PREFIX = "aggregate_include__";
const CONFIGURATION_PATTERN = /^aggregate__(.+?)__(.+)$/;

function shortReportTitle(title) {
  const parts = String(title || "Report").split(" - ");
  return parts.at(-1) || "Report";
}

function groupAggregateFields(fields) {
  const includeFields = [];
  const configurationFields = new Map();
  const sharedFields = [];

  fields.forEach((field) => {
    if (field.id.startsWith(INCLUDE_PREFIX)) {
      includeFields.push({ reportId: field.id.slice(INCLUDE_PREFIX.length), field });
      return;
    }

    const match = field.id.match(CONFIGURATION_PATTERN);
    if (!match) {
      sharedFields.push(field);
      return;
    }

    const [, reportId] = match;
    const grouped = configurationFields.get(reportId) || [];
    grouped.push(field);
    configurationFields.set(reportId, grouped);
  });

  return {
    sharedFields,
    sections: includeFields.map(({ reportId, field }) => {
      const title = String(field.label || "Report").replace(/^Include\s+/i, "");
      return {
        id: reportId,
        title,
        shortTitle: shortReportTitle(title),
        description: field.description,
        includeField: field,
        fields: configurationFields.get(reportId) || [],
      };
    }),
  };
}

function fieldWithoutReportPrefix(field, reportTitle) {
  const prefix = `${reportTitle} - `;
  return field.label?.startsWith(prefix)
    ? { ...field, label: field.label.slice(prefix.length) }
    : field;
}

export function AggregateConfigurationSections({ fields, values, onValueChange, renderField }) {
  const { sharedFields, sections } = groupAggregateFields(fields);
  const [expandedSectionId, setExpandedSectionId] = useState("");

  return (
    <div className="space-y-3">
      {sharedFields.map((field) => renderField(field, "compact"))}

      {sections.map((section, index) => {
        const isIncluded = values?.[section.includeField.id] !== false;
        const isExpanded = expandedSectionId === section.id;
        const headingId = `aggregate-configuration-${section.id}`;
        const panelId = `${headingId}-panel`;

        return (
          <section
            key={section.id}
            aria-labelledby={headingId}
            className={`overflow-hidden rounded-xl border bg-slate-950/30 transition ${
              isExpanded ? "border-emerald-300/30" : "border-white/10"
            }`}
          >
            <div className="flex items-stretch">
              <h3 id={headingId} className="min-w-0 flex-1">
                <button
                  type="button"
                  aria-expanded={isExpanded}
                  aria-controls={panelId}
                  onClick={() =>
                    setExpandedSectionId((current) =>
                      current === section.id ? "" : section.id
                    )
                  }
                  className="flex h-full w-full items-center justify-between gap-3 px-3.5 py-3 text-left transition hover:bg-white/[0.04] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-300/40"
                >
                  <span className="min-w-0">
                    <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-300">
                      Report {index + 1}
                    </span>
                    <span className="mt-0.5 block truncate text-sm font-semibold text-white">
                      {section.shortTitle}
                    </span>
                  </span>
                  <svg
                    aria-hidden="true"
                    className={`h-4 w-4 text-slate-400 transition-transform ${
                      isExpanded ? "rotate-180" : ""
                    }`}
                    viewBox="0 0 20 20"
                    fill="none"
                  >
                    <path
                      d="m6 8 4 4 4-4"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1.75"
                    />
                  </svg>
                </button>
              </h3>
              <label className="flex shrink-0 cursor-pointer items-center gap-2 border-l border-white/10 px-3 text-xs font-medium text-slate-300 hover:text-white">
                <input
                  type="checkbox"
                  checked={isIncluded}
                  onChange={(event) => {
                    const checked = event.target.checked;
                    onValueChange(section.includeField.id, checked);
                    if (!checked) {
                      setExpandedSectionId((current) =>
                        current === section.id ? "" : current
                      );
                    }
                  }}
                  className="h-4 w-4 rounded border-white/20 bg-transparent text-emerald-400 focus:ring-emerald-400"
                />
                Enable
              </label>
            </div>

            <div
              id={panelId}
              role="region"
              aria-labelledby={headingId}
              aria-hidden={!isExpanded}
              inert={isExpanded ? undefined : ""}
              className={`grid transition-[grid-template-rows,opacity] duration-300 ease-in-out motion-reduce:transition-none ${
                isExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
              }`}
            >
              <div className="min-h-0 overflow-hidden">
                <div className="border-t border-white/10 px-3.5 pb-3.5 pt-3">
                  {section.description ? (
                    <p className="mb-3 text-xs leading-5 text-slate-500">{section.description}</p>
                  ) : null}
                  {isIncluded && section.fields.length ? (
                    <div className="space-y-3">
                      {section.fields.map((field) =>
                        renderField(fieldWithoutReportPrefix(field, section.title), "compact")
                      )}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}
