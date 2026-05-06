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
  url.searchParams.set(REPORT_ID_PARAM, reportId);
  url.searchParams.set(REPORT_VALUES_PARAM, encodeReportValues(values));
  return url.toString();
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

