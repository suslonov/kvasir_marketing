"""
Book catalog lookup for Quizly / Kvasir.

Detects whether a candidate thread mentions a book or author available on
quizly.pub/books and whether the target community is game-related.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

_CATALOG_PATH = Path(os.environ.get("SOCIAL_SCANNER_HOME", Path(__file__).parent.parent)) / "config" / "book_catalog.yaml"


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    if not _CATALOG_PATH.exists():
        return {}
    return yaml.safe_load(_CATALOG_PATH.read_text(encoding="utf-8")) or {}


def reading_hall_url() -> str:
    return _load_catalog().get("reading_hall_url", "https://quizly.pub/books")


def quizly_url() -> str:
    return _load_catalog().get("quizly_url", "https://quizly.pub")


def welcome_url() -> str:
    return _load_catalog().get("welcome_url", "https://quizly.pub/welcome")


def contests_url() -> str:
    return _load_catalog().get("contests_url", "https://quizly.pub/contests")


def reading_hall_cta() -> str:
    return _load_catalog().get(
        "reading_hall_cta",
        "you can read the book, discuss it with our AI adviser, generate a video on the book, "
        "and take part in contests — all at quizly.pub/books",
    )


def welcome_cta() -> str:
    return _load_catalog().get(
        "welcome_cta",
        "you can try it immediately at quizly.pub/welcome — no login needed, just "
        "pick a contest entry and ask the AI character anything",
    )


def persona_cta() -> str:
    return _load_catalog().get(
        "persona_cta",
        "you can build an AI chat as any literary character, share it, and let others "
        "vote on the best answers — try a live example at quizly.pub/welcome",
    )


def _game_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("game_subreddits", [])}


def _persona_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("persona_subreddits", [])}


def _ai_video_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("ai_video_subreddits", [])}


@lru_cache(maxsize=1)
def _compiled_author_patterns() -> list[tuple[str, list[re.Pattern]]]:  # type: ignore[type-arg]
    """Build compiled regex patterns for each author."""
    catalog = _load_catalog()
    result = []
    for entry in catalog.get("authors", []):
        canonical = entry.get("canonical", "")
        patterns = [
            re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE)
            for alias in entry.get("match", [])
        ]
        result.append((canonical, patterns))
    return result


def find_book_match(title: str, body: str) -> Optional[str]:
    """
    Return the canonical author/book name if the text mentions anything from
    the catalog. Returns None if no match found.
    """
    text = f"{title} {body}"
    for canonical, patterns in _compiled_author_patterns():
        if any(p.search(text) for p in patterns):
            return canonical
    return None


def is_game_subreddit(subreddit: str) -> bool:
    """Return True if the subreddit is in the game/quiz category."""
    return subreddit.lower() in _game_subreddits()


def is_persona_subreddit(subreddit: str) -> bool:
    """Return True if the subreddit is a CharacterAI / AI-persona community."""
    return subreddit.lower() in _persona_subreddits()


def is_ai_video_subreddit(subreddit: str) -> bool:
    """Return True if the subreddit is an AI video / AI art community."""
    return subreddit.lower() in _ai_video_subreddits()


def build_book_context(title: str, body: str, parent_target: str) -> dict[str, str]:
    """
    Return a context dict for the Claude prompt with book/game/persona detection.

    Keys:
      book_match           — matched canonical author name, or empty string
      reading_hall_url     — URL to quizly.pub/books
      reading_hall_cta     — CTA text when a book is matched
      quizly_url           — URL to quizly.pub main site
      welcome_url          — URL to quizly.pub/welcome (try-it demo)
      welcome_cta          — CTA text for top-of-funnel / no-login contexts
      persona_cta          — CTA text for CharacterAI / AI persona contexts
      is_game_community    — "true" or "false"
      is_persona_community — "true" or "false"
      is_ai_video_community — "true" or "false"
    """
    match = find_book_match(title, body)
    game = is_game_subreddit(parent_target)
    persona = is_persona_subreddit(parent_target)
    ai_video = is_ai_video_subreddit(parent_target)

    return {
        "book_match": match or "",
        "reading_hall_url": reading_hall_url(),
        "reading_hall_cta": reading_hall_cta(),
        "quizly_url": quizly_url(),
        "welcome_url": welcome_url(),
        "welcome_cta": welcome_cta(),
        "persona_cta": persona_cta(),
        "is_game_community": "true" if game else "false",
        "is_persona_community": "true" if persona else "false",
        "is_ai_video_community": "true" if ai_video else "false",
    }
