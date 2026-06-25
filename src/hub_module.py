"""Social Scanner module for ai-home-hub.

Implements the Module protocol expected by ai-home-hub's loader.

The module handles:
  GET  /            → serve rendered HTML report
  POST /api/re-render → re-render HTML from current DB state
  POST /api/opportunities/expired → JSON page of expired items ({"page": 1}, 20 per page)
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

Response = tuple[int, str, bytes]

# Match `const API_BASE = "...";` across render versions (preserve leading indent).
_API_BASE_ASSIGN = re.compile(
    rb'^(\s*)const API_BASE = "[^"]*";',
    re.MULTILINE,
)


def _patch_served_html_api_base(content: bytes, prefix: str) -> bytes:
    """Inject hub mount prefix so fetch() hits this module (same idea as ai-news-agent)."""
    assign = f'const API_BASE = "{prefix}";'.encode()

    def repl(m: re.Match[bytes]) -> bytes:
        return m.group(1) + assign

    patched, count = _API_BASE_ASSIGN.subn(repl, content, count=1)
    if count != 1:
        logger.warning(
            "Could not patch API_BASE in HTML (matches=%s); Refresh may call the wrong URL",
            count,
        )
    return patched if count == 1 else content


def normalize_hub_rel_path(prefix: str, path: str) -> str:
    """Strip optional mount prefix; return path like `/api/re-render` (no trailing slash except `/`)."""
    raw = path.split("?", 1)[0]
    if not raw.startswith("/"):
        raw = "/" + raw
    pref = (prefix or "").strip().rstrip("/")
    if not pref:
        return raw.rstrip("/") or "/"
    if raw == pref or raw == pref + "/":
        return "/"
    if raw.startswith(pref + "/"):
        rest = raw[len(pref) :]
        return rest.rstrip("/") or "/"
    return raw.rstrip("/") or "/"


class SocialScannerModule:
    name = "Social Scanner"
    description = "Quizly/Kvasir marketing opportunity scanner"

    def __init__(self, prefix: str, config: dict, repo_path: Path) -> None:
        self.prefix = prefix
        self.repo_path = repo_path.resolve()

        self.sources_yaml = (
            self.repo_path / config.get("sources_yaml", "config/sources.yaml")
        ).resolve()

        _ensure_on_path(self.repo_path)

        try:
            from src.settings import load_config
            from src.models import GlobalConfig
            app_config = load_config(self.sources_yaml)
            self.db_path = Path(app_config.global_config.db_path).expanduser().resolve()
            self.output_path = Path(app_config.global_config.output_html).expanduser().resolve()
        except Exception:
            from src.models import GlobalConfig
            _defaults = GlobalConfig()
            self.db_path = Path(config.get("db_path", _defaults.db_path)).expanduser().resolve()
            self.output_path = Path(config.get("output_html", _defaults.output_html)).expanduser().resolve()

    def _normalized_rel_path(self, path: str) -> str:
        return normalize_hub_rel_path(self.prefix, path)

    def handle(self, method: str, path: str, body: bytes, headers: dict) -> Response:
        rel = self._normalized_rel_path(path)
        if method in ("GET", "HEAD") and rel in ("/", "/index.html"):
            return self._serve_html()
        if method == "POST" and rel == "/api/re-render":
            return self._re_render()
        if method == "POST" and rel == "/api/opportunities/expired":
            return self._expired_feed(body)
        return 404, "text/plain", b"Not found"

    def _serve_html(self) -> Response:
        try:
            content = self.output_path.read_bytes()
            content = _patch_served_html_api_base(content, self.prefix)
            return 200, "text/html; charset=utf-8", content
        except FileNotFoundError:
            return 404, "text/plain", b"No report found. Run the pipeline first."

    def _re_render(self) -> Response:
        try:
            from src import db as database
            from src import opportunity_queue, render

            queue_items = opportunity_queue.get_review_inbox(self.db_path, limit=200)
            summary = opportunity_queue.summarize(self.db_path)
            recent_runs = database.get_recent_runs(self.db_path, limit=5)
            skipped_items = database.get_skipped_queue_items(self.db_path, limit=200)
            backlog_items = database.get_unevaluated_candidates(self.db_path, limit=200)
            spotted_items = database.get_spotted_queue_items(self.db_path, limit=200)
            count = render.render_html(
                output_path=self.output_path,
                queue_items=queue_items,
                summary=summary,
                recent_runs=recent_runs,
                skipped_items=skipped_items,
                backlog_items=backlog_items,
                spotted_items=spotted_items,
                api_base=self.prefix,
            )
            return 200, "application/json", _json({"ok": True, "rendered": count})
        except Exception as exc:
            logger.error("Re-render failed: %s", exc, exc_info=True)
            return 500, "application/json", _json({"ok": False, "error": str(exc)})

    def _expired_feed(self, body: bytes) -> Response:
        try:
            from src import opportunity_queue

            page = 1
            if body.strip():
                spec = json.loads(body.decode())
                page = max(1, int(spec.get("page", 1)))
            payload = opportunity_queue.get_expired_feed_page(self.db_path, page=page)
            return 200, "application/json; charset=utf-8", json.dumps(payload).encode()
        except Exception as exc:
            logger.error("Expired feed failed: %s", exc, exc_info=True)
            return 500, "application/json", _json({"ok": False, "error": str(exc)})


def _json(data: dict) -> bytes:
    return json.dumps(data).encode()


def _ensure_on_path(repo_path: Path) -> None:
    repo_str = str(repo_path)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
