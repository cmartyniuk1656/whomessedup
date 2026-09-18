# Vashnik aggregate performance audit

Audited release `b148604` on September 18, 2026 UTC using report
`X6FGCJm3pqjQMNdv` (17 Mythic pulls), default aggregate settings, and fresh local
execution against WCL. Production was inspected with a read-only request for an
existing completed job. No application or production configuration was changed.

## Measurements

| Stage | Measured result |
| --- | ---: |
| Full aggregate handler, default two child workers | 32.92 s |
| Death report | 5.58 s |
| Avoidable damage | 5.01 s |
| Target damage | 1.36 s |
| Mechanics | 27.34 s |
| Mechanics start after aggregate submission | 5.59 s |
| WCL GraphQL requests across the aggregate | 64 |
| Aggregate JSON, compact UTF-8 | 49.18 MB |
| Same JSON compressed with gzip level 6 | 2.68 MB |
| Local gzip compression time | 0.14 s |

Times are wall-clock measurements on the development computer, not production
CPU benchmarks. Child execution overlaps. WCL response caching and network
latency can affect repeat runs; the prototype results below are individual
observations, not guaranteed speedups. Sizes use decimal MB.

The production seven-pull mechanics job returned `Content-Length: 16941903`
without `Content-Encoding`, despite `Accept-Encoding: gzip`. Its result alone is
16.94 MB of compact JSON (the saved pretty-printed snapshot is 37.87 MB).
Offline gzip reduced that result to 0.97 MB. The aggregate size above was measured
locally using the deployed code, not by starting another production job.

## Findings and recommended changes

### 1. Compress report JSON responses

The application does not install compression middleware, and the production
proxy did not compress the inspected JSON response. The frontend keeps its
processing state until `response.json()` finishes, so downloading a completed
report contributes directly to the apparent processing delay.

Compress large JSON responses using application middleware, covering completed
job polling, immediate cached POST results, and cached-report GET results.
Compression reduces this aggregate's transfer size by approximately **94.6%**
without changing its report contract. It does not remove browser parsing or
allocation costs, so it complements rather than replaces payload reduction.
Verify compression negotiation, `Vary: Accept-Encoding`, uncompressed clients,
and decompressed payload equality before release.

Relevant code: `app.py:get_job_status`, `create_v2_report_job`,
`get_cached_v2_report`; `frontend/src/hooks/useReportJob.js`.

### 2. Partition large mechanics streams by complete pulls

`vashnik_mechanics._fetch_streams` assigns one worker to each event stream across
every selected pull. Each stream's `nextPageTimestamp` pagination is serial.
Having four stream workers does not parallelize a single large stream.

The add-damage stream was the critical path:

- 27 sequential pages, approximately 78.48 MB of decoded JSON from WCL.
- Started at aggregate +8.52 s and finished at +29.48 s.
- Incoming damage needed another seven pages and approximately 9.62 MB.
- The death-table completeness fix needed three table requests totaling only
  0.86 s in this sample; it is not the main delay.

An audit-only prototype split the selected fights into four disjoint groups for
each large stream and merged results by fight ID. It used four task workers and
retained the existing global four-request semaphore. Complete fight boundaries
and all paginated events were preserved.

| Mechanics strategy | Stream fetch | Total mechanics | Entire page equals baseline |
| --- | ---: | ---: | --- |
| Current | approximately 23.89 s* | 27.34 s | baseline |
| Partition add damage only | 17.21 s | 21.20 s | yes |
| Partition add damage and incoming damage | 11.32 s | 15.20 s | yes |

*Current fetch duration is inferred from the first and final stream request
timestamps. Prototype fetch stages were timed directly. Prototype totals include
metadata and token setup and ran standalone, whereas baseline mechanics ran
inside the aggregate. The observed total mechanics reduction is approximately
44%, not an end-to-end production guarantee. Calculation took about 1.57 s in
both prototypes, so network fetching remained the larger cost.

Implement this as an opt-in shared event-fetch helper with bounded workers,
disjoint complete-pull partitions, deterministic merging, and conservative
fallbacks for small selections. Test empty selections, noncontiguous fight IDs,
pagination, per-fight ordering, error propagation, and configured concurrency.
Do not simply raise global WCL concurrency or drop events to achieve speed.

### 3. Send each evidence row once

The mechanics table repeats row objects under `rows`, `rowsByView`, and
`rowsByCombinedView`, including aggregate/pull scopes and set-view aliases.
JSON expands every reference into another complete copy.

For the 17-pull mechanics page:

- 5,023 row occurrences contain only 2,186 distinct row IDs.
- Every duplicate ID had exactly equal content in this sample.
- Repeated row bodies total 26.99 MB; one copy per ID totals 6.88 MB, before
  accounting for the small lists of row references.
- The aggregate also duplicates approximately 6.39 MB from its first child at
  the root, in addition to storing that child under `reportsByView`.

