"""Queue-first pipeline orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src import db, opportunity_queue, render, scoring
from src.models import AppConfig, CandidateItem, Platform
from src.settings import (
    get_anthropic_api_key,
    get_max_posts_per_target,
    get_max_targets_per_run,
    get_platform_targets,
    get_youtube_api_key,
    is_platform_enabled,
    load_platforms_config,
    project_root,
)

logger = logging.getLogger(__name__)


def run_pipeline(
    db_path: Path,
    output_path: Path,
    platforms_config: Optional[dict[str, Any]] = None,
    app_config: Optional[AppConfig] = None,
    skip_claude: bool = False,
    stale_ttl_hours: int = 48,
) -> dict[str, Any]:
    """
    Run one full scan cycle.

    Flow:
    1. Init DB
    2. Start scanner run record
    3. Collect candidates from each enabled platform
    4. Pre-score and filter
    5. Evaluate with Claude (unless skip_claude)
    6. Upsert queue items
    7. Expire stale items
    8. Render HTML
    9. Finish scanner run record

    Returns a stats dict.
    """
    if platforms_config is None:
        platforms_config = load_platforms_config()

    db.init_db(db_path)
    run_id = db.start_scanner_run(db_path)

    stats: dict[str, Any] = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "discovered": 0,
        "after_filter": 0,
        "queued": 0,
        "expired": 0,
        "errors": [],
    }

    # ── 1. Collect candidates ──────────────────────────────────────────────────
    all_candidates: list[CandidateItem] = []
    platform_errors: list[str] = []

    if is_platform_enabled(platforms_config, "reddit"):
        try:
            reddit_candidates = _collect_reddit(platforms_config)
            all_candidates.extend(reddit_candidates)
            logger.info("Reddit: collected %d candidates", len(reddit_candidates))
        except Exception as exc:
            msg = f"Reddit collector failed: {exc}"
            logger.error(msg)
            platform_errors.append(msg)

    if is_platform_enabled(platforms_config, "twitter"):
        try:
            twitter_candidates = _collect_twitter(platforms_config, app_config)
            all_candidates.extend(twitter_candidates)
            logger.info("Twitter: collected %d candidates", len(twitter_candidates))
        except Exception as exc:
            msg = f"Twitter collector failed: {exc}"
            logger.error(msg)
            platform_errors.append(msg)

    if is_platform_enabled(platforms_config, "youtube"):
        try:
            youtube_candidates = _collect_youtube(platforms_config)
            all_candidates.extend(youtube_candidates)
            logger.info("YouTube: collected %d candidates", len(youtube_candidates))
        except Exception as exc:
            msg = f"YouTube collector failed: {exc}"
            logger.error(msg)
            platform_errors.append(msg)

    stats["discovered"] = len(all_candidates)
    stats["errors"] = platform_errors

    # ── 2. Dedupe within batch ─────────────────────────────────────────────────
    seen: set[str] = set()
    unique_candidates: list[CandidateItem] = []
    for c in all_candidates:
        key = c.unique_key()
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    # ── 3. Pre-score and filter ────────────────────────────────────────────────
    min_score = app_config.global_config.min_score if app_config else 10
    min_comments = app_config.global_config.min_comments if app_config else 5

    scored = scoring.score_and_filter(unique_candidates, min_score=min_score, min_comments=min_comments)
    stats["after_filter"] = len(scored)
    logger.info("After scoring/filter: %d candidates (from %d)", len(scored), len(unique_candidates))

    # ── 4. Persist candidates ──────────────────────────────────────────────────
    for candidate, _ in scored:
        try:
            db.upsert_candidate(db_path, candidate)
        except Exception as exc:
            logger.warning("Failed to upsert candidate '%s': %s", candidate.title[:60], exc)

    # ── 5. Claude evaluation ───────────────────────────────────────────────────
    queued_count = 0
    if not skip_claude:
        queued_count = _evaluate_and_queue(scored, db_path, app_config, platforms_config)
    else:
        logger.info("Skipping Claude evaluation (skip_claude=True).")

    stats["queued"] = queued_count

    # ── 6. Expire stale items ──────────────────────────────────────────────────
    expired = opportunity_queue.expire_stale(db_path, ttl_hours=stale_ttl_hours)
    stats["expired"] = expired

    # ── 7. Render HTML ─────────────────────────────────────────────────────────
    try:
        queue_items = opportunity_queue.get_review_inbox(db_path)
        summary = opportunity_queue.summarize(db_path)
        recent_runs = db.get_recent_runs(db_path, limit=5)
        render.render_html(
            queue_items=queue_items,
            summary=summary,
            recent_runs=recent_runs,
            output_path=output_path,
        )
        logger.info("Rendered %d queue items to %s", len(queue_items), output_path)
    except Exception as exc:
        logger.error("Render failed: %s", exc)
        stats["errors"].append(f"Render failed: {exc}")

    # ── 8. Close run record ────────────────────────────────────────────────────
    error_text = "; ".join(stats["errors"])
    run_status = "error" if platform_errors else "ok"
    db.finish_scanner_run(
        db_path, run_id, run_status,
        discovered_count=stats["discovered"],
        queued_count=queued_count,
        error_text=error_text,
    )

    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    return stats


def _evaluate_and_queue(
    scored: list[tuple[CandidateItem, float]],
    db_path: Path,
    app_config: Optional[AppConfig],
    platforms_config: dict[str, Any],
) -> int:
    """Run Claude on scored candidates and upsert results to queue. Returns queued count."""
    try:
        api_key = get_anthropic_api_key()
    except EnvironmentError as exc:
        logger.warning("Skipping Claude evaluation: %s", exc)
        return 0

    from src import decisions

    model = app_config.global_config.claude_model if app_config else "claude-sonnet-4-6"
    max_tokens = app_config.global_config.claude_max_tokens if app_config else 2048
    max_batch = app_config.global_config.max_claude_batch_size if app_config else 20

    batch = scored[:max_batch]
    if not batch:
        logger.info("No candidates to evaluate.")
        return 0

    logger.info("Evaluating %d candidates with Claude (%s).", len(batch), model)
    evaluated = decisions.evaluate_batch(batch, api_key, model, max_tokens)

    queued = 0
    for candidate, decision in evaluated:
        try:
            row_id = opportunity_queue.process_decision(db_path, candidate, decision)
            if row_id:
                queued += 1
        except Exception as exc:
            logger.warning("Queue upsert failed for %s: %s", candidate.platform_object_id, exc)

    logger.info("Claude queued %d/%d items.", queued, len(batch))
    return queued


def _collect_reddit(platforms_config: dict[str, Any]) -> list[CandidateItem]:
    """Collect from Reddit using the browser collector."""
    from scripts.discover_subreddits import discover_subreddits, load_enabled_discovered, save_discovered
    from src.collectors.reddit_browser import RedditBrowserCollector
    from src.settings import get_browser_profile_dir, is_headless

    profile_dir = get_browser_profile_dir(platforms_config)
    headless = is_headless(platforms_config, "reddit")
    max_posts = get_max_posts_per_target(platforms_config, "reddit")
    max_targets = get_max_targets_per_run(platforms_config, "reddit")

    # Static targets from platforms.yaml
    targets = get_platform_targets(platforms_config, "reddit")

    # Merge enabled discovered subreddits
    discovered_targets = load_enabled_discovered()
    if discovered_targets:
        logger.info("Adding %d enabled discovered subreddits", len(discovered_targets))
        targets = targets + discovered_targets

    # Run subreddit discovery in the background (save results for human review)
    try:
        new_discovered = discover_subreddits(headless=headless, dry_run=False)
        if new_discovered:
            save_discovered(new_discovered)
    except Exception as exc:
        logger.warning("Subreddit discovery failed (non-fatal): %s", exc)

    collector = RedditBrowserCollector(
        profile_dir=profile_dir,
        headless=headless,
        max_posts_per_target=max_posts,
        max_targets_per_run=max_targets,
    )
    return collector.collect(targets)


def _collect_youtube(platforms_config: dict[str, Any]) -> list[CandidateItem]:
    """Collect from YouTube using the Data API v3."""
    from src.collectors.youtube import YouTubeAPIError, collect as youtube_collect

    api_key = get_youtube_api_key()
    if not api_key:
        logger.debug("YouTube collection skipped: YOUTUBE_API_KEY not set in .env")
        return []

    targets = get_platform_targets(platforms_config, "youtube")
    if not targets:
        return []

    max_results = get_max_posts_per_target(platforms_config, "youtube")
    max_targets = get_max_targets_per_run(platforms_config, "youtube")

    try:
        return youtube_collect(
            targets,
            api_key=api_key,
            max_results=max_results,
            max_targets_per_run=max_targets,
        )
    except YouTubeAPIError as exc:
        logger.error("YouTube API error (quota or key issue): %s", exc)
        return []


def _collect_twitter(
    platforms_config: dict[str, Any],
    app_config: Optional[AppConfig],
) -> list[CandidateItem]:
    """Collect from Twitter/X."""
    from src.collectors.twitter import collect as twitter_collect
    from src.settings import get_x_bearer_token

    try:
        bearer_token = get_x_bearer_token()
    except EnvironmentError as exc:
        logger.warning("Twitter collection skipped: %s", exc)
        return []

    targets = get_platform_targets(platforms_config, "twitter")
    if not targets:
        return []

    # Build a minimal config-like object for the legacy collector
    queries = [t["value"] for t in targets if t.get("type") == "search"]
    return twitter_collect(queries, bearer_token, max_per_query=10)
