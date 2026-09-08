import { useCallback, useEffect, useRef, useState } from "react";
import { encodeReportValues } from "../utils/reportShareLink";

export function useReportJob() {
  const [page, setPage] = useState(null);
  const [error, setError] = useState("");
  const [pendingJob, setPendingJob] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const pollRef = useRef({ timer: null, jobId: null });

  const stopPolling = useCallback(() => {
    if (pollRef.current.timer) {
      clearTimeout(pollRef.current.timer);
    }
    pollRef.current = { timer: null, jobId: null };
  }, []);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  const clearReportState = useCallback(() => {
    stopPolling();
    setPage(null);
    setError("");
    setPendingJob(null);
    setIsSubmitting(false);
    setIsRefreshing(false);
  }, [stopPolling]);

  const requestJobStatus = useCallback(
    async (jobId) => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          throw new Error(detail?.detail || "Failed to fetch job status.");
        }
        const data = await response.json();
        if (pollRef.current.jobId !== jobId) {
          return;
        }

        if (data.status === "completed" && data.result) {
          stopPolling();
          setPendingJob(null);
          setIsSubmitting(false);
          setIsRefreshing(false);
          setPage(data.result);
          return;
        }

        if (data.status === "failed") {
          stopPolling();
          setPendingJob(null);
          setIsSubmitting(false);
          setIsRefreshing(false);
          setError(data.error || "Report generation failed.");
          return;
        }

        setPendingJob(data);
        pollRef.current.timer = setTimeout(() => requestJobStatus(jobId), 500);
      } catch (err) {
        if (pollRef.current.jobId !== jobId) {
          return;
        }
        stopPolling();
        setPendingJob(null);
        setIsSubmitting(false);
        setIsRefreshing(false);
        setError(err.message || "Failed to poll job status.");
      }
    },
    [stopPolling]
  );

  const submitReport = useCallback(
    async ({ reportId, values, preservePage = false }) => {
      if (!reportId) {
        setError("No report selected.");
        return false;
      }

      stopPolling();
      setError("");
      setPendingJob(null);
      if (!preservePage) {
        setPage(null);
      }
      setIsSubmitting(true);
      setIsRefreshing(preservePage);

      try {
        const response = await fetch(`/api/v2/reports/${reportId}/jobs`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ values }),
        });

        if (response.status === 202) {
          const payload = await response.json().catch(() => null);
          const job = payload?.job;
          if (!job?.id) {
            throw new Error("Unable to queue report job.");
          }
          setPendingJob(job);
          pollRef.current.jobId = job.id;
          requestJobStatus(job.id);
          return true;
        }

        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          throw new Error(detail?.detail || `Request failed (${response.status}).`);
        }

        const data = await response.json();
        setPage(data);
        setIsRefreshing(false);
        return true;
      } catch (err) {
        const message =
          err instanceof TypeError
            ? "Report request failed. Confirm the backend and development API proxy are running."
            : err.message || "Something went wrong.";
        setError(message);
        setIsRefreshing(false);
        return false;
      } finally {
        if (!pollRef.current.jobId) {
          setIsSubmitting(false);
        }
      }
    },
    [requestJobStatus, stopPolling]
  );

  const runReport = useCallback(
    ({ reportId, values }) => submitReport({ reportId, values, preservePage: false }),
    [submitReport]
  );

  const refreshReport = useCallback(
    ({ reportId, values }) =>
      submitReport({
        reportId,
        values: { ...values, fresh_run: true },
        preservePage: true,
      }),
    [submitReport]
  );

  const loadCachedReport = useCallback(
    async ({ reportId, values }) => {
      if (!reportId) {
        setError("No report selected.");
        return { ok: false, cacheMiss: false };
      }

      stopPolling();
      setError("");
      setPendingJob(null);
      setPage(null);
      setIsSubmitting(true);
      setIsRefreshing(false);

      try {
        const encodedValues = encodeReportValues(values);
        const response = await fetch(
          `/api/v2/reports/${reportId}/cached?values=${encodeURIComponent(encodedValues)}`
        );

        if (response.status === 404) {
          return { ok: false, cacheMiss: true };
        }

        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          throw new Error(detail?.detail || `Cached report request failed (${response.status}).`);
        }

        const data = await response.json();
        setPage(data);
        return { ok: true, cacheMiss: false };
      } catch (err) {
        const message =
          err instanceof TypeError
            ? "Cached report request failed. Confirm the backend and development API proxy are running."
            : err.message || "Cached report request failed.";
        setError(message);
        return { ok: false, cacheMiss: false };
      } finally {
        setIsSubmitting(false);
      }
    },
    [stopPolling]
  );

  return {
    clearReportState,
    page,
    error,
    isSubmitting,
    isRefreshing,
    pendingJob,
    loadCachedReport,
    runReport,
    refreshReport,
    setError,
  };
}
