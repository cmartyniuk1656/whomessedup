import { useCallback, useEffect, useRef, useState } from "react";

const normalizeBoolean = (value) => {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    return value === "true" || value === "1";
  }
  if (typeof value === "number") {
    return value === 1;
  }
  return Boolean(value);
};

const resolveConfigForTile = (tile, overrides) => {
  if (!tile?.configOptions?.length) {
    return {};
  }
  const resolved = {};
  tile.configOptions.forEach((opt) => {
    const optionType = opt.type ?? "checkbox";
    let rawValue;
    if (Object.prototype.hasOwnProperty.call(overrides, opt.id)) {
      rawValue = overrides[opt.id];
    } else if (opt.default !== undefined) {
      rawValue = opt.default;
    } else if (optionType === "select" && Array.isArray(opt.options) && opt.options.length > 0) {
      rawValue = opt.options[0].value;
    } else if (optionType === "multi-text") {
      rawValue = [];
    } else if (optionType === "checkbox") {
      rawValue = false;
    }

    if (rawValue === undefined) {
      return;
    }

    if (optionType === "select") {
      resolved[opt.id] = String(rawValue);
      return;
    }
    if (optionType === "multi-text") {
      if (Array.isArray(rawValue)) {
        resolved[opt.id] = rawValue.map((entry) => (entry == null ? "" : String(entry)));
      } else if (typeof rawValue === "string") {
        resolved[opt.id] = [rawValue];
      } else {
        resolved[opt.id] = [];
      }
      return;
    }
    if (optionType === "checkbox") {
      resolved[opt.id] = normalizeBoolean(rawValue);
      return;
    }
    resolved[opt.id] = rawValue;
  });

  return resolved;
};

export function useTileRunner() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loadingId, setLoadingId] = useState(null);
  const [pendingJob, setPendingJob] = useState(null);
  const jobPollRef = useRef({ timer: null, id: null });

  const stopJobPolling = useCallback(() => {
    if (jobPollRef.current.timer) {
      clearTimeout(jobPollRef.current.timer);
    }
    jobPollRef.current = { timer: null, id: null };
  }, []);

  useEffect(() => {
    return () => {
      stopJobPolling();
    };
  }, [stopJobPolling]);

  const requestJobStatus = useCallback(
    async (jobId, tile) => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          throw new Error(detail?.detail || "Failed to fetch job status.");
        }
        const data = await response.json();
        if (jobPollRef.current.id !== jobId) {
          return;
        }

        if (data.status === "completed" && data.result) {
          stopJobPolling();
          setPendingJob(null);
          setLoadingId(null);
          setResult({
            ...data.result,
            abilityLabel: tile.title,
            tileTitle: tile.title,
          });
          return;
        }

        if (data.status === "failed") {
          stopJobPolling();
          setPendingJob(null);
          setLoadingId(null);
          setError(data.error || "Report generation failed.");
          return;
        }

        setPendingJob(data);
        jobPollRef.current.timer = setTimeout(() => requestJobStatus(jobId, tile), 1500);
      } catch (err) {
        if (jobPollRef.current.id !== jobId) {
          return;
        }
        stopJobPolling();
        setPendingJob(null);
        setLoadingId(null);
        setError(err.message || "Failed to poll job status.");
      }
    },
    [stopJobPolling]
  );

  const runTile = useCallback(
    async ({
      tile,
      reportCode,
      fightName,
      ignoreAfterDeaths,
      ignoreFinalSeconds,
      configOverrides = {},
    }) => {
      if (!tile) {
        setError("No tile selected.");
        return;
      }
      if (!reportCode) {
        setError("Enter a Warcraft Logs report URL or code first.");
        return;
      }

      stopJobPolling();
      setPendingJob(null);
      setError("");
      setResult(null);
      setLoadingId(tile.id);

      const params = new URLSearchParams({ report: reportCode });
      if (fightName?.trim()) {
        params.set("fight", fightName.trim());
      }
      if (tile.params) {
        Object.entries(tile.params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.set(key, String(value));
          }
        });
      }

      const deathsValue = (ignoreAfterDeaths || "").trim();
      const deathsNum = deathsValue ? Number.parseInt(deathsValue, 10) : NaN;
      if (!Number.isNaN(deathsNum) && deathsNum > 0) {
        params.set("ignore_after_deaths", String(deathsNum));
      }

      const finalValue = (ignoreFinalSeconds || "").trim();
      const finalNum = finalValue ? Number.parseFloat(finalValue) : NaN;
      if (!Number.isNaN(finalNum) && finalNum > 0) {
        params.set("ignore_final_seconds", String(finalNum));
      }

      const resolvedConfig = resolveConfigForTile(tile, configOverrides);
      if (tile.configOptions?.length) {
        tile.configOptions.forEach((opt) => {
          const optionType = opt.type ?? "checkbox";
          const value = resolvedConfig[opt.id];
          if (value === undefined || value === null) {
            return;
          }
          if (optionType === "select") {
            params.set(opt.param, String(value));
            return;
          }
          if (optionType === "multi-text") {
            const list = Array.isArray(value) ? value : [value];
            list
              .map((entry) => (entry == null ? "" : String(entry).trim()))
              .filter((entry) => entry.length > 0)
              .forEach((entry) => {
                params.append(opt.param, entry);
              });
            return;
          }
          const boolValue = normalizeBoolean(value);
          if (opt.value !== undefined) {
            if (boolValue) {
              params.append(opt.param, String(opt.value));
            }
          } else {
            params.set(opt.param, boolValue ? "true" : "false");
          }
        });
      }

      let jobQueued = false;
      try {
        const response = await fetch(`${tile.endpoint}?${params.toString()}`);
        if (response.status === 202) {
          const payload = await response.json().catch(() => null);
          const job = payload?.job;
          if (!job?.id) {
            throw new Error("Unable to queue report job.");
          }
          jobQueued = true;
          setPendingJob(job);
          jobPollRef.current.id = job.id;
          requestJobStatus(job.id, tile);
          return;
        }
        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          throw new Error(detail?.detail || "Request failed");
        }

        const data = await response.json();
        setResult({
          ...data,
          tileTitle: tile.title,
          abilityLabel: tile.title,
        });
      } catch (err) {
        setError(err.message || "Something went wrong.");
      } finally {
        if (!jobQueued) {
          setLoadingId(null);
        }
      }
    },
    [requestJobStatus, stopJobPolling]
  );

  const cancelJob = useCallback(() => {
    stopJobPolling();
    setPendingJob(null);
    setLoadingId(null);
  }, [stopJobPolling]);

  return {
    result,
    error,
    setError,
    loadingId,
    pendingJob,
    runTile,
    cancelJob,
  };
}
