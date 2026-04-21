"""Load application configuration from config/sources.yaml and environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from src.models import AppConfig, GlobalConfig

_PROJECT_ROOT = Path(os.environ.get("SOCIAL_SCANNER_HOME", Path(__file__).parent.parent))
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "sources.yaml"


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load and return the full application config."""
    path = config_path or _DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(path.read_text())
    cfg = AppConfig(**raw)

    global_overrides: dict = {}
    if v := os.environ.get("MAX_ITEMS_PER_SUBREDDIT"):
        global_overrides["max_items_per_subreddit"] = int(v)
    if v := os.environ.get("MAX_CLAUDE_BATCH_SIZE"):
        global_overrides["max_claude_batch_size"] = int(v)
    if v := os.environ.get("CLAUDE_MODEL"):
        global_overrides["claude_model"] = v
    if v := os.environ.get("CLAUDE_MAX_TOKENS"):
        global_overrides["claude_max_tokens"] = int(v)

    if v := os.environ.get("ENABLE_X_PRODUCTION"):
        global_overrides["enable_twitter"] = v.lower() in ("1", "true", "yes")
    if v := os.environ.get("TWITTER_REQUEST_DELAY_SECONDS"):
        global_overrides["twitter_request_delay_seconds"] = float(v)
    if v := os.environ.get("MAX_ITEMS_PER_SEARCH"):
        global_overrides["max_items_per_search"] = int(v)

    if global_overrides:
        updated = cfg.global_config.model_copy(update=global_overrides)
        cfg = cfg.model_copy(update={"global_config": updated})

    return cfg


def get_anthropic_api_key() -> str:
    """Return the Anthropic API key from the environment."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or key == "replace_me":
        raise EnvironmentError("ANTHROPIC_API_KEY is not set or is a placeholder value.")
    return key


def get_x_bearer_token() -> str:
    """Return the X/Twitter Bearer Token from the environment."""
    token = os.environ.get("X_BEARER_TOKEN", "")
    if not token or token == "replace_me":
        raise EnvironmentError("X_BEARER_TOKEN is not set or is a placeholder value.")
    return token


def get_reddit_credentials() -> tuple[str, str] | None:
    """Return (client_id, client_secret) for Reddit OAuth, or None if not configured."""
    client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret or client_id == "replace_me":
        return None
    return client_id, client_secret


def project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT
