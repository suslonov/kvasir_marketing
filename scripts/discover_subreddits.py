"""
Discover new relevant subreddits via Reddit search and update config/discovered_subreddits.yaml.

Run standalone:
    python scripts/discover_subreddits.py [--headless] [--dry-run]

Called automatically by the pipeline each run (via src/collectors/reddit_browser.py).

Results are written to config/discovered_subreddits.yaml.  Each entry gets
`enabled: false` until a human reviews and flips it.  Once enabled, the
pipeline picks them up alongside the hardcoded targets in platforms.yaml.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
DISCOVERED_PATH = CONFIG_DIR / "discovered_subreddits.yaml"
PLATFORMS_PATH = CONFIG_DIR / "platforms.yaml"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Search queries for subreddit discovery
_DISCOVERY_QUERIES = [
    "books reading literature",
    "ai learning education",
    "quiz trivia games",
    "classic literature",
    "book recommendations",
    "interactive learning",
]

_MIN_SUBSCRIBERS = 5_000
_REDDIT_BASE = "https://www.reddit.com"
_NAV_TIMEOUT_MS = 20_000


def _load_existing_known(platforms_path: Path, discovered_path: Path) -> set[str]:
    """Return set of subreddit names already known (platforms.yaml + discovered.yaml)."""
    known: set[str] = set()

    if platforms_path.exists():
        data = yaml.safe_load(platforms_path.read_text(encoding="utf-8")) or {}
        for target in data.get("platforms", {}).get("reddit", {}).get("targets", []):
            if target.get("type", "").startswith("subreddit:"):
                known.add(target["value"].lower())

    if discovered_path.exists():
        data = yaml.safe_load(discovered_path.read_text(encoding="utf-8")) or {}
        for entry in data.get("discovered", []):
            known.add(entry["name"].lower())

    return known


def _load_profile_dir() -> Path:
    if PLATFORMS_PATH.exists():
        data = yaml.safe_load(PLATFORMS_PATH.read_text(encoding="utf-8")) or {}
        raw = data.get("platforms", {}).get("reddit", {}).get("browser_profile_dir", "")
        if raw:
            return Path(raw).expanduser().resolve()
    return Path.home() / ".kvasir" / "browser_profiles" / "reddit_profile"


def _extract_subreddits_from_page(page: Any) -> list[dict]:
    """Extract subreddit cards from a Reddit search result page."""
    results: list[dict] = []
    try:
        # Wait briefly for community cards to render
        page.wait_for_timeout(2000)
        html = page.content()
    except Exception:
        return results

    # Match subreddit links like /r/SomeSubreddit
    names = re.findall(r'href=["\']https?://(?:www\.)?reddit\.com/r/([A-Za-z0-9_]+)/?["\']', html)
    # Deduplicate preserving order
    seen: set[str] = set()
    for name in names:
        lower = name.lower()
        if lower not in seen and lower not in ("all", "popular", "home", "search"):
            seen.add(lower)
            results.append({"name": name})
    return results


def discover_subreddits(headless: bool = True, dry_run: bool = False) -> list[dict]:
    """
    Use Playwright to search Reddit for new subreddits.
    Returns list of new subreddit dicts suitable for discovered_subreddits.yaml.
    """
    profile_dir = _load_profile_dir()
    if not profile_dir.exists():
        logger.warning(
            "Browser profile not found at %s. "
            "Run scripts/bootstrap_reddit_session.py first.",
            profile_dir,
        )
        return []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    known = _load_existing_known(PLATFORMS_PATH, DISCOVERED_PATH)
    logger.info("Already known subreddits: %d", len(known))

    candidates: list[dict] = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        try:
            page = context.new_page()
            page.set_default_timeout(_NAV_TIMEOUT_MS)

            for query in _DISCOVERY_QUERIES:
                encoded = query.replace(" ", "+")
                url = f"{_REDDIT_BASE}/search/?q={encoded}&type=sr&sort=relevance"
                logger.info("Searching: %s", url)
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
                except Exception as exc:
                    logger.warning("Failed to load search for %r: %s", query, exc)
                    continue

                found = _extract_subreddits_from_page(page)
                new_count = 0
                for sr in found:
                    lower = sr["name"].lower()
                    if lower not in known:
                        known.add(lower)
                        sr["discovered_via"] = query
                        sr["discovered_at"] = str(date.today())
                        sr["enabled"] = False
                        candidates.append(sr)
                        new_count += 1
                logger.info("Query %r → %d new subreddits", query, new_count)

                import time, random
                time.sleep(random.uniform(2.0, 4.0))

        finally:
            context.close()

    logger.info("Total new candidates: %d", len(candidates))
    return candidates


def save_discovered(new_entries: list[dict], path: Path = DISCOVERED_PATH) -> None:
    """Merge new entries into discovered_subreddits.yaml."""
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        data = {}
    data.setdefault("discovered", [])

    existing_names = {e["name"].lower() for e in data["discovered"]}
    added = 0
    for entry in new_entries:
        if entry["name"].lower() not in existing_names:
            data["discovered"].append(entry)
            added += 1

    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    logger.info("Saved %d new entries to %s", added, path)


def load_enabled_discovered() -> list[dict]:
    """
    Return platform target dicts for all enabled discovered subreddits.
    Called by the pipeline to merge discovered targets into the scan list.
    """
    if not DISCOVERED_PATH.exists():
        return []
    data = yaml.safe_load(DISCOVERED_PATH.read_text(encoding="utf-8")) or {}
    targets = []
    for entry in data.get("discovered", []):
        if entry.get("enabled"):
            targets.append({"type": "subreddit:hot", "value": entry["name"]})
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="Show the browser window")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print results without writing")
    args = parser.parse_args()

    new_entries = discover_subreddits(headless=args.headless, dry_run=args.dry_run)

    if not new_entries:
        print("No new subreddits discovered.")
        return

    print(f"\nDiscovered {len(new_entries)} new subreddits:")
    for e in new_entries:
        print(f"  r/{e['name']}  (via: {e.get('discovered_via', '?')})")

    if args.dry_run:
        print("\n[dry-run] Not saved.")
        return

    save_discovered(new_entries)
    print(f"\nSaved to {DISCOVERED_PATH}")
    print("Review the file and set `enabled: true` for subreddits you want to scan.")


if __name__ == "__main__":
    main()
