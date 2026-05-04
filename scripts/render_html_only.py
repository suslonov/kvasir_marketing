#!/usr/bin/env python3
"""Re-render the opportunity queue HTML from the SQLite DB — no scraping, no Claude.

Usage:
    python scripts/render_html_only.py
    python scripts/render_html_only.py --output /tmp/queue.html
    python scripts/render_html_only.py --db ~/.kvasir/social_scanner.db
"""

from __future__ import annotations

import argparse
import logging
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

from src import db, opportunity_queue, render
from src.settings import (
    get_db_path,
    get_output_html_path,
    load_config,
    project_root,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("render_html_only")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render queue HTML only (read DB → write HTML).")
    p.add_argument("--output", type=Path, default=None, help="Override output HTML path.")
    p.add_argument("--db", type=Path, default=None, help="Override SQLite DB path.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    app_config = load_config(root / "config" / "sources.yaml")

    db_path = args.db or get_db_path(app_config)
    output_path = args.output or get_output_html_path(app_config)

    if not db_path.exists():
        logger.error("Database not found: %s", db_path)
        sys.exit(1)

    db.init_db(db_path)
    queue_items = opportunity_queue.get_review_inbox(db_path, limit=200)
    summary = opportunity_queue.summarize(db_path)
    recent_runs = db.get_recent_runs(db_path, limit=5)

    count = render.render_html(
        output_path=output_path,
        queue_items=queue_items,
        summary=summary,
        recent_runs=recent_runs,
    )
    logger.info("Wrote %d items to %s", count, output_path)


if __name__ == "__main__":
    main()
