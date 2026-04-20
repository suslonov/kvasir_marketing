"""Tests for HTML rendering."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.render import render_html


def _make_opportunity(**kwargs) -> dict:
    defaults = {
        "item_id": 1,
        "platform": "reddit",
        "subreddit": "books",
        "title": "Great book discussion thread",
        "url": "https://reddit.com/r/books/test",
        "author": "test_user",
        "score": 150,
        "num_comments": 30,
        "created_at": "2026-04-20T10:00:00",
        "content_text": "Looking for AI book recommendations",
        "tags_json": '["books", "ai"]',
        "heuristic_score": 65.0,
        "opportunity_type": "comment_opportunity",
        "relevance_score": 80,
        "confidence_score": 75,
        "self_promo_risk_score": 25,
        "audience_angle": "book_discussion_tool",
        "recommended_action": "Reply with a helpful comment mentioning Quizly",
        "rationale": "User is asking for book discussion tools, Quizly is a direct fit.",
        "ad_text": "Try Quizly — AI-powered book quizzes for readers.",
        "organic_post_text": "",
        "comment_reply_text": "I've been using Quizly for book club discussions — really engaging!",
        "moderation_notes": "r/books allows tool mentions in relevant threads.",
        "priority_score": 78,
        "evaluated_at": "2026-04-20T11:00:00",
    }
    defaults.update(kwargs)
    return defaults


def test_render_creates_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "index.html"
        count = render_html(opportunities=[_make_opportunity()], output_path=output)
        assert count == 1
        assert output.exists()


def test_render_empty_opportunities() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "index.html"
        count = render_html(opportunities=[], output_path=output)
        assert count == 0
        assert output.exists()


def test_render_contains_expected_content() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "index.html"
        opp = _make_opportunity(title="Unique thread title XYZ789")
        render_html(opportunities=[opp], output_path=output)
        content = output.read_text()
        assert "Unique thread title XYZ789" in content
        assert "r/books" in content
        assert "comment_opportunity" in content.lower() or "comment opportunity" in content.lower()


def test_render_multiple_subreddits() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "index.html"
        opps = [
            _make_opportunity(item_id=1, subreddit="books"),
            _make_opportunity(item_id=2, subreddit="ChatGPT", title="AI tools for reading"),
        ]
        count = render_html(opportunities=opps, output_path=output)
        assert count == 2
        content = output.read_text()
        assert "r/books" in content
        assert "r/ChatGPT" in content


def test_render_creates_parent_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "nested" / "dir" / "index.html"
        render_html(opportunities=[], output_path=output)
        assert output.exists()
