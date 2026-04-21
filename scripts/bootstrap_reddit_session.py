#!/usr/bin/env python3
"""
Bootstrap a persistent Reddit browser session for Kvasir.

Usage:
    python scripts/bootstrap_reddit_session.py

Steps:
1. Opens a visible Chromium window.
2. You log in to Reddit manually (including any 2FA steps).
3. Press Enter here when login is complete.
4. The browser profile is saved to runtime/browser_profiles/reddit_profile/.
5. The script verifies login by opening r/books.

The saved profile is used by the Reddit browser collector on every scheduler run.

Security:
- The profile dir is listed in .gitignore.
- Do NOT commit it to git.
- Do NOT sync it to a public cloud bucket.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Resolve project root
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

from src.settings import get_browser_profile_dir, load_platforms_config

_REDDIT_URL = "https://www.reddit.com"
_VERIFY_URL = "https://www.reddit.com/r/books/hot/"


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright is not installed.")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    platforms_config = load_platforms_config()
    profile_dir = get_browser_profile_dir(platforms_config)
    profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProfile directory: {profile_dir}")
    print("=" * 60)
    print("A Chromium window will open.")
    print("Log in to Reddit manually.")
    print("Complete any 2FA or verification steps.")
    print("Then come back here and press Enter.")
    print("=" * 60)
    input("\nPress Enter when ready to open the browser... ")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()
        print(f"\nOpening {_REDDIT_URL} ...")
        page.goto(_REDDIT_URL)

        print("\nPlease log in to Reddit in the browser window.")
        input("Press Enter here after you have successfully logged in... ")

        # Verify login
        print(f"\nVerifying session by opening {_VERIFY_URL} ...")
        page.goto(_VERIFY_URL, wait_until="domcontentloaded", timeout=20_000)

        from src.extractors.reddit_extract import check_session_valid

        if check_session_valid(page):
            print("\n✓ Session verified successfully!")
            print(f"✓ Profile saved to: {profile_dir}")
        else:
            print("\n✗ Session check failed — you may not be logged in.")
            print("  Please try again or check your credentials.")
            print(f"  Current URL: {page.url}")

        context.close()

    print("\nDone. You can now run the scheduler.")
    print("  python -m src.scheduler_entry")
    print("  or: scripts/run_scheduler.sh")


if __name__ == "__main__":
    main()
