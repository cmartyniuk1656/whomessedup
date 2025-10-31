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

> ⚠️ **Never commit credentials** to source control.

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

### 4. Sample Request

```http
GET /api/hits?report=QDbKNwLr3dRXy9TV&ability_id=1227472
```

Sample response:

```json
{
  "report": "QDbKNwLr3dRXy9TV",
  "data_type": "DamageTaken",
  "filters": {
    "ability": null,
    "ability_regex": null,
    "ability_id": "1227472",
    "source": null,
    "fight_name": null,
    "fight_ids": null
  },
  "total_hits": {
    "PlayerOne": 11,
    "PlayerTwo": 8,
    "PlayerThree": 23
  },
  "per_player": {
    "PlayerOne": 11,
    "PlayerTwo": 8,
    "PlayerThree": 23
  },
  "breakdown": [
    { "player": "PlayerThree", "ability": "Shadowflame", "hits": 23 },
    { "player": "PlayerOne", "ability": "Shadowflame", "hits": 11 },
    { "player": "PlayerTwo", "ability": "Shadowflame", "hits": 8 }
  ],
  "fights": [
    { "id": 1, "name": "Prototype Encounter", "start": 123456, "end": 127890, "kill": true }
  ]
}
```

---

## CLI Utilities (Existing Workflows)

- `wcl_fetch_events.py` — download raw events to JSONL for offline analysis.
- `wcl_hit_counter.py` — count hits from JSON/JSONL/CSV exports using the shared analysis engine in `who_messed_up/` (supports `--only-ability`, `--ability-id`, and regex filters).

Example:

```bash
python wcl_hit_counter.py events.jsonl --ability-id 1227472
```

Both scripts now consume the shared package modules, so new features in the FastAPI layer automatically benefit the CLIs.

---

## Production Deployment Notes

1. Point Nginx (or Nginx Proxy Manager) at `http://127.0.0.1:8080` for the `/api/*` path.
2. Serve the static frontend (planned `static/index.html`) from a web root like `/var/www/who-messed-up`.
3. Enable HTTPS via Let's Encrypt in the proxy layer.
4. Use a process manager (systemd, supervisord, or Docker) to keep `uvicorn` running.
5. Store client credentials in environment variables or a secret manager on the server.

---

## Repository Layout

```text
who-got-hit/
├── app.py                # FastAPI application
├── requirements.txt
├── wcl_fetch_events.py   # CLI: fetch events to JSONL
├── wcl_hit_counter.py    # CLI: summarize hits from exports
├── who_messed_up/
│   ├── __init__.py
│   ├── analysis.py       # Normalization and hit counting helpers
│   ├── api.py            # Warcraft Logs GraphQL client helpers
│   └── service.py        # Orchestration for the API/CLI layers
└── README.md
```

---

## Security Checklist

- Keep your client secret server-side only.
- Use HTTPS end-to-end.
- Consider rate limiting, caching, and sanitizing user input.
- Rotate secrets immediately if they leak or are suspected compromised.
