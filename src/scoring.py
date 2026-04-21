"""Deterministic pre-LLM scoring for candidate items."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Optional

from src.models import CandidateItem

# ── Quizly / Kvasir relevance signals ─────────────────────────────────────────

_TOPIC_PATTERNS = [
    r"book quiz", r"literature quiz", r"book club", r"reading discussion",
    r"discussion questions", r"classics discussion", r"ai for teachers",
    r"ai classroom", r"trivia game", r"word game", r"character chat",
    r"ai book", r"book challenge", r"reading app", r"ai reading",
    r"interactive learning", r"book recommendations", r"book summary",
    r"ai tools", r"what should i read", r"how to learn", r"recommend",
    r"quiz app", r"edtech", r"homeschool", r"book club tool", r"suggest.*book",
    r"what.*read", r"resources.*for", r"literary", r"book discussion",
    # Catalog authors / titles — matched as topic signals
    r"\bdostoevsky\b", r"\bdostoyevsky\b", r"\bchekhov\b", r"\btolstoy\b",
    r"\bbulgakov\b", r"\bgogol\b", r"\bpushkin\b", r"\bturgenev\b",
    r"\blermontov\b", r"\bleskov\b", r"\bbunin\b", r"\bgoncharov\b",
    r"\bdickens\b", r"\bausten\b", r"\bhemingway\b", r"\bshakespeare\b",
    r"\bwilde\b", r"\bpoe\b", r"edgar allan poe", r"\bcarroll\b",
    r"\bconan doyle\b", r"sherlock holmes", r"\bchristie\b",
    r"jack london", r"great gatsby", r"crime and punishment",
    r"brothers karamazov", r"master and margarita", r"war and peace",
    r"dead souls", r"\boblomov\b", r"jules verne", r"\bfrankenstein\b",
    r"alice in wonderland", r"treasure island", r"pride and prejudice",
    r"jane eyre", r"\bmiddlemarch\b",
    # Game / quiz signals
    r"trivia night", r"board game", r"tabletop", r"quiz night", r"pub quiz",
]

_COMPILED_TOPICS = [re.compile(p, re.IGNORECASE) for p in _TOPIC_PATTERNS]

_ANTI_SIGNALS = [
    r"\bporn\b", r"\bnsfw\b", r"\bonlyfans\b", r"\bleaked\b", r"\bpiracy\b",
    r"\bwarez\b", r"\btorrent\b",
]
_COMPILED_ANTI = [re.compile(p, re.IGNORECASE) for p in _ANTI_SIGNALS]

# Subreddits we consider high-value
_HIGH_VALUE_TARGETS = {
    "books", "suggestmeabook", "bookclub", "literature", "classics",
    "52book", "reading", "ChatGPT", "artificial", "MachineLearning",
    "singularity", "learnprogramming", "education", "Teachers", "homeschool",
    "edtech", "trivia", "wordgames", "SideProject",
}


def _text_for_matching(item: CandidateItem) -> str:
    return f"{item.title} {item.body_excerpt}".lower()


def topic_hit_count(item: CandidateItem) -> int:
    text = _text_for_matching(item)
    return sum(1 for p in _COMPILED_TOPICS if p.search(text))


def has_anti_signal(item: CandidateItem) -> bool:
    text = _text_for_matching(item)
    return any(p.search(text) for p in _COMPILED_ANTI)


def freshness_score(item: CandidateItem, max_age_hours: int = 72) -> float:
    """0–20 score decaying with post age."""
    if not item.published_at:
        return 10.0
    now = datetime.now(timezone.utc)
    pub = item.published_at
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)
    age_hours = (now - pub).total_seconds() / 3600
    return max(0.0, 20.0 * (1 - age_hours / max_age_hours))


def engagement_score(item: CandidateItem) -> float:
    """0–30 score based on score + comment traction."""
    engagement = item.score + item.comment_count * 2
    return min(math.log1p(engagement) * 5, 30.0)


def target_weight(item: CandidateItem) -> float:
    """Bonus for high-value subreddits/targets (0 or 10)."""
    return 10.0 if item.parent_target in _HIGH_VALUE_TARGETS else 0.0


def _catalog_bonus(item: CandidateItem) -> float:
    """
    Return a bonus score if the thread mentions a book/author from the catalog.
    This makes catalog-matched threads bubble up even with lower engagement.
    """
    try:
        from src.catalog import find_book_match
        match = find_book_match(item.title, item.body_excerpt)
        return 15.0 if match else 0.0
    except Exception:
        return 0.0


def compute_pre_score(item: CandidateItem, max_age_hours: int = 72) -> float:
    """Composite heuristic relevance score (0–100)."""
    topic_hits = topic_hit_count(item)
    keyword_score = min(topic_hits * 15, 40.0)
    return round(
        keyword_score
        + engagement_score(item)
        + freshness_score(item, max_age_hours)
        + target_weight(item)
        + _catalog_bonus(item),
        2,
    )


def should_skip_early(item: CandidateItem, min_score: int = 10, min_comments: int = 5) -> bool:
    """True if item clearly fails baseline thresholds and should not be sent to LLM."""
    if has_anti_signal(item):
        return True
    if item.score < min_score and item.comment_count < min_comments:
        return True
    return False


def score_and_filter(
    items: list[CandidateItem],
    min_score: int = 10,
    min_comments: int = 5,
    max_age_hours: int = 72,
) -> list[tuple[CandidateItem, float]]:
    """
    Return (item, pre_score) pairs that pass baseline filtering, sorted descending.
    """
    result: list[tuple[CandidateItem, float]] = []
    for item in items:
        if should_skip_early(item, min_score, min_comments):
            continue
        score = compute_pre_score(item, max_age_hours)
        result.append((item, score))
    return sorted(result, key=lambda x: x[1], reverse=True)
