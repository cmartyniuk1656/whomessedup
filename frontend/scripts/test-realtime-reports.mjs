/** Simulate uploads and refreshed pages without relying on a live raid. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createServer } from "vite";
import React from "react";
import { JSDOM } from "jsdom";
import { reportPulls } from "../src/utils/reportPullUpdates.js";

const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "https://hklogs.example/", pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
Object.defineProperty(globalThis, "navigator", { configurable: true, value: dom.window.navigator });
const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: "custom" });
const originalNow = Date.now;
const originalFetch = globalThis.fetch;
let now = 0;
let nextTimer = 0;
const timers = new Map();
Date.now = () => now;
window.setTimeout = (callback, delay) => { const id = ++nextTimer; timers.set(id, { callback, at: now + delay }); return id; };
window.clearTimeout = (id) => timers.delete(id);
try {
  const { renderHook, render, fireEvent, cleanup, act } = await import("@testing-library/react");
  const { useRealtimeReport } = await server.ssrLoadModule("/src/hooks/useRealtimeReport.js");
  const { ReportResultsPanel } = await server.ssrLoadModule("/src/components/v2/organisms/ReportResultsPanel.jsx");
  const advance = async (ms) => {
    now += ms;
    const due = [...timers].filter(([, timer]) => timer.at <= now);
    await act(async () => { for (const [id, timer] of due) { timers.delete(id); await timer.callback(); } });
  };
  const pull = (code, id) => ({ id: `${code}:${id}`, reportCode: code, fightId: id, label: `Pull ${id}` });
  const page = (pulls, variant = "defensive_timeline") => ({ reportCode: "A, B", content: { variant, timeline: { pulls } } });
  let payload = { revisions: { A: 1, B: 1 }, fights: [{ report_code: "A", id: 1, end_time: 1000 }, { report_code: "B", id: 1, end_time: 2000 }] };
  let requests = 0;
  globalThis.fetch = async () => { requests++; return { ok: true, json: async () => payload }; };
  const queued = [];
  const refreshReport = async (request) => { queued.push(request); return true; };
  let props = { page: page([pull("A", 1)]), reportId: "defensive", values: { report_codes: ["A", "B"] }, isActive: true, isJobBusy: false, refreshReport };
  let hook = renderHook((input) => useRealtimeReport(input), { initialProps: props });
  assert.equal(hook.result.current.isAvailable, true);
  await act(async () => hook.result.current.toggle());
  await advance(0);
  assert.equal(queued.length, 0, "Do not fetch a report while its new pull is still uploading");
  payload.fights[1].end_time = 3000;
  await advance(10000);
  assert.equal(queued.length, 0, "An advancing fight end time resets stability");
  await advance(10000);
  assert.equal(queued.length, 1, "A fight with the same ID in another log is new");
  props = { ...props, isJobBusy: true };
  hook.rerender(props);
  const requestsBefore = requests;
  await advance(10000);
  assert.equal(requests, requestsBefore, "No polling while regenerating the report");
  props = { ...props, isJobBusy: false, page: page([pull("A", 1), pull("B", 1)]) };
  hook.rerender(props);
  assert.equal(hook.result.current.notice.viewId, "B:1");
  await advance(0);
  assert.equal(queued.length, 1, "Already loaded pulls are not regenerated");
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
  const beforeHidden = requests;
  await advance(10000);
  assert.equal(requests, beforeHidden, "Background tabs pause polling");
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
  await act(async () => hook.result.current.toggle());
  await act(async () => hook.result.current.refresh());
  assert.equal(queued.length, 2, "Manual refresh reloads late events even without new fights");
  hook.rerender({ ...props, page: structuredClone(props.page) });
  assert.equal(hook.result.current.notice.title, "No new pulls found");
  assert.equal(hook.result.current.isRefreshing, false);
  hook.unmount();

  // A failed metadata request retries, and revisions pick up edits to existing pulls.
  let fail = true;
  globalThis.fetch = async () => {
    if (fail) throw new Error("Temporary connection failure");
    return { ok: true, json: async () => payload };
  };
  hook = renderHook((input) => useRealtimeReport(input), { initialProps: props });
  await act(async () => hook.result.current.toggle());
  await advance(0);
  assert.equal(hook.result.current.status, "error");
  fail = false;
  await advance(20000);
  assert.equal(hook.result.current.status, "watching");
  payload.revisions.B++;
  await advance(10000);
  assert.equal(queued.length, 3, "A revision in either source reloads existing pulls");
  hook.unmount();

  for (const variant of ["defensive_timeline", "timeline"]) {
    hook = renderHook((input) => useRealtimeReport(input), { initialProps: { ...props, page: page([], variant) } });
    assert.equal(hook.result.current.isAvailable, true, "Empty timelines can pick up their first pull");
    hook.unmount();
  }
  const table = { content: { table: { viewControl: { options: [{ value: "pull:A:9", label: "Pull 9" }] } } } };
  assert.equal(reportPulls(table).get("A:9").value, "pull:A:9");

  // A stale manual metadata response must not regenerate the previous report after navigation.
  let resolveFetch;
  globalThis.fetch = () => new Promise((resolve) => { resolveFetch = resolve; });
  hook = renderHook((input) => useRealtimeReport(input), { initialProps: props });
  let pending;
  await act(async () => { pending = hook.result.current.refresh(); });
  hook.rerender({ ...props, reportId: "other-report" });
  await act(async () => { resolveFetch({ ok: true, json: async () => payload }); await pending; });
  assert.equal(queued.length, 3);
  hook.unmount();

  // Append a real fixture pull while retaining selections, then explicitly jump to it.
  const fixture = JSON.parse(await readFile(new URL("../../tests/fixtures/defensive_usage_page.json", import.meta.url), "utf8"));
  const first = structuredClone(fixture);
  first.content.timeline.pulls = first.content.timeline.pulls.slice(0, 1);
  const realtime = { isVisible: true, isAvailable: true, clearNotice: () => {} };
  const ui = render(React.createElement(ReportResultsPanel, { page: first, realtime }));
  const player = first.content.timeline.pulls[0].players[0];
  fireEvent.change(ui.getByLabelText("Defensive player"), { target: { value: player.id } });
  fireEvent.click(ui.getByRole("button", { name: "Across pulls" }));
  const boss = ui.container.querySelector(".coverage-boss-filters button[aria-pressed]");
  fireEvent.click(boss);
  const bossState = boss.getAttribute("aria-pressed");
  ui.rerender(React.createElement(ReportResultsPanel, { page: fixture, realtime: { ...realtime, notice: { title: "New pull available", message: "Added", viewId: fixture.content.timeline.pulls[1].id } } }));
  assert.equal(ui.getByLabelText("Defensive player").value, player.id);
  assert.equal(ui.getByRole("button", { name: "Across pulls" }).getAttribute("aria-pressed"), "true");
  assert.equal(ui.container.querySelector(".coverage-boss-filters button[aria-pressed]").getAttribute("aria-pressed"), bossState);
  fireEvent.click(ui.getByRole("button", { name: "View pull" }));
  assert.equal(ui.getByLabelText("Defensive pull").value, fixture.content.timeline.pulls[1].id);
  assert.equal(ui.getByLabelText("Defensive player").value, player.id);
  cleanup();
  console.log("Realtime reports: stable uploads, multiple logs, refresh, pause, cancellation and preserved timeline selections passed.");
} finally {
  Date.now = originalNow;
  globalThis.fetch = originalFetch;
  await server.close();
  dom.window.close();
}
