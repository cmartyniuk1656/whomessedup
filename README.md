# Who Messed Up – Raid Report Dashboard

Who Messed Up is a self-hosted toolkit that turns Warcraft Logs reports into actionable raid insights. It keeps the heavy lifting on your own box: fetch a report, crunch the data against curated queries ("fuck up" dashboards, damage/healing breakdowns, etc.), and view the results in a modern Tailwind-based frontend or through JSON APIs. Nothing leaves your server except the calls to the official Warcraft Logs API.

## What the App Does

- Accepts a Warcraft Logs report URL or code and runs purpose-built analyses (“tiles”).
- Talks directly to the Warcraft Logs GraphQL v2 API using your client credentials.
- Queues long-running jobs so multiple users can request reports without colliding.
- Caches recent results so repeated runs return instantly unless you force a refresh.
- Serves a single-page React app alongside the FastAPI backend so hosting is dead-simple.
- Allows CSV export of any tile so you can take the numbers into spreadsheets, Google Sheets, etc.

## Quick Start

1. **Clone & setup environment**
   ```bash
   git clone <your-repo>
   cd who-messed-up
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Provide Warcraft Logs credentials**
   - Create a `.env` file (or export in your shell) with `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET`.
   - These should be the OAuth “client credentials” from https://www.warcraftlogs.com/api/clients.

3. **Install and run the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Vite will serve the React app (default http://localhost:5510) and proxy API calls to the backend.

4. **Run the backend**
   ```bash
   python scripts/run_backend.py
   ```
   The API lives at http://localhost:5511 (see interactive docs at `/docs`). It also serves the frontend build once you run `npm run build`.

   Both development ports can be overridden without editing source. Set `WHO_MESSED_UP_WEB_PORT` for Vite and `WHO_MESSED_UP_API_PORT` for both the backend launcher and Vite proxy. Set `WHO_MESSED_UP_API_ORIGIN` instead when proxying to a non-local API origin.

   These are local-development defaults only. The production service may keep its existing port; the current VPS systemd service and reverse proxy continue to use `8088`.

## Production Hosting

- Build the frontend (`npm run build`) and run `uvicorn app:app --host 0.0.0.0 --port 8088` under a process manager (systemd, Supervisor, Docker, etc.). Choose a different production port only when the service definition and reverse proxy are updated together.
- Put Nginx/Traefik/Nginx Proxy Manager in front to terminate TLS and proxy `/` and `/api/*` to the app.
- Store `WCL_CLIENT_ID` / `WCL_CLIENT_SECRET` securely as environment variables.
- The job queue and Warcraft Logs request limiter run in-process. Prefer one Uvicorn worker and tune the bounded report pool with `WHO_MESSED_UP_JOB_WORKERS` (default `2`) so separate processes do not independently exceed the upstream rate limit.
- `WCL_MAX_CONCURRENT_REQUESTS` caps concurrent Warcraft Logs requests (default `4`), `WCL_TABLE_BATCH_WORKERS` controls how many independent table batches can run in parallel (default `4`), and `WCL_REQUEST_ATTEMPTS` controls transient 429/5xx retries (default `3`).
- Real-time report mode works with any public report code and polls lightweight report metadata every 10 seconds while the results tab is visible. Guild configuration is only needed for recent-report discovery. `WCL_REPORT_WATCH_CACHE_TTL_SECONDS` shares those checks across browser sessions for a report (default `5`, maximum `30`).
- Aggregate Reports run the selected non-cooldown reports together. `WHO_MESSED_UP_AGGREGATE_REPORT_WORKERS` bounds parallel child-report generation (default `2`, maximum `4`); Warcraft Logs calls remain subject to `WCL_MAX_CONCURRENT_REQUESTS`.

## Development Tips

- The backend auto-loads `.env` via python-dotenv. Restart the server if you change credentials.
- Frontend state resets between tiles; cached job results are in memory only—restart clears them.
- Use `npm run build` to ensure the SPA compiles before deploying.
- CSV exports are generated client-side, so if you modify table columns, update the CSV builder in `frontend/src/App.jsx`.

## Architecture Plans

- See `docs/report-view-model-refactor.md` for the planned frontend/backend decoupling work, target model contract, and migration phases.

## Repository Layout

```text
who-messed-up/
+-- app.py               # FastAPI app + SPA static serving
+-- frontend/            # React + Vite + Tailwind UI
¦   +-- public/          # Static assets (favicon.png, etc.)
¦   +-- src/             # Application code
¦   +-- dist/            # Production build output
+-- who_messed_up/       # Shared backend logic used by API and CLIs
¦   +-- api.py           # Warcraft Logs GraphQL helpers
¦   +-- service.py       # Report orchestration, caching, job queue
¦   +-- analysis.py      # Event normalization & counting utilities
+-- wcl_fetch_events.py  # CLI helper to download raw logs (optional)
+-- wcl_hit_counter.py   # CLI helper to analyze JSON/CSV logs (optional)
+-- requirements.txt
+-- README.md
```

## Security and API Usage Notes

- Keep your client secret server-side only. Treat it like any other OAuth secret.
- Warcraft Logs enforces rate limits—avoid spamming simultaneous fresh runs.
- The queue is in-memory; restart clears jobs. Persist results externally if you need long-term history.
- Use HTTPS in front of the app and lock management endpoints (e.g., /docs) if you expose it publicly.

## Regression Test References

- Report responses use gzip above 1 KB. Vashnik mechanics uses `services/event_streams.py` to partition add-damage and incoming-damage streams by complete pulls with one four-worker pool; WCL's global request semaphore still applies. Other streams remain unpartitioned. See the [performance audit and measured results](docs/analysis/vashnik-aggregate-performance.md).
- `view_models/indexed_rows.py` is an opt-in transport optimization: Vashnik mechanics sends canonical row bodies in `rowsById` and ordered storage keys in `rowIds`, `rowIdsByView`, and `rowIdsByCombinedView`. These storage keys are separate from display row IDs. `frontend/src/utils/reportRows.js` resolves the selected view without cloning evidence and also accepts existing inline-row tables. Keep presentation/calculation builders on the inline contract and index only their final serialized pages. Run `node --test tests/reportRows.test.js` from `frontend` for resolver coverage.
- Aggregates keep child content only in `reportsByView`; the lightweight root retains pull controls for live watching. Mechanics executes first while selector order stays unchanged. `JobManager.execute_registered(..., use_cache=True)` shares completed and running child work with standalone jobs without waiting on queued jobs. Aggregate pool tasks explicitly inherit `fresh_run`; fresh executions bypass older results and prevent superseded work from overwriting the cache.
- Mythic Vashnik base reports use `6x4fbqFQLagcRCKD` (six wipes and one kill). See [log evidence and classifications](docs/analysis/vashnik-mythic.md) for the 12-pull research sample, source exclusions, and `vashnik_mythic_*` regression cases. Mythic reports reuse the existing wrappers and select a difficulty-specific manifest and page configuration.
- Shared death reports use `death_tables.py` to split saturated WCL death-table requests by fight. WCL returns at most 200 death recaps with no continuation token; accepting that response directly loses later pulls. `vashnik_mythic_deaths_long_session` covers `X6FGCJm3pqjQMNdv` (324 deaths over 17 pulls). A single pull saturating the table fails explicitly rather than returning an unverified partial report.
- `vashnik-the-malignant-mythic-mechanics` adds Totems & Plague Waves, Froth Spreading, Exploding Infection Dispels, Stygian Healing, Living Venom Control, and Bile Soaks to the Mythic aggregate. [The mechanics audit](docs/analysis/vashnik-mythic-mechanics-audit.md) documents attribution limits and validation. WCL has no individual totem kill credit: the report labels timing-based wave associations and rare single-carrier inferences explicitly.
- Mechanics services share aura/event helpers, pull contexts, and evidence records in `mechanics_events.py`, `mechanics_context.py`, and `mechanics_models.py`; existing Sentinels imports remain compatible. Vashnik's fetch orchestration and independent calculators live under `vashnik_mechanics*`. The configurable `view_models/mechanics.py` renders pull-scoped evidence and contribution bars through the existing frontend table contract.
- Vashnik Totems defaults to stacked outcome bars (cleared, missed/detonated, unresolved), with separate **Wave carriers** and **Totem details** views. Every Froth assignment group appears in the wave roster, including zero-clear groups and missing releases. The reusable `outcome_bar` cell renders in `OutcomeBar.jsx`; its typed cell subclass preserves the serialization of existing cells. Subview-specific summary metrics fall back to the parent mechanic's metrics.
- All Vashnik mechanics views opt into `CompactTableModel`: two or three primary columns, time beneath the set name, responsive rows, and collapsible event evidence. `view_models/compact_mechanics.py` configures metric cells, outcome bars, and detail metrics without changing the calculations. `MetricList`, `RelativeBar`, and `CompactEventDetails` are reusable frontend components; other reports retain their existing presentation until opting in. See [the UI choices](docs/analysis/vashnik-mechanics-ui.md).

- Mythic Entombed Sentinels base reports use `J3y9gP2bqmkphY7f` (11 wipes). See [the metadata and mechanics research notes](docs/analysis/entombed-sentinels-mythic.md) for classification evidence, spell IDs, and the `sentinels_mythic_*` regression cases. The existing Heroic report IDs remain available; Mythic base report IDs end in `-mythic`.
- `entombed-sentinels-mythic-mechanics` adds Protovenom, Helical Toxins, Miasma, Droplets, Coagulations, Dispels, and Intermission Resolution to the Mythic catalog and aggregate. Fetch/merge orchestration, pure per-pull analysis, event lifetimes, and rendering live in separate `entombed_sentinels_mechanics*` service modules. All seven views use the shared pull selectors and expandable table contract. Dispels offers cast sets and healer bars; Intermission Resolution separates toxin-clear timing from full Stasis healing. Their calculators live in `entombed_sentinels_mechanics_resolution.py`, and the renderer shares count-bar aggregation between dispels and droplets.
- All avoidable-damage reports use the shared `view_models/avoidable_damage.py` source chart in expanded player rows, in both Damage bars and Table layouts. Charts sum filtered damage by spell and follow the selected pull/report scope. `RowDetailsModel.barChartPosition` can place a chart before the event history; existing detail charts default to after it.

When refactoring or adding features, sanity-check the existing reports against these known Warcraft Logs reports:

- **Nexus-King Regression**: `WczAN4bDfXxPhV93` (use the Nexus-King tiles, including phase damage and combined fuck-up dashboards).
- **Dimensius Regression**: `W4cZgnxQfR2AH1dT` (covers Dimensius phase damage plus the “Phase 1 Add Damage” report with and without “Ignore first add set”).

Recommended workflow:

1. Run the backend (`python scripts/run_backend.py`) and the frontend dev server.
2. Load each tile using the report codes above, once with cached results and once using the “Force fresh run” option.
3. Export CSVs before/after your changes; diff them (ignoring timestamp/order shifts) to confirm metrics remain identical unless intentionally changed.
4. When backend-only refactors are done, hit the REST endpoints directly (`/api/nexus-phase1`, `/api/nexus-phase-damage`, `/api/dimensius-add-damage`) with the codes above and compare JSON responses.

Automating these checks (e.g., via a pytest script that fetches the endpoints and compares snapshots) is encouraged as we continue to split the codebase into reusable modules.

### Capturing New Baselines

Run the helper script (ensure the backend is running locally) to refresh the stored snapshots:

```bash
.\.venv\Scripts\python.exe scripts/capture_regressions.py --base-url http://localhost:5511 --out-dir regression_snapshots
```

The generated JSON lives in `regression_snapshots/` and acts as the “golden” expectations for future diffs. To run a single case without re-running the entire suite, pass one or more `--case` flags (each matching the case name from `scripts/capture_regressions.py`). Example:

```bash
.\.venv\Scripts\python.exe scripts/capture_regressions.py --base-url http://localhost:5511 --out-dir regression_snapshots_current --case ghosts_all
git diff --no-index regression_snapshots/ghosts_all.json regression_snapshots_current/ghosts_all.json
```

## Feedback & Contributions

Open PRs/issues, or fork and customize your own tiles. The architecture keeps tiles modular, so adding new analyses is just a matter of wiring a service function + frontend card.
