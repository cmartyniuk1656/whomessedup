/** Reopen real copied links in fresh mounts, exercising production control initialization. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createServer } from "vite";
import React from "react";
import { JSDOM } from "jsdom";
import { buildCachedReportUrl, buildReportViewUrl, readReportView } from "../src/utils/reportShareLink.js";

const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "https://hklogs.example/", pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
let copied;
Object.defineProperty(globalThis, "navigator", { configurable: true, value: { userAgent: "test", clipboard: { writeText: async (text) => { copied = text; } } } });
const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: "custom" });
try {
  const { render, fireEvent, cleanup, act, configure } = await import("@testing-library/react");
  configure({ getElementError: (message) => new Error(message.split("Here are")[0]) });
  const { ReportResultsPanel } = await server.ssrLoadModule("/src/components/v2/organisms/ReportResultsPanel.jsx");
  const load = async (file) => JSON.parse(await readFile(new URL(`../../tests/fixtures/${file}`, import.meta.url), "utf8"));
  const defensive = await load("defensive_usage_page.json");
  const health = await load("defensive_health_samples.json");
  for (const pull of defensive.content.timeline.pulls) for (const player of pull.players) player.health = health[pull.id][player.id];
  const base = (page) => buildCachedReportUrl({ reportId: page.reportId, values: { report_codes: [page.reportCode] } });
  const mount = (page, url = base(page)) => {
    window.history.replaceState(null, "", url);
    return render(React.createElement(React.StrictMode, null, React.createElement(ReportResultsPanel, { page, shareUrl: base(page) })));
  };
  const share = async (view) => {
    await act(async () => fireEvent.click(view.getByRole("button", { name: "Share Report" })));
    assert.ok(copied.includes("#view="));
    return copied;
  };
  let view = mount(defensive);
  const mage = defensive.content.timeline.pulls[0].players.find((player) => player.name === "Chocolate");
  fireEvent.change(view.getByLabelText("Defensive player"), { target: { value: mage.id } });
  fireEvent.change(view.getByLabelText("Defensive pull"), { target: { value: defensive.content.timeline.pulls[1].id } });
  fireEvent.click(view.getByLabelText("Player health"));
  fireEvent.click(view.getByLabelText("Damage to health"));
  fireEvent.change(view.getByLabelText("Zoom"), { target: { value: "2" } });
  fireEvent.change(view.getByLabelText("Damage graph scale"), { target: { value: "full" } });
  fireEvent.click(view.getByRole("button", { name: "Exit full width" }));
  const bossButton = view.container.querySelector(".coverage-boss-filters button[aria-pressed]");
  assert.ok(bossButton);
  fireEvent.click(bossButton);
  const bossState = [...view.container.querySelectorAll(".coverage-boss-filters button[aria-pressed]")].map((button) => button.getAttribute("aria-pressed"));
  const cast = view.container.querySelector(".defensive-cast");
  const castName = cast.getAttribute("aria-label");
  fireEvent.click(cast);
  view.getByRole("region", { name: "Defensive usage timeline" }).scrollLeft = 220;
  let link = await share(view);
  assert.ok(link.length < 6000, `Link should hold control IDs, not report data: ${link.length}`);
  cleanup();
  view = mount(defensive, link);
  assert.equal(view.getByLabelText("Defensive player").value, mage.id);
  assert.equal(view.getByLabelText("Defensive pull").value, defensive.content.timeline.pulls[1].id);
  assert.equal(view.getByLabelText("Player health").checked, true);
  assert.equal(view.getByLabelText("Damage to health").checked, false);
  assert.equal(view.getByLabelText("Zoom").value, "2");
  assert.equal(view.getByLabelText("Damage graph scale").value, "full");
  assert.ok(view.getByRole("button", { name: "Expand report to full width" }));
  assert.ok(view.getByLabelText("Defensive usage details"));
  assert.ok(view.getByLabelText(castName));
  assert.equal(view.getByRole("region", { name: "Defensive usage timeline" }).scrollLeft, 220);
  assert.deepEqual([...view.container.querySelectorAll(".coverage-boss-filters button[aria-pressed]")].map((button) => button.getAttribute("aria-pressed")), bossState);
  fireEvent.click(view.getByLabelText("Close defensive details"));
  fireEvent.click(view.getByRole("button", { name: "Across pulls" }));
  const mechanic = defensive.content.timeline.pulls[0].bossLanes[0].spellId;
  fireEvent.change(view.getByLabelText("Aggregate alignment"), { target: { value: String(mechanic) } });
  fireEvent.change(view.getByLabelText("Mechanic occurrence"), { target: { value: "2" } });
  link = await share(view);
  cleanup(); view = mount(defensive, link);
  assert.equal(view.getByRole("button", { name: "Across pulls" }).getAttribute("aria-pressed"), "true");
  assert.equal(view.getByLabelText("Aggregate alignment").value, String(mechanic));
  assert.equal(view.getByLabelText("Mechanic occurrence").value, "2");
  fireEvent.click(view.getByRole("button", { name: "This pull" }));
  fireEvent.change(view.getByLabelText("Defensive player"), { target: { value: "all" } });
  fireEvent.click(view.getByRole("button", { name: "Hide all players" }));
  fireEvent.click(view.getByLabelText(`Show ${mage.name}`));
  link = await share(view);
  cleanup(); view = mount(defensive, link);
  assert.equal(view.getByLabelText("Defensive player").value, "all");
  assert.equal(view.container.querySelectorAll(".defensive-row").length, 1);
  assert.ok(view.getByText("Hidden players"));
  cleanup();

  const coverage = await load("cooldown_coverage_page.json");
  view = mount(coverage);
  fireEvent.change(view.getByLabelText("Pull"), { target: { value: coverage.content.timeline.pulls[1].id } });
  fireEvent.click(view.getByLabelText("Damage + heal absorbs"));
  fireEvent.click(view.getByLabelText("Estimated readiness"));
  const healer = view.getByLabelText("Healer").options[1].value;
  fireEvent.change(view.getByLabelText("Healer"), { target: { value: healer } });
  fireEvent.change(view.getByLabelText("Timeline zoom"), { target: { value: "2.5" } });
  fireEvent.click(view.container.querySelector(".coverage-cast:not(.coverage-boss-cast)"));
  link = await share(view);
  cleanup(); view = mount(coverage, link);
  assert.equal(view.getByLabelText("Pull").value, coverage.content.timeline.pulls[1].id);
  assert.equal(view.getByLabelText("Damage + heal absorbs").checked, false);
  assert.equal(view.getByLabelText("Estimated readiness").checked, false);
  assert.equal(view.getByLabelText("Healer").value, healer);
  assert.equal(view.getByLabelText("Timeline zoom").value, "2.5");
  assert.ok(view.getByLabelText("Ability details"));
  cleanup();

  // Synthetic table covers the shared controls used by mechanics/damage reports.
  const options = (ids) => ids.map((id) => ({ id, label: id }));
  const control = (id, values) => ({ id, label: id, defaultValue: values[0], options: values.map((value) => ({ value, label: value })) });
  const row = (id) => ({ id, cells: { name: { value: id }, role: { value: "healer" }, amount: { value: 10 }, targetTotal: { value: 10 } }, details: { metrics: [{ label: "Hits", value: 2 }] } });
  const tablePage = { reportId: "mechanics", reportCode: "test", title: "Mechanics", header: { subtitle: "test" }, summary: [], footnotes: [], content: { variant: "table", table: {
    columns: [{ id: "name", label: "Player", cellKind: "text", sortable: true }, { id: "amount", label: "Amount", cellKind: "number", sortable: true }, { id: "targetTotal", label: "Target damage", cellKind: "number" }], rows: [row("Alpha"), row("Zulu")],
    viewControl: control("Attempt", ["All attempts", "Pull two"]), secondaryViewControl: control("Category", ["Overview", "Orbs"]), subViewControlByView: { Orbs: control("Orb view", ["All orbs", "During channel"]) },
    rowFilter: { id: "role", label: "Role", options: options(["healer", "tank"]) }, columnFilter: { id: "columns", label: "Columns", options: options(["amount"]) },
    damageFilterConfig: { targetFilter: { id: "targets", label: "Targets", options: options(["Boss", "Adds"]) }, metricFilter: { id: "metrics", label: "Metrics", options: options(["totals", "averages"]) }, targetColumns: [{ targetId: "Boss", totalColumnId: "targetTotal" }] },
  } } };
  const multi = { ...tablePage, reportId: "combined", reportControl: control("Subreport", ["Default report", "Orb mechanics"]), reportsByView: { "Default report": tablePage, "Orb mechanics": tablePage } };
  view = mount(multi);
  const choose = (label, option) => { fireEvent.click(view.getByRole("button", { name: label })); fireEvent.click(view.getByRole("option", { name: option })); };
  choose("Subreport", "Orb mechanics");
  choose("Attempt", "Pull two"); choose("Category", "Orbs"); choose("Orb view", "During channel");
  for (const name of ["tank", "amount", "Adds", "averages"]) fireEvent.click(view.getByRole("button", { name, exact: true }));
  fireEvent.click(view.getByRole("button", { name: "Player" }));
  fireEvent.click(view.getByRole("button", { name: "Show details for Zulu" }));
  await act(async () => new Promise((resolve) => window.requestAnimationFrame(resolve)));
  link = await share(view);
  cleanup(); view = mount(multi, link);
  for (const [label, text] of [["Subreport", "Orb mechanics"], ["Attempt", "Pull two"], ["Category", "Orbs"], ["Orb view", "During channel"]]) assert.ok(view.getByRole("button", { name: label }).textContent.includes(text));
  for (const name of ["tank", "amount", "Adds", "averages"]) assert.equal(view.getByRole("button", { name, exact: true }).getAttribute("aria-pressed"), "false");
  assert.ok(view.getByRole("button", { name: "Hide details for Zulu" }));
  assert.equal(view.container.querySelector("tbody tr td").textContent.includes("Zulu"), true);
  await act(async () => {
    window.history.replaceState(null, "", buildReportViewUrl(base(multi), { "/fullWidth": true }));
    window.dispatchEvent(new window.HashChangeEvent("hashchange"));
  });
  assert.ok(view.getByRole("button", { name: "Exit full width" }));
  assert.ok(view.getByRole("button", { name: "Subreport" }).textContent.includes("Default report"), "A different view fragment restores in an already-open report too");
  cleanup();
  // Bad fragments and stale identifiers fall back safely; old input-only URLs still open.
  assert.deepEqual(readReportView(base(defensive), { href: `${base(defensive)}#view=garbage` }), {});
  assert.deepEqual(readReportView(base(defensive), { href: buildReportViewUrl(base(coverage), { "/fullWidth": false }) }), {});
  view = mount(defensive, buildReportViewUrl(base(defensive), { "/fullWidth": "invalid", [`/${defensive.reportId}/playerId`]: "missing", [`/${defensive.reportId}/bossSelection`]: "invalid" }));
  assert.ok(view.getByRole("button", { name: "Exit full width" }));
  assert.notEqual(view.getByLabelText("Defensive player").value, "missing");
  cleanup();
  view = mount(defensive);
  assert.equal(view.getByLabelText("Player health").checked, false);
  cleanup();
  console.log("Sharing passed: tables, subreports, filters, sorting, expanded rows, defensives, coverage, open casts, graph layers, alignment, hidden players, full width, zoom/scroll, old and invalid links.");
} finally { await server.close(); dom.window.close(); }
