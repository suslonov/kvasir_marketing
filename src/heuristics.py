"""Keyword filtering and heuristic relevance scoring."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from src.models import AppConfig, ThreadItem

_QUIZLY_ANGLES = [
    "book quiz", "literature quiz", "book club tool", "reading discussion",
    "classics discussion", "ai for teachers", "ai classroom", "trivia game",
    "word game", "character chat", "ai book", "book challenge",
    "reading app", "ai reading", "literary", "book recommendations",
    "discussion questions", "book discussion", "reading list",
    "book summary", "ai tools for", "interactive learning",
    "ai tutor", "ai game", "edtech", "homeschool", "book club",
    "suggest.*book", "what.*read", "how.*learn", "resources.*for",
    # Russian
    "книг", "литератур", "чтени", "читать", "что почитать",
    "классик", "обсуждени", "рекомендаци", "квиз", "викторин",
    "книжный клуб", "интерактивн", "ИИ",
]

_COMPILED_ANGLES = [re.compile(p, re.IGNORECASE) for p in _QUIZLY_ANGLES]


def _text_for_matching(item: ThreadItem) -> str:
    return f"{item.title} {item.content_text}".lower()


def _keyword_hit_count(text: str, patterns: list[re.Pattern]) -> int:  # type: ignore[type-arg]
    return sum(1 for p in patterns if p.search(text))


def passes_filter(item: ThreadItem, config: AppConfig) -> bool:
    """Return True if item passes include/exclude keyword filters and engagement thresholds."""
    text = _text_for_matching(item)

    for kw in config.exclude_keywords:
        if kw.lower() in text:
            return False

    min_score = config.global_config.min_score
    min_comments = config.global_config.min_comments
    if item.score < min_score and item.num_comments < min_comments:
        return False

    if config.include_keywords:
        if not any(kw.lower() in text for kw in config.include_keywords):
            if _keyword_hit_count(text, _COMPILED_ANGLES) == 0:
                return False

    return True


def score_item(item: ThreadItem, config: AppConfig) -> float:
    """Compute a 0–100 heuristic relevance score for a thread."""
    text = _text_for_matching(item)

    angle_hits = _keyword_hit_count(text, _COMPILED_ANGLES)
    keyword_score = min(angle_hits * 15, 50)

    engagement = item.score + item.num_comments * 2
    engagement_score = min(math.log1p(engagement) * 5, 30)

    freshness_score = 0.0
    if item.created_at:
        now = datetime.now(timezone.utc)
        age_hours = (now - item.created_at.replace(tzinfo=timezone.utc if item.created_at.tzinfo is None else item.created_at.tzinfo)).total_seconds() / 3600
        max_age = config.global_config.item_age_limit_hours
        freshness_score = max(0.0, 20.0 * (1 - age_hours / max_age))

    return round(keyword_score + engagement_score + freshness_score, 2)


def deduplicate(items: list[ThreadItem]) -> tuple[list[ThreadItem], list[ThreadItem]]:
    """Remove duplicate items within the batch by external_id.

    Returns (unique_items, duplicates).
    """
    seen: set[str] = set()
    unique: list[ThreadItem] = []
    dupes: list[ThreadItem] = []

    for item in items:
        key = f"{item.platform}:{item.external_id}"
        if key in seen:
            dupes.append(item)
        else:
            seen.add(key)
            unique.append(item)

    return unique, dupes


def filter_and_score(
    items: list[ThreadItem],
    config: AppConfig,
) -> list[ThreadItem]:
    """Apply filters and compute relevance scores. Returns scored, filtered items."""
    result: list[ThreadItem] = []
    for item in items:
        if not passes_filter(item, config):
            continue
        item = item.model_copy(update={"relevance_score": score_item(item, config)})
        result.append(item)
    return sorted(result, key=lambda x: x.relevance_score, reverse=True)
