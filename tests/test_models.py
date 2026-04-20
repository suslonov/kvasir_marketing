"""Tests for Pydantic models and DB init."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.models import (
    AudienceAngle,
    ClaudeDecision,
    GlobalConfig,
    OpportunityType,
    ThreadItem,
)


def test_thread_item_requires_title() -> None:
    with pytest.raises(Exception):
        ThreadItem(
            subreddit="books",
            external_id="abc",
            title="",
            url="https://reddit.com/r/books/abc",
        )


def test_thread_item_strips_title() -> None:
    item = ThreadItem(
        subreddit="books",
        external_id="abc",
        title="  Hello World  ",
        url="https://reddit.com/r/books/abc",
    )
    assert item.title == "Hello World"


def test_thread_item_defaults() -> None:
    item = ThreadItem(
        subreddit="books",
        external_id="abc",
        title="Test thread",
        url="https://reddit.com/r/books/abc",
    )
    assert item.platform == "reddit"
    assert item.score == 0
    assert item.num_comments == 0
    assert item.content_text == ""
    assert item.tags == []


def test_claude_decision_defaults() -> None:
    decision = ClaudeDecision(keep=True)
    assert decision.opportunity_type == OpportunityType.skip
    assert decision.audience_angle == AudienceAngle.generic
    assert decision.priority_score == 0


def test_claude_decision_score_validation() -> None:
    with pytest.raises(Exception):
        ClaudeDecision(keep=True, priority_score=150)


def test_global_config_defaults() -> None:
    cfg = GlobalConfig()
    assert cfg.max_items_per_subreddit == 50
    assert cfg.min_score == 10
    assert cfg.min_comments == 5


def test_db_init() -> None:
    from src import db
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db.init_db(db_path)
        assert db_path.exists()


def test_db_upsert_and_retrieve() -> None:
    from src import db
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db.init_db(db_path)

        item = ThreadItem(
            subreddit="books",
            external_id="test123",
            title="Great book discussion",
            url="https://reddit.com/r/books/test123",
            score=50,
            num_comments=10,
            content_text="What books do you recommend?",
        )
        item_id = db.upsert_item(db_path, item)
        assert item_id > 0

        candidates = db.get_candidates(db_path)
        assert len(candidates) == 1
        assert candidates[0]["title"] == "Great book discussion"


def test_db_upsert_idempotent() -> None:
    from src import db
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db.init_db(db_path)

        item = ThreadItem(
            subreddit="books",
            external_id="test123",
            title="Great book discussion",
            url="https://reddit.com/r/books/test123",
        )
        id1 = db.upsert_item(db_path, item)
        id2 = db.upsert_item(db_path, item)
        assert id1 == id2

        candidates = db.get_candidates(db_path)
        assert len(candidates) == 1
