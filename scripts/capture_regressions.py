#!/usr/bin/env python
"""Capture regression baselines for key reports."""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

NEXUS_REPORT = "WczAN4bDfXxPhV93"
DIMENSIUS_REPORT = "W4cZgnxQfR2AH1dT"

REGRESSION_CASES: List[Dict[str, Any]] = [
    {
        "name": "nexus_phase_combined",
        "path": "/api/nexus-phase1",
        "params": {
            "report": NEXUS_REPORT,
            "fight": "Nexus-King Salhadaar",
            "hit_ability_id": 1227472,
            "ghost_ability_id": 1224737,
            "data_type": "DamageTaken",
            "first_hit_only": True,
            "ghost_miss_mode": "first_per_set",
        },
    },
    {
        "name": "nexus_phase_damage_full",
        "path": "/api/nexus-phase-damage",
        "params": {
            "report": NEXUS_REPORT,
            "fight": "Nexus-King Salhadaar",
            "phase": ["full"],
            "phase_profile": "nexus",
        },
    },
    {
        "name": "dimensius_phase_damage_full",
        "path": "/api/nexus-phase-damage",
        "params": {
            "report": DIMENSIUS_REPORT,
            "fight": "Dimensius, the All-Devouring",
            "phase": ["full"],
            "phase_profile": "dimensius",
        },
    },
    {
        "name": "dimensius_add_damage_default",
        "path": "/api/dimensius-add-damage",
        "params": {
            "report": DIMENSIUS_REPORT,
            "fight": "Dimensius, the All-Devouring",
            "ignore_first_add_set": False,
        },
    },
    {
        "name": "dimensius_add_damage_ignore_first",
        "path": "/api/dimensius-add-damage",
        "params": {
            "report": DIMENSIUS_REPORT,
            "fight": "Dimensius, the All-Devouring",
            "ignore_first_add_set": True,
        },
    },
    {
        "name": "ghosts_first_per_set",
        "path": "/api/ghosts",
        "params": {
            "report": NEXUS_REPORT,
            "ability_id": 1224737,
            "fight": "Nexus-King Salhadaar",
            "ghost_miss_mode": "first_per_set",
        },
    },
    {
        "name": "ghosts_all",
        "path": "/api/ghosts",
        "params": {
            "report": NEXUS_REPORT,
            "ability_id": 1224737,
            "fight": "Nexus-King Salhadaar",
            "ghost_miss_mode": "all",
        },
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture regression baselines from the running API server.")
    parser.add_argument("--base-url", default="http://localhost:8088", help="Backend base URL (default: http://localhost:8088)")
    parser.add_argument(
        "--out-dir",
        default="regression_snapshots",
        help="Directory to store JSON snapshots (default: regression_snapshots)",
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help="Name of a specific regression case to run (can be provided multiple times). Defaults to all cases.",
    )
    args = parser.parse_args()

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    failures = 0

    selected_names = {name.strip() for name in (args.cases or []) if name and name.strip()}
    cases = REGRESSION_CASES
    if selected_names:
        cases = [case for case in REGRESSION_CASES if case["name"] in selected_names]
        missing = selected_names - {case["name"] for case in cases}
        if missing:
            print(f"Warning: unknown regression case(s): {', '.join(sorted(missing))}")
    for case in cases:
        url = args.base_url.rstrip("/") + case["path"]
        params = case["params"]
        print(f"Fetching {case['name']} -> {url}")
        try:
            data = fetch_with_poll(session, url, params=params, base_url=args.base_url)
        except Exception as exc:  # pylint: disable=broad-except
            failures += 1
            print(f"  ERROR: {exc}")
            continue

        out_path = output_dir / f"{case['name']}.json"
        out_path.write_text(json.dumps(data, indent=2, sort_keys=True))
        print(f"  Saved {out_path}")

    if failures:
        print(f"Completed with {failures} failures.")
        return 1
    print("All regression snapshots captured successfully.")
    return 0


def fetch_with_poll(
    session: requests.Session,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    base_url: str,
    poll_interval: float = 2.0,
    poll_timeout: float = 180.0,
) -> Dict[str, Any]:
    response = session.get(url, params=params, timeout=120)
    if response.status_code == 202:
        payload = response.json()
        job = payload.get("job") or {}
        job_id = job.get("id")
        if not job_id:
            raise RuntimeError("Job queued but no job ID returned.")
        return poll_job(session, base_url, job_id, poll_interval=poll_interval, poll_timeout=poll_timeout)

    response.raise_for_status()
    return response.json()


def poll_job(
    session: requests.Session,
    base_url: str,
    job_id: str,
    *,
    poll_interval: float,
    poll_timeout: float,
) -> Dict[str, Any]:
    job_url = f"{base_url.rstrip('/')}/api/jobs/{job_id}"
    deadline = time.time() + poll_timeout
    last_status = None

    while time.time() < deadline:
        resp = session.get(job_url, timeout=60)
        resp.raise_for_status()
        job = resp.json()
        status = job.get("status")
        last_status = status
        if status == "completed":
            result = job.get("result")
            if result is None:
                raise RuntimeError(f"Job {job_id} completed but returned no result.")
            return result
        if status == "failed":
            raise RuntimeError(f"Job {job_id} failed: {job.get('error')}")
        time.sleep(poll_interval)

    raise TimeoutError(f"Timed out waiting for job {job_id} (last status={last_status}).")


if __name__ == "__main__":
    sys.exit(main())
