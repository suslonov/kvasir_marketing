"""End-to-end pipeline orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from src import db, heuristics, render
from src.collectors import reddit
from src.models import AppConfig, RunStats
from src.settings import get_anthropic_api_key

logger = logging.getLogger(__name__)


def run_pipeline(
    config: AppConfig,
    db_path: Path,
    output_path: Path,
    skip_claude: bool = False,
) -> RunStats:
    """Run the full social scanner pipeline.

    Steps:
    1. DB init + record run start
    2. Collect from Reddit
    3. Deduplicate within batch
    4. Heuristic filter + scoring
    5. Persist new items
    6. Claude evaluation (optional)
    7. Render HTML
    8. Record run end
    """
    stats = RunStats()
    db.init_db(db_path)
    run_id = db.mark_run_start(db_path)
    stats = stats.model_copy(update={"run_id": run_id})

    # ── 1. Collect ──────────────────────────────────────────────────────────────
    raw_items = _collect_all(config)
    stats = stats.model_copy(update={"fetched": len(raw_items)})
    logger.info("Collected %d raw items", len(raw_items))

    # ── 2. Batch dedupe ────────────────────────────────────────────────────────
    deduped, dups = heuristics.deduplicate(raw_items)
    stats = stats.model_copy(update={"duplicates": len(dups)})

    # ── 3. Filter + score ──────────────────────────────────────────────────────
    scored = heuristics.filter_and_score(deduped, config)
    dropped_count = len(deduped) - len(scored)
    stats = stats.model_copy(update={"dropped": dropped_count})
    logger.info("After filter: %d items (dropped %d)", len(scored), dropped_count)

    # ── 4. Persist new items ───────────────────────────────────────────────────
    new_count = 0
    for item in scored:
        try:
            db.upsert_item(db_path, item)
            new_count += 1
        except Exception as exc:
            logger.warning("Failed to upsert item '%s': %s", item.title, exc)

    stats = stats.model_copy(update={"kept": new_count})

    # ── 5. Claude evaluation ───────────────────────────────────────────────────
    if not skip_claude:
        evaluated_count = _evaluate_with_claude(config, db_path)
        stats = stats.model_copy(update={"claude_evaluated": evaluated_count})

    # ── 6. Render HTML ─────────────────────────────────────────────────────────
    opportunities = db.get_opportunities_for_render(db_path, limit=200)
    rendered_count = render.render_html(
        opportunities=opportunities,
        output_path=output_path,
    )
    stats = stats.model_copy(update={"rendered_count": rendered_count})

    # ── 7. Close run ───────────────────────────────────────────────────────────
    finished = datetime.now(timezone.utc)
    stats = stats.model_copy(update={"finished_at": finished})
    db.mark_run_end(db_path, run_id, stats)

    logger.info(
        "Run complete: fetched=%d kept=%d dups=%d dropped=%d claude=%d rendered=%d",
        stats.fetched, stats.kept, stats.duplicates, stats.dropped,
        stats.claude_evaluated, stats.rendered_count,
    )
    return stats


def _collect_all(config: AppConfig) -> list:
    """Collect from all enabled sources."""
    items = []
    errors = []

    try:
        reddit_items = reddit.collect(config)
        items.extend(reddit_items)
        logger.info("Reddit: collected %d items", len(reddit_items))
    except Exception as exc:
        logger.error("Reddit collector failed: %s", exc)
        errors.append(str(exc))

    return items


def _evaluate_with_claude(config: AppConfig, db_path: Path) -> int:
    """Run Claude evaluation on candidate items. Returns count of evaluated items."""
    try:
        api_key = get_anthropic_api_key()
    except EnvironmentError as exc:
        logger.warning("Skipping Claude evaluation: %s", exc)
        return 0

    from src.claude.evaluate import evaluate_batch

    candidates = db.get_candidates(db_path, limit=config.global_config.max_claude_batch_size)
    if not candidates:
        logger.info("No candidate items for Claude evaluation.")
        return 0

    decisions = evaluate_batch(
        items=candidates,
        api_key=api_key,
        model=config.global_config.claude_model,
        max_tokens=config.global_config.claude_max_tokens,
    )

    count = 0
    for item_id_str, decision in decisions.items():
        try:
            db.upsert_opportunity(db_path, int(item_id_str), decision, config.global_config.claude_model)
            count += 1
        except Exception as exc:
            logger.warning("Failed to persist decision for item %s: %s", item_id_str, exc)

    logger.info("Claude evaluated %d/%d items", count, len(candidates))
    return count
