const REPORT_ID_PARAM = "reportId";
const REPORT_VALUES_PARAM = "values";

function toBase64Url(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromBase64Url(value) {
  const normalized = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
  const padded = `${normalized}${"=".repeat((4 - (normalized.length % 4)) % 4)}`;
  const binary = window.atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function encodeReportValues(values) {
  return toBase64Url(JSON.stringify(values ?? {}));
}

export function decodeReportValues(encodedValues) {
  const decoded = fromBase64Url(encodedValues);
  const values = JSON.parse(decoded);
  if (!values || typeof values !== "object" || Array.isArray(values)) {
    throw new Error("Cached report values must decode to an object.");
  }
  return values;
}

export function buildCachedReportUrl({ reportId, values, location = window.location }) {
  const url = new URL(location.href);
  url.hash = "";
  url.searchParams.set(REPORT_ID_PARAM, reportId);
  url.searchParams.set(REPORT_VALUES_PARAM, encodeReportValues(values));
  return url.toString();
}

// UI state belongs in the fragment: it does not alter API cache keys or reach the server.
export function buildReportViewUrl(baseUrl, state) {
  const url = new URL(baseUrl);
  url.hash = `view=${encodeReportValues({ version: 1, state })}`;
  return url.toString();
}

export function readReportView(baseUrl, location = window.location) {
  try {
    if (!baseUrl) return {};
    const base = new URL(baseUrl);
    const current = new URL(location.href);
    if ([REPORT_ID_PARAM, REPORT_VALUES_PARAM].some((key) => base.searchParams.get(key) !== current.searchParams.get(key))) return {};
    const encoded = new URLSearchParams(current.hash.slice(1)).get("view");
    if (!encoded || encoded.length > 64000) return {};
    const { version, state } = decodeReportValues(encoded);
    if (version !== 1 || !state || Array.isArray(state) || typeof state !== "object") return {};
    const entries = Object.entries(state);
    if (entries.length > 200) return {};
    return Object.fromEntries(entries.filter(([key]) => key.startsWith("/") && key.length < 1000));
  } catch {
    return {}; // Stale or malformed UI state must not prevent opening the report.
  }
}

export function parseCachedReportParams(search = window.location.search) {
  const params = new URLSearchParams(search);
  const reportId = params.get(REPORT_ID_PARAM);
  const encodedValues = params.get(REPORT_VALUES_PARAM);
  if (!reportId || !encodedValues) {
    return null;
  }
  return {
    reportId,
    values: decodeReportValues(encodedValues),
  };
}

