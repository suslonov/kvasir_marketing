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


def project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT
