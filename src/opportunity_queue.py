"""Opportunity queue business logic: dedupe, upsert policy, status transitions."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src import db
from src.models import CandidateItem, OpportunityDecision, PlacementType, QueueStatus

logger = logging.getLogger(__name__)

# How long a rejected item must wait before it can resurface
_REJECTED_COOLDOWN_HOURS = 72

# Items not acted on within this window become expired
_STALE_TTL_HOURS = 48


def process_decision(
    db_path: Path,
    candidate: CandidateItem,
    decision: OpportunityDecision,
    source_item_id: Optional[int] = None,
) -> Optional[int]:
    """
    Apply a decision to the queue.

    Returns the queue row id if an item was upserted, otherwise None.
    """
    if decision.placement_type == PlacementType.skip or not decision.place_here:
        logger.debug(
            "Skipping %s: %s", candidate.platform_object_id, decision.skip_reason or "no fit"
        )
        return None

    if _is_on_cooldown(db_path, candidate, decision):
        logger.debug("Cooldown active for %s, skipping upsert.", candidate.platform_object_id)
        return None

    row_id = db.upsert_opportunity(db_path, candidate, decision, source_item_id)
    if row_id:
        logger.info(
            "Queue upsert: [%s] %s -> %s (fit=%d risk=%d)",
            candidate.platform.value,
            candidate.title[:60],
            decision.placement_type.value,
            decision.fit_score,
            decision.risk_score,
        )
    return row_id


def _is_on_cooldown(
    db_path: Path, candidate: CandidateItem, decision: OpportunityDecision
) -> bool:
    """Return True if the candidate was recently rejected and is still cooling down."""
    with db._connect(db_path) as conn:
        row = conn.execute(
            """SELECT status, cooldown_until FROM opportunity_queue
               WHERE platform = ? AND platform_object_id = ? AND placement_type = ?""",
            (candidate.platform.value, candidate.platform_object_id, decision.placement_type.value),
        ).fetchone()

    if not row:
        return False

    if row["status"] == "rejected" and row["cooldown_until"]:
        try:
            cutoff = datetime.fromisoformat(row["cooldown_until"])
            if datetime.utcnow() < cutoff:
                return True
        except (ValueError, TypeError):
            pass

    return False


def set_rejected_with_cooldown(db_path: Path, item_id: int) -> None:
    """Mark item rejected and set a cooldown expiry."""
    cooldown_until = (datetime.utcnow() + timedelta(hours=_REJECTED_COOLDOWN_HOURS)).isoformat()
    now = datetime.utcnow().isoformat()
    with db._connect(db_path) as conn:
        conn.execute(
            "UPDATE opportunity_queue SET status = 'rejected', cooldown_until = ?, updated_at = ? WHERE id = ?",
            (cooldown_until, now, item_id),
        )


def expire_stale(db_path: Path, ttl_hours: int = _STALE_TTL_HOURS) -> int:
    """Expire new items that have not been seen within the TTL window."""
    return db.expire_stale_items(db_path, ttl_hours=ttl_hours)


def get_review_inbox(
    db_path: Path,
    platform: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    """Return actionable queue items grouped logically for the HTML inbox."""
    return db.get_open_queue_items(db_path, platform=platform, limit=limit)


def summarize(db_path: Path) -> dict:
    """Return summary counts for the queue."""
    by_status = db.queue_counts_by_status(db_path)
    by_platform = db.queue_counts_by_platform(db_path)
    return {
        "by_status": by_status,
        "by_platform": by_platform,
        "total_open": sum(
            v for k, v in by_status.items() if k not in ("expired", "skip")
        ),
    }