Add a reusable, opt-in `rowsById` plus ordered row-ID lists per view and resolve
them in a shared frontend utility. Preserve the existing inline-row contract for
older reports. Avoid copying a complete child into the aggregate wrapper; retain
only the metadata and pull options needed by report selection and live watching.
Keep row details available in the canonical row so existing expansion and export
behavior remain intact. A later step could fetch evidence only when expanded,
but that is a larger API/cache change and is not required for initial deduplication.

Relevant code: `services/view_models/mechanics.py`, `vashnik_totems.py`,
`compact_mechanics.py`, `app.py:_execute_v2_aggregate_report_job`,
`frontend/src/components/v2/organisms/ReportPageView.jsx`, and
`frontend/src/hooks/useRealtimeReport.js`.

### 4. Start expensive children earlier; reuse compatible child results

The aggregate starts deaths and avoidable damage first, delaying mechanics by
5.59 s in this run. Schedule known expensive children first while retaining the
original selector order in the result. This can overlap more useful work without
raising concurrency; contention means the entire scheduling delay is not a
guaranteed saving.

`JobManager.execute_registered` bypasses child result caching. A separately
completed mechanics report is recalculated when a new aggregate is requested,
and aggregate children do not populate the standalone report cache. Add shared
child execution/cache handling with explicit propagation of fresh-run semantics
and coalescing for identical in-flight requests. Do not wait on jobs queued to
the same saturated worker pool, which could deadlock. The complete aggregate is
already cached; this improvement specifically concerns reuse across different
aggregate selections and standalone requests.

Only two exact duplicate WCL queries occurred in the measured run. Metadata
cache coalescing is worthwhile eventually, but is much less valuable here than
large-stream fetching and response size.

## Suggested delivery order

1. JSON compression and bounded partitioning of the two large streams.
2. Canonical rows and lightweight aggregate wrappers, with frontend compatibility.
3. Child scheduling, freshness-aware cache reuse, and user-visible stage timing.

Preserve the verified 324 deaths across all 17 pulls and compare every mechanics
selector's rows, summaries, attribution, and details. Repeat the standard ghost,
phase-damage, and add-damage regressions when shared fetching changes. Measure
backend duration, compressed bytes, and time until the report becomes usable
separately. Test fresh runs, cached runs, and concurrent users.

Audit evidence and disposable prototypes are in the ignored local directory
`.local/vashnik-performance/`: `audit.py`, `measurements.json`,
`aggregate.json.gz`, `sharded_probe.py`, `sharded-measurements.json`, and
`both-sharded-measurements.json`. They contain no recorded authentication tokens.

## Implemented updates and verification

The follow-up implementation adds gzip (level 6, 1 KB threshold), the bounded
shared `services/event_streams.py` helper, opt-in indexed Vashnik rows, lightweight
aggregate wrappers, mechanics-first scheduling, and child cache/in-flight reuse.
The global WCL concurrency limit is unchanged. Freshness is passed explicitly
into aggregate worker threads; newer executions supersede older cache writes.
Failed shared executions wake their waiters and allow subsequent retries. The
implementation does not wait on pending queue records, avoiding parent/child
queue deadlocks.

A fresh local HTTP aggregate for the same 17-pull report measured:

| Metric | Before | Updated |
| --- | ---: | ---: |
| Backend generation | 32.92 s | 16.71 s |
| Uncompressed JSON | 49.18 MB | 22.65 MB |
| HTTP transfer | approximately 49.18 MB without compression | 1.20 MB with gzip |

The before transfer figure uses the measured baseline aggregate size and the
production compression check; the updated transfer figure is the actual local
HTTP response's `Content-Length`. Submission through fully parsed response took
17.69 seconds locally. These are individual WCL runs, so timing varies with
network latency and upstream caching; output sizes are deterministic for the
same evidence.

All four child pages exactly matched the baseline after resolving row references.
The frontend resolver matched all 361 mechanics row-list selections, including
empty views, repeated references, ordering, and full event evidence. A repeated
aggregate request and every standalone child returned immediate cached HTTP 200
responses. The cached aggregate completed its local HTTP round trip in 2.48 s.
Ghosts, Nexus phase damage, Dimensius add damage, and the 324-death long-session
case matched their previous regression snapshots exactly.

Automated coverage includes partition pagination and boundaries, concurrency,
failed requests, compression across polling/POST/cache endpoints, model
round-tripping, row-ID collisions, legacy contracts, child cache reuse, fresh-run
propagation, stale write prevention, and queue deadlock prevention. Frontend
resolver tests, targeted ESLint, and the production build passed. The changes
have been verified locally and have not been deployed.

Follow-up evidence is in `.local/vashnik-performance/updated-measurements.json`,
`updated-aggregate.json.gz`, `verify_updates.py`, and `regressions/`.
