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

_CONFIG_DIR = Path(os.environ.get("SOCIAL_SCANNER_HOME", Path(__file__).parent.parent)) / "config"
_CATALOG_PATH = _CONFIG_DIR / "book_catalog.yaml"
_BOOK_PAGES_PATH = _CONFIG_DIR / "book_pages.yaml"
_SUBREDDIT_POLICY_PATH = _CONFIG_DIR / "subreddit_policy.yaml"


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    if not _CATALOG_PATH.exists():
        return {}
    return yaml.safe_load(_CATALOG_PATH.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _load_subreddit_policy() -> dict:
    if not _SUBREDDIT_POLICY_PATH.exists():
        return {}
    return yaml.safe_load(_SUBREDDIT_POLICY_PATH.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _link_safe_subreddits() -> set[str]:
    return {s.lower() for s in _load_subreddit_policy().get("link_safe", [])}


@lru_cache(maxsize=1)
def _no_link_subreddits() -> set[str]:
    return {s.lower() for s in _load_subreddit_policy().get("no_link", [])}


def subreddit_link_policy(subreddit: str) -> str:
    """Return the link-posting policy for a subreddit.

    "safe"    — links / self-promo tolerated; OK to drop a quizly.pub URL.
    "no_link" — strict no-promo; mention Quizly by name only, no URL.
    "unknown" — not yet reviewed; default to link-free until a human promotes it.
    """
    name = (subreddit or "").lower()
    if name in _link_safe_subreddits():
        return "safe"
    if name in _no_link_subreddits():
        return "no_link"
    return "unknown"


@lru_cache(maxsize=1)
def _load_book_pages() -> dict:
    """Load the auto-generated id -> book-page map (quizly.pub/book/<id>)."""
    if not _BOOK_PAGES_PATH.exists():
        return {}
    return yaml.safe_load(_BOOK_PAGES_PATH.read_text(encoding="utf-8")) or {}


def book_url_template() -> str:
    return _load_book_pages().get("url_template", "https://quizly.pub/book/{id}")


def book_page_url(book_id: int) -> str:
    return book_url_template().format(id=book_id)


# Matches an existing quizly.pub / kvasir.pub mention (optionally with scheme,
# www, and path). Used to spot threads where someone already dropped our link.
_QUIZLY_MENTION_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:quizly|kvasir)\.pub(?:/[^\s)\]\"'>]*)?",
    re.IGNORECASE,
)


def find_quizly_mention(*texts: str) -> Optional[str]:
    """Return the first quizly.pub/kvasir.pub mention found across the given
    texts, or None. Used to detect threads where our link is already present."""
    for text in texts:
        if not text:
            continue
        m = _QUIZLY_MENTION_RE.search(text)
        if m:
            return m.group(0)
    return None


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


def book_page_cta() -> str:
    return _load_catalog().get(
        "book_page_cta",
        "on its page you can read it, talk it through with the AI book adviser, "
        "generate a video scene from it, and enter contests",
    )


def welcome_cta() -> str:
    return _load_catalog().get(
        "welcome_cta",
        "you can try it at quizly.pub/welcome — pick a contest entry, sign up, and "
        "ask the AI character anything",
    )


def persona_cta() -> str:
    return _load_catalog().get(
        "persona_cta",
        "you can build an AI chat as any literary character, share it, and let others "
        "vote on the best answers — try a live example at quizly.pub/welcome",
    )


def entertainment_cta() -> str:
    return _load_catalog().get(
        "entertainment_cta",
        "there's a fun one where you chat with animal characters and people vote on the "
        "funniest answers — you can try it free at quizly.pub/welcome/8",
    )


def welcome_contests() -> list[dict]:
    """Live welcome-page contest entries the classifier can deep-link to."""
    return _load_catalog().get("welcome_contests", [])


def format_welcome_contests() -> str:
    """Render the welcome-contest catalog as a markdown bullet list for the prompt."""
    base = welcome_url().rstrip("/")
    lines = []
    for c in welcome_contests():
        cid = c.get("id")
        if cid is None:
            continue
        lines.append(
            f"- {base}/{cid} — \"{c.get('title', '')}\" "
            f"[lang={c.get('lang', 'en')}, vibe={c.get('vibe', '')}] — "
            f"good for: {c.get('theme', '')}"
        )
    return "\n".join(lines)


def _game_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("game_subreddits", [])}


def _persona_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("persona_subreddits", [])}


def _ai_video_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("ai_video_subreddits", [])}


def _entertainment_subreddits() -> set[str]:
    catalog = _load_catalog()
    return {s.lower() for s in catalog.get("entertainment_subreddits", [])}


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


