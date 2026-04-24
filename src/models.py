"""Pydantic models for the Kvasir opportunity queue pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class Platform(str, Enum):
    reddit = "reddit"
    twitter = "twitter"
    youtube = "youtube"
    other = "other"


class PlacementType(str, Enum):
    comment_reply = "comment_reply"
    organic_post = "organic_post"
    paid_ad_target = "paid_ad_target"
    monitor = "monitor"
    skip = "skip"


class QueueStatus(str, Enum):
    new = "new"
    reviewed = "reviewed"
    approved = "approved"
    rejected = "rejected"
    posted = "posted"
    expired = "expired"


class TargetType(str, Enum):
    subreddit_new = "subreddit:new"
    subreddit_hot = "subreddit:hot"
    subreddit_search = "subreddit:search"
    multi_subreddit = "multi_subreddit"
    manual_url = "manual_url"
    search = "search"
    account = "account"
    channel = "channel"
    video_topic = "video_topic"


# ── Core data models ──────────────────────────────────────────────────────────

class CandidateItem(BaseModel):
    """A normalized candidate from any platform, ready for scoring and LLM evaluation."""

    platform: Platform
    platform_object_id: str
    parent_target: str = ""
    url: str
    title: str
    body_excerpt: str = ""
    author: str = ""
    score: int = 0
    comment_count: int = 0
    published_at: Optional[datetime] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    raw_json: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    def unique_key(self) -> str:
        return f"{self.platform.value}:{self.platform_object_id}"


class OpportunityDecision(BaseModel):
    """Structured LLM decision for a candidate item."""

    placement_type: PlacementType = PlacementType.skip
    place_here: bool = False
    target_name: str = ""
    target_url: str = ""
    why_this_place: str = ""
    timing_reason: str = ""
    audience_fit: str = ""
    self_promo_risk: str = ""
    recommended_angle: str = ""
    recommended_text_short: str = ""
    recommended_text_medium: str = ""
    recommended_text_long: str = ""
    recommended_cta: str = ""
    moderation_risk_notes: str = ""
    confidence_score: int = Field(ge=0, le=100, default=0)
    fit_score: int = Field(ge=0, le=100, default=0)
    risk_score: int = Field(ge=0, le=100, default=50)
    urgency_score: int = Field(ge=0, le=100, default=0)
    priority_score: int = Field(ge=0, le=100, default=0)
    skip_reason: str = ""
    decision_model: str = ""
    decision_version: str = "1"


class OpportunityQueueItem(BaseModel):
    """A durable opportunity record in the review queue."""

    id: Optional[int] = None
    platform: Platform
    placement_type: PlacementType
    target_name: str
    target_url: str
    platform_object_id: str
    source_item_id: Optional[int] = None
    title_snapshot: str
    body_snapshot: str = ""
    why_now: str = ""
    fit_score: int = 0
    risk_score: int = 50
    urgency_score: int = 0
    confidence_score: int = 0
    recommended_angle: str = ""
    recommended_text_short: str = ""
    recommended_text_medium: str = ""
    recommended_text_long: str = ""
    recommended_cta: str = ""
    risk_notes: str = ""
    decision_model: str = ""
    decision_version: str = "1"
    status: QueueStatus = QueueStatus.new
    cooldown_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)

    def priority_score(self) -> int:
        """Composite score for sorting the queue."""
        return int(
            self.fit_score * 0.4
            + self.urgency_score * 0.35
            + self.confidence_score * 0.25
            - self.risk_score * 0.2
        )


class ScannerRun(BaseModel):
    """Record of a single pipeline run."""

    id: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    status: str = "running"
    platform: str = "all"
    discovered_count: int = 0
    queued_count: int = 0
    error_text: str = ""

    def to_db_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "platform": self.platform,
            "discovered_count": self.discovered_count,
            "queued_count": self.queued_count,
            "error_text": self.error_text,
        }


class PlatformTarget(BaseModel):
    """A configured discovery target (subreddit, search query, account, etc.)."""

    id: Optional[int] = None
    platform: Platform
    target_type: str
    target_value: str
    is_enabled: bool = True
    priority: int = 0
    notes: str = ""


# ── Legacy config models (kept for backward compat with sources.yaml) ─────────

class SubredditConfig(BaseModel):
    name: str
    enabled: bool = True
    max_items: Optional[int] = None


class TwitterSearchConfig(BaseModel):
    query: str
    enabled: bool = True
    max_items: Optional[int] = None


class GlobalConfig(BaseModel):
    timezone: str = "UTC"
    output_html: str = "~/social_scanner/rendered/index.html"
    db_path: str = "~/social_scanner/state.db"
    book_list_path: str = "~/git/kvasir_proto/src/html/kvasir.pub/book-list.txt"
    max_items_per_subreddit: int = 50
    max_claude_batch_size: int = 20
    min_score: int = 10
    min_comments: int = 5
    item_age_limit_hours: int = 72
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 4096
    reddit_request_delay_seconds: float = 1.0


class AppConfig(BaseModel):
    global_config: GlobalConfig = Field(alias="global", default_factory=GlobalConfig)
    subreddits: list[SubredditConfig] = Field(default_factory=list)
    twitter_searches: list[TwitterSearchConfig] = Field(default_factory=list)
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# ── Legacy models (kept for backward compat with tests and heuristics.py) ─────

class OpportunityType(str, Enum):
    skip = "skip"
    monitor = "monitor"
    comment_opportunity = "comment_opportunity"
    organic_post_opportunity = "organic_post_opportunity"
    paid_ad_target = "paid_ad_target"
    research_only = "research_only"


class AudienceAngle(str, Enum):
    literary_ai_game = "literary_ai_game"
    book_discussion_tool = "book_discussion_tool"
    creator_contest = "creator_contest"
    classic_text_chat = "classic_text_chat"
    quiz_challenge = "quiz_challenge"
    classroom_tool = "classroom_tool"
    generic = "generic"


class ThreadItem(BaseModel):
    """Legacy normalized thread model (kept for backward compat)."""

    platform: str = "reddit"
    subreddit: str
    external_id: str
    title: str
    url: str
    author: str = ""
    score: int = 0
    num_comments: int = 0
    created_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    content_text: str = ""
    tags: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    canonical_hash: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()


class ClaudeDecision(BaseModel):
    """Legacy Claude decision model (kept for backward compat)."""

    keep: bool
    opportunity_type: OpportunityType = OpportunityType.skip
    relevance_score: int = Field(ge=0, le=100, default=0)
    confidence_score: int = Field(ge=0, le=100, default=0)
    self_promo_risk_score: int = Field(ge=0, le=100, default=50)
    audience_angle: AudienceAngle = AudienceAngle.generic
    recommended_action: str = ""
    rationale: str = ""
    moderation_notes: str = ""
    ad_text: str = ""
    organic_post_text: str = ""
    comment_reply_text: str = ""
    priority_score: int = Field(ge=0, le=100, default=0)


class RunStats(BaseModel):
    """Legacy run statistics model."""

    run_id: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    fetched: int = 0
    kept: int = 0
    duplicates: int = 0
    dropped: int = 0
    claude_evaluated: int = 0
    rendered_count: int = 0
    errors: list[str] = Field(default_factory=list)

    def to_db_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "fetched": self.fetched,
            "kept": self.kept,
            "duplicates": self.duplicates,
            "dropped": self.dropped,
            "claude_evaluated": self.claude_evaluated,
            "rendered_count": self.rendered_count,
        }
