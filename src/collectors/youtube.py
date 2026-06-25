"""
YouTube collector using the YouTube Data API v3.

Requires:
    YOUTUBE_API_KEY  environment variable (Google Cloud project with YouTube Data API enabled)

Supported target types (configured in platforms.yaml):
    video_search   — search for videos matching ``value`` (query string).
                     Optional keys: ``relevance_language`` (ISO 639-1, default ``en``),
                     ``region_code`` (ISO 3166-1 alpha-2, e.g. ``RU``).
    channel        — recent uploads from a specific channel ID or handle

For each video found the collector returns a CandidateItem where:
    score          = like count  (comparable to Reddit upvotes)
    comment_count  = YouTube comment count
    body_excerpt   = description snippet + top comment (if available)
    url            = https://www.youtube.com/watch?v=<video_id>

The intended opportunity type for YouTube is `comment_reply`:
suggest a helpful comment on a relevant video that mentions quizly.pub.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from src.models import CandidateItem, Platform

logger = logging.getLogger(__name__)

_BASE = "https://www.googleapis.com/youtube/v3"
_WATCH = "https://www.youtube.com/watch?v="

# Cost-aware defaults: each search costs 100 quota units,
# each videos.list costs 1 unit per video, commentThreads costs 1 unit.
# Free tier: 10 000 units / day.
_MAX_RESULTS_PER_QUERY = 10
_REQUEST_TIMEOUT = 15


class YouTubeAPIError(RuntimeError):
    """Raised on non-retryable API errors (bad key, quota exceeded, etc.)."""


class YouTubeCollector:
    """
    Collects YouTube video candidates via the Data API v3.

    Usage::

        collector = YouTubeCollector(api_key="...", max_results=10)
        items = collector.collect(targets)
    """

    def __init__(
        self,
        api_key: str,
        max_results: int = _MAX_RESULTS_PER_QUERY,
        max_targets_per_run: int = 5,
        fetch_top_comment: bool = True,
        inter_request_sleep: tuple[float, float] = (1.5, 3.5),
        max_age_days: int = 365,
        fresh_comment_days: int = 30,
    ) -> None:
        self.api_key = api_key
        self.max_results = max_results
        self.max_targets_per_run = max_targets_per_run
        self.fetch_top_comment = fetch_top_comment
        self.inter_request_sleep = inter_request_sleep
        # A video qualifies on recency alone if published within this window
        # (0 = no recency requirement → age never disqualifies a video).
        self.max_age_days = max(0, int(max_age_days))
        # An OLDER video is rescued if its newest comment falls within this window
        # — i.e. the conversation is still alive (0 disables the rescue).
        # Needs fetch_top_comment to be on, since that's where comment dates come from.
        self.fresh_comment_days = max(0, int(fresh_comment_days))
        self._client = httpx.Client(timeout=_REQUEST_TIMEOUT)

    # ── Freshness helpers ─────────────────────────────────────────────────────

    def _video_recent(self, published_at: Optional[datetime]) -> bool:
        """True if the video is recent enough to qualify on its own.

        Unknown publish dates are treated as recent (we don't penalise on
        missing data). max_age_days == 0 means age never disqualifies anything.
        """
        if not self.max_age_days or published_at is None:
            return True
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        return published_at >= cutoff

    def _comment_fresh(self, last_comment_at: Optional[datetime]) -> bool:
        """True if the newest comment is within fresh_comment_days (a live thread).

        Disabled (returns False) when fresh_comment_days == 0 or when we have no
        datable comment to judge by.
        """
        if not self.fresh_comment_days or last_comment_at is None:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.fresh_comment_days)
        return last_comment_at >= cutoff

    # ── Public interface ──────────────────────────────────────────────────────

    def collect(self, targets: list[dict[str, Any]]) -> list[CandidateItem]:
        """Collect from a random subset of targets and return CandidateItems."""
        run_targets = random.sample(targets, min(self.max_targets_per_run, len(targets)))
        logger.info("YouTube: selected %d/%d targets", len(run_targets), len(targets))

        results: list[CandidateItem] = []
        for target in run_targets:
            try:
                items = self._collect_target(target)
                results.extend(items)
                logger.info(
                    "YouTube target %s=%r: %d videos",
                    target.get("type"), target.get("value"), len(items),
                )
            except YouTubeAPIError:
                raise
            except Exception as exc:
                logger.warning("YouTube target %r failed: %s", target.get("value"), exc)
            _sleep(self.inter_request_sleep)

        return results

    # ── Target dispatch ───────────────────────────────────────────────────────

    def _collect_target(self, target: dict[str, Any]) -> list[CandidateItem]:
        t = target.get("type", "")
        value = target.get("value", "")
        if t == "video_search":
            return self._search_videos(target)
        if t == "channel":
            return self._channel_videos(value)
        logger.warning("Unknown YouTube target type: %s", t)
        return []

    # ── video_search ──────────────────────────────────────────────────────────

    def _search_videos(self, target: dict[str, Any]) -> list[CandidateItem]:
        query = (target.get("value") or "").strip()
        if not query:
            return []

        rel_lang = (target.get("relevance_language") or target.get("relevanceLanguage") or "en").strip()
        region = target.get("region_code") or target.get("regionCode")
        region_s = region.strip() if isinstance(region, str) else ""

        params: dict[str, Any] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": self.max_results,
            "order": "relevance",
            "relevanceLanguage": rel_lang,
            "safeSearch": "moderate",
        }
        if region_s:
            params["regionCode"] = region_s

        data = self._get("search", params)
        items = data.get("items", [])
        if not items:
            return []

        video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
        stats = self._fetch_video_stats(video_ids)

        candidates: list[CandidateItem] = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if not vid:
                continue
            cand = self._build_candidate(item["snippet"], vid, stats.get(vid, {}), query)
            if cand is not None:
                candidates.append(cand)
        return candidates

    # ── channel ───────────────────────────────────────────────────────────────

    def _channel_videos(self, channel_id_or_handle: str) -> list[CandidateItem]:
        # Resolve handle → channelId if needed
        channel_id = self._resolve_channel_id(channel_id_or_handle)
        if not channel_id:
            return []

        params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "maxResults": self.max_results,
            "order": "date",
        }
        data = self._get("search", params)
        items = data.get("items", [])
        if not items:
            return []

        video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
        stats = self._fetch_video_stats(video_ids)

        candidates: list[CandidateItem] = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if not vid:
                continue
            cand = self._build_candidate(
                item["snippet"], vid, stats.get(vid, {}), channel_id_or_handle
            )
            if cand is not None:
                candidates.append(cand)
        return candidates

    # ── Build CandidateItem ───────────────────────────────────────────────────

    def _build_candidate(
        self,
        snippet: dict,
        video_id: str,
        stats: dict,
        parent_target: str,
    ) -> Optional[CandidateItem]:
        """Build a CandidateItem, or return None if it fails a freshness filter."""
        published_raw = snippet.get("publishedAt", "")
        try:
            published_at: Optional[datetime] = datetime.fromisoformat(
                published_raw.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            published_at = None

        like_count = int(stats.get("likeCount", 0) or 0)
        comment_count = int(stats.get("commentCount", 0) or 0)
        view_count = int(stats.get("viewCount", 0) or 0)

        description = (snippet.get("description") or "").strip()[:400]
        title = snippet.get("title", "").strip()
        top_comment = ""
        last_comment_at: Optional[datetime] = None
        spotted_comment = ""
        if self.fetch_top_comment and comment_count > 0:
            top_comment, last_comment_at, spotted_comment = self._fetch_comment_info(video_id)

        # Keep a video if it is EITHER recently published OR still has a live
        # conversation (a fresh comment). Drop only when it's old AND quiet.
        if not self._video_recent(published_at) and not self._comment_fresh(last_comment_at):
            logger.debug(
                "YouTube: skipping %s — older than %dd and no comment within %dd",
                video_id, self.max_age_days, self.fresh_comment_days,
            )
            return None

        body_parts = [p for p in [description, top_comment] if p]
        body_excerpt = "\n\n[recent comment] ".join(body_parts) if top_comment else description

        # An existing quizly link in the comments (or the video's own
        # description/title) means the audience was already reached here.
        from src.catalog import find_quizly_mention
        spotted_context = spotted_comment or (find_quizly_mention(title, description) or "")

        return CandidateItem(
            platform=Platform.youtube,
            platform_object_id=video_id,
            parent_target=parent_target,
            url=f"{_WATCH}{video_id}",
            title=title,
            body_excerpt=body_excerpt,
            author=snippet.get("channelTitle", "").strip(),
            score=like_count,
            comment_count=comment_count,
            published_at=published_at,
            discovered_at=datetime.now(timezone.utc),
            spotted_quizly=bool(spotted_context),
            spotted_context=spotted_context,
            raw_json=json.dumps({
                "view_count": view_count,
                "last_comment_at": last_comment_at.isoformat() if last_comment_at else None,
            }),
        )

    # ── API helpers ───────────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict) -> dict:
        params["key"] = self.api_key
        url = f"{_BASE}/{endpoint}?{urlencode(params)}"
        resp = self._client.get(url)
        if resp.status_code == 403:
            data = resp.json()
            reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
            raise YouTubeAPIError(
                f"YouTube API 403 ({reason}). Check your API key and quota."
            )
        resp.raise_for_status()
        return resp.json()

    def _fetch_video_stats(self, video_ids: list[str]) -> dict[str, dict]:
        """Return {video_id: {likeCount, commentCount, viewCount}} for a batch of IDs."""
        if not video_ids:
            return {}
        params = {
            "part": "statistics",
            "id": ",".join(video_ids),
        }
        data = self._get("videos", params)
        return {
            item["id"]: item.get("statistics", {})
            for item in data.get("items", [])
        }

    def _fetch_comment_info(
        self, video_id: str
    ) -> tuple[str, Optional[datetime], str]:
        """Return (representative recent comment, newest-comment timestamp,
        spotted-quizly comment).

        Fetches the most recent comments (order=time) in a single call, so we
        learn how fresh the conversation is, get a good comment for context, and
        notice whether someone already dropped a quizly.pub link in the comments.
        The displayed comment is the most-liked among the recent batch.
        """
        from src.catalog import find_quizly_mention

        try:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": 20,
                "order": "time",
                "textFormat": "plainText",
            }
            data = self._get("commentThreads", params)
            items = data.get("items", [])
            if not items:
                return "", None, ""

            best_text = ""
            best_likes = -1
            last_comment_at: Optional[datetime] = None
            spotted_comment = ""
            for it in items:
                top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                ts = self._parse_dt(top.get("publishedAt") or top.get("updatedAt"))
                if ts and (last_comment_at is None or ts > last_comment_at):
                    last_comment_at = ts
                text = (top.get("textDisplay", "") or "").strip()
                if not spotted_comment and find_quizly_mention(text):
                    spotted_comment = text
                likes = int(top.get("likeCount", 0) or 0)
                if likes > best_likes:
                    best_likes = likes
                    best_text = text

            return best_text[:300], last_comment_at, spotted_comment[:300]
        except Exception as exc:
            logger.debug("Could not fetch comments for %s: %s", video_id, exc)
            return "", None, ""

    @staticmethod
    def _parse_dt(raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _resolve_channel_id(self, handle_or_id: str) -> Optional[str]:
        """Resolve a @handle or channel name to a channelId."""
        if handle_or_id.startswith("UC"):
            return handle_or_id  # already a channel ID
        q = handle_or_id.lstrip("@")
        try:
            params = {"part": "snippet", "q": q, "type": "channel", "maxResults": 1}
            data = self._get("search", params)
            items = data.get("items", [])
            if items:
                return items[0]["id"].get("channelId")
        except Exception as exc:
            logger.warning("Could not resolve channel %r: %s", handle_or_id, exc)
        return None

    def __del__(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


# ── Legacy function interface (used by pipeline.py) ───────────────────────────

def collect(
    targets: list[dict[str, Any]],
    api_key: str = "",
    max_results: int = _MAX_RESULTS_PER_QUERY,
    max_targets_per_run: int = 5,
    fetch_top_comment: bool = True,
    inter_request_sleep: tuple[float, float] = (1.5, 3.5),
    max_age_days: int = 365,
    fresh_comment_days: int = 30,
    **kwargs: Any,
) -> list[CandidateItem]:
    if not api_key:
        logger.debug("YouTube collect() called without api_key — returning empty list.")
        return []
    collector = YouTubeCollector(
        api_key=api_key,
        max_results=max_results,
        max_targets_per_run=max_targets_per_run,
        fetch_top_comment=fetch_top_comment,
        inter_request_sleep=inter_request_sleep,
        max_age_days=max_age_days,
        fresh_comment_days=fresh_comment_days,
    )
    return collector.collect(targets)


def _sleep(inter_request_sleep: tuple[float, float] = (1.5, 3.5)) -> None:
    time.sleep(random.uniform(*inter_request_sleep))
