#!/usr/bin/env python3
"""
wcl_fetch_events.py
Download events from a Warcraft Logs v2 GraphQL API report and save them as JSONL (one event per line).

Usage:
  # Using client id/secret as env vars:
  WCL_CLIENT_ID=xxx WCL_CLIENT_SECRET=yyy python wcl_fetch_events.py QDbKNwLr3dRXy9TV

  # Or pass a bearer token directly:
  python wcl_fetch_events.py QDbKNwLr3dRXy9TV --token YOUR_BEARER_TOKEN

  # Choose data type, output file, and filter fights by name:
  python wcl_fetch_events.py <REPORT_CODE> --data-type DamageTaken --only-fight "Salhadaar" --out events.jsonl

Then feed the JSONL to the hit counter:
  python wcl_hit_counter.py events.jsonl
"""
import argparse
import json
import os
import sys
from typing import Iterable, List

import requests

from who_messed_up.env import load_env
from who_messed_up.api import Fight, events_for_fights, fetch_fights, filter_fights, get_token_from_client

def main():
    load_env()

    ap = argparse.ArgumentParser(description="Fetch Warcraft Logs v2 events to JSONL.")
    ap.add_argument("report_code")
    ap.add_argument("--data-type", default="DamageTaken")
    ap.add_argument("--only-fight", help="Substring match on fight name.")
    ap.add_argument("--fight-id", action="append", type=int, help="Restrict to one or more fight IDs.")
    ap.add_argument("--ability-id", type=int, help="Only include events matching this ability GUID/ID.")
    ap.add_argument("--out", default="events.jsonl")
    ap.add_argument("--limit", type=int, default=5000)
    ap.add_argument("--token")
    args = ap.parse_args()

    token = args.token or get_token_from_client(os.getenv("WCL_CLIENT_ID"), os.getenv("WCL_CLIENT_SECRET"))
    if not token:
        print("ERROR: Provide --token or WCL_CLIENT_ID/WCL_CLIENT_SECRET env vars.", file=sys.stderr)
        sys.exit(2)

    s = requests.Session()

    try:
        fights, actor_names, actor_classes, actor_owners = fetch_fights(s, token, args.report_code)
    except Exception as exc:
        print(f"ERROR fetching fights: {exc}", file=sys.stderr)
        sys.exit(2)

    chosen: List[Fight] = filter_fights(fights, args.only_fight)
    if args.fight_id:
        allowed = set(int(fid) for fid in args.fight_id)
        chosen = [fight for fight in chosen if fight.id in allowed]

    if not chosen:
        print("No fights matched.", file=sys.stderr)
        sys.exit(1)

    wrote = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        events: Iterable[dict] = events_for_fights(
            s,
            token,
            code=args.report_code,
            data_type=args.data_type,
            fights=chosen,
            limit=args.limit,
            ability_id=args.ability_id,
            actor_names=actor_names,
        )
        for event in events:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
            wrote += 1

    print(f"Wrote {wrote} events to {args.out}")
    print(f"Next: python wcl_hit_counter.py {args.out}")

if __name__ == "__main__":
    main()
