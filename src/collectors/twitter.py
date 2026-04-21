"""Twitter/X collector using the v2 API with Bearer Token authentication."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from src.models import CandidateItem, Platform

logger = logging.getLogger(__name__)

_TWITTER_BASE = "https://api.twitter.com/2"
_SEARCH_RECENT = f"{_TWITTER_BASE}/tweets/search/recent"
_TWEET_FIELDS = "created_at,author_id,public_metrics,entities,text"
_MAX_RESULTS_PER_REQUEST = 100


def _parse_tweet(tweet: dict, query: str) -> Optional[CandidateItem]:
    """Parse a raw Twitter v2 tweet dict into a CandidateItem."""
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
        published_at: Optional[datetime] = None
        if created_raw:
            try:
                published_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                pass

        title = text if len(text) <= 120 else text[:117] + "…"
        url = f"https://twitter.com/i/web/status/{tweet_id}"
        author_id = tweet.get("author_id", "")
        score = like_count + retweet_count * 2

        return CandidateItem(
            platform=Platform.twitter,
            platform_object_id=tweet_id,
            parent_target=query,
            url=url,
            title=title,
            body_excerpt=text[:500],
            author=author_id,
            score=score,
            comment_count=reply_count,
            published_at=published_at,
            discovered_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.warning("Failed to parse tweet: %s", exc)
        return None


def _fetch_search(
    client: httpx.Client,
    bearer_token: str,
    query: str,
    max_results: int = 50,
) -> list[dict]:
    """Fetch tweets matching a search query via Twitter API v2."""
    headers = {"Authorization": f"Bearer {bearer_token}"}
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


def collect(
    queries: list[str],
    bearer_token: str,
    max_per_query: int = 10,
    delay_seconds: float = 2.0,
) -> list[CandidateItem]:
    """
    Collect candidates from a list of Twitter search queries.
    Returns a flat list of CandidateItem objects.
    """
    if not queries:
        logger.warning("No Twitter search queries configured.")
        return []

    items: list[CandidateItem] = []

    with httpx.Client(follow_redirects=True) as client:
        for i, query in enumerate(queries):
            logger.info("Collecting Twitter search: '%s' (limit=%d)", query, max_per_query)
            raw_tweets = _fetch_search(client, bearer_token, query, max_results=max_per_query)
            if delay_seconds > 0 and i < len(queries) - 1:
                time.sleep(delay_seconds)

            count = 0
            for tweet in raw_tweets:
                item = _parse_tweet(tweet, query)
                if item:
                    items.append(item)
                    count += 1

            logger.info("Twitter '%s': collected %d items", query, count)

    return items
