"""Reddit collector using a persistent Playwright browser session (human login)."""

from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.extractors.reddit_extract import check_session_valid, extract_posts_from_page
from src.models import CandidateItem, Platform

logger = logging.getLogger(__name__)

_REDDIT_BASE = "https://www.reddit.com"
_LOGIN_TIMEOUT_MS = 30_000
_NAV_TIMEOUT_MS = 20_000
_INTER_REQUEST_DELAY_MIN = 2.0
_INTER_REQUEST_DELAY_MAX = 5.0

# After this many consecutive empty runs a target is excluded from sampling.
_MAX_CONSECUTIVE_FAILURES = 3
_FAILURES_FILE = Path(__file__).resolve().parents[2] / "runtime" / "state" / "target_failures.json"


# ── Target failure tracking ───────────────────────────────────────────────────

def _target_key(target: dict) -> str:
    return f"{target.get('type', '')}:{target.get('value', '')}"


def _load_failures() -> dict[str, int]:
    if _FAILURES_FILE.exists():
        try:
            return json.loads(_FAILURES_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_failures(data: dict[str, int]) -> None:
    _FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    _FAILURES_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))


def _filter_active_targets(
    targets: list[dict], failures: dict[str, int]
) -> tuple[list[dict], list[str]]:
    """Return (active_targets, skipped_keys) based on consecutive failure count."""
    active, skipped = [], []
    for t in targets:
        key = _target_key(t)
        if failures.get(key, 0) >= _MAX_CONSECUTIVE_FAILURES:
            skipped.append(key)
        else:
            active.append(t)
    return active, skipped

# Selectors that confirm posts have rendered (Reddit new design)
_POST_READY_SELECTORS = ["shreddit-post", "article[data-testid='post-container']"]


def _wait_for_posts(page: Any) -> None:
    """
    Wait until post elements are visible in the DOM, then scroll to
    trigger lazy-loading of additional posts.

    Reddit renders posts client-side; domcontentloaded fires before any
    post cards exist.  We wait up to 8 s for the first known selector,
    then do a gentle scroll so the feed loads the full first page.
    """
    for sel in _POST_READY_SELECTORS:
        try:
            page.wait_for_selector(sel, timeout=8_000)
            break
        except Exception:
            continue

    # Scroll to the bottom of the visible feed to trigger lazy rendering,
    # then back to top so extraction starts from post #1.
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.8)")
        page.wait_for_timeout(1_200)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
    except Exception:
        pass


class RedditSessionError(RuntimeError):
    """Raised when the browser session is not authenticated or is challenged."""


