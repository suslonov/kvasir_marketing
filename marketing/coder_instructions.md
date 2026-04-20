# Coding Agent Schedule: Site Improvements

Practical implementation schedule based on critical_improvements.md and site_evaluation.md findings. No social network integrations. Code-only tasks.

# Improve: Hero Section

## Current state
- Hero exists in `echoes.html:216-224` — `class="hidden"`, **no JS ever unhides it**
- Contains only a bland title + subtitle, nothing else
- The animated promo section below already shows featured games with cards — no need to duplicate that
- `mainContentSection` h1 reads "Game and chat with AI. Contests in prompt crafting" — vague, grammatically off
- `brief.html` has great selling copy and game descriptions but is buried at `/brief`

## What to fix

### 1. Wire up the hero
**Files:** `js/echoes.js`, `echoes.html`

- If user is NOT logged in: remove `hidden` from `#heroSection`
- Logged-in users skip straight to the promo/catalog
- Add small "x" dismiss, stores `localStorage.heroSeen`

### 2. Replace hero content with selling text (no cards — promo section handles that)

Replace the current empty hero with a compact text block. Keep it to 3-5 lines max. The promo carousel is right below, so the hero just needs to explain what this site is and hook the visitor.

**Recommended hero content:**

```html
<section id="heroSection" class="hidden">
  <div class="hero-container">
    <div class="hero-text">
      <h1 class="hero-title">AI-Powered Word Games, Book Chats & Contests</h1>
      <p class="hero-subtitle">
        Play the Turing Test. Chat with Prince Hamlet. Guess words with AI.
        Or craft your own game and compete in prompt-writing contests.
      </p>
      <p class="hero-cta-line">
        Free in your browser — just pick a game below and start chatting.
      </p>
    </div>
  </div>
</section>
```

Why this works:
- **Line 1 (title):** Names the three content types — games, book chats, contests
- **Line 2 (examples):** Four specific games by name — gives immediate concrete picture
- **Line 3 (CTA):** Free, no signup, points down to the promo section

### 3. Add a small CSS style for the CTA line
```css
.hero-cta-line {
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: #2563eb;
  font-weight: 600;
  margin-top: 0.5rem;
}
```

### 4. Fix the mainContentSection h1
**Current:** "Game and chat with AI. Contests in prompt crafting"
**Replace with:** "AI Chat Games & Contests" — works as a section header once the hero is dismissed.

### 5. Optional: add a background image
The hero currently has no visual. Consider reusing one of the existing background images from `img/background/`:
- `city-pale.jpg` — subtle, doesn't compete with text
- `sakura.jpg` — warm, inviting

Apply lightly: `background: url('img/background/city-pale.jpg') center/cover; background-blend-mode: soft-light;` with a semi-transparent overlay so text stays readable.

### 6. Mobile
- Title wraps naturally (max 2 lines)
- Subtitle: 2-3 lines
- CTA line: 1 line
- Total height: ~200px, no scroll needed before promo section appears





# Archive - done

## Current State Checks

### Contest Board Announcement: WORKING
Contests are auto-announced on the board when created/activated (`kv2_board/lambda_function.py:301-313`). Three types: "New Contest started!", "Contest started!", "New Contest announced!" with trophy/megaphone emoji.

**Needed:** Add an "Announce Winner" button on the contest page of `admin.html`. Currently the admin can edit contest rows (author, language, title, status, dates, rules, properties) but has no way to announce a winner from the admin UI. The button should:
- Appear per contest row (next to Rules/Props buttons)
- Open a small form: select winning entry (component), optional message
- Call `add_info_board` with type "echo", component=winner's component_id, content="Contest winner!", award="🏆"
- Send a notification to the winner via `common_add_notification`

### Winner Announcement + Notification: PARTIALLY WORKING
In-game winners are detected automatically via AI outcome parsing (`kv2_AI_echo/lambda_function.py:833-835`). On in-game win: NFT awarded, board post created ("Contest winner"), personal notification sent via `common_add_notification()` (`kv2_AI_echo/lambda_function.py:905-907`).

**Needed:** Contest-level winner announcement (admin picks the best entry overall) is missing. Add an "Announce Winner" button in admin.html contest page that:
- Posts to the board: "[Contest Title] Winner: [Entry Title] by [Author]"
- Sends notification to the winning user
- Optionally awards NFT/achievement

