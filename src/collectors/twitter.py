"""Twitter/X collector using the v2 API with Bearer Token authentication."""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.models import AppConfig, ThreadItem, TwitterSearchConfig

logger = logging.getLogger(__name__)

_TWITTER_BASE = "https://api.twitter.com/2"
_SEARCH_RECENT = f"{_TWITTER_BASE}/tweets/search/recent"
_TWEET_FIELDS = "created_at,author_id,public_metrics,entities,text"
_MAX_RESULTS_PER_REQUEST = 100


def _make_hash(platform: str, external_id: str) -> str:
    return hashlib.sha1(f"{platform}:{external_id}".encode()).hexdigest()


def _parse_tweet(tweet: dict, query: str) -> Optional[ThreadItem]:
    """Parse a raw Twitter v2 tweet dict into a ThreadItem."""
    try:
        tweet_id = tweet.get("id", "")
        if not tweet_id:
            return None

        text = (tweet.get("text") or "").strip()
        if not text:
            return None

        metrics = tweet.get("public_metrics", {})
        like_count = int(metrics.get("like_count", 0))
        reply_count = int(metrics.get("reply_count", 0))
        retweet_count = int(metrics.get("retweet_count", 0))

        created_raw = tweet.get("created_at")
        created_at: Optional[datetime] = None
        if created_raw:
            try:
                created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Tweets have no title — use truncated text as a stand-in
        title = text if len(text) <= 120 else text[:117] + "…"

        url = f"https://twitter.com/i/web/status/{tweet_id}"
        author_id = tweet.get("author_id", "")

        # Aggregate engagement as "score" (likes + retweets weighted)
        score = like_count + retweet_count * 2

        return ThreadItem(
            platform="twitter",
            subreddit=query,  # reuse field as search-context label
            external_id=tweet_id,
            title=title,
            url=url,
            author=author_id,
            score=score,
            num_comments=reply_count,
            created_at=created_at,
            content_text=text,
            canonical_hash=_make_hash("twitter", tweet_id),
        )
    except Exception as exc:
        logger.warning("Failed to parse tweet: %s", exc)
        return None


def _fetch_search(
    client: httpx.Client,
    bearer_token: str,
    query: str,
    max_results: int = 100,
) -> list[dict]:
    """Fetch tweets matching a search query via Twitter API v2."""
    headers = {"Authorization": f"Bearer {bearer_token}"}
    # cap per-request at API max (100 for Basic+)
    per_page = min(max_results, _MAX_RESULTS_PER_REQUEST)
    params = {
        "query": f"({query}) -is:retweet lang:en",
        "max_results": per_page,
        "tweet.fields": _TWEET_FIELDS,
    }

    all_tweets: list[dict] = []
    next_token: Optional[str] = None

    while len(all_tweets) < max_results:
        if next_token:
            params["next_token"] = next_token
        try:
            resp = client.get(_SEARCH_RECENT, params=params, headers=headers, timeout=15.0)
            resp.raise_for_status()
            body = resp.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                logger.error("Twitter: invalid or expired Bearer Token (401).")
            elif status == 429:
                logger.warning("Twitter: rate limit hit (429) for query '%s'.", query)
            else:
                logger.warning("Twitter HTTP error for query '%s': %s", query, exc)
            break
        except Exception as exc:
            logger.warning("Twitter request error for query '%s': %s", query, exc)
            break

        tweets = body.get("data") or []
        all_tweets.extend(tweets)

        meta = body.get("meta", {})
        next_token = meta.get("next_token")
        if not next_token or len(all_tweets) >= max_results:
            break

    return all_tweets[:max_results]


def collect(config: AppConfig, bearer_token: str) -> list[ThreadItem]:
    """Collect tweets from all enabled search queries.

    Returns a flat list of ThreadItem objects.
    """
    if not config.global_config.enable_twitter:
        logger.info("Twitter collection disabled (enable_twitter=false).")
        return []

    enabled_searches = [s for s in config.twitter_searches if s.enabled]
    if not enabled_searches:
        logger.warning("No enabled Twitter search queries configured.")
        return []

    delay = config.global_config.twitter_request_delay_seconds
    max_per_search = config.global_config.max_items_per_search
    items: list[ThreadItem] = []

    with httpx.Client(follow_redirects=True) as client:
        for search_cfg in enabled_searches:
            query = search_cfg.query
            limit = min(search_cfg.max_items or max_per_search, max_per_search)
            logger.info("Collecting Twitter search: '%s' (limit=%d)", query, limit)

            raw_tweets = _fetch_search(client, bearer_token, query, max_results=limit)
            if delay > 0 and enabled_searches[-1] is not search_cfg:
                time.sleep(delay)

            count = 0
            for tweet in raw_tweets:
                item = _parse_tweet(tweet, query)
                if item:
                    items.append(item)
                    count += 1

            logger.info("Twitter '%s': collected %d items", query, count)

    return items
