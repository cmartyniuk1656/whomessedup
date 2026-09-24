/** Capture mounted report controls without rerendering the report on every change. */
import { useCallback, useContext, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";
import { ViewContext, ScopeContext } from "./reportViewContext";

function compatible(value, fallback) {
  if (fallback == null) return value == null || typeof value === "string" || typeof value === "object";
  if (Array.isArray(fallback)) return Array.isArray(value) && value.every((item) => ["string", "number"].includes(typeof item));
  if (typeof fallback === "object") return value && !Array.isArray(value) && Object.keys(fallback).every((key) => typeof value[key] === typeof fallback[key]);
  return typeof value === typeof fallback && (typeof value !== "number" || Number.isFinite(value));
}

export function useReportViewState(name, initial, { resetKey = "", validate } = {}) {
  const context = useContext(ViewContext);
  const scope = useContext(ScopeContext);
  const key = `${scope}/${name}${resetKey ? `:${resetKey}` : ""}`;
  const initialize = () => {
    const fallback = typeof initial === "function" ? initial() : initial;
    const saved = context?.registry.saved[key];
    return { key, value: saved !== undefined && compatible(saved, fallback) && (!validate || validate(saved)) ? saved : fallback };
  };
  const [state, setState] = useState(initialize);
  let current = state;
  if (state.key !== key) {
    current = initialize();
    setState(current);
  }
  const value = current.value;
  useLayoutEffect(() => {
    if (!context) return;
    context.registry.saved[key] = value;
    context.registry.active.set(key, () => value);
    return () => { context.registry.active.delete(key); };
  }, [context, key, value]);
  const setValue = useCallback((next) => setState((previous) => {
    const value = typeof next === "function" ? next(previous.value) : next;
    return previous.key === key && Object.is(previous.value, value) ? previous : { key, value };
  }), [key]);
  return [value, setValue];
}

export function useReportShareUrl() {
  const context = useContext(ViewContext);
  return context?.share ?? ((url) => url);
}

export function useReportViewScroll(name) {
  const context = useContext(ViewContext);
  const scope = useContext(ScopeContext);
  const ref = useRef(null);
  const key = `${scope}/scroll:${name}`;
  useLayoutEffect(() => {
    const element = ref.current;
    if (!context || !element) return;
    const position = context.registry.saved[key];
    if (Number.isFinite(position) && position >= 0) element.scrollLeft = position;
    context.registry.active.set(key, () => element.scrollLeft);
    return () => {
      context.registry.saved[key] = element.scrollLeft;
      context.registry.active.delete(key);
    };
  }, [context, key]);
  return ref;
}

const subscribeHash = (listener) => {
  window.addEventListener("hashchange", listener);
  return () => window.removeEventListener("hashchange", listener);
};
export function useReportViewHash() {
  return useSyncExternalStore(subscribeHash, () => window.location.hash, () => "");
}
