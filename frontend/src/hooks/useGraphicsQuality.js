import { useCallback, useEffect, useLayoutEffect, useState } from "react";

const STORAGE_KEY = "who-messed-up.graphics-quality.v1";

export const GRAPHICS_QUALITY = {
  HIGH: "high",
  LOW: "low",
};

function normalizeGraphicsQuality(value) {
  return value === GRAPHICS_QUALITY.LOW ? GRAPHICS_QUALITY.LOW : GRAPHICS_QUALITY.HIGH;
}

function readStoredGraphicsQuality() {
  try {
    return normalizeGraphicsQuality(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return GRAPHICS_QUALITY.HIGH;
  }
}

export function useGraphicsQuality() {
  const [graphicsQuality, setGraphicsQualityState] = useState(readStoredGraphicsQuality);

  useLayoutEffect(() => {
    document.documentElement.dataset.graphicsQuality = graphicsQuality;
    try {
      window.localStorage.setItem(STORAGE_KEY, graphicsQuality);
    } catch {
      // The preference still applies for this session when storage is unavailable.
    }
  }, [graphicsQuality]);

  useEffect(() => {
    const handleStorage = (event) => {
      if (event.key === STORAGE_KEY) {
        setGraphicsQualityState(normalizeGraphicsQuality(event.newValue));
      }
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const setGraphicsQuality = useCallback((quality) => {
    setGraphicsQualityState(normalizeGraphicsQuality(quality));
  }, []);

  return { graphicsQuality, setGraphicsQuality };
}
