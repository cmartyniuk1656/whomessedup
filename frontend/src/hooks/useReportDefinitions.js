import { useEffect, useState } from "react";

export function useReportDefinitions() {
  const [reports, setReports] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isCancelled = false;

    async function loadDefinitions() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch("/api/v2/report-definitions");
        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          throw new Error(detail?.detail || `Failed to load report definitions (${response.status}).`);
        }
        const data = await response.json();
        if (!isCancelled) {
          setReports(Array.isArray(data?.reports) ? data.reports : []);
        }
      } catch (err) {
        const message =
          err instanceof TypeError
            ? "Failed to load report definitions. Confirm the backend is running on http://localhost:8088."
            : err.message || "Failed to load report definitions.";
        if (!isCancelled) {
          setError(message);
          setReports([]);
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    }

    loadDefinitions();

    return () => {
      isCancelled = true;
    };
  }, []);

  return {
    reports,
    error,
    loading,
  };
}
