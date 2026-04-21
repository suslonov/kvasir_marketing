#!/usr/bin/env python3
"""
Run one full pipeline cycle immediately, with optional overrides.

Usage:
    python scripts/run_once.py
    python scripts/run_once.py --skip-claude
    python scripts/run_once.py --platform reddit
    python scripts/run_once.py --output /tmp/queue.html
"""

from __future__ import annotations

import argparse
import logging
import os
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

from src import pipeline
from src.settings import (
    get_db_path,
    get_output_html_path,
    load_config,
    load_platforms_config,
    project_root,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("run_once")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one Kvasir scan cycle.")
    parser.add_argument("--skip-claude", action="store_true", help="Skip LLM evaluation.")
    parser.add_argument("--output", type=Path, default=None, help="Override output HTML path.")
    parser.add_argument("--db", type=Path, default=None, help="Override DB path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()

    app_config = load_config(root / "config" / "sources.yaml")
    platforms_config = load_platforms_config(root / "config" / "platforms.yaml")

    db_path = args.db or get_db_path(app_config)
    output_path = args.output or get_output_html_path(app_config)

    logger.info("DB: %s", db_path)
    logger.info("Report: %s", output_path)
    logger.info("Skip Claude: %s", args.skip_claude)

    stats = pipeline.run_pipeline(
        db_path=db_path,
        output_path=output_path,
        platforms_config=platforms_config,
        app_config=app_config,
        skip_claude=args.skip_claude,
    )

    logger.info(
        "Done: discovered=%d after_filter=%d queued=%d expired=%d errors=%d",
        stats["discovered"],
        stats["after_filter"],
        stats["queued"],
        stats["expired"],
        len(stats["errors"]),
    )
    for err in stats["errors"]:
        logger.warning("Error: %s", err)

    if stats["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
