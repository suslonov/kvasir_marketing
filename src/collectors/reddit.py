"""Reddit collector — uses OAuth (client_credentials) when credentials are present,
falls back to the public JSON endpoint otherwise."""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.models import AppConfig, ThreadItem
from src.settings import get_reddit_credentials

logger = logging.getLogger(__name__)

_REDDIT_BASE = "https://www.reddit.com"
_OAUTH_BASE = "https://oauth.reddit.com"
_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# Reddit requires a descriptive User-Agent; the OAuth variant must follow
# the format:  <platform>:<app_id>:<version> (by /u/<username>)
# For anonymous use we keep a generic but honest string.
_ANON_HEADERS = {
    "User-Agent": "kvasir-marketing-scanner/1.0 (automated research; no posting)",
    "Accept": "application/json",
}


def _make_hash(platform: str, external_id: str) -> str:
    return hashlib.sha1(f"{platform}:{external_id}".encode()).hexdigest()


def _fetch_oauth_token(client_id: str, client_secret: str) -> Optional[str]:
    """Exchange client credentials for an OAuth bearer token."""
    headers = {"User-Agent": _ANON_HEADERS["User-Agent"]}
    try:
        resp = httpx.post(
            _TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers=headers,
            timeout=15.0,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            logger.error("Reddit OAuth: no access_token in response: %s", resp.text)
            return None
        logger.debug("Reddit OAuth: obtained access token.")
        return token
    except Exception as exc:
        logger.error("Reddit OAuth token fetch failed: %s", exc)
        return None


def _build_headers(token: Optional[str]) -> dict[str, str]:
    if token:
        return {
            "User-Agent": _ANON_HEADERS["User-Agent"],
            "Authorization": f"bearer {token}",
            "Accept": "application/json",
        }
    return _ANON_HEADERS


def _base_url(token: Optional[str]) -> str:
    return _OAUTH_BASE if token else _REDDIT_BASE


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
            datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else None
        )

        selftext = (post_data.get("selftext") or "").strip()
        if selftext in ("[deleted]", "[removed]"):
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
    token: Optional[str],
    sort: str = "hot",
    limit: int = 50,
) -> list[dict]:
    """Fetch raw posts from a subreddit, using OAuth if a token is available."""
    base = _base_url(token)
    url = f"{base}/r/{subreddit}/{sort}.json"
    headers = _build_headers(token)
    params = {"limit": limit, "raw_json": 1}
    try:
        resp = client.get(url, params=params, headers=headers, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        return [child["data"] for child in data.get("data", {}).get("children", [])]
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code == 404:
            logger.warning("Subreddit r/%s not found (404), skipping.", subreddit)
        elif code == 403:
            logger.warning(
                "Subreddit r/%s is private or restricted (403), skipping. "
                "If this is unexpected, ensure REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are set.",
                subreddit,
            )
        else:
            logger.warning("HTTP %s fetching r/%s: %s", code, subreddit, exc)
        return []
    except Exception as exc:
        logger.warning("Error fetching r/%s: %s", subreddit, exc)
        return []


def collect(config: AppConfig) -> list[ThreadItem]:
    """Collect threads from all configured subreddits."""
    items: list[ThreadItem] = []
    delay = config.global_config.reddit_request_delay_seconds
    max_per_sub = config.global_config.max_items_per_subreddit

    enabled_subs = [s for s in config.subreddits if s.enabled]
    if not enabled_subs:
        logger.warning("No enabled subreddits configured.")
        return []

    creds = get_reddit_credentials()
    token: Optional[str] = None
    if creds:
        logger.info("Reddit: OAuth credentials found, fetching access token.")
        token = _fetch_oauth_token(*creds)
        if token:
            logger.info("Reddit: using OAuth API (oauth.reddit.com).")
        else:
            logger.warning("Reddit: OAuth token fetch failed, falling back to anonymous requests.")
    else:
        logger.info(
            "Reddit: no OAuth credentials configured (REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET). "
            "Using anonymous requests — may result in 403 blocks."
        )

    with httpx.Client(follow_redirects=True) as client:
        for sub_cfg in enabled_subs:
            sub = sub_cfg.name
            limit = min(sub_cfg.max_items or max_per_sub, max_per_sub)
            logger.info("Collecting r/%s (limit=%d)", sub, limit)

            raw_posts = _fetch_subreddit(client, sub, token, sort="hot", limit=limit)
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
