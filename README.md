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
   Vite will serve the React app (default http://localhost:5173) and proxy API calls to the backend.

4. **Run the backend**
   ```bash
   uvicorn app:app --reload --port 8088
   ```
   The API lives at http://localhost:8088 (see interactive docs at /docs). It also serves the frontend build once you run `npm run build`.

## Production Hosting

- Build the frontend (`npm run build`) and run `uvicorn app:app --host 0.0.0.0 --port 8088` under a process manager (systemd, Supervisor, Docker, etc.).
- Put Nginx/Traefik/Nginx Proxy Manager in front to terminate TLS and proxy `/` and `/api/*` to the app.
- Store `WCL_CLIENT_ID` / `WCL_CLIENT_SECRET` securely as environment variables.
- The job queue runs in-process; scale by adding more Uvicorn workers if you saturate a single worker (bear in mind rate limits from Warcraft Logs).

## Development Tips

- The backend auto-loads `.env` via python-dotenv. Restart the server if you change credentials.
- Frontend state resets between tiles; cached job results are in memory only—restart clears them.
- Use `npm run build` to ensure the SPA compiles before deploying.
- CSV exports are generated client-side, so if you modify table columns, update the CSV builder in `frontend/src/App.jsx`.

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

When refactoring or adding features, sanity-check the existing reports against these known Warcraft Logs reports:

- **Nexus-King Regression**: `WczAN4bDfXxPhV93` (use the Nexus-King tiles, including phase damage and combined fuck-up dashboards).
- **Dimensius Regression**: `W4cZgnxQfR2AH1dT` (covers Dimensius phase damage plus the “Phase 1 Add Damage” report with and without “Ignore first add set”).

Recommended workflow:

1. Run the backend (`uvicorn app:app --reload --port 8088`) and the frontend dev server.
2. Load each tile using the report codes above, once with cached results and once using the “Force fresh run” option.
3. Export CSVs before/after your changes; diff them (ignoring timestamp/order shifts) to confirm metrics remain identical unless intentionally changed.
4. When backend-only refactors are done, hit the REST endpoints directly (`/api/nexus-phase1`, `/api/nexus-phase-damage`, `/api/dimensius-add-damage`) with the codes above and compare JSON responses.

Automating these checks (e.g., via a pytest script that fetches the endpoints and compares snapshots) is encouraged as we continue to split the codebase into reusable modules.

### Capturing New Baselines

Run the helper script (ensure the backend is running locally) to refresh the stored snapshots:

```bash
.\.venv\Scripts\python.exe scripts/capture_regressions.py --base-url http://localhost:8088 --out-dir regression_snapshots
```

The generated JSON lives in `regression_snapshots/` and acts as the “golden” expectations for future diffs. To run a single case without re-running the entire suite, pass one or more `--case` flags (each matching the case name from `scripts/capture_regressions.py`). Example:

```bash
.\.venv\Scripts\python.exe scripts/capture_regressions.py --base-url http://localhost:8088 --out-dir regression_snapshots_current --case ghosts_all
git diff --no-index regression_snapshots/ghosts_all.json regression_snapshots_current/ghosts_all.json
```

## Feedback & Contributions

Open PRs/issues, or fork and customize your own tiles. The architecture keeps tiles modular, so adding new analyses is just a matter of wiring a service function + frontend card.
