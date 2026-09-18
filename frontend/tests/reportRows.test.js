import assert from "node:assert/strict";
import test from "node:test";
import { resolveReportRows } from "../src/utils/reportRows.js";

const one = { id: "one", cells: {}, details: { groups: [{ id: "evidence" }] } };
const two = { id: "two", cells: {} };
const legacy = {
  rows: [one],
  rowsByView: { all: [one, two], empty: [] },
  rowsByCombinedView: { "all::sets": [two, one, two], empty: [] },
};
const indexed = {
  rowStorage: "indexed", rowsById: { a: one, b: two }, rowIds: ["a"],
  rowIdsByView: { all: ["a", "b"], empty: [] },
  rowIdsByCombinedView: { "all::sets": ["b", "a", "b"], empty: [] },
};

test("indexed and inline tables resolve the same rows for every fallback", () => {
  for (const args of [[], ["all"], ["missing", null, "all"], ["all", "all::sets"],
    ["empty", null, "all"], ["all", "empty"], ["all", "missing"], ["missing"]]) {
    assert.deepEqual(resolveReportRows(indexed, ...args), resolveReportRows(legacy, ...args));
  }
});

test("selected views share original row objects and preserve duplicate references", () => {
  const rows = resolveReportRows(indexed, "all", "all::sets");
  assert.equal(rows[0], rows[2]);
  assert.equal(rows[1], one);
  assert.equal(rows[1].details, one.details);
  assert.deepEqual(resolveReportRows(undefined), []);
});
