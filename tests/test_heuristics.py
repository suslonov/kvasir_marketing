"""Tests for heuristic filtering and scoring."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.heuristics import deduplicate, filter_and_score, passes_filter, score_item
from src.models import AppConfig, GlobalConfig, SubredditConfig, ThreadItem


def _make_config(**overrides) -> AppConfig:
    global_cfg = GlobalConfig(**{
        "min_score": 10,
        "min_comments": 5,
        "item_age_limit_hours": 72,
        **{k: v for k, v in overrides.items() if k in GlobalConfig.model_fields},
    })
    return AppConfig.model_construct(
        global_config=global_cfg,
        subreddits=[SubredditConfig(name="books")],
        include_keywords=[],
        exclude_keywords=["nsfw", "porn"],
    )


def _make_item(**kwargs) -> ThreadItem:
    defaults = {
        "subreddit": "books",
        "external_id": "abc1",
        "title": "Best books for AI learning",
        "url": "https://reddit.com/r/books/abc1",
        "score": 100,
        "num_comments": 20,
        "content_text": "Looking for AI book recommendations",
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return ThreadItem(**defaults)


def test_passes_filter_engagement_threshold() -> None:
    cfg = _make_config()
    item = _make_item(score=5, num_comments=2)
    assert not passes_filter(item, cfg)


def test_passes_filter_enough_score() -> None:
    cfg = _make_config()
    item = _make_item(score=15, num_comments=2)
    assert passes_filter(item, cfg)


def test_passes_filter_enough_comments() -> None:
    cfg = _make_config()
    item = _make_item(score=3, num_comments=10)
    assert passes_filter(item, cfg)


def test_passes_filter_exclude_keyword() -> None:
    cfg = _make_config()
    item = _make_item(title="Best nsfw books")
    assert not passes_filter(item, cfg)


def test_score_increases_with_keyword_hits() -> None:
    cfg = _make_config()
    item_low = _make_item(title="Random thread about cooking", content_text="")
    item_high = _make_item(
        title="AI book quiz for book club",
        content_text="reading discussion about classics",
    )
    assert score_item(item_high, cfg) > score_item(item_low, cfg)


def test_score_is_bounded() -> None:
    cfg = _make_config()
    item = _make_item(
        title="ai book quiz literature quiz book club tool reading discussion ai for teachers",
        content_text="trivia game word game character chat ai reading interactive learning",
        score=10000,
        num_comments=5000,
    )
    score = score_item(item, cfg)
    assert 0 <= score <= 100


def test_deduplicate_removes_dupes() -> None:
    items = [
        _make_item(external_id="x1"),
        _make_item(external_id="x1"),
        _make_item(external_id="x2"),
    ]
    unique, dupes = deduplicate(items)
    assert len(unique) == 2
    assert len(dupes) == 1


def test_filter_and_score_returns_sorted() -> None:
    cfg = _make_config()
    items = [
        _make_item(external_id="a", title="Random unrelated thread", content_text=""),
        _make_item(external_id="b", title="AI book quiz for literature class", content_text="book club discussion"),
        _make_item(external_id="c", title="Book recommendations for classics", content_text="reading list ai"),
    ]
    scored = filter_and_score(items, cfg)
    scores = [i.relevance_score for i in scored]
    assert scores == sorted(scores, reverse=True)
