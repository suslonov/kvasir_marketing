"""
YouTube collector using the YouTube Data API v3.

Requires:
    YOUTUBE_API_KEY  environment variable (Google Cloud project with YouTube Data API enabled)

Supported target types (configured in platforms.yaml):
    video_search   — search for videos matching a query string
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
from datetime import datetime, timezone
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
    ) -> None:
        self.api_key = api_key
        self.max_results = max_results
        self.max_targets_per_run = max_targets_per_run
        self.fetch_top_comment = fetch_top_comment
        self.inter_request_sleep = inter_request_sleep
        self._client = httpx.Client(timeout=_REQUEST_TIMEOUT)

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
            return self._search_videos(value)
        if t == "channel":
            return self._channel_videos(value)
        logger.warning("Unknown YouTube target type: %s", t)
        return []

    # ── video_search ──────────────────────────────────────────────────────────

    def _search_videos(self, query: str) -> list[CandidateItem]:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": self.max_results,
            "order": "relevance",
            "relevanceLanguage": "en",
            "safeSearch": "moderate",
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
            candidates.append(self._build_candidate(item["snippet"], vid, stats.get(vid, {}), query))
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
            candidates.append(
                self._build_candidate(item["snippet"], vid, stats.get(vid, {}), channel_id_or_handle)
            )
        return candidates

    # ── Build CandidateItem ───────────────────────────────────────────────────

    def _build_candidate(
        self,
        snippet: dict,
        video_id: str,
        stats: dict,
        parent_target: str,
    ) -> CandidateItem:
        like_count = int(stats.get("likeCount", 0) or 0)
        comment_count = int(stats.get("commentCount", 0) or 0)
        view_count = int(stats.get("viewCount", 0) or 0)

        description = (snippet.get("description") or "").strip()[:400]
        top_comment = ""
        if self.fetch_top_comment and comment_count > 0:
            top_comment = self._fetch_top_comment(video_id) or ""

        body_parts = [p for p in [description, top_comment] if p]
        body_excerpt = "\n\n[top comment] ".join(body_parts) if top_comment else description

        published_raw = snippet.get("publishedAt", "")
        try:
            published_at: Optional[datetime] = datetime.fromisoformat(
                published_raw.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            published_at = None

        return CandidateItem(
            platform=Platform.youtube,
            platform_object_id=video_id,
            parent_target=parent_target,
            url=f"{_WATCH}{video_id}",
            title=snippet.get("title", "").strip(),
            body_excerpt=body_excerpt,
            author=snippet.get("channelTitle", "").strip(),
            score=like_count,
            comment_count=comment_count,
            published_at=published_at,
            discovered_at=datetime.now(timezone.utc),
            raw_json=json.dumps({"view_count": view_count}),
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

    def _fetch_top_comment(self, video_id: str) -> str:
        """Return the text of the top (most-liked) comment, or empty string."""
        try:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": 1,
                "order": "relevance",
                "textFormat": "plainText",
            }
            data = self._get("commentThreads", params)
            items = data.get("items", [])
            if not items:
                return ""
            text = (
                items[0]
                .get("snippet", {})
                .get("topLevelComment", {})
                .get("snippet", {})
                .get("textDisplay", "")
            )
            return text.strip()[:300]
        except Exception as exc:
            logger.debug("Could not fetch top comment for %s: %s", video_id, exc)
            return ""

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
    )
    return collector.collect(targets)


def _sleep(inter_request_sleep: tuple[float, float] = (1.5, 3.5)) -> None:
    time.sleep(random.uniform(*inter_request_sleep))
