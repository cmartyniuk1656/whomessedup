import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "who-messed-up.guild-report-discovery.v1";

function readStoredSettings() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null");
    if (parsed?.guildName && parsed?.serverSlug && parsed?.serverRegion) {
      return parsed;
    }
  } catch {
    // Ignore malformed or unavailable browser storage.
  }
  return null;
}

async function requestGuildReports(settings) {
  const params = new URLSearchParams({
    guild_name: settings.guildName.trim(),
    server_slug: settings.serverSlug.trim(),
    server_region: settings.serverRegion.trim(),
    limit: "20",
  });
  const response = await fetch(`/api/v2/wcl/guild-reports?${params.toString()}`);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Unable to load guild reports (${response.status}).`);
  }
  return payload;
}

export function useGuildReportDiscovery() {
  const [settings, setSettings] = useState(readStoredSettings);
  const [guild, setGuild] = useState(null);
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const skipNextAutomaticLoadRef = useRef(false);

  const load = useCallback(async (candidate) => {
    if (!candidate) {
      setGuild(null);
      setReports([]);
      return null;
    }
    setIsLoading(true);
    setError("");
    try {
      const payload = await requestGuildReports(candidate);
      setGuild(payload.guild);
      setReports(payload.reports || []);
      return payload;
    } catch (err) {
      setGuild(null);
      setReports([]);
      setError(err.message || "Unable to load guild reports.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (settings) {
      if (skipNextAutomaticLoadRef.current) {
        skipNextAutomaticLoadRef.current = false;
        return;
      }
      load(settings).catch(() => {});
    }
  }, [load, settings]);

  const saveSettings = useCallback(async (candidate) => {
    const normalized = {
      guildName: candidate.guildName.trim(),
      serverSlug: candidate.serverSlug.trim().toLowerCase(),
      serverRegion: candidate.serverRegion.trim().toUpperCase(),
    };
    const payload = await load(normalized);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
    skipNextAutomaticLoadRef.current = true;
    setSettings(normalized);
    return payload;
  }, [load]);

  const clearSettings = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    skipNextAutomaticLoadRef.current = false;
    setSettings(null);
    setGuild(null);
    setReports([]);
    setError("");
  }, []);

  return {
    settings,
    guild,
    reports,
    isLoading,
    error,
    saveSettings,
    clearSettings,
    refresh: () => load(settings),
  };
}
