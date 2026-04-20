"""Claude evaluation adapter for social thread opportunity analysis."""

from __future__ import annotations

import json
import logging
from typing import Any

from src.claude.prompts import render_evaluate_prompt
from src.models import AudienceAngle, ClaudeDecision, OpportunityType

logger = logging.getLogger(__name__)


def _items_to_prompt_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(item.get("id", "")),
            "platform": item.get("platform", "reddit"),
            "subreddit": item.get("subreddit", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "score": item.get("score", 0),
            "num_comments": item.get("num_comments", 0),
            "snippet": (item.get("content_text") or "")[:500],
        }
        for item in items
    ]


def _parse_decision(entry: dict[str, Any]) -> ClaudeDecision:
    """Parse a single decision dict from Claude's response."""
    opp_type_raw = entry.get("opportunity_type", "skip")
    try:
        opp_type = OpportunityType(opp_type_raw)
    except ValueError:
        opp_type = OpportunityType.skip

    angle_raw = entry.get("audience_angle", "generic")
    try:
        angle = AudienceAngle(angle_raw)
    except ValueError:
        angle = AudienceAngle.generic

    return ClaudeDecision(
        keep=bool(entry.get("keep", False)),
        opportunity_type=opp_type,
        relevance_score=int(entry.get("relevance_score", 0)),
        confidence_score=int(entry.get("confidence_score", 0)),
        self_promo_risk_score=int(entry.get("self_promo_risk_score", 50)),
        audience_angle=angle,
        recommended_action=str(entry.get("recommended_action", "")),
        rationale=str(entry.get("rationale", "")),
        moderation_notes=str(entry.get("moderation_notes", "")),
        ad_text=str(entry.get("ad_text", "")),
        organic_post_text=str(entry.get("organic_post_text", "")),
        comment_reply_text=str(entry.get("comment_reply_text", "")),
        priority_score=int(entry.get("priority_score", 0)),
    )


def _parse_response(raw_json: str, expected_ids: list[str]) -> dict[str, ClaudeDecision]:
    """Parse the JSON array from Claude into a dict keyed by item id."""
    # Strip markdown code fences if present
    text = raw_json.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Claude returned invalid JSON: %s", exc)
        return {}

    if not isinstance(data, list):
        logger.warning("Claude returned non-list JSON: %r", type(data))
        return {}

    results: dict[str, ClaudeDecision] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        item_id = str(entry.get("id", ""))
        if not item_id or item_id not in expected_ids:
            continue
        try:
            results[item_id] = _parse_decision(entry)
        except Exception as exc:
            logger.warning("Could not parse decision for item %s: %s", item_id, exc)

    return results


def evaluate_batch(
    items: list[dict[str, Any]],
    api_key: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 4096,
) -> dict[str, ClaudeDecision]:
    """Send a batch of items to Claude for evaluation.

    Returns a dict mapping item id (str) → ClaudeDecision.
    Falls back to an empty dict on any API error.
    """
    if not items:
        return {}

    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package is not installed. Run: pip install anthropic")
        return {}

    prompt_items = _items_to_prompt_dicts(items)
    expected_ids = [d["id"] for d in prompt_items]
    prompt = render_evaluate_prompt(prompt_items)

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text
    except Exception as exc:
        logger.error("Claude API call failed: %s", exc)
        return {}

    decisions = _parse_response(raw_text, expected_ids)
    logger.info("Claude evaluated %d/%d items", len(decisions), len(items))
    return decisions