# Split a page title into its main name (drop subtitle after these separators).
_TITLE_SUBTITLE_SPLIT = re.compile(r"[,:;(]|\s[—–-]\s")


def _normalize_title_key(title: str) -> str:
    """Lowercase title, drop the subtitle, collapse non-word runs to spaces."""
    main = _TITLE_SUBTITLE_SPLIT.split(title, 1)[0]
    main = re.sub(r"[^\w\s]", " ", main, flags=re.UNICODE).lower()
    return re.sub(r"\s+", " ", main).strip()


def _key_is_distinctive(key: str) -> bool:
    """Avoid false positives from short, common single-word titles."""
    if len(key) < 6:
        return False
    return " " in key or len(key) >= 8


@lru_cache(maxsize=1)
def _compiled_book_page_patterns() -> list[tuple[int, str, re.Pattern]]:  # type: ignore[type-arg]
    """Compile a word-boundary regex per book page, longest key first."""
    compiled: list[tuple[int, str, re.Pattern]] = []  # type: ignore[type-arg]
    seen_keys: set[str] = set()
    for page in _load_book_pages().get("pages", []):
        title = page.get("title", "")
        key = _normalize_title_key(title)
        if not _key_is_distinctive(key) or key in seen_keys:
            continue
        seen_keys.add(key)
        pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.IGNORECASE | re.UNICODE)
        compiled.append((int(page["id"]), title, pattern))
    # Match the most specific (longest) title first.
    compiled.sort(key=lambda t: len(t[1]), reverse=True)
    return compiled


def find_book_page(title: str, body: str) -> Optional[dict]:
    """
    Resolve a thread's book mention to a *specific* catalog page so we can
    deep-link quizly.pub/book/<id>. Matches against actual page titles (in the
    language the page exists), so the link always points at a real book.

    Returns {id, title, url} for the most specific match, or None.
    """
    text = f"{title} {body}"
    norm = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)).lower()
    for book_id, page_title, pattern in _compiled_book_page_patterns():
        if pattern.search(norm):
            return {"id": book_id, "title": page_title, "url": book_page_url(book_id)}
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


def is_entertainment_subreddit(subreddit: str) -> bool:
    """Return True if the subreddit is an entertainment / fun / animal community."""
    return subreddit.lower() in _entertainment_subreddits()


def build_book_context(title: str, body: str, parent_target: str, platform: str = "reddit") -> dict[str, str]:
    """
    Return a context dict for the Claude prompt with book/game/persona detection.

    Keys:
      book_match           — matched canonical author name, or empty string
      book_page_url        — specific quizly.pub/book/<id> link, or empty string
      book_page_title      — title of the matched book page, or empty string
      book_page_cta        — CTA text for a specific book page (mentions adviser)
      reading_hall_url     — URL to quizly.pub/books
      reading_hall_cta     — CTA text when a book is matched
      quizly_url           — URL to quizly.pub main site
      welcome_url          — URL to quizly.pub/welcome (try-it demo)
      welcome_cta          — CTA text for top-of-funnel contexts
      persona_cta          — CTA text for CharacterAI / AI persona contexts
      is_game_community    — "true" or "false"
      is_persona_community — "true" or "false"
      is_ai_video_community — "true" or "false"
      subreddit_link_policy — "safe" | "no_link" | "unknown" (reddit), else "na"
    """
    match = find_book_match(title, body)
    page = find_book_page(title, body)
    game = is_game_subreddit(parent_target)
    persona = is_persona_subreddit(parent_target)
    ai_video = is_ai_video_subreddit(parent_target)
    entertainment = is_entertainment_subreddit(parent_target)

    return {
        "book_match": match or "",
        "book_page_url": page["url"] if page else "",
        "book_page_title": page["title"] if page else "",
        "book_page_cta": book_page_cta(),
        "reading_hall_url": reading_hall_url(),
        "reading_hall_cta": reading_hall_cta(),
        "quizly_url": quizly_url(),
        "welcome_url": welcome_url(),
        "welcome_cta": welcome_cta(),
        "persona_cta": persona_cta(),
        "entertainment_cta": entertainment_cta(),
        "welcome_contests": format_welcome_contests(),
        "is_game_community": "true" if game else "false",
        "is_persona_community": "true" if persona else "false",
        "is_ai_video_community": "true" if ai_video else "false",
        "is_entertainment_community": "true" if entertainment else "false",
        "subreddit_link_policy": subreddit_link_policy(parent_target) if platform == "reddit" else "na",
    }