### Hero Section: MISSING
Homepage (echoes.html) has no hero/landing section. New visitors land on an empty loading catalog. This is the #1 conversion blocker.

### Contest Entry UX (Friend's Feedback): NEEDS WORK
The echo-contest.html editor has these problems:
1. **Where to write the prompt**: The "Instructions" and "Character prompt" fields exist but their purpose is unclear. Placeholder text says "Behaviour instructions for the echo chat" which is vague.
2. **No example prompt**: No example text, tooltip, or template showing what a good contest entry prompt looks like.
3. **No technical contest description**: Contest pages only show marketing text. No explanation of how the AI game engine works, what models mean, what "Multistep" vs "Discussion" does.

### Save Order Bug in Contest Editor: EXISTS
The character prompt and title picture are stored in S3 (not in the component record). This causes several UX bugs:
1. **Prompt entered before first save**: The text editor is disabled until after first save, but this is not clearly communicated. If a user types into other fields expecting the prompt to be saved, they lose work.
2. **Save before prompt fully loaded**: If the user saves while the S3 text asset is still loading, the save overwrites the prompt with empty/partial content.
3. **Picture removed on save**: When a user selects a title picture, it's uploaded to S3 as an asset. But if they save the component before the picture upload completes, or if the save doesn't preserve the asset reference, the picture is removed from the asset record.

---

## Week 1: Landing Page + Contest UX Fix

### Day 1-2: Hero Section on Homepage
**File:** `src/html/kvasir.pub/echoes.html` + `src/html/kvasir.pub/js/echoes.js`

Add a small but clear hero section above `promotedContainer` in echoes.html:
```
- Headline: "Play AI Games and Chat with Book Characters"
- Subtext: "Free in your browser. No download needed."
- 2-3 featured game cards with "Play Now" buttons (hardcoded IDs of best games)
- "Browse All Games" button scrolling to the catalog below
- Show hero only to non-logged-in users (logged-in users go straight to catalog)
- Store a localStorage flag after first visit to hide hero on return
```

Implementation notes:
- Keep it compact: one screen height max, no excessive padding or animations
- A single row of 2-3 cards with a headline above, not a full-page splash
- Insert as a new `<section>` before `<div id="promotedContainer">`
- Use existing Tailwind classes. Match the site's blue-white theme
- Featured games: hardcode 3 component IDs with titles/images (avoid API call to keep it fast)
- On mobile: stack vertically, hero fits in one screen without scrolling

### Day 2-3: Fix Contest Entry Editor UX (Friend's Feedback)
**File:** `src/html/kvasir.pub/echo-contest.html` + `src/html/kvasir.pub/js/echo-contest.js`

**Problem 0 - Save order bug (S3 assets):**
The prompt text and title picture are stored as S3 assets, separate from the component record. This creates race conditions:

Fix instructions:
- **Prompt before first save:** Show a clear message above the Character prompt textarea: "Save your chat first to enable the prompt editor." Disable the textarea visually (grey background, no cursor) and add a tooltip explaining why.
- **Save before prompt loaded:** Add a loading state flag (`promptLoaded = false`). Set it to `true` only after the S3 text asset fetch completes. In `saveEdit()`, check this flag — if the prompt hasn't loaded yet, warn the user: "Prompt is still loading. Please wait." and abort save.
- **Picture removed on save:** In `saveEdit()`, do not overwrite the asset/picture fields if the user hasn't explicitly changed them. Track a `pictureChanged` flag that is set only when the user selects a new picture. On save, only include picture data in the API call if `pictureChanged === true`. Similarly, only include the prompt text if the text editor has been touched (`promptChanged` flag).

**Problem 1 - Where to write the prompt:**
- Add a step-by-step guide panel at the top of the editor (collapsible, shown by default for first-time creators)
- Steps: "1. Pick a nickname -> 2. Name your chat -> 3. Save -> 4. Write the character prompt -> 5. Test it -> 6. Change status to Free to publish"
- Highlight the "Character prompt" textarea as the main creative area

