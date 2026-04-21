"""SQLite database initialization, schema migration, and CRUD helpers."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.models import (
    CandidateItem,
    OpportunityDecision,
    OpportunityQueueItem,
    Platform,
    PlacementType,
    QueueStatus,
    ScannerRun,
)

logger = logging.getLogger(__name__)

# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS candidate_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    platform            TEXT NOT NULL,
    platform_object_id  TEXT NOT NULL,
    parent_target       TEXT DEFAULT '',
    url                 TEXT NOT NULL,
    title               TEXT NOT NULL,
    body_excerpt        TEXT DEFAULT '',
    author              TEXT DEFAULT '',
    score               INTEGER DEFAULT 0,
    comment_count       INTEGER DEFAULT 0,
    published_at        TEXT,
    discovered_at       TEXT NOT NULL,
    raw_json            TEXT,
    UNIQUE(platform, platform_object_id)
);

CREATE INDEX IF NOT EXISTS idx_candidates_platform ON candidate_items (platform);
CREATE INDEX IF NOT EXISTS idx_candidates_discovered ON candidate_items (discovered_at);

CREATE TABLE IF NOT EXISTS opportunity_queue (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    platform                TEXT NOT NULL,
    placement_type          TEXT NOT NULL DEFAULT 'skip',
    target_name             TEXT NOT NULL DEFAULT '',
    target_url              TEXT NOT NULL DEFAULT '',
    platform_object_id      TEXT NOT NULL,
    source_item_id          INTEGER,
    title_snapshot          TEXT NOT NULL DEFAULT '',
    body_snapshot           TEXT DEFAULT '',
    why_now                 TEXT DEFAULT '',
    fit_score               INTEGER DEFAULT 0,
    risk_score              INTEGER DEFAULT 50,
    urgency_score           INTEGER DEFAULT 0,
    confidence_score        INTEGER DEFAULT 0,
    recommended_angle       TEXT DEFAULT '',
    recommended_text_short  TEXT DEFAULT '',
    recommended_text_medium TEXT DEFAULT '',
    recommended_text_long   TEXT DEFAULT '',
    recommended_cta         TEXT DEFAULT '',
    risk_notes              TEXT DEFAULT '',
    decision_model          TEXT DEFAULT '',
    decision_version        TEXT DEFAULT '1',
    status                  TEXT NOT NULL DEFAULT 'new',
    cooldown_until          TEXT,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL,
    last_seen_at            TEXT NOT NULL,
    UNIQUE(platform, platform_object_id, placement_type)
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON opportunity_queue (status);
CREATE INDEX IF NOT EXISTS idx_queue_platform ON opportunity_queue (platform);
CREATE INDEX IF NOT EXISTS idx_queue_placement ON opportunity_queue (placement_type);
CREATE INDEX IF NOT EXISTS idx_queue_fit ON opportunity_queue (fit_score DESC);
CREATE INDEX IF NOT EXISTS idx_queue_updated ON opportunity_queue (updated_at);

CREATE TABLE IF NOT EXISTS scanner_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    status              TEXT DEFAULT 'running',
    platform            TEXT DEFAULT 'all',
    discovered_count    INTEGER DEFAULT 0,
    queued_count        INTEGER DEFAULT 0,
    error_text          TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS platform_targets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT NOT NULL,
    target_type     TEXT NOT NULL,
    target_value    TEXT NOT NULL,
    is_enabled      INTEGER DEFAULT 1,
    priority        INTEGER DEFAULT 0,
    notes           TEXT DEFAULT '',
    UNIQUE(platform, target_type, target_value)
);

CREATE INDEX IF NOT EXISTS idx_targets_platform ON platform_targets (platform);
CREATE INDEX IF NOT EXISTS idx_targets_enabled ON platform_targets (is_enabled);
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


# ── Candidate items ────────────────────────────────────────────────────────────

def upsert_candidate(db_path: Path, item: CandidateItem) -> int:
    """Insert or update a candidate item. Returns the row id."""
    discovered_at = item.discovered_at.isoformat()
    published_at = item.published_at.isoformat() if item.published_at else None

    with _connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM candidate_items WHERE platform = ? AND platform_object_id = ?",
            (item.platform.value, item.platform_object_id),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE candidate_items SET
                    score = ?, comment_count = ?, body_excerpt = ?,
                    discovered_at = ?
                WHERE id = ?""",
                (
                    item.score, item.comment_count, item.body_excerpt,
                    discovered_at, existing["id"],
                ),
            )
            return existing["id"]

        cursor = conn.execute(
            """INSERT INTO candidate_items (
                platform, platform_object_id, parent_target, url, title,
                body_excerpt, author, score, comment_count,
                published_at, discovered_at, raw_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                item.platform.value, item.platform_object_id, item.parent_target,
                item.url, item.title, item.body_excerpt, item.author,
                item.score, item.comment_count,
                published_at, discovered_at, item.raw_json,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]


# ── Opportunity queue ─────────────────────────────────────────────────────────

def upsert_opportunity(
    db_path: Path,
    candidate: CandidateItem,
    decision: OpportunityDecision,
    source_item_id: Optional[int] = None,
) -> Optional[int]:
    """
    Upsert an opportunity queue record.
    Skips items if `placement_type == skip`.
    Returns the row id or None if skipped.
    """
    if decision.placement_type == PlacementType.skip:
        return None

    now = datetime.utcnow().isoformat()

    with _connect(db_path) as conn:
        existing = conn.execute(
            """SELECT id, status FROM opportunity_queue
               WHERE platform = ? AND platform_object_id = ? AND placement_type = ?""",
            (candidate.platform.value, candidate.platform_object_id, decision.placement_type.value),
        ).fetchone()

        if existing:
            status = existing["status"]
            # Never re-open posted items; respect rejected cooldown
            if status in ("posted",):
                return existing["id"]
            conn.execute(
                """UPDATE opportunity_queue SET
                    fit_score = ?, risk_score = ?, urgency_score = ?, confidence_score = ?,
                    recommended_angle = ?, recommended_text_short = ?,
                    recommended_text_medium = ?, recommended_text_long = ?,
                    recommended_cta = ?, risk_notes = ?, why_now = ?,
                    decision_model = ?, decision_version = ?,
                    last_seen_at = ?, updated_at = ?
                WHERE id = ?""",
                (
                    decision.fit_score, decision.risk_score, decision.urgency_score,
                    decision.confidence_score, decision.recommended_angle,
                    decision.recommended_text_short, decision.recommended_text_medium,
                    decision.recommended_text_long, decision.recommended_cta,
                    decision.moderation_risk_notes, decision.why_this_place,
                    decision.decision_model, decision.decision_version,
                    now, now, existing["id"],
                ),
            )
            return existing["id"]

        cursor = conn.execute(
            """INSERT INTO opportunity_queue (
                platform, placement_type, target_name, target_url,
                platform_object_id, source_item_id,
                title_snapshot, body_snapshot, why_now,
                fit_score, risk_score, urgency_score, confidence_score,
                recommended_angle, recommended_text_short, recommended_text_medium,
                recommended_text_long, recommended_cta, risk_notes,
                decision_model, decision_version,
                status, created_at, updated_at, last_seen_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                candidate.platform.value, decision.placement_type.value,
                decision.target_name, decision.target_url,
                candidate.platform_object_id, source_item_id,
                candidate.title, candidate.body_excerpt, decision.why_this_place,
                decision.fit_score, decision.risk_score, decision.urgency_score,
                decision.confidence_score, decision.recommended_angle,
                decision.recommended_text_short, decision.recommended_text_medium,
                decision.recommended_text_long, decision.recommended_cta,
                decision.moderation_risk_notes,
                decision.decision_model, decision.decision_version,
                QueueStatus.new.value, now, now, now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def get_open_queue_items(
    db_path: Path,
    platform: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    """Return non-expired queue items ordered by fit_score desc."""
    with _connect(db_path) as conn:
        base = """
            SELECT * FROM opportunity_queue
            WHERE status NOT IN ('expired', 'skip')
            AND placement_type != 'skip'
        """
        params: list = []
        if platform:
            base += " AND platform = ?"
            params.append(platform)
        base += " ORDER BY fit_score DESC, urgency_score DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(base, params).fetchall()
        return [dict(r) for r in rows]


def expire_stale_items(db_path: Path, ttl_hours: int = 48) -> int:
    """Mark new/reviewed items older than ttl_hours as expired. Returns count."""
    cutoff = (datetime.utcnow() - timedelta(hours=ttl_hours)).isoformat()
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """UPDATE opportunity_queue SET status = 'expired', updated_at = ?
               WHERE status IN ('new') AND last_seen_at < ?""",
            (datetime.utcnow().isoformat(), cutoff),
        )
        count = cursor.rowcount
    if count:
        logger.info("Expired %d stale queue items (ttl=%dh)", count, ttl_hours)
    return count


def update_queue_status(db_path: Path, item_id: int, status: str) -> None:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE opportunity_queue SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, item_id),
        )


