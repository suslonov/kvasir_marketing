"""Reddit DOM extraction helpers — all selectors live here to contain breakage."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from src.extractors.common import clean_excerpt, parse_reddit_age_string, parse_vote_count

logger = logging.getLogger(__name__)

# ── Post card selectors (Reddit new design, 2024+) ────────────────────────────
# These are listed in priority order; first match wins.

_POST_CONTAINER_SELECTORS = [
    "article[data-testid='post-container']",
    "shreddit-post",
    "div[data-testid='post-container']",
    "[data-scindex]",
]

_TITLE_SELECTORS = [
    "h1[slot='title']",
    "a[slot='full-post-link']",
    "h3 a",
    "[data-testid='post-container'] h3",
    ".Post h3",
    "shreddit-post h1",
]

_VOTE_SELECTORS = [
    "faceplate-number[pretty]",
    "[data-testid='vote-count']",
    ".score",
    "shreddit-post [aria-label*='upvote']",
]

_COMMENT_SELECTORS = [
    "a[data-testid='comments-page-link-num-comments']",
    "shreddit-post [href*='comments'] faceplate-number",
    ".numComments",
    "a[aria-label*='comment']",
]

_AUTHOR_SELECTORS = [
    "a[data-testid='post_author_link']",
    "shreddit-post [slot='authorName']",
    ".author",
]

_AGE_SELECTORS = [
    "time[datetime]",
    "a[data-testid='post_timestamp']",
    "faceplate-timeago",
]

_BODY_SELECTORS = [
    "div[data-testid='post-rtjson-content']",
    "shreddit-post div[slot='text-body']",
    ".usertext-body",
    "[data-testid='post-rtjson-content'] p",
]

_PERMALINK_SELECTORS = [
    "a[data-testid='comments-page-link-num-comments']",
    "a[slot='full-post-link']",
    "a[data-click-id='body']",
    "shreddit-post a[href*='/comments/']",
]


def _try_selector(page: Any, selectors: list[str], attribute: str = "innerText") -> str:
    """Try each selector in order; return first non-empty result."""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if not el:
                continue
            if attribute == "innerText":
                val = el.inner_text().strip()
            else:
                val = el.get_attribute(attribute) or ""
            if val:
                return val
        except Exception:
            pass
    return ""


def extract_post_from_element(element: Any, subreddit: str) -> Optional[dict[str, Any]]:
    """
    Extract post metadata from a Playwright element handle.
    Returns a dict with normalized fields, or None on failure.
    """
    try:
        # Title — find text only, don't stop when href is absent
        title = ""
        for sel in _TITLE_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    t = el.inner_text().strip()
                    if t:
                        title = t
                        break
            except Exception:
                pass

        # Permalink — try every link selector independently
        permalink = ""
        for sel in _TITLE_SELECTORS + _PERMALINK_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    href = el.get_attribute("href") or ""
                    if href and "/comments/" in href:
                        permalink = href
                        break
            except Exception:
                pass

        if not title:
            return None

        # Ensure absolute URL
        if permalink and not permalink.startswith("http"):
            permalink = f"https://www.reddit.com{permalink}"

        # Vote score
        vote_text = ""
        for sel in _VOTE_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    vote_text = el.inner_text().strip() or el.get_attribute("pretty") or ""
                    if vote_text:
                        break
            except Exception:
                pass
        score = parse_vote_count(vote_text)

        # Comment count
        comment_text = ""
        for sel in _COMMENT_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    comment_text = el.inner_text().strip()
                    if comment_text:
                        break
            except Exception:
                pass
        comment_count = parse_vote_count(comment_text)

        # Author
        author = ""
        for sel in _AUTHOR_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    author = el.inner_text().strip().lstrip("u/").lstrip("Posted by ")
                    if author:
                        break
            except Exception:
                pass

        # Age / timestamp
        published_at = None
        for sel in _AGE_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    dt_attr = el.get_attribute("datetime") or ""
                    if dt_attr:
                        from datetime import datetime, timezone
                        published_at = datetime.fromisoformat(dt_attr.replace("Z", "+00:00"))
                        break
                    age_text = el.inner_text().strip()
                    if age_text:
                        published_at = parse_reddit_age_string(age_text)
                        break
            except Exception:
                pass

        # Body excerpt
        body = ""
        for sel in _BODY_SELECTORS:
            try:
                el = element.query_selector(sel)
                if el:
                    body = el.inner_text().strip()
                    if body:
                        break
            except Exception:
                pass

        # Post ID from permalink
        post_id = ""
        if permalink:
            m = re.search(r"/comments/([a-z0-9]+)/", permalink)
            if m:
                post_id = m.group(1)

        return {
            "post_id": post_id,
            "title": title,
            "url": permalink,
            "subreddit": subreddit,
            "author": author,
            "score": score,
            "comment_count": comment_count,
            "published_at": published_at,
            "body_excerpt": clean_excerpt(body),
        }

    except Exception as exc:
        logger.debug("Failed to extract post element: %s", exc)
        return None


def extract_posts_from_page(page: Any, subreddit: str, max_posts: int = 12) -> list[dict[str, Any]]:
    """
    Extract multiple posts from a loaded Reddit page.
    Returns a list of normalized post dicts.
    """
    posts: list[dict[str, Any]] = []

    for container_sel in _POST_CONTAINER_SELECTORS:
        try:
            elements = page.query_selector_all(container_sel)
            if not elements:
                continue
            logger.debug("Found %d post elements with selector '%s'", len(elements), container_sel)
            for el in elements[:max_posts]:
                post = extract_post_from_element(el, subreddit)
                if post and post.get("title") and post.get("url"):
                    posts.append(post)
            if posts:
                break
        except Exception as exc:
            logger.debug("Selector '%s' failed: %s", container_sel, exc)

    if not posts:
        logger.warning("Could not extract posts from r/%s — selectors may need updating.", subreddit)

    return posts[:max_posts]


def check_session_valid(page: Any) -> bool:
    """
    Return True if the current page indicates an active Reddit session.
    Detects logout state, challenge pages, etc.
    """
    try:
        url = page.url
        # Challenge or login page
        if any(x in url for x in ["/login", "/register", "/challenge", "reddit.com/account"]):
            return False

        page_text = page.inner_text("body") or ""

        # Check for logged-out indicators
        logout_signals = [
            "log in or sign up",
            "continue with google",
            "sign up for reddit",
        ]
        page_lower = page_text.lower()
        if any(s in page_lower for s in logout_signals):
            # Allow false positives if we also see user-specific content
            logged_in_signals = ["my profile", "user settings", "log out", "create post"]
            if not any(s in page_lower for s in logged_in_signals):
                return False

        return True
    except Exception:
        return False
