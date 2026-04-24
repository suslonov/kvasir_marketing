"""
Sync config/book_catalog.yaml with the canonical book-list.txt from kvasir_proto.

Run:
    python scripts/update_book_catalog.py [--book-list PATH] [--catalog PATH] [--dry-run]

What it does:
- Parses book-list.txt (each line: `Author`  `Title`)
- Groups titles by author
- Detects Cyrillic names / titles and sends them ALL in one Claude batch call to
  get standard English transliterations + known English title translations
- For authors NOT yet in book_catalog.yaml, appends a new entry with aliases
  (original name, AI-provided transliteration, book titles in both languages)
- For authors already in the catalog, extends their `match` list with any new
  aliases not already present
- Preserves all hand-crafted entries untouched
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
DEFAULT_CATALOG = REPO_ROOT / "config" / "book_catalog.yaml"


from src.settings import get_book_list_path

DEFAULT_BOOK_LIST = get_book_list_path()

_LINE_RE = re.compile(r"`([^`]+)`\s+`([^`]+)`")
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")


def _has_cyrillic(text: str) -> bool:
    return bool(_CYRILLIC.search(text))


def parse_book_list(path: Path) -> dict[str, list[str]]:
    """Return {author: [title, ...]} grouped from book-list.txt."""
    by_author: dict[str, list[str]] = defaultdict(list)
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = _LINE_RE.match(raw)
        if not m:
            continue
        author, title = m.group(1).strip(), m.group(2).strip()
        by_author[author].append(title)
    return dict(by_author)


# ── Claude translation batch ──────────────────────────────────────────────────

_TRANSLATE_PROMPT = """\
You are a literary reference expert. I will give you a JSON list of Russian / \
Cyrillic author names and book titles that appear in an online book catalog.

For each item return a JSON object with:
  "original"     – the exact input string (unchanged)
  "en_name"      – standard English spelling / transliteration of the name/title
  "aliases"      – list of additional English spellings or abbreviations commonly
                   used in Reddit discussions (lowercase, deduplicated, at most 6)

Rules:
- If the item is a well-known author, include surname-only alias and common
  transliteration variants (e.g. "dostoevsky", "dostoyevsky").
- If the item is a book title with a well-known English translation, include it.
- If purely transliterated (no standard English title), just transliterate.
- All aliases must be lowercase.
- Do NOT include the original Cyrillic in aliases.
- Return ONLY a JSON array, no prose.

Input:
{items_json}
"""


def _translate_batch(items: list[str], api_key: str) -> dict[str, dict[str, Any]]:
    """
    Send all Cyrillic strings to Claude in one call.
    Returns {original: {"en_name": str, "aliases": [str, ...]}}
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _TRANSLATE_PROMPT.format(items_json=json.dumps(items, ensure_ascii=False, indent=2))

    print(f"Sending {len(items)} Cyrillic strings to Claude for translation…")
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    parsed: list[dict] = json.loads(raw)
    return {entry["original"]: entry for entry in parsed}


# ── Catalog helpers ───────────────────────────────────────────────────────────

def _catalog_has_author(authors: list[dict], name: str) -> int | None:
    name_lower = name.lower()
    for i, entry in enumerate(authors):
        if entry.get("canonical", "").lower() == name_lower:
            return i
        for alias in entry.get("match", []):
            if alias.lower() == name_lower:
                return i
    return None


def _merge_aliases(existing: list[str], new: list[str]) -> list[str]:
    seen = {a.lower() for a in existing}
    result = list(existing)
    for a in new:
        if a.lower() not in seen:
            result.append(a.lower())
            seen.add(a.lower())
    return result


# ── Main update logic ─────────────────────────────────────────────────────────

def update_catalog(
    book_list_path: Path,
    catalog_path: Path,
    dry_run: bool = False,
    api_key: str | None = None,
) -> None:
    by_author = parse_book_list(book_list_path)
    total_books = sum(len(v) for v in by_author.values())
    print(f"Parsed {total_books} books across {len(by_author)} authors from {book_list_path}")

    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    authors: list[dict] = catalog.setdefault("authors", [])

    # ── Collect all Cyrillic strings for batch translation ────────────────────
    cyrillic_items: list[str] = []
    for author, titles in by_author.items():
        if _has_cyrillic(author):
            cyrillic_items.append(author)
        for title in titles:
            if _has_cyrillic(title):
                cyrillic_items.append(title)
    cyrillic_items = list(dict.fromkeys(cyrillic_items))  # deduplicate, preserve order

    translations: dict[str, dict] = {}
    if cyrillic_items:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            print(
                f"WARNING: {len(cyrillic_items)} Cyrillic strings found but "
                "ANTHROPIC_API_KEY is not set — skipping AI translation.\n"
                "Set the env var or pass --api-key to enable it."
            )
        else:
            translations = _translate_batch(cyrillic_items, key)
            print(f"Received translations for {len(translations)} strings.")

    # ── Apply to catalog ──────────────────────────────────────────────────────
    added_authors = 0
    extended_entries = 0
    added_aliases = 0

    for author, titles in sorted(by_author.items()):
        # Build full alias set for this author
        author_t = translations.get(author, {})
        author_aliases: list[str] = [author.lower()]
        if author_t.get("en_name"):
            author_aliases.append(author_t["en_name"].lower())
        author_aliases.extend(a.lower() for a in author_t.get("aliases", []))

        title_aliases: list[str] = []
        for title in titles:
            title_aliases.append(title.lower())
            title_t = translations.get(title, {})
            if title_t.get("en_name"):
                title_aliases.append(title_t["en_name"].lower())
            title_aliases.extend(a.lower() for a in title_t.get("aliases", []))

        all_new_aliases = list(dict.fromkeys(author_aliases + title_aliases))

        idx = _catalog_has_author(authors, author)
        if idx is None:
            # Use AI canonical name if available, else original
            canonical = author_t.get("en_name") or author
            new_entry: dict = {
                "canonical": canonical,
                "match": all_new_aliases,
                "_auto": True,
            }
            authors.append(new_entry)
            added_authors += 1
            added_aliases += len(all_new_aliases)
            print(f"  + NEW: {canonical!r}  ({len(titles)} books, {len(all_new_aliases)} aliases)")
        else:
            entry = authors[idx]
            before = len(entry.get("match", []))
            entry["match"] = _merge_aliases(entry.get("match", []), all_new_aliases)
            delta = len(entry["match"]) - before
            if delta:
                added_aliases += delta
                extended_entries += 1
                print(f"  ~ EXTENDED: {entry['canonical']!r} — +{delta} aliases")

    print(f"\nSummary: {added_authors} new authors, "
          f"{extended_entries} extended entries, "
          f"{added_aliases} new aliases total")

    if dry_run:
        print("\n[dry-run] No changes written.")
        return

    catalog_path.write_text(
        yaml.dump(catalog, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"\nWritten: {catalog_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book-list", type=Path, default=DEFAULT_BOOK_LIST)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--api-key", default=None,
                        help="Anthropic API key (default: $ANTHROPIC_API_KEY)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print changes without writing")
    args = parser.parse_args()

    if not args.book_list.exists():
        sys.exit(f"ERROR: book-list.txt not found: {args.book_list}")
    if not args.catalog.exists():
        sys.exit(f"ERROR: catalog not found: {args.catalog}")

    update_catalog(args.book_list, args.catalog, dry_run=args.dry_run, api_key=args.api_key)


if __name__ == "__main__":
    main()