def is_duplicate(db_path: Path, platform: str, platform_object_id: str) -> bool:
    """Return True if this object was already queued recently."""
    with _connect(db_path) as conn:
        row = conn.execute(
            """SELECT id FROM opportunity_queue
               WHERE platform = ? AND platform_object_id = ?
               AND status NOT IN ('expired')
               LIMIT 1""",
            (platform, platform_object_id),
        ).fetchone()
        return row is not None


# ── Scanner runs ──────────────────────────────────────────────────────────────

def start_scanner_run(db_path: Path, platform: str = "all") -> int:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO scanner_runs (started_at, status, platform) VALUES (?, 'running', ?)",
            (now, platform),
        )
        return cursor.lastrowid  # type: ignore[return-value]


def finish_scanner_run(
    db_path: Path,
    run_id: int,
    status: str,
    discovered_count: int,
    queued_count: int,
    error_text: str = "",
) -> None:
    now = datetime.utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """UPDATE scanner_runs SET
                finished_at = ?, status = ?,
                discovered_count = ?, queued_count = ?, error_text = ?
               WHERE id = ?""",
            (now, status, discovered_count, queued_count, error_text, run_id),
        )


def get_recent_runs(db_path: Path, limit: int = 10) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM scanner_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_active_run(db_path: Path) -> Optional[dict]:
    """Return the most recent run if it is still marked running."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM scanner_runs WHERE status = 'running' ORDER BY started_at DESC LIMIT 1",
        ).fetchone()
        return dict(row) if row else None


# ── Platform targets ──────────────────────────────────────────────────────────

def get_enabled_targets(db_path: Path, platform: Optional[str] = None) -> list[dict]:
    with _connect(db_path) as conn:
        if platform:
            rows = conn.execute(
                "SELECT * FROM platform_targets WHERE is_enabled = 1 AND platform = ? ORDER BY priority DESC",
                (platform,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM platform_targets WHERE is_enabled = 1 ORDER BY platform, priority DESC",
            ).fetchall()
        return [dict(r) for r in rows]


def upsert_platform_target(db_path: Path, target: dict) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """INSERT INTO platform_targets (platform, target_type, target_value, is_enabled, priority, notes)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(platform, target_type, target_value) DO UPDATE SET
                is_enabled = excluded.is_enabled,
                priority = excluded.priority,
                notes = CASE WHEN excluded.notes != '' THEN excluded.notes ELSE notes END""",
            (
                target["platform"], target["target_type"], target["target_value"],
                int(target.get("is_enabled", 1)), target.get("priority", 0), target.get("notes", ""),
            ),
        )


def queue_counts_by_status(db_path: Path) -> dict[str, int]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM opportunity_queue GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}


def queue_counts_by_platform(db_path: Path) -> dict[str, int]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """SELECT platform, COUNT(*) as cnt FROM opportunity_queue
               WHERE status NOT IN ('expired', 'skip') GROUP BY platform"""
        ).fetchall()
        return {r["platform"]: r["cnt"] for r in rows}


# ── Legacy shims (kept for backward compat with old tests) ────────────────────

def upsert_item(db_path: Path, item: "Any") -> int:
    """Legacy shim: convert a ThreadItem into a CandidateItem and upsert."""
    from datetime import timezone
    candidate = CandidateItem(
        platform=Platform.reddit,
        platform_object_id=item.external_id,
        parent_target=getattr(item, "subreddit", ""),
        url=item.url,
        title=item.title,
        body_excerpt=getattr(item, "content_text", "")[:500],
        author=getattr(item, "author", ""),
        score=getattr(item, "score", 0),
        comment_count=getattr(item, "num_comments", 0),
        published_at=getattr(item, "created_at", None),
    )
    return upsert_candidate(db_path, candidate)


def get_candidates(db_path: Path, limit: int = 100) -> list[dict]:
    """Legacy shim: return candidate items as dicts for backward compat."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM candidate_items ORDER BY discovered_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        # Map to the old schema shape tests expect
        result = []
        for r in rows:
            d = dict(r)
            d.setdefault("subreddit", d.get("parent_target", ""))
            d.setdefault("external_id", d.get("platform_object_id", ""))
            d.setdefault("content_text", d.get("body_excerpt", ""))
            d.setdefault("num_comments", d.get("comment_count", 0))
            result.append(d)
        return result
