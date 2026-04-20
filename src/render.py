"""Render the static HTML report from opportunity records using Jinja2."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _fmt_date(value: Optional[str]) -> str:
    if not value:
        return "–"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return str(value)[:10]


def _from_json(value: Optional[str]) -> list:
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []


def _build_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["fmt_date"] = _fmt_date
    env.filters["from_json"] = _from_json
    return env


def render_html(
    opportunities: list[dict],
    output_path: Path,
    api_base: str = "",
) -> int:
    """Render opportunities to a static HTML file.

    Returns the count of rendered opportunities.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    by_subreddit: dict[str, list[dict]] = defaultdict(list)
    by_type: dict[str, list[dict]] = defaultdict(list)
    top_opps: list[dict] = []

    for opp in opportunities:
        sub = opp.get("subreddit", "unknown")
        opp_type = opp.get("opportunity_type", "skip")
        by_subreddit[sub].append(opp)
        by_type[opp_type].append(opp)

    top_opps = sorted(opportunities, key=lambda x: x.get("priority_score", 0), reverse=True)[:20]
    high_risk = [o for o in opportunities if (o.get("self_promo_risk_score") or 0) >= 70]
    comment_opps = by_type.get("comment_opportunity", [])
    paid_targets = by_type.get("paid_ad_target", [])

    env = _build_env(_TEMPLATE_DIR)
    template = env.get_template("report.jinja2")
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = template.render(
        opportunities=opportunities,
        top_opps=top_opps,
        by_subreddit=dict(sorted(by_subreddit.items())),
        by_type=dict(by_type),
        comment_opps=comment_opps,
        paid_targets=paid_targets,
        high_risk=high_risk,
        generated_at=generated_at,
        api_base=api_base,
        total_count=len(opportunities),
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info("Rendered %d opportunities to %s", len(opportunities), output_path)
    return len(opportunities)
