"""
Cron-safe pipeline entry point with overlap guard.

Usage:
    python -m src.scheduler_entry

Crontab example (every 10 minutes):
    */10 * * * * bash /path/to/kvasir_marketing/scripts/run_scheduler.sh >> ~/logs/kvasir.log 2>&1
"""

from __future__ import annotations

import fcntl
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional


def _find_repo_root(start: Path) -> Path:
    current = start.resolve()
    while current != current.parent:
        if (current / "src").is_dir():
            return current
        current = current.parent
    return start.resolve()


try:
    _PROJECT_ROOT = _find_repo_root(Path(__file__).resolve())
except NameError:
    _PROJECT_ROOT = _find_repo_root(Path(os.getcwd()).resolve())

_root_str = str(_PROJECT_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
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
logger = logging.getLogger("scheduler")

_LOCK_FILE = _PROJECT_ROOT / "runtime" / "state" / "scheduler.lock"


def _acquire_lock() -> Optional[Any]:
    """
    Acquire a file lock to prevent overlapping runs.
    Returns the lock file handle on success, None if already locked.
    """
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = open(_LOCK_FILE, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except OSError:
        fh.close()
        return None


def main() -> None:
    lock = _acquire_lock()
    if lock is None:
        logger.warning("Another scheduler run is already active — skipping this cycle.")
        sys.exit(0)

    try:
        root = project_root()
        app_config = load_config(root / "config" / "sources.yaml")
        platforms_config = load_platforms_config(root / "config" / "platforms.yaml")

        db_path = get_db_path(app_config)
        output_path = get_output_html_path(app_config)

        logger.info("=== Kvasir scheduler starting (db=%s) ===", db_path)

        stats = pipeline.run_pipeline(
            db_path=db_path,
            output_path=output_path,
            platforms_config=platforms_config,
            app_config=app_config,
        )

        logger.info(
            "Run complete: discovered=%d after_filter=%d queued=%d expired=%d errors=%d",
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

    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    main()
