"""Tests for expired opportunity pagination."""

from __future__ import annotations

from pathlib import Path

from src import db
from src.opportunity_queue import get_expired_feed_page


def _insert_queue_row(
    conn,
    *,
    status: str = "expired",
    title: str = "t",
    platform_object_id: str = "x1",
) -> None:
    now = "2026-05-01T12:00:00"
    conn.execute(
        """INSERT INTO opportunity_queue (
            platform, placement_type, target_name, target_url,
            platform_object_id, title_snapshot, why_now,
            fit_score, risk_score, urgency_score, confidence_score,
            status, created_at, updated_at, last_seen_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "reddit",
            "comment_reply",
            "r/books",
            "https://example.com/p/1",
            platform_object_id,
            title,
            "why",
            50,
            30,
            10,
            70,
            status,
            now,
            now,
            now,
        ),
    )


def test_count_and_page_expired(tmp_path: Path) -> None:
    db_path = tmp_path / "q.db"
    db.init_db(db_path)
    with db._connect(db_path) as conn:
        for i in range(25):
            _insert_queue_row(conn, platform_object_id=f"post-{i}", title=f"Title {i}")
        conn.commit()

    assert db.count_queue_items_with_status(db_path, "expired") == 25
    page1 = db.get_expired_queue_page(db_path, limit=20, offset=0)
    assert len(page1) == 20
    page2 = db.get_expired_queue_page(db_path, limit=20, offset=20)
    assert len(page2) == 5


def test_get_expired_feed_page_json(tmp_path: Path) -> None:
    db_path = tmp_path / "q.db"
    db.init_db(db_path)
    with db._connect(db_path) as conn:
        _insert_queue_row(conn, platform_object_id="a", title="Hello")
        conn.commit()

    out = get_expired_feed_page(db_path, page=1)
    assert out["ok"] is True
    assert out["total"] == 1
    assert out["per_page"] == 20
    assert out["has_more"] is False
    assert len(out["items"]) == 1
    assert out["items"][0]["title_snapshot"] == "Hello"
    assert "fit_score_class" in out["items"][0]
