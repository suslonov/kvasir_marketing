"""SQLite database initialization and helper methods."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models import ClaudeDecision, RunStats, ThreadItem

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS source_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    platform            TEXT NOT NULL DEFAULT 'reddit',
    subreddit           TEXT NOT NULL,
    external_id         TEXT NOT NULL,
    title               TEXT NOT NULL,
    url                 TEXT NOT NULL,
    author              TEXT,
    score               INTEGER DEFAULT 0,
    num_comments        INTEGER DEFAULT 0,
    created_at          TEXT,
    fetched_at          TEXT NOT NULL,
    content_text        TEXT,
    tags_json           TEXT DEFAULT '[]',
    relevance_score     REAL DEFAULT 0.0,
    canonical_hash      TEXT,
    status              TEXT DEFAULT 'candidate'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_source_items_external
    ON source_items (platform, external_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_source_items_hash
    ON source_items (canonical_hash)
    WHERE canonical_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_source_items_subreddit ON source_items (subreddit);
CREATE INDEX IF NOT EXISTS idx_source_items_status ON source_items (status);
CREATE INDEX IF NOT EXISTS idx_source_items_created_at ON source_items (created_at);

CREATE TABLE IF NOT EXISTS opportunities (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id          INTEGER NOT NULL REFERENCES source_items(id),
    opportunity_type        TEXT NOT NULL DEFAULT 'skip',
    relevance_score         INTEGER DEFAULT 0,
    confidence_score        INTEGER DEFAULT 0,
    self_promo_risk_score   INTEGER DEFAULT 50,
    audience_angle          TEXT DEFAULT 'generic',
    recommended_action      TEXT,
    rationale               TEXT,
    ad_text                 TEXT,
    organic_post_text       TEXT,
    comment_reply_text      TEXT,
    moderation_notes        TEXT,
    priority_score          INTEGER DEFAULT 0,
    decision_model          TEXT,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_opportunities_source_item
    ON opportunities (source_item_id);

CREATE INDEX IF NOT EXISTS idx_opportunities_priority ON opportunities (priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_type ON opportunities (opportunity_type);

CREATE TABLE IF NOT EXISTS runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    fetched             INTEGER DEFAULT 0,
    kept                INTEGER DEFAULT 0,
    duplicates          INTEGER DEFAULT 0,
    dropped             INTEGER DEFAULT 0,
    claude_evaluated    INTEGER DEFAULT 0,
    rendered_count      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS community_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    platform            TEXT NOT NULL DEFAULT 'reddit',
    community           TEXT NOT NULL,
    promo_tolerance     TEXT DEFAULT 'unknown',
    audience_fit        TEXT DEFAULT 'unknown',
    dominant_topics     TEXT,
    notes               TEXT,
    last_seen_at        TEXT,
    UNIQUE(platform, community)
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path) -> None:
    """Create all tables and indexes if they do not already exist."""
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA_SQL)
    logger.info("Database initialized at %s", db_path)


def upsert_item(db_path: Path, item: ThreadItem) -> int:
    """Insert or update a source item. Returns the row id."""
    now = datetime.utcnow().isoformat()
    tags_json = json.dumps(item.tags)
    created_at = item.created_at.isoformat() if item.created_at else None
    fetched_at = item.fetched_at.isoformat()

    with _connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM source_items WHERE platform = ? AND external_id = ?",
            (item.platform, item.external_id),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE source_items SET
                    score = ?, num_comments = ?, fetched_at = ?,
                    relevance_score = ?, tags_json = ?
                WHERE id = ?""",
                (item.score, item.num_comments, fetched_at,
                 item.relevance_score, tags_json, existing["id"]),
            )
            return existing["id"]

        cursor = conn.execute(
            """INSERT INTO source_items (
                platform, subreddit, external_id, title, url, author,
                score, num_comments, created_at, fetched_at, content_text,
                tags_json, relevance_score, canonical_hash, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                item.platform, item.subreddit, item.external_id,
                item.title, item.url, item.author,
                item.score, item.num_comments, created_at, fetched_at,
                item.content_text, tags_json, item.relevance_score,
                item.canonical_hash, "candidate",
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def upsert_opportunity(
    db_path: Path,
    source_item_id: int,
    decision: ClaudeDecision,
    model: str,
) -> None:
    """Insert or update an opportunity record."""
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM opportunities WHERE source_item_id = ?",
            (source_item_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE opportunities SET
                    opportunity_type = ?, relevance_score = ?, confidence_score = ?,
                    self_promo_risk_score = ?, audience_angle = ?,
                    recommended_action = ?, rationale = ?, ad_text = ?,
                    organic_post_text = ?, comment_reply_text = ?,
                    moderation_notes = ?, priority_score = ?,
                    decision_model = ?, updated_at = ?
                WHERE id = ?""",
                (
                    decision.opportunity_type.value, decision.relevance_score,
                    decision.confidence_score, decision.self_promo_risk_score,
                    decision.audience_angle.value, decision.recommended_action,
                    decision.rationale, decision.ad_text, decision.organic_post_text,
                    decision.comment_reply_text, decision.moderation_notes,
                    decision.priority_score, model, now, existing["id"],
                ),
            )
        else:
            conn.execute(
                """INSERT INTO opportunities (
                    source_item_id, opportunity_type, relevance_score, confidence_score,
                    self_promo_risk_score, audience_angle, recommended_action, rationale,
                    ad_text, organic_post_text, comment_reply_text, moderation_notes,
                    priority_score, decision_model, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    source_item_id, decision.opportunity_type.value,
                    decision.relevance_score, decision.confidence_score,
                    decision.self_promo_risk_score, decision.audience_angle.value,
                    decision.recommended_action, decision.rationale,
                    decision.ad_text, decision.organic_post_text,
                    decision.comment_reply_text, decision.moderation_notes,
                    decision.priority_score, model, now, now,
                ),
            )

        conn.execute(
            "UPDATE source_items SET status = ? WHERE id = ?",
            ("kept" if decision.keep else "dropped", source_item_id),
        )


def get_candidates(db_path: Path, limit: int = 100) -> list[dict]:
    """Return candidate items not yet evaluated by Claude."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """SELECT s.* FROM source_items s
               LEFT JOIN opportunities o ON o.source_item_id = s.id
               WHERE s.status = 'candidate' AND o.id IS NULL
               ORDER BY s.relevance_score DESC, s.score DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_opportunities_for_render(db_path: Path, limit: int = 200) -> list[dict]:
    """Return opportunities joined with source items, ordered by priority."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """SELECT
                s.id as item_id, s.platform, s.subreddit, s.title, s.url,
                s.author, s.score, s.num_comments, s.created_at, s.content_text,
                s.tags_json, s.relevance_score as heuristic_score,
                o.id as opp_id, o.opportunity_type, o.relevance_score,
                o.confidence_score, o.self_promo_risk_score,
                o.audience_angle, o.recommended_action, o.rationale,
                o.ad_text, o.organic_post_text, o.comment_reply_text,
                o.moderation_notes, o.priority_score, o.created_at as evaluated_at
               FROM opportunities o
               JOIN source_items s ON s.id = o.source_item_id
               WHERE o.opportunity_type != 'skip'
               ORDER BY o.priority_score DESC, o.relevance_score DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_run_start(db_path: Path) -> int:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        cursor = conn.execute("INSERT INTO runs (started_at) VALUES (?)", (now,))
        return cursor.lastrowid  # type: ignore[return-value]


def mark_run_end(db_path: Path, run_id: int, stats: RunStats) -> None:
    data = stats.to_db_dict()
    with _connect(db_path) as conn:
        conn.execute(
            """UPDATE runs SET
                finished_at = ?, fetched = ?, kept = ?, duplicates = ?,
                dropped = ?, claude_evaluated = ?, rendered_count = ?
            WHERE id = ?""",
            (
                data["finished_at"] or datetime.utcnow().isoformat(),
                data["fetched"], data["kept"], data["duplicates"],
                data["dropped"], data["claude_evaluated"], data["rendered_count"],
                run_id,
            ),
        )


def upsert_community_profile(
    db_path: Path,
    platform: str,
    community: str,
    promo_tolerance: str,
    audience_fit: str,
    notes: str = "",
) -> None:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO community_profiles
                (platform, community, promo_tolerance, audience_fit, notes, last_seen_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(platform, community) DO UPDATE SET
                promo_tolerance = excluded.promo_tolerance,
                audience_fit = excluded.audience_fit,
                notes = CASE WHEN excluded.notes != '' THEN excluded.notes ELSE notes END,
                last_seen_at = excluded.last_seen_at""",
            (platform, community, promo_tolerance, audience_fit, notes, now),
        )


def get_community_profile(db_path: Path, platform: str, community: str) -> Optional[dict]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM community_profiles WHERE platform = ? AND community = ?",
            (platform, community),
        ).fetchone()
        return dict(row) if row else None
