#!/usr/bin/env python
"""Capture regression baselines for key reports."""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

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
    args = parser.parse_args()

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    failures = 0

    for case in REGRESSION_CASES:
        url = args.base_url.rstrip("/") + case["path"]
        params = case["params"]
        print(f"Fetching {case['name']} -> {url}")
        try:
            response = session.get(url, params=params, timeout=120)
            response.raise_for_status()
        except requests.RequestException as exc:
            failures += 1
            print(f"  ERROR: {exc}")
            continue

        data = response.json()
        out_path = output_dir / f"{case['name']}.json"
        out_path.write_text(json.dumps(data, indent=2, sort_keys=True))
        print(f"  Saved {out_path}")

    if failures:
        print(f"Completed with {failures} failures.")
        return 1
    print("All regression snapshots captured successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
