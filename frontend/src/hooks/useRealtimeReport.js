import { reportPulls, watchedPulls, watchRevision } from "../utils/reportPullUpdates";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const POLL_INTERVAL_MS = 10_000;
const ERROR_RETRY_MS = 20_000;
const REQUIRED_STABLE_OBSERVATIONS = 2;
const MIN_STABLE_ELAPSED_MS = 8_000;

async function fetchWatchSnapshot({ reportId, values, forceRefresh = false, signal }) {
  const response = await fetch(`/api/v2/reports/${reportId}/watch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values, force_refresh: forceRefresh }),
    signal,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(
      payload.detail || `Unable to check Warcraft Logs (${response.status}).`
    );
  }
  return payload;
}

export function useRealtimeReport({
  page,
  reportId,
  values,
  isActive,
  isJobBusy,
  jobError,
  refreshReport,
}) {
  const [enabled, setEnabled] = useState(false);
  const [status, setStatus] = useState("off");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(null);
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const knownFightIdsRef = useRef(new Set());
  const observationsRef = useRef(new Map());
  const revisionRef = useRef(null);
  const pendingRefreshRef = useRef(null);
  const pageRef = useRef(page);
  const manualControllerRef = useRef(null);
  const reportCode = String(values?.report_codes || values?.report_code || page?.reportCode || "");
  const currentPulls = useMemo(() => reportPulls(page), [page]);

  const supportsPullUpdates = currentPulls.size > 0 || ["timeline", "defensive_timeline"].includes(page?.content?.variant);
  const hasFixedFightSelection = values?.fight_selection === "specific";
  const isAvailable =
    supportsPullUpdates && Boolean(reportCode) && !hasFixedFightSelection;
  const unavailableReason = !supportsPullUpdates
      ? "This report does not expose pull-level updates."
      : !reportCode
        ? "This report does not expose a Warcraft Logs report code."
        : hasFixedFightSelection
          ? "Real-time mode requires All pulls or Last pull instead of a fixed pull."
        : "";

  useEffect(() => {
    for (const fightId of currentPulls.keys()) {
      knownFightIdsRef.current.add(fightId);
    }

    const pending = pendingRefreshRef.current;
    if (!pending || pageRef.current === page) {
      pageRef.current = page;
      return;
    }
    pageRef.current = page;

    const refreshedFightIds = pending.manual
      ? [...currentPulls.keys()].filter(
          (fightId) => !pending.previousFightIds.has(fightId)
        )
      : pending.fightIds;
    const newestFightId = refreshedFightIds.at(-1);
    const newestPull = currentPulls.get(newestFightId);
    if (refreshedFightIds.length && !newestPull) {
      return;
    }

    pendingRefreshRef.current = null;
    setIsManualRefreshing(false);
    setStatus(enabled ? "watching" : "off");
    if (newestPull) {
      setNotice({
        title: "New pull available",
        message:
          refreshedFightIds.length === 1
            ? `${newestPull.label} added`
            : `${refreshedFightIds.length} new pulls added`,
        viewId: newestPull.value,
      });
    } else if (pending.manual) {
      setNotice({
        title: "No new pulls found",
        message: "Latest Warcraft Logs data loaded; no new pulls were found.",
        viewId: null,
      });
    } else {
      setNotice({
        title: "Report updated",
        message: "Report refreshed from Warcraft Logs",
        viewId: null,
      });
    }
  }, [enabled, page, currentPulls]);

  useEffect(() => {
    setEnabled(false);
    setStatus("off");
    setError("");
    setNotice(null);
    setIsManualRefreshing(false);
    observationsRef.current.clear();
    revisionRef.current = null;
    pendingRefreshRef.current = null;
    knownFightIdsRef.current = new Set(reportPulls(pageRef.current).keys());
    return () => manualControllerRef.current?.abort();
  }, [reportCode, reportId]);

  useEffect(() => {
    if (enabled && !isAvailable) {
      setEnabled(false);
      setStatus("off");
    }
  }, [enabled, isAvailable]);

  useEffect(() => {
    if (enabled && !isActive && !isJobBusy) {
      setStatus("paused");
    }
  }, [enabled, isActive, isJobBusy]);

  useEffect(() => {
    if (!pendingRefreshRef.current || isJobBusy || !jobError) {
      return;
    }
    pendingRefreshRef.current = null;
    setIsManualRefreshing(false);
    setStatus(enabled ? "error" : "off");
    setError(jobError);
  }, [enabled, isJobBusy, jobError]);

  useEffect(() => {
    if (!enabled || !isAvailable || !isActive || isJobBusy || isManualRefreshing) {
      return undefined;
    }

    let disposed = false;
    let timer = null;
    let controller = null;
    let checking = false;

    const schedule = (delay = POLL_INTERVAL_MS) => {
      if (!disposed) {
        timer = window.setTimeout(checkForUpdates, delay);
      }
    };

    const checkForUpdates = async () => {
      if (disposed || checking) {
        return;
      }
      if (document.visibilityState === "hidden") {
        setStatus("paused");
        schedule();
        return;
      }

      checking = true;
      controller = new AbortController();
      setStatus("checking");
      try {
        const payload = await fetchWatchSnapshot({
          reportId,
          values,
          signal: controller.signal,
        });
        if (disposed) {
          return;
        }

        const previousRevision = revisionRef.current;
        revisionRef.current = watchRevision(payload);
        const newFights = watchedPulls(payload)
          .filter((fight) => !knownFightIdsRef.current.has(fight.key));
        const visibleNewFightIds = new Set(newFights.map((fight) => fight.key));
        for (const fightId of observationsRef.current.keys()) {
          if (!visibleNewFightIds.has(fightId)) {
            observationsRef.current.delete(fightId);
          }
        }

        const stableFights = [];
        for (const fight of newFights) {
          const fightId = fight.key;
          const endTime = Number(fight.end_time);
          const prior = observationsRef.current.get(fightId);
          const observedAt = Date.now();
          const sameEndTime = prior?.endTime === endTime;
          const stableCount =
            sameEndTime && observedAt - prior.firstObservedAt >= MIN_STABLE_ELAPSED_MS
              ? prior.stableCount + 1
              : 1;
          observationsRef.current.set(fightId, {
            endTime,
            stableCount,
            firstObservedAt: sameEndTime ? prior.firstObservedAt : observedAt,
          });
          if (stableCount >= REQUIRED_STABLE_OBSERVATIONS) {
            stableFights.push(fight);
          }
        }

        const revisionChangedWithoutNewPull =
          previousRevision !== null &&
          watchRevision(payload) !== previousRevision &&
          newFights.length === 0;
        if (stableFights.length || revisionChangedWithoutNewPull) {
          const fightIds = stableFights.map((fight) => fight.key);
          pendingRefreshRef.current = { fightIds };
          setStatus("updating");
          setError("");
          const queued = await refreshReport({ reportId, values });
          if (!queued && !disposed) {
            pendingRefreshRef.current = null;
            setStatus("error");
            setError("Unable to queue the real-time report update.");
            schedule(ERROR_RETRY_MS);
          }
          return;
        }

        setError("");
        setStatus("watching");
        schedule();
      } catch (err) {
        if (disposed || err.name === "AbortError") {
          return;
        }
        setStatus("error");
        setError(err.message || "Unable to check Warcraft Logs for new pulls.");
        schedule(ERROR_RETRY_MS);
      } finally {
        checking = false;
      }
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState !== "hidden") {
        if (timer) {
          window.clearTimeout(timer);
        }
        checkForUpdates();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    schedule(0);
    return () => {
      disposed = true;
      if (timer) {
        window.clearTimeout(timer);
      }
      controller?.abort();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [enabled, isActive, isAvailable, isJobBusy, isManualRefreshing, refreshReport, reportId, values]);

  const toggle = useCallback(() => {
    if (!isAvailable) {
      return;
    }
    setEnabled((current) => {
      const next = !current;
      setStatus(next ? "checking" : "off");
      setError("");
      if (!next) {
        observationsRef.current.clear();
        pendingRefreshRef.current = null;
      }
      return next;
    });
  }, [isAvailable]);

  const refresh = useCallback(async () => {
    if (!reportId || isJobBusy || isManualRefreshing) {
      return;
    }
    const previousFightIds = new Set(reportPulls(pageRef.current).keys());
    const controller = new AbortController();
    manualControllerRef.current = controller;
    setIsManualRefreshing(true);
    setStatus("checking");
    setError("");
    setNotice(null);
    try {
      const snapshot = await fetchWatchSnapshot({
        reportId,
        values,
        forceRefresh: true,
        signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      const newFightIds = watchedPulls(snapshot)
        .map((fight) => fight.key)
        .filter((fightId) => !previousFightIds.has(fightId));

      pendingRefreshRef.current = {
        fightIds: newFightIds,
        manual: true,
        previousFightIds,
      };
      setStatus("updating");
      const queued = await refreshReport({ reportId, values });
      if (controller.signal.aborted) return;
      if (queued) {
        return;
      }

      pendingRefreshRef.current = null;
      setIsManualRefreshing(false);
      setStatus(enabled ? "error" : "off");
      setError("Unable to queue the report refresh.");
    } catch (err) {
      if (controller.signal.aborted || err.name === "AbortError") return;
      pendingRefreshRef.current = null;
      setIsManualRefreshing(false);
      setStatus(enabled ? "error" : "off");
      setError(err.message || "Unable to check Warcraft Logs for new pulls.");
    }
  }, [enabled, isJobBusy, isManualRefreshing, refreshReport, reportId, values]);

  return {
    enabled,
    status,
    error,
    notice,
    isAvailable,
    isVisible: supportsPullUpdates,
    isBusy: isJobBusy || isManualRefreshing,
    isRefreshing: isManualRefreshing,
    unavailableReason,
    toggle,
    refresh,
    clearNotice: () => setNotice(null),
  };
}
