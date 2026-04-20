"""Reddit collector using public JSON endpoints (no auth required)."""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.models import AppConfig, SubredditConfig, ThreadItem

logger = logging.getLogger(__name__)

_REDDIT_BASE = "https://www.reddit.com"
_HEADERS = {
    "User-Agent": "social-scanner/1.0 (local marketing research tool)",
    "Accept": "application/json",
}


def _make_hash(platform: str, external_id: str) -> str:
    return hashlib.sha1(f"{platform}:{external_id}".encode()).hexdigest()


def _parse_post(post_data: dict, subreddit: str) -> Optional[ThreadItem]:
    """Parse a raw Reddit post dict into a ThreadItem."""
    try:
        title = post_data.get("title", "").strip()
        if not title:
            return None

        external_id = post_data.get("id", "")
        if not external_id:
            return None

        permalink = post_data.get("permalink", "")
        url = f"https://www.reddit.com{permalink}" if permalink else post_data.get("url", "")

        created_utc = post_data.get("created_utc")
        created_at = (
            datetime.fromtimestamp(created_utc, tz=timezone.utc)
            if created_utc
            else None
        )

        selftext = (post_data.get("selftext") or "").strip()
        if selftext == "[deleted]" or selftext == "[removed]":
            selftext = ""

        return ThreadItem(
            platform="reddit",
            subreddit=subreddit,
            external_id=external_id,
            title=title,
            url=url,
            author=post_data.get("author", ""),
            score=int(post_data.get("score", 0)),
            num_comments=int(post_data.get("num_comments", 0)),
            created_at=created_at,
            content_text=selftext,
            canonical_hash=_make_hash("reddit", external_id),
        )
    except Exception as exc:
        logger.warning("Failed to parse Reddit post: %s", exc)
        return None


def _fetch_subreddit(
    client: httpx.Client,
    subreddit: str,
    sort: str = "hot",
    limit: int = 50,
) -> list[dict]:
    """Fetch raw posts from a subreddit JSON endpoint."""
    url = f"{_REDDIT_BASE}/r/{subreddit}/{sort}.json"
    params = {"limit": limit, "raw_json": 1}
    try:
        resp = client.get(url, params=params, headers=_HEADERS, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        return [child["data"] for child in data.get("data", {}).get("children", [])]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            logger.warning("Subreddit r/%s not found (404), skipping.", subreddit)
        elif exc.response.status_code == 403:
            logger.warning("Subreddit r/%s is private or restricted (403), skipping.", subreddit)
        else:
            logger.warning("HTTP error fetching r/%s: %s", subreddit, exc)
        return []
    except Exception as exc:
        logger.warning("Error fetching r/%s: %s", subreddit, exc)
        return []


def collect(config: AppConfig) -> list[ThreadItem]:
    """Collect threads from all configured subreddits.

    Returns a flat list of ThreadItem objects.
    """
    items: list[ThreadItem] = []
    delay = config.global_config.reddit_request_delay_seconds
    max_per_sub = config.global_config.max_items_per_subreddit

    enabled_subs = [s for s in config.subreddits if s.enabled]
    if not enabled_subs:
        logger.warning("No enabled subreddits configured.")
        return []

    with httpx.Client(follow_redirects=True) as client:
        for sub_cfg in enabled_subs:
            sub = sub_cfg.name
            limit = min(sub_cfg.max_items or max_per_sub, max_per_sub)
            logger.info("Collecting r/%s (limit=%d)", sub, limit)

            raw_posts = _fetch_subreddit(client, sub, sort="hot", limit=limit)
            if delay > 0:
                time.sleep(delay)

            count = 0
            for post_data in raw_posts:
                item = _parse_post(post_data, sub)
                if item:
                    items.append(item)
                    count += 1

            logger.info("r/%s: collected %d items", sub, count)

    return items
