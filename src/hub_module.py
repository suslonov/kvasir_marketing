"""Social Scanner module for ai-home-hub.

Implements the Module protocol expected by ai-home-hub's loader.

The module handles:
  GET  /            → serve rendered HTML report
  POST /api/re-render → re-render HTML from current DB state
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

Response = tuple[int, str, bytes]


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
            import os
            app_config = load_config(self.sources_yaml)
            self.db_path = Path(os.path.expanduser(app_config.global_config.db_path)).resolve()
            self.output_path = Path(os.path.expanduser(app_config.global_config.output_html)).resolve()
        except Exception:
            self.db_path = Path(os.path.expanduser(config.get("db_path", "~/social_scanner/state.db"))).resolve()
            self.output_path = Path(os.path.expanduser(config.get("output_html", "~/social_scanner/rendered/index.html"))).resolve()

    def handle(self, method: str, path: str, body: bytes, headers: dict) -> Response:
        if method in ("GET", "HEAD") and path in ("", "/", "/index.html"):
            return self._serve_html()
        if method == "POST" and path == "/api/re-render":
            return self._re_render()
        return 404, "text/plain", b"Not found"

    def _serve_html(self) -> Response:
        try:
            content = self.output_path.read_bytes()
            content = content.replace(
                b'const API_BASE = "";',
                f'const API_BASE = "{self.prefix}";'.encode(),
            )
            return 200, "text/html; charset=utf-8", content
        except FileNotFoundError:
            return 404, "text/plain", b"No report found. Run the pipeline first."

    def _re_render(self) -> Response:
        try:
            from src import db as database, render
            from src.settings import load_config

            config = load_config(self.sources_yaml)
            opportunities = database.get_opportunities_for_render(self.db_path, limit=200)
            count = render.render_html(
                opportunities=opportunities,
                output_path=self.output_path,
                api_base=self.prefix,
            )
            return 200, "application/json", _json({"ok": True, "rendered": count})
        except Exception as exc:
            logger.error("Re-render failed: %s", exc, exc_info=True)
            return 500, "application/json", _json({"ok": False, "error": str(exc)})


def _json(data: dict) -> bytes:
    return json.dumps(data).encode()


def _ensure_on_path(repo_path: Path) -> None:
    repo_str = str(repo_path)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
