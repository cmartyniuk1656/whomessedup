# Who Messed Up - Warcraft Logs Analyzer

### Project Charter

**Goal:**  
Create a self-hosted FastAPI service that analyzes Warcraft Logs reports and surfaces raid mistakes, starting with "how many times each player was hit by a specific ability."

**Phase 1 Objectives**

1. Accept a Warcraft Logs **report code**.
2. Use the **Warcraft Logs GraphQL v2 API** to fetch combat events.
3. Count and summarize **hits per player for a chosen ability** (or regex).
4. Expose the analysis through both CLI tools and a simple web API.

**Stretch Goals (Later Phases)**

- Additional preset queries (Top Damage Taken, Mechanic Failures, etc.).
- Per-fight breakdowns and richer filtering.
- OAuth PKCE flow for private/guild logs.
- Visualizations (graphs, heatmaps) for the web UI.
- Persistent caching and shareable links.

**Stack Overview**

| Layer      | Technology                                            |
| ---------- | ----------------------------------------------------- |
| Frontend   | Static HTML + Vanilla JS (planned)                    |
| Backend    | FastAPI (Python 3.11+)                                |
| API        | Warcraft Logs GraphQL v2                              |
| Hosting    | Linux VPS (Ubuntu) behind Nginx Proxy Manager         |
| Auth       | OAuth 2.0 - Client Credentials flow                   |
| Deployment | systemd service or Docker container (optional)        |

---

## Local Development

### 1. Environment Variables

Create a `.env` file (or export in your shell) with your own Warcraft Logs client credentials:

```bash
export WCL_CLIENT_ID="YOUR_CLIENT_ID"
export WCL_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

> âš ï¸ **Never commit credentials** to source control.

On Windows PowerShell:

```powershell
$env:WCL_CLIENT_ID="YOUR_CLIENT_ID"
$env:WCL_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

### 2. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PowerShell activation:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app:app --reload --port 8080
```

Then open http://localhost:8080/docs for the automatically generated API docs.

> Note: The app and CLI tools auto-load `.env` via `python-dotenv`, so define `WCL_CLIENT_ID` / `WCL_CLIENT_SECRET` there and they will be picked up automatically.

### 4. Run the Frontend (dev)

```bash
cd frontend
npm install        # first run only
npm run dev
```

Visit the printed Vite URL (default http://localhost:5173). The dev server proxies API requests to `http://localhost:8080` while both services are running.

### 5. Sample API Request

```http
GET /api/hits?report=QDbKNwLr3dRXy9TV&ability_id=1227472
```
---

## CLI Utilities (Existing Workflows)

- `wcl_fetch_events.py` — download raw events to JSONL (pass `--ability-id`/`--only-ability` to filter server-side and embed actor names).
- `wcl_hit_counter.py` — count hits from JSON/JSONL/CSV exports using the shared analysis engine in `who_messed_up/` (supports `--only-ability`, `--ability-id`, and regex filters).

Examples:

```bash
# Fetch only Besiege hits and keep the JSONL tight
python wcl_fetch_events.py QDbKNwLr3dRXy9TV --data-type DamageTaken --ability-id 1227472 --out besiege.jsonl

# Summarize the hits with the CLI (names already injected)
python wcl_hit_counter.py besiege.jsonl --ability-id 1227472
```

Both scripts now consume the shared package modules, so new features in the FastAPI layer automatically benefit the CLIs.
---

## Production Deployment Notes

1. Build the frontend before deployment:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   The build output in `frontend/dist/` is served automatically by FastAPI.
2. Run the API behind a process manager (`uvicorn`, `gunicorn`, or `uvicorn` via systemd/Docker).
3. Point Nginx (or Nginx Proxy Manager) at `http://127.0.0.1:8080` for the `/api/*` path and the SPA root `/`.
4. Enable HTTPS via Let's Encrypt in the proxy layer.
5. Store client credentials in environment variables or a secret manager on the server.
---

## Repository Layout

```text
who-messed-up/
+-- app.py                 # FastAPI backend & SPA static serving
+-- frontend/              # React + Vite + Tailwind frontend
¦   +-- src/
¦   +-- dist/              # Production build output (generated)
+-- requirements.txt
+-- wcl_fetch_events.py
+-- wcl_hit_counter.py
+-- who_messed_up/
¦   +-- __init__.py
¦   +-- analysis.py
¦   +-- api.py
¦   +-- service.py
+-- README.md
```

---

## Security Checklist

- Keep your client secret server-side only.
- Use HTTPS end-to-end.
- Consider rate limiting, caching, and sanitizing user input.
- Rotate secrets immediately if they leak or are suspected compromised.


