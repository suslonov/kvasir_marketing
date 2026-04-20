"""Pydantic models for the Social Scanner pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


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


class SubredditConfig(BaseModel):
    name: str
    enabled: bool = True
    max_items: Optional[int] = None


class GlobalConfig(BaseModel):
    timezone: str = "UTC"
    output_html: str = "data/rendered/index.html"
    db_path: str = "data/state.db"
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
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ThreadItem(BaseModel):
    """A normalized social thread ready for scoring and evaluation."""

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
    """Structured response from Claude evaluation pass."""

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
    """Statistics for a single pipeline run."""

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
