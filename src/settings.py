"""Load application configuration from YAML files and .env credentials."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from src.models import AppConfig, GlobalConfig

# Project root is always the directory two levels above this file.
# SOCIAL_SCANNER_HOME in .env is not needed — kept there only as documentation.
_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "sources.yaml"
_PLATFORMS_CONFIG_PATH = _PROJECT_ROOT / "config" / "platforms.yaml"


# ── Sources config ────────────────────────────────────────────────────────────

def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load and return the full application config from sources.yaml."""
    path = config_path or _DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(path.read_text())
    return AppConfig(**raw)


# ── Platforms config ──────────────────────────────────────────────────────────

def load_platforms_config(config_path: Optional[Path] = None) -> dict[str, Any]:
    """Load platforms.yaml and return the raw dict."""
    path = config_path or _PLATFORMS_CONFIG_PATH
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def get_scan_interval_minutes(platforms_cfg: dict[str, Any]) -> int:
    return int(platforms_cfg.get("scan_interval_minutes", 10))


def get_platform_targets(platforms_cfg: dict[str, Any], platform: str) -> list[dict[str, Any]]:
    p = platforms_cfg.get("platforms", {}).get(platform, {})
    return p.get("targets", [])


def is_platform_enabled(platforms_cfg: dict[str, Any], platform: str) -> bool:
    p = platforms_cfg.get("platforms", {}).get(platform, {})
    return bool(p.get("enabled", False))


def get_browser_profile_dir(platforms_cfg: dict[str, Any]) -> Path:
    reddit_cfg = platforms_cfg.get("platforms", {}).get("reddit", {})
    raw = reddit_cfg.get("browser_profile_dir", "~/.kvasir/browser_profiles/reddit_profile")
    expanded = Path(raw).expanduser()
    if expanded.is_absolute():
        return expanded
    return _PROJECT_ROOT / raw


def get_max_posts_per_target(platforms_cfg: dict[str, Any], platform: str = "reddit") -> int:
    p = platforms_cfg.get("platforms", {}).get(platform, {})
    return int(p.get("max_posts_per_target", 12))


def get_max_targets_per_run(platforms_cfg: dict[str, Any], platform: str = "reddit") -> int:
    p = platforms_cfg.get("platforms", {}).get(platform, {})
    return int(p.get("max_targets_per_run", 8))


def is_headless(platforms_cfg: dict[str, Any], platform: str = "reddit") -> bool:
    p = platforms_cfg.get("platforms", {}).get(platform, {})
    return bool(p.get("headless", True))


# ── Path helpers (read from sources.yaml, not env) ────────────────────────────

def get_db_path(app_config: Optional[AppConfig] = None) -> Path:
    """Resolve the database path from sources.yaml (global.db_path)."""
    if app_config:
        return Path(app_config.global_config.db_path).expanduser()
    cfg = load_config()
    return Path(cfg.global_config.db_path).expanduser()


def get_output_html_path(app_config: Optional[AppConfig] = None) -> Path:
    """Resolve the HTML report output path from sources.yaml (global.output_html)."""
    if app_config:
        return Path(app_config.global_config.output_html).expanduser()
    cfg = load_config()
    return Path(cfg.global_config.output_html).expanduser()


# ── Credentials (loaded from .env via load_dotenv at entry points) ────────────

def get_anthropic_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key or key == "replace_me":
        raise EnvironmentError("ANTHROPIC_API_KEY is not set in .env")
    return key


def get_x_bearer_token() -> str:
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token or token == "replace_me":
        raise EnvironmentError("X_BEARER_TOKEN is not set in .env")
    return token


def get_youtube_api_key() -> Optional[str]:
    """Return the YouTube Data API key from .env, or None if not configured."""
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key or key == "replace_me":
        return None
    return key


def get_reddit_credentials() -> Optional[tuple[str, str]]:
    """Return (client_id, client_secret) from .env, or None if not configured."""
    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret or client_id == "replace_me":
        return None
    return client_id, client_secret


def project_root() -> Path:
    return _PROJECT_ROOT
