#!/usr/bin/env python3
"""
wcl_hit_counter.py
Count how many times each player was hit by abilities from a Warcraft Logs export (JSON/CSV).

Supported inputs:
- JSON (single JSON with "events":[...], or JSONL where each line is a JSON event)
- CSV (columns such as ability/spellName and target/destName are auto-detected)

Examples:
  python wcl_hit_counter.py report.json
  python wcl_hit_counter.py events.csv --only-ability "Shadowflame"
  python wcl_hit_counter.py report.jsonl --ability-regex "(Fireball|Pyroblast)" --output hits.csv
  python wcl_hit_counter.py events.csv --source "Raszageth"  # only hits from a certain source
"""
import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

from who_messed_up.env import load_env
from who_messed_up.analysis import build_counter


def write_summary_csv(out_path: Path, by_ability: Dict[Tuple[str, str], int]) -> None:
    # Sort by target then by descending hits
    rows = [ (t, a, c) for (t, a), c in by_ability.items() ]
    rows.sort(key=lambda x: (x[0].lower(), -x[2], x[1].lower()))
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player", "ability", "hits"])
        w.writerows(rows)

def main():
    load_env()

    ap = argparse.ArgumentParser(description="Count how many times players got hit by abilities from a Warcraft Logs export (JSON/CSV).")
    ap.add_argument("input", type=str, help="Path to JSON/JSONL/CSV exported from Warcraft Logs (Events).")
    ap.add_argument("--only-ability", type=str, help="Exact ability name to include (case sensitive).")
    ap.add_argument("--ability-id", type=int, help="Only include events matching this ability GUID/ID.")
    ap.add_argument("--ability-regex", type=str, help="Regex to match ability names (case sensitive by default; use (?i) for CI).")
    ap.add_argument("--source", type=str, help="Only include events from this source name (boss/mob/player).")
    ap.add_argument("--output", type=str, default="hit_summary.csv", help="Where to write the per-player per-ability CSV (default: hit_summary.csv).")
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: Input not found: {path}", file=sys.stderr)
        sys.exit(2)

    ability_re = re.compile(args.ability_regex) if args.ability_regex else None

    aggregate = build_counter(
        path=path,
        ability_regex=ability_re,
        only_ability=args.only_ability,
        only_ability_id=args.ability_id,
        only_source=args.source,
    )

    total_counter = aggregate.hits_by_player

    # Human-readable stdout summary
    print("=== Hits per player (all abilities) ===")
    for player, hits in sorted(total_counter.items(), key=lambda kv: (-kv[1], kv[0].lower())):
        print(f"{player}: {hits}")

    if aggregate.damage_by_player:
        print("\n=== Damage taken per player ===")
        for player, dmg in sorted(aggregate.damage_by_player.items(), key=lambda kv: (-kv[1], kv[0].lower())):
            print(f"{player}: {dmg:,.0f}")

    if aggregate.fight_total_hits:
        pull_count = len(aggregate.fight_total_hits)
        total_hits = sum(aggregate.fight_total_hits.values())
        avg_hits = total_hits / pull_count if pull_count else 0
        print(f"\nPulls counted: {pull_count}  |  Total hits: {total_hits}  |  Avg hits per pull: {avg_hits:.2f}")

    # Detailed CSV (player, ability, hits)
    out_path = Path(args.output)
    write_summary_csv(out_path, aggregate.hits_by_player_ability)
    print(f"\nDetailed breakdown written to: {out_path.resolve()}")

if __name__ == "__main__":
    main()