**Problem 2 - Example prompt:**
- Add an "Example" button next to the Character prompt label
- Clicking it shows a modal with 2-3 example prompts, e.g.:
  ```
  Example 1 (Book Discussion):
  "You are Elizabeth Bennet from Pride and Prejudice. The player will discuss
  themes of the book with you. Stay in character. Challenge their assumptions
  about marriage and social class. If they show deep understanding, mark them
  as the winner."

  Example 2 (Quiz Game):
  "You are a quiz master about The Great Gatsby. Ask the player 5 questions
  about the book. Track their score. After 5 questions, if they got 4+ right,
  they win."
  ```
- Add a "Use this example" button that copies the example into the editor

**Problem 3 - Technical contest description:**
- Add an info section on contest.html explaining the game engine:
  - "How it works: You write a character prompt. The AI follows your instructions to chat with players."
  - "Models: Game = faster responses. Discussion = deeper analysis. Multistep = AI tracks game state across turns."
  - "Winning: The AI decides when a player wins based on your instructions."

### Day 3-4: Brand Naming Cleanup
**Files:** All HTML files in `src/html/quizly.pub/`

Find-and-replace across quizly.pub:
- All `<title>` tags: ensure "Quizly" not "Kvasir" or "Quizzly"
- All `<meta>` description/OG tags: same
- Page headings and footer text
- Note: kvasir.pub keeps "Kvasir" branding (it's the editor domain)

### Day 4-5: Social Proof + Metrics Display
**Files:** `src/html/kvasir.pub/echoes.html`, `src/html/kvasir.pub/js/echoes.js`, possibly `kv2_board/lambda_function.py`

- Add a "games played this week" counter in the hero section
- Add participation count on contest pages (contest.html)
- Backend: add an API endpoint or extend `get_info_board` to return aggregate stats
- Frontend: display "X entries" on each contest card

---

## Week 2: Shareable Results + Notifications + SEO

### Day 1-2: Shareable Result Cards
**Files:** `src/html/kvasir.pub/echo.html`, `src/html/kvasir.pub/js/echo.js`

When a game ends (win/lose/complete):
- Generate a share card using Canvas API or HTML-to-image:
  - Game title, score/outcome, Quizly branding, QR code or short URL
- Show share buttons: Copy Link, Twitter/X intent URL, Telegram share URL, WhatsApp share URL
- Share URLs use web intents (no API keys needed):
  - Twitter: `https://twitter.com/intent/tweet?text=...&url=...`
  - Telegram: `https://t.me/share/url?url=...&text=...`
  - WhatsApp: `https://wa.me/?text=...`

Implementation:
- Create a `generateShareCard(title, score, outcome)` function
- Use `<canvas>` to render the card, then `canvas.toDataURL()` for the image
- Add share modal that appears after game completion

### Day 3: Notification Subscription for New Content
**Files:** `src/html/kvasir.pub/echoes.html`, `src/html/kvasir.pub/js/echoes.js`, `src/html/kvasir.pub/js/notifications.js`

Use the existing notification subscription system (same pattern as author follow, forum subscriptions, and info page notifications). The infrastructure already exists:
- `toggle_notification_trigger` action in `kv2_feedback/lambda_function.py`
- `get_notification_trigger` to check subscription state
- Bell icon UI pattern in `notifications.js`

Implementation:
- Add a "Subscribe to new games & contests" toggle on the echoes page (for logged-in users)
- Use `toggle_notification_trigger` with a source like `"echoes_updates"` or `"contests"`
- When new contests are created or new featured games appear, trigger notifications to subscribers
- Backend: in `update_contest` (kv2_board), after creating/activating a contest, also fire notifications to users subscribed to `"contests"` source

### Day 4-5: SEO Pre-rendering for Homepage
**Files:** `src/html/kvasir.pub/echoes.html`

- Add `<noscript>` block with:
  - Platform description
  - Links to top 10-20 games (hardcoded)
  - Contest links
- Add structured data (JSON-LD) for the organization and games
- Ensure all page `<title>` and `<meta description>` are unique and descriptive

---

## Week 3: Admin Winner Button + Contest Polish

### Day 1-2: Admin Winner Announcement Button
**Files:** `src/html/kvasir.pub/admin.html`, `src/html/kvasir.pub/js/admin.js`, `src/lambda_v2/kv2_board/app/lambda_function.py`

Add per-contest "Announce Winner" button in admin.html:

Frontend (admin.js):
- Add a "Winner" button in each contest row (after Props button)
- `renderContestRow()`: add `<button class="btn btn-sm btn-outline-warning" onclick="announceWinner(${item.id})">Winner</button>`
- `announceWinner(contestId)`:
  - Fetch contest entries via `get_contest` action
  - Show a modal listing all entries with radio buttons to select winner
  - Optional message input
  - On confirm: call `boardURL` with `action: "announce_winner"`, `contest_id`, `winner_component_id`, `message`

Backend (kv2_board/lambda_function.py):
- Add `announce_winner` action handler:
  - Get contest title, winner component details, winner's user_id
  - Call `db.add_info_board("echo", winner_user_id, winner_component_id, contest_title, "Contest Winner!", "🏆")`
  - Send notification to winner via `common_add_notification` with link to their winning entry
  - Optionally update contest status to "closed"

### Day 3-4: Contest Page Improvements
**Files:** `src/html/kvasir.pub/contest.html`, `src/html/kvasir.pub/js/contest.js`

- Add countdown timer for active contests (end_at field exists)
- Show contest entries count and unique participants
- Add "Winners" section showing past winners from board data
- Better rules display with formatted sections

### Day 5: Sitemap + SEO Cleanup
**Files:** `scripts/seo/generate_sitemaps.py`, sitemap XML files

- Add `<lastmod>` dates from database
- Add `hreflang` tags for bilingual pages
- Automate regeneration (trigger on content change or daily cron)
- Submit updated sitemaps to Google Search Console

---

## Priority Order (If Time Is Limited)

If you can only do a few items, do them in this exact order:

1. **Hero section** (Day 1-2, Week 1) - highest conversion impact
2. **Contest entry example prompts + save order fix** (Day 2-3, Week 1) - unblocks contest participation
3. **Admin winner announcement button** (Day 1-2, Week 3) - enables contest lifecycle completion
4. **Shareable result cards** (Day 1-2, Week 2) - enables organic growth loop
5. **Brand naming cleanup** (Day 3-4, Week 1) - SEO hygiene
6. **Notification subscription** (Day 3, Week 2) - re-engagement via existing system

---

## Files Reference

### Frontend (edit in kvasir.pub, mirror shows on quizly.pub)
| File | Purpose |
|------|---------|
| `src/html/kvasir.pub/echoes.html` | Homepage layout |
| `src/html/kvasir.pub/js/echoes.js` | Homepage logic, promoted/contests sections |
| `src/html/kvasir.pub/echo.html` | Chat game page |
| `src/html/kvasir.pub/js/echo.js` | Chat game logic |
| `src/html/kvasir.pub/echo-contest.html` | Contest entry editor |
| `src/html/kvasir.pub/js/echo-contest.js` | Contest entry editor logic |
| `src/html/kvasir.pub/contest.html` | Contest display page |
| `src/html/kvasir.pub/js/contest.js` | Contest display logic |
| `src/html/kvasir.pub/admin.html` | Admin panel |
| `src/html/kvasir.pub/js/admin.js` | Admin logic (contests, promo, users, tags) |
| `src/html/kvasir.pub/js/notifications.js` | Notification UI + subscription triggers |
| `src/html/kvasir.pub/js/common.js` | Shared utilities, API URLs |
| `src/html/kvasir.pub/static/custom.css` | Custom styles |

### Backend (Lambda)
| File | Purpose |
|------|---------|
| `src/lambda_v2/kv2_board/app/lambda_function.py` | Board, contests CRUD, announcements |
| `src/lambda_v2/kv2_AI_echo/app/lambda_function.py` | AI chat engine, winner detection |
| `src/lambda_v2/kv2_user/app/lambda_function.py` | User management |
| `src/lambda_v2/kv2_feedback/app/lambda_function.py` | Feedback, notifications, subscriptions |
| `src/lambda_v2/layer_db/python/common_sql.py` | Database operations |
| `src/lambda_v2/layer_db/python/notify.py` | Notification system |

### Build & Deploy
```bash
# Frontend CSS build
cd src/html/kvasir.pub && npm run build:css

# Frontend deploy
cd src/html && ./deploy.sh

# Backend deploy
cd src/lambda_v2 && sam deploy
```
