export function getDefaultFieldValue(field) {
  if (field.defaultValue !== undefined && field.defaultValue !== null) {
    if (field.kind === "multi_text") {
      if (Array.isArray(field.defaultValue) && field.defaultValue.length > 0) {
        return field.defaultValue.map((entry) => String(entry ?? ""));
      }
      return [""];
    }
    return field.defaultValue;
  }

  if (field.kind === "checkbox") {
    return false;
  }
  if (field.kind === "multi_text") {
    return [""];
  }
  return "";
}

export function buildInitialReportValues(reportDefinition) {
  const values = {};
  const fields = reportDefinition?.requestSchema?.fields ?? [];
  fields.forEach((field) => {
    values[field.id] = getDefaultFieldValue(field);
  });
  return values;
}
