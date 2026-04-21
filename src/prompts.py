"""Prompt loading and rendering utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_PROMPTS_DIR = Path(os.environ.get("SOCIAL_SCANNER_HOME", Path(__file__).parent.parent)) / "config" / "prompts"


def _load(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def _render(template: str, variables: dict[str, Any]) -> str:
    """
    Render a prompt template with {{ variable }} substitution and
    {% if var %}...{% endif %} / {% if var == "val" %}...{% endif %} blocks.
    """
    import re as _re

    # Process {% if var == "val" %} ... {% endif %}
    def _eval_if_eq(m: _re.Match) -> str:  # type: ignore[type-arg]
        var, val, body = m.group(1).strip(), m.group(2).strip(), m.group(3)
        actual = str(variables.get(var, ""))
        return body if actual == val else ""

    template = _re.sub(
        r'\{%\s*if\s+(\w+)\s*==\s*"([^"]+)"\s*%\}(.*?)\{%\s*endif\s*%\}',
        _eval_if_eq,
        template,
        flags=_re.DOTALL,
    )

    # Process {% if var %} ... {% endif %} (truthy check)
    def _eval_if_truthy(m: _re.Match) -> str:  # type: ignore[type-arg]
        var, body = m.group(1).strip(), m.group(2)
        return body if variables.get(var) else ""

    template = _re.sub(
        r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}',
        _eval_if_truthy,
        template,
        flags=_re.DOTALL,
    )

    # Substitute {{ variable }}
    for key, value in variables.items():
        template = template.replace("{{ " + key + " }}", str(value))
        template = template.replace("{{" + key + "}}", str(value))

    return template


def render_classifier_prompt(candidate: Any, pre_score: float = 0.0) -> str:
    """Render the opportunity classifier prompt for a candidate item."""
    from src.catalog import build_book_context

    template = _load("opportunity_classifier.md")
    parent_target = candidate.parent_target or ""
    title = candidate.title
    body = (candidate.body_excerpt or "")[:500]

    book_ctx = build_book_context(title, body, parent_target)

    variables = {
        "platform": getattr(candidate.platform, "value", str(candidate.platform)),
        "parent_target": parent_target,
        "title": title,
        "body_excerpt": body,
        "url": candidate.url,
        "score": candidate.score,
        "comment_count": candidate.comment_count,
        "pre_score": round(pre_score, 1),
        **book_ctx,
    }
    return _render(template, variables)


def render_recommendation_prompt(opportunity: dict[str, Any]) -> str:
    """Render the recommendation writer prompt for an opportunity dict."""
    template = _load("recommendation_writer.md")
    variables = {
        "platform": opportunity.get("platform", ""),
        "target_name": opportunity.get("target_name", ""),
        "recommended_angle": opportunity.get("recommended_angle", ""),
        "audience_fit": opportunity.get("audience_fit", ""),
    }
    return _render(template, variables)


def load_platform_style_rules() -> str:
    """Return raw platform style rules text."""
    return _load("platform_style_rules.md")
