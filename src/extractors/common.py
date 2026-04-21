"""Common extraction utilities shared across platform extractors."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional


def parse_reddit_age_string(age_text: str) -> Optional[datetime]:
    """
    Parse Reddit age strings like '2 hours ago', '3 days ago' into a UTC datetime.
    Returns None on failure.
    """
    if not age_text:
        return None

    age_text = age_text.strip().lower()
    now = datetime.now(timezone.utc)

    patterns = [
        (r"(\d+)\s+second", "seconds"),
        (r"(\d+)\s+minute", "minutes"),
        (r"(\d+)\s+hour", "hours"),
        (r"(\d+)\s+day", "days"),
        (r"(\d+)\s+week", "weeks"),
        (r"(\d+)\s+month", "months"),
        (r"(\d+)\s+year", "years"),
    ]

    from datetime import timedelta

    for pattern, unit in patterns:
        m = re.search(pattern, age_text)
        if not m:
            continue
        n = int(m.group(1))
        if unit == "seconds":
            return now - timedelta(seconds=n)
        if unit == "minutes":
            return now - timedelta(minutes=n)
        if unit == "hours":
            return now - timedelta(hours=n)
        if unit == "days":
            return now - timedelta(days=n)
        if unit == "weeks":
            return now - timedelta(weeks=n)
        if unit == "months":
            return now - timedelta(days=n * 30)
        if unit == "years":
            return now - timedelta(days=n * 365)

    return None


def parse_vote_count(text: str) -> int:
    """Parse Reddit vote strings like '1.2k', '342', '·'."""
    if not text:
        return 0
    text = text.strip().replace(",", "").lower()
    try:
        if text.endswith("k"):
            return int(float(text[:-1]) * 1000)
        return int(float(text))
    except (ValueError, TypeError):
        return 0


def clean_excerpt(text: str, max_len: int = 500) -> str:
    """Trim and clean a text excerpt."""
    text = (text or "").strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "…"
    return text
