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

## Feedback & Contributions

Open PRs/issues, or fork and customize your own tiles. The architecture keeps tiles modular, so adding new analyses is just a matter of wiring a service function + frontend card.

