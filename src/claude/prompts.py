"""Load and render prompt templates from config/prompts/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROMPT_DIR = Path(__file__).parent.parent.parent / "config" / "prompts"


def load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_evaluate_prompt(items: list[dict[str, Any]]) -> str:
    template = load_prompt("evaluate")
    items_json = json.dumps(items, indent=2, ensure_ascii=False, default=str)
    return template.replace("{{ items_json }}", items_json)
