export function isOptionEnabled(option, values = {}) {
  if (!option || !option.dependsOn) {
    return true;
  }
  const dependencies = Array.isArray(option.dependsOn) ? option.dependsOn : [option.dependsOn];
  return dependencies.every((depId) => {
    if (!depId) {
      return true;
    }
    const raw = values?.[depId];
    if (typeof raw === "boolean") {
      return raw;
    }
    if (Array.isArray(raw)) {
      return raw.length > 0;
    }
    if (raw === null || raw === undefined) {
      return false;
    }
    if (typeof raw === "number") {
      return raw !== 0;
    }
    const normalized = String(raw).trim();
    if (!normalized || normalized === "false") {
      return false;
    }
    return true;
  });
}