class RedditBrowserCollector:
    """
    Collects Reddit posts using a persistent Playwright browser context.

    The browser profile must be bootstrapped with `scripts/bootstrap_reddit_session.py`
    before first use.
    """

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        max_posts_per_target: int = 12,
        max_targets_per_run: int = 8,
    ) -> None:
        self.profile_dir = profile_dir
        self.headless = headless
        self.max_posts = max_posts_per_target
        self.max_targets_per_run = max_targets_per_run

    def collect(self, targets: list[dict[str, Any]]) -> list[CandidateItem]:
        """
        Collect candidates from a random subset of configured targets.

        Each run selects up to `max_targets_per_run` targets at random so that
        the full list rotates across many runs rather than always hitting the
        same subreddits first.  A random sleep between requests reduces the
        chance of rate-limiting.

        Raises RedditSessionError if the browser session is invalid.
        Handles per-target failures gracefully.
        """
        if not self.profile_dir.exists():
            raise RedditSessionError(
                f"Browser profile directory not found: {self.profile_dir}. "
                "Run scripts/bootstrap_reddit_session.py to create it."
            )

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "playwright is not installed. Run: pip install playwright && playwright install chromium"
            ) from exc

        # Load persistent failure counts and filter out consistently empty targets
        failures = _load_failures()
        active_targets, skipped = _filter_active_targets(targets, failures)
        if skipped:
            logger.info(
                "Skipping %d target(s) with %d+ consecutive empty runs: %s",
                len(skipped), _MAX_CONSECUTIVE_FAILURES, skipped,
            )

        # Random subset from the remaining active targets
        run_targets = random.sample(active_targets, min(self.max_targets_per_run, len(active_targets)))
        logger.info("Selected %d/%d active targets for this run", len(run_targets), len(active_targets))

        results: list[CandidateItem] = []

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(self.profile_dir),
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            try:
                page = context.new_page()
                page.set_default_timeout(_NAV_TIMEOUT_MS)

                # Verify session before scanning
                self._verify_session(page)

                for target in run_targets:
                    key = _target_key(target)
                    try:
                        items = self._collect_target(page, target)
                        results.extend(items)
                        logger.info(
                            "Target %s=%s: collected %d candidates",
                            target.get("type"), target.get("value"), len(items),
                        )
                        if items:
                            failures[key] = 0  # reset on success
                        else:
                            failures[key] = failures.get(key, 0) + 1
                            if failures[key] >= _MAX_CONSECUTIVE_FAILURES:
                                logger.warning(
                                    "Target %s reached %d consecutive empty runs — "
                                    "will be excluded from future sampling.",
                                    key, failures[key],
                                )
                    except RedditSessionError:
                        raise
                    except Exception as exc:
                        logger.warning(
                            "Target %s=%s failed: %s",
                            target.get("type"), target.get("value"), exc,
                        )
                        failures[key] = failures.get(key, 0) + 1

                    delay = random.uniform(_INTER_REQUEST_DELAY_MIN, _INTER_REQUEST_DELAY_MAX)
                    logger.debug("Sleeping %.1fs before next target", delay)
                    time.sleep(delay)

            finally:
                context.close()

        _save_failures(failures)
        return results

    def _verify_session(self, page: Any) -> None:
        """Navigate to Reddit and verify the session is logged in."""
        try:
            page.goto(_REDDIT_BASE, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
        except Exception as exc:
            raise RedditSessionError(f"Failed to load Reddit: {exc}") from exc

        if not check_session_valid(page):
            raise RedditSessionError(
                "Reddit session appears to be logged out or challenged. "
                "Run scripts/bootstrap_reddit_session.py to refresh the session."
            )
        logger.info("Reddit session verified.")

    def _collect_target(self, page: Any, target: dict[str, Any]) -> list[CandidateItem]:
        target_type = target.get("type", "")
        value = target.get("value", "")

        if target_type in ("subreddit:hot", "subreddit:new"):
            sort = "hot" if "hot" in target_type else "new"
            return self._collect_subreddit(page, value, sort)

        if target_type == "subreddit:search":
            return self._collect_subreddit_search(page, value)

        if target_type == "manual_url":
            return self._collect_url(page, value)

        logger.warning("Unknown target type: %s", target_type)
        return []

    def _collect_subreddit(
        self, page: Any, subreddit: str, sort: str = "hot"
    ) -> list[CandidateItem]:
        url = f"{_REDDIT_BASE}/r/{subreddit}/{sort}/"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
        except Exception as exc:
            logger.warning("Failed to load r/%s/%s: %s", subreddit, sort, exc)
            return []

        if not check_session_valid(page):
            raise RedditSessionError("Session expired while loading r/" + subreddit)

        _wait_for_posts(page)

        raw_posts = extract_posts_from_page(page, subreddit, self.max_posts)
        return [self._to_candidate(p, subreddit) for p in raw_posts if p.get("url")]

    def _collect_subreddit_search(self, page: Any, query: str) -> list[CandidateItem]:
        """Search Reddit globally for a query string."""
        encoded = query.replace(" ", "+")
        url = f"{_REDDIT_BASE}/search/?q={encoded}&sort=hot&t=week"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
        except Exception as exc:
            logger.warning("Failed to load search '%s': %s", query, exc)
            return []

        if not check_session_valid(page):
            raise RedditSessionError("Session expired during search.")

        _wait_for_posts(page)

        raw_posts = extract_posts_from_page(page, "search", self.max_posts)
        for post in raw_posts:
            if not post.get("subreddit") or post["subreddit"] == "search":
                import re
                m = re.search(r"/r/([^/]+)/", post.get("url", ""))
                post["subreddit"] = m.group(1) if m else "unknown"

        return [self._to_candidate(p, p.get("subreddit", "unknown")) for p in raw_posts if p.get("url")]

    def _collect_url(self, page: Any, url: str) -> list[CandidateItem]:
        """Collect from a specific manually-configured URL."""
        import re
        m = re.search(r"/r/([^/]+)", url)
        subreddit = m.group(1) if m else "unknown"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
        except Exception as exc:
            logger.warning("Failed to load URL %s: %s", url, exc)
            return []
        raw_posts = extract_posts_from_page(page, subreddit, self.max_posts)
        return [self._to_candidate(p, subreddit) for p in raw_posts if p.get("url")]

    def _to_candidate(self, post: dict[str, Any], parent_target: str) -> CandidateItem:
        return CandidateItem(
            platform=Platform.reddit,
            platform_object_id=post.get("post_id") or post["url"],
            parent_target=parent_target,
            url=post["url"],
            title=post["title"],
            body_excerpt=post.get("body_excerpt", ""),
            author=post.get("author", ""),
            score=post.get("score", 0),
            comment_count=post.get("comment_count", 0),
            published_at=post.get("published_at"),
            discovered_at=datetime.now(timezone.utc),
        )
