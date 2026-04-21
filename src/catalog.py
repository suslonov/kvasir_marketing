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


def reading_hall_cta() -> str:
    return _load_catalog().get(
        "reading_hall_cta",
        "you can read the book, discuss it with our AI adviser, generate a video on the book, "
        "and take part in contests — all at quizly.pub/books",
    )


def _game_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("game_subreddits", [])}


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


def build_book_context(title: str, body: str, parent_target: str) -> dict[str, str]:
    """
    Return a context dict for the Claude prompt with book/game detection results.

    Keys:
      book_match        — matched canonical author name, or empty string
      reading_hall_url  — URL to quizly.pub/books
      reading_hall_cta  — CTA text to append when a book is matched
      quizly_url        — URL to quizly.pub main site
      is_game_community — "true" or "false"
    """
    match = find_book_match(title, body)
    game = is_game_subreddit(parent_target)

    return {
        "book_match": match or "",
        "reading_hall_url": reading_hall_url(),
        "reading_hall_cta": reading_hall_cta(),
        "quizly_url": quizly_url(),
        "is_game_community": "true" if game else "false",
    }
