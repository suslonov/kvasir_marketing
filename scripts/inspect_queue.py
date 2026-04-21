#!/usr/bin/env python3
"""
Inspect the opportunity queue from the command line.

Usage:
    python scripts/inspect_queue.py
    python scripts/inspect_queue.py --status new
    python scripts/inspect_queue.py --platform reddit
    python scripts/inspect_queue.py --runs
    python scripts/inspect_queue.py --summary
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

from src import db, opportunity_queue
from src.settings import get_db_path, load_config, project_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the Kvasir opportunity queue.")
    parser.add_argument("--status", default=None, help="Filter by status (new, reviewed, etc.)")
    parser.add_argument("--platform", default=None, help="Filter by platform (reddit, twitter)")
    parser.add_argument("--limit", type=int, default=20, help="Max items to show (default 20)")
    parser.add_argument("--runs", action="store_true", help="Show recent scanner runs.")
    parser.add_argument("--summary", action="store_true", help="Show queue summary only.")
    return parser.parse_args()


def fmt(val: object, width: int = 0) -> str:
    s = str(val or "")
    if width and len(s) > width:
        s = s[:width - 1] + "…"
    return s.ljust(width) if width else s


def main() -> None:
    args = parse_args()
    root = project_root()
    app_config = load_config(root / "config" / "sources.yaml")
    db_path = get_db_path(app_config)

    if not db_path.exists():
        print(f"No database found at {db_path}")
        print("Run the pipeline first: python scripts/run_once.py")
        sys.exit(1)

    db.init_db(db_path)

    if args.summary or (not args.runs and not args.status):
        summary = opportunity_queue.summarize(db_path)
        print("\n=== Queue Summary ===")
        print(f"  Total open:  {summary['total_open']}")
        print("\n  By status:")
        for status, count in sorted(summary["by_status"].items()):
            print(f"    {status:<12} {count}")
        print("\n  By platform:")
        for platform, count in sorted(summary["by_platform"].items()):
            print(f"    {platform:<12} {count}")
        print()

    if args.runs:
        runs = db.get_recent_runs(db_path, limit=10)
        print("\n=== Recent Runs ===")
        header = f"{'ID':<5} {'Started':<20} {'Finished':<20} {'Status':<10} {'Found':<7} {'Queued':<7} {'Error'}"
        print(header)
        print("-" * len(header))
        for run in runs:
            print(
                f"{fmt(run['id'], 5)} "
                f"{fmt(run['started_at'], 20)} "
                f"{fmt(run['finished_at'], 20)} "
                f"{fmt(run['status'], 10)} "
                f"{fmt(run['discovered_count'], 7)} "
                f"{fmt(run['queued_count'], 7)} "
                f"{fmt(run['error_text'], 40)}"
            )
        print()
        return

    # Show queue items
    items = db.get_open_queue_items(db_path, platform=args.platform, limit=args.limit)
    if args.status:
        items = [i for i in items if i.get("status") == args.status]

    if not items:
        print("No queue items found.")
        return

    print(f"\n=== Queue Items ({len(items)}) ===\n")
    for item in items:
        print(
            f"[{item['status'].upper():<10}] "
            f"[{item['platform']:<8}] "
            f"[{item['placement_type']:<15}] "
            f"fit={item['fit_score']:<3} risk={item['risk_score']:<3}"
        )
        print(f"  Title: {fmt(item['title_snapshot'], 80)}")
        print(f"  URL:   {fmt(item['target_url'], 80)}")
        if item.get("why_now"):
            print(f"  Why:   {fmt(item['why_now'], 80)}")
        if item.get("recommended_text_short"):
            print(f"  Short: {fmt(item['recommended_text_short'], 80)}")
        print()


if __name__ == "__main__":
    main()
