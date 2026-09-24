/** CPU/render benchmark using a saved report page; no Warcraft Logs requests. */
import { readFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createServer } from "vite";
import React from "react";
import { JSDOM } from "jsdom";

const fixture = JSON.parse(await readFile(process.argv[2] || "../tests/fixtures/defensive_usage_page.json", "utf8"));
const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "http://localhost" });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: "custom" });
try {
  const { render, fireEvent, cleanup } = await import("@testing-library/react");
  const { ReportPageView } = await server.ssrLoadModule("/src/components/v2/organisms/ReportPageView.jsx");
  const durations = [];
  const start = performance.now();
  const view = render(React.createElement(React.Profiler, { id: "defensives", onRender: (_, phase, actualDuration) => durations.push(actualDuration) }, React.createElement(ReportPageView, { page: fixture })));
  const mountMs = performance.now() - start;
  const measure = (callback) => {
    durations.length = 0;
    callback();
    const sorted = [...durations].sort((a, b) => a - b);
    return { commits: sorted.length, medianMs: Number(sorted[Math.floor(sorted.length / 2)]?.toFixed(2)), totalMs: Number(sorted.reduce((sum, value) => sum + value, 0).toFixed(2)) };
  };
  const cursor = () => { for (let value = 1; value <= 40; value++) fireEvent.change(view.getByLabelText("Inspect defensive timeline time"), { target: { value: String(value) } }); };
  const personalCursor = measure(cursor);
  fireEvent.change(view.getByLabelText("Defensive player"), { target: { value: "all" } });
  const everyoneCursor = measure(cursor);
  const everyoneNodes = view.container.querySelectorAll("*").length;
  if (view.queryByLabelText("Player health")) fireEvent.click(view.getByLabelText("Player health"));
  const everyoneHealthCursor = measure(cursor);
  const aggregate = measure(() => fireEvent.click(view.getByRole("button", { name: "Across pulls" })));
  console.log(JSON.stringify({ pulls: fixture.content.timeline.pulls.length, mountMs: Math.round(mountMs), personalCursor, everyoneCursor, everyoneHealthCursor, everyoneNodes, aggregate }, null, 2));
  cleanup();
} finally { await server.close(); dom.window.close(); }
