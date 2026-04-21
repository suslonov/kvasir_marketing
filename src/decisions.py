"""Bridge from normalized CandidateItem to OpportunityDecision via Claude."""

from __future__ import annotations

import json
import logging
from typing import Optional

from src.models import (
    CandidateItem,
    OpportunityDecision,
    PlacementType,
)
from src.prompts import render_classifier_prompt

logger = logging.getLogger(__name__)


def _call_claude(prompt: str, api_key: str, model: str, max_tokens: int) -> str:
    """Call Claude and return the raw text response."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text  # type: ignore[index]


def _parse_decision(raw: str, candidate: CandidateItem, model: str) -> OpportunityDecision:
    """Parse Claude's JSON response into an OpportunityDecision."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = -1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Claude returned invalid JSON for %s: %s", candidate.platform_object_id, exc)
        return _fallback_decision(candidate, model, reason=f"JSON parse error: {exc}")

    placement_raw = data.get("placement_type", "skip")
    try:
        placement = PlacementType(placement_raw)
    except ValueError:
        placement = PlacementType.skip

    return OpportunityDecision(
        placement_type=placement,
        place_here=bool(data.get("place_here", False)),
        target_name=str(data.get("target_name", candidate.parent_target)),
        target_url=str(data.get("target_url", candidate.url)),
        why_this_place=str(data.get("why_this_place", "")),
        timing_reason=str(data.get("timing_reason", "")),
        audience_fit=str(data.get("audience_fit", "")),
        self_promo_risk=str(data.get("self_promo_risk", "")),
        recommended_angle=str(data.get("recommended_angle", "")),
        recommended_text_short=str(data.get("recommended_text_short", "")),
        recommended_text_medium=str(data.get("recommended_text_medium", "")),
        recommended_text_long=str(data.get("recommended_text_long", "")),
        recommended_cta=str(data.get("recommended_cta", "")),
        moderation_risk_notes=str(data.get("moderation_risk_notes", "")),
        confidence_score=_clamp(data.get("confidence_score", 0)),
        fit_score=_clamp(data.get("fit_score", 0)),
        risk_score=_clamp(data.get("risk_score", 50)),
        urgency_score=_clamp(data.get("urgency_score", 0)),
        priority_score=_clamp(data.get("priority_score", 0)),
        skip_reason=str(data.get("skip_reason", "")),
        decision_model=model,
    )


def _clamp(val: object, lo: int = 0, hi: int = 100) -> int:
    try:
        return max(lo, min(hi, int(val)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return lo


def _fallback_decision(
    candidate: CandidateItem, model: str, reason: str = ""
) -> OpportunityDecision:
    return OpportunityDecision(
        placement_type=PlacementType.skip,
        place_here=False,
        skip_reason=reason or "fallback",
        decision_model=model,
    )


def evaluate_candidate(
    candidate: CandidateItem,
    api_key: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
    pre_score: float = 0.0,
) -> OpportunityDecision:
    """
    Evaluate a single candidate item with Claude.
    Returns a parsed OpportunityDecision.
    Falls back to skip on any error.
    """
    try:
        prompt = render_classifier_prompt(candidate, pre_score=pre_score)
        raw = _call_claude(prompt, api_key, model, max_tokens)
        return _parse_decision(raw, candidate, model)
    except Exception as exc:
        logger.error("Claude evaluation failed for %s: %s", candidate.platform_object_id, exc)
        return _fallback_decision(candidate, model, reason=str(exc))


def evaluate_batch(
    candidates: list[tuple[CandidateItem, float]],
    api_key: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
) -> list[tuple[CandidateItem, OpportunityDecision]]:
    """
    Evaluate a batch of (candidate, pre_score) pairs.
    Returns paired (candidate, decision) list.
    """
    results: list[tuple[CandidateItem, OpportunityDecision]] = []
    for candidate, pre_score in candidates:
        decision = evaluate_candidate(
            candidate, api_key, model, max_tokens, pre_score=pre_score
        )
        results.append((candidate, decision))
    return results
