/** Render real WCL fixture data through the report entry point, without a browser. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createServer } from "vite";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { JSDOM } from "jsdom";
import {
  preciseCoverageTime,
  pressurePath,
  coverageSegments,
  clusterBossCasts,
} from "../src/utils/coverageTimeline.js";

const fixture = JSON.parse(
  await readFile(
    new URL(
      "../../tests/fixtures/cooldown_coverage_page.json",
      import.meta.url,
    ),
    "utf8",
  ),
);
const server = await createServer({
  server: { middlewareMode: true },
  appType: "custom",
});
try {
  const { ReportPageView } = await server.ssrLoadModule(
    "/src/components/v2/organisms/ReportPageView.jsx",
  );
  const html = renderToStaticMarkup(
    React.createElement(ReportPageView, { page: fixture }),
  );
  assert.ok(html.includes("Cooldown Coverage Report"));
  assert.ok(html.includes("Damage + heal absorbs"));
  assert.ok(html.includes("Timeline zoom"));
  assert.ok(html.includes("Shifting Protovenom at 0:36.205"));
  assert.ok(
    !html.includes("Shifting Protovenom at 0:36.378"),
    "Other pulls must not leak into the selected pull",
  );
  assert.ok(
    !html.includes("Download CSV"),
    "A timeline must not expose a table export",
  );
  assert.ok(html.includes("/cooldown-coverage/icons/lorrgs/spells/"));
  assert.equal(preciseCoverageTime(96.137), "1:36.137");
  assert.equal(pressurePath([], 100, 1), "");
  assert.ok(
    !pressurePath([{ time: 0, damage: 0, healAbsorbs: 0 }], 100, 1).includes(
      "NaN",
    ),
  );
  const dom = new JSDOM("<!doctype html><html><body></body></html>", {
    url: "http://localhost",
  });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  globalThis.HTMLElement = dom.window.HTMLElement;
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  const { render, fireEvent, cleanup } = await import("@testing-library/react");
  const view = render(React.createElement(ReportPageView, { page: fixture }));
  const firstDeath = fixture.content.timeline.pulls[0].deaths[0];
  const firstDeathMarker = [
    ...view.container.querySelectorAll(".coverage-death-marker"),
  ].find((marker) =>
    marker.title.includes(
      `${firstDeath.player} died at ${preciseCoverageTime(firstDeath.time)}`,
    ),
  );
  assert.ok(
    firstDeathMarker,
    "Recorded deaths appear at their own pull-relative times",
  );
  fireEvent.click(firstDeathMarker);
  assert.ok(
    view
      .getByRole("complementary", { name: "Ability details" })
      .textContent.includes(firstDeath.player),
  );
  assert.equal(
    view.container.querySelectorAll(".coverage-pressure-graph").length,
    1,
  );
  assert.ok(view.container.querySelector(".coverage-pressure-shading rect"));
  assert.equal(view.container.querySelectorAll(".coverage-row-boss").length, 1);
  const filters = view.getByRole("group", { name: "Boss ability filters" });
  const firstToggle = filters.querySelector('button[aria-pressed="true"]');
  assert.ok(firstToggle);
  const tooltip = document.getElementById(
    firstToggle.getAttribute("aria-describedby"),
  );
  assert.ok(
    tooltip.textContent.length > 20,
    "Boss icon includes an ability description",
  );
  fireEvent.click(firstToggle);
  assert.equal(firstToggle.getAttribute("aria-pressed"), "false");
  fireEvent.click(view.getByRole("button", { name: "None", exact: true }));
  assert.equal(
    view.container.querySelectorAll(".coverage-boss-cast").length,
    0,
  );
  fireEvent.click(view.getByRole("button", { name: "All", exact: true }));
  assert.ok(
    [...filters.querySelectorAll("button[aria-pressed]")].every(
      (button) => button.getAttribute("aria-pressed") === "true",
    ),
  );
  fireEvent.change(view.getByLabelText("Pull"), {
    target: { value: fixture.content.timeline.pulls[1].id },
  });
  const bossCast = view.getByRole("button", {
    name: /Shifting Protovenom at 0:36.378/,
  });
  assert.equal(
    view.queryByRole("complementary", { name: "Ability details" }),
    null,
    "Changing pulls clears the previous death selection",
  );
  const deathTrack = view.container.querySelector(
    ".coverage-death-row",
  ).innerHTML;
  assert.equal(
    view.queryByRole("button", { name: /Shifting Protovenom at 0:36.205/ }),
    null,
  );
  fireEvent.click(bossCast);
  assert.ok(
    view
      .getByRole("complementary", { name: "Ability details" })
      .textContent.includes("0:36.378"),
  );
  fireEvent.click(view.getByLabelText("Damage + heal absorbs"));
  assert.equal(view.container.querySelector(".coverage-pressure-graph"), null);
  assert.equal(
    view.container.querySelector(".coverage-pressure-backdrop"),
    null,
  );
  assert.equal(
    view.container.querySelector(".coverage-pressure-shading"),
    null,
  );
  const strip = view.container.querySelector(".coverage-strip-track").innerHTML;
  fireEvent.change(view.getByLabelText("Healer"), {
    target: { value: "Sample Restoration Druid" },
  });
  assert.equal(
    view.container.querySelectorAll(".coverage-row-healer").length,
    2,
  );
  assert.ok(view.container.querySelectorAll(".coverage-row-boss").length > 0);
  assert.equal(
    view.container.querySelector(".coverage-strip-track").innerHTML,
    strip,
    "Healer filters must not change raid coverage",
  );
  assert.equal(
    view.container.querySelector(".coverage-death-row").innerHTML,
    deathTrack,
    "Death markers remain raid-wide when pressure or healer filters change",
  );
  fireEvent.click(view.container.querySelector(".coverage-strip-gap"));
  assert.ok(
    view
      .getByRole("complementary", { name: "Ability details" })
      .textContent.includes("Review this gap"),
  );
  fireEvent.keyDown(document, { key: "Escape" });
  assert.equal(
    view.queryByRole("complementary", { name: "Ability details" }),
    null,
  );
  fireEvent.click(
    view.container.querySelector(".coverage-row-healer .coverage-cast"),
  );
  assert.ok(view.getByRole("region", { name: "Cast effectiveness" }));
  assert.ok(
    view
      .getByRole("complementary", { name: "Ability details" })
      .textContent.includes("Overhealing"),
  );
  assert.ok(
    view.getByRole("img", { name: /effective healing, .* overhealing/ }),
  );
  assert.equal(view.container.querySelector(".coverage-timing-details"), null);
  assert.equal(view.queryByText("Players helped"), null);
  assert.ok(view.container.querySelector(".coverage-cast-selected"));
  fireEvent.click(view.getByLabelText("Estimated readiness"));
  assert.equal(view.container.querySelector(".coverage-ready"), null);
  fireEvent.change(view.getByLabelText("Timeline zoom"), {
    target: { value: "2" },
  });
  assert.equal(
    view.container.querySelector(".coverage-canvas").style.width,
    "200%",
  );
  cleanup();
  const clusteredPage = structuredClone(fixture);
  const clusteredPull = clusteredPage.content.timeline.pulls[0];
  const clusteredLane = clusteredPull.lanes.find(
    (lane) => lane.kind === "boss" && lane.shownByDefault,
  );
  clusteredLane.events = [
    { ...clusteredLane.events[0], time: 1 },
    { ...clusteredLane.events[0], time: 1.01 },
  ];
  clusteredPull.lanes = [clusteredLane];
  const clusteredView = render(
    React.createElement(ReportPageView, { page: clusteredPage }),
  );
  fireEvent.click(
    clusteredView.getByRole("button", { name: "2 boss casts near 0:01.000" }),
  );
  fireEvent.click(
    clusteredView.getByRole("button", { name: new RegExp("0:01.010") }),
  );
  assert.ok(
    clusteredView
      .getByRole("complementary", { name: "Ability details" })
      .textContent.includes(clusteredLane.description),
  );
  cleanup();
  const sampleLane = {
    kind: "healer",
    events: [
      { time: 0, end: 2 },
      { time: 3, end: 3 },
      { time: 6, end: null, label: "Store" },
    ],
  };
  const segments = coverageSegments(
    {
      duration: 8,
      lanes: [sampleLane],
      pressure: [0, 2, 4, 6].map((time) => ({
        time,
        damage: 100,
        healAbsorbs: 0,
      })),
    },
    2,
  );
  assert.equal(segments[0].active.length, 1);
  assert.equal(segments[1].bursts.length, 1);
  assert.equal(
    segments[1].potentialGap,
    false,
    "Instant casts are distinct from sustained coverage",
  );
  assert.equal(segments[2].potentialGap, true);
  assert.equal(
    segments[3].potentialGap,
    true,
    "Stasis preparation does not fill a coverage gap",
  );
  const grouped = clusterBossCasts(
    [{ events: [{ time: 1 }, { time: 1.01 }, { time: 9 }] }],
    10,
    1000,
  );
  assert.equal(grouped.length, 2);
  assert.equal(
    grouped[0][1].event.time,
    1.01,
    "Clustering must preserve exact cast times",
  );
  dom.window.close();
  console.log(
    "Coverage passed: real pull isolation, boss filters/clusters, raid coverage gaps, cast effectiveness, overlay/readiness toggles, healer filter, zoom and keyboard dismissal.",
  );
} finally {
  await server.close();
}
