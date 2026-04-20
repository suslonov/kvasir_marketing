"""Main CLI entry point with --smoke-test mode."""

from __future__ import annotations
import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path


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
from src.settings import load_config, project_root

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Social Scanner pipeline")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run with 2 subreddits, skip Claude, render to a temp file.",
    )
    parser.add_argument(
        "--skip-claude",
        action="store_true",
        help="Skip Claude evaluation pass.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to sources.yaml (defaults to config/sources.yaml).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root()
    config_path = args.config or (root / "config" / "sources.yaml")
    config = load_config(config_path)

    db_path = Path(os.path.expanduser(config.global_config.db_path))
    output_path = Path(os.path.expanduser(config.global_config.output_html))

    if args.smoke_test:
        logger.info("=== SMOKE TEST MODE ===")
        limited_subs = config.subreddits[:2]
        config = config.model_copy(update={"subreddits": limited_subs})
        fd, tmp = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        output_path = Path(tmp)
        skip_claude = True
    else:
        skip_claude = args.skip_claude

    try:
        stats = pipeline.run_pipeline(config, db_path, output_path, skip_claude=skip_claude)
        logger.info(
            "Done: fetched=%d kept=%d dups=%d dropped=%d claude=%d rendered=%d",
            stats.fetched, stats.kept, stats.duplicates, stats.dropped,
            stats.claude_evaluated, stats.rendered_count,
        )
        if args.smoke_test:
            logger.info("Smoke test HTML written to: %s", output_path)
        return 0
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
