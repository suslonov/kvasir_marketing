"""Render the opportunity queue as a static HTML review inbox."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_TEMPLATE_NAME = "opportunity_queue.html"


def _fmt_date(value: Optional[str]) -> str:
    if not value:
        return "–"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%b %d %H:%M")
    except Exception:
        return str(value)[:16]


def _score_class(score: int) -> str:
    if score >= 70:
        return "score-high"
    if score >= 40:
        return "score-mid"
    return "score-low"


def _risk_class(score: int) -> str:
    if score >= 70:
        return "risk-high"
    if score >= 40:
        return "risk-mid"
    return "risk-low"


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure a queue item dict has the fields the template expects.
    Handles legacy opportunity dicts from the old schema.
    """
    item = dict(item)
    # Map legacy fields to new names
    if "title_snapshot" not in item:
        item["title_snapshot"] = item.get("title", "")
    if "target_url" not in item:
        item["target_url"] = item.get("url", "")
    if "target_name" not in item:
        item["target_name"] = item.get("subreddit", "")
    if "placement_type" not in item:
        # Map old opportunity types to new placement types
        opp_type = item.get("opportunity_type", "skip")
        mapping = {
            "comment_opportunity": "comment_reply",
            "organic_post_opportunity": "organic_post",
            "paid_ad_target": "paid_ad_target",
            "monitor": "monitor",
        }
        item["placement_type"] = mapping.get(opp_type, "skip")
    if "why_now" not in item:
        item["why_now"] = item.get("rationale", "")
    if "fit_score" not in item:
        item["fit_score"] = item.get("relevance_score", 0)
    if "risk_score" not in item:
        item["risk_score"] = item.get("self_promo_risk_score", 50)
    if "urgency_score" not in item:
        item["urgency_score"] = 0
    if "confidence_score" not in item:
        item.setdefault("confidence_score", 0)
    if "recommended_text_short" not in item:
        item["recommended_text_short"] = item.get("comment_reply_text", "")
    if "recommended_text_medium" not in item:
        item["recommended_text_medium"] = ""
    if "recommended_text_long" not in item:
        item["recommended_text_long"] = item.get("organic_post_text", "")
    if "recommended_cta" not in item:
        item["recommended_cta"] = ""
    if "risk_notes" not in item:
        item["risk_notes"] = item.get("moderation_notes", "")
    if "status" not in item:
        item["status"] = "new"
    if "created_at" not in item:
        item["created_at"] = item.get("evaluated_at", "")
    if "last_seen_at" not in item:
        item["last_seen_at"] = item.get("created_at", "")
    if "decision_model" not in item:
        item["decision_model"] = ""
    return item


def _build_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["fmt_date"] = _fmt_date
    env.filters["score_class"] = _score_class
    env.filters["risk_class"] = _risk_class
    return env


def _group_by_placement(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        placement = item.get("placement_type", "skip")
        if placement != "skip":
            groups[placement].append(item)
    return dict(groups)


def render_html(
    output_path: Path,
    queue_items: Optional[list[dict[str, Any]]] = None,
    summary: Optional[dict[str, Any]] = None,
    recent_runs: Optional[list[dict[str, Any]]] = None,
    # Legacy keyword (old tests pass opportunities= positional)
    opportunities: Optional[list[dict[str, Any]]] = None,
    **_kwargs: Any,
) -> int:
    """Render queue items to a static HTML review inbox. Returns item count."""
    # Legacy compat: accept old-style opportunities= kwarg
    if queue_items is None:
        queue_items = opportunities or []
    if summary is None:
        summary = {"by_status": {}, "by_platform": {}, "total_open": len(queue_items)}
    if recent_runs is None:
        recent_runs = []

    # Normalize legacy item shapes to new queue item field names
    queue_items = [_normalize_item(item) for item in queue_items]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    by_placement = _group_by_placement(queue_items)

    # Sort each section by fit_score descending
    for section in by_placement.values():
        section.sort(key=lambda x: (x.get("fit_score", 0), x.get("urgency_score", 0)), reverse=True)

    # Build ordered sections for the report
    section_order = [
        ("comment_reply", "Reply Opportunities"),
        ("organic_post", "Organic Post Opportunities"),
        ("paid_ad_target", "Paid Ad Targets"),
        ("monitor", "Monitor"),
    ]
    sections = [
        (key, label, by_placement.get(key, []))
        for key, label in section_order
    ]

    env = _build_env(_TEMPLATE_DIR)
    template = env.get_template(_TEMPLATE_NAME)
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = template.render(
        sections=sections,
        summary=summary,
        recent_runs=recent_runs,
        generated_at=generated_at,
        total_count=len(queue_items),
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info("Rendered %d queue items to %s", len(queue_items), output_path)
    return len(queue_items)
