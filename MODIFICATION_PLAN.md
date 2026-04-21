# MODIFICATION_PLAN.md

## Purpose

This document is the implementation plan for converting `suslonov/kvasir_marketing` from a generic social opportunity scanner into a **cross-platform opportunity queue** focused on one question:

> **Where should I post or reply, and what text should I use?**

Primary target channels for the first implementation phase:

- Reddit
- X / Twitter
- YouTube (design now, implement later)

This system is **not** an auto-poster. It is a **scanner + recommender + drafting system** for human review.

---

## Product-level change

### Current repo direction

The current repo already points toward:

- scanning communities,
- collecting source items,
- scoring them,
- asking Claude to classify opportunities,
- drafting copy,
- rendering an HTML report.

### New direction

The system should now optimize for:

1. **queueing actionable opportunities** rather than storing lots of raw posts,
2. **running every 10 minutes**,
3. recommending:
   - **where** to reply,
   - **where** to create a post,
   - **where** paid placement may be worth considering,
4. generating:
   - a recommended ad/reply text for each opportunity,
   - rationale and risk notes,
5. using **your human Reddit login via local browser session** instead of trying to make Reddit API collection the center of the system.

---

## Non-goals

Do **not** build these in v1:

- automatic posting
- account rotation
- large-scale post archive
- full Reddit scraping framework
- broad user profiling
- moderation automation
- distributed worker system
- cloud deployment

The target is a **local, review-first, durable queue**.

---

## Core behavior after the modification

Every 10 minutes, the scheduler should:

1. load configured sources and targets,
2. collect a **small candidate set** from each enabled platform,
3. normalize candidates,
4. ask the decision layer:
   - is this worth replying to?
   - is this a place for a native post?
   - is this useful only as an ad-targeting hint?
   - should this be ignored?
5. create or update queue items,
6. generate recommended copy for each viable opportunity,
7. render an HTML review page.

---

## Architectural shift

### Old center of gravity

`source_items` -> score -> derived opportunities -> HTML

### New center of gravity

`candidate observations` -> decision engine -> `opportunity_queue` -> HTML review inbox

The implementation should still keep a **minimal evidence layer**, but the durable object should now be the **opportunity**.

---

## Data model changes

### Keep

You may still keep a minimal `source_items` or `candidate_items` table for provenance.

### Add: `opportunity_queue`

Create a new first-class queue table.

Recommended fields:

- `id`
- `platform`  
  Values: `reddit`, `twitter`, `youtube`, `other`
- `placement_type`  
  Values:
  - `comment_reply`
  - `organic_post`
  - `paid_ad_target`
  - `monitor`
  - `skip`
- `target_name`  
  Examples:
  - subreddit name
  - X account handle
  - YouTube channel name
- `target_url`
- `platform_object_id`
- `source_item_id` nullable
- `title_snapshot`
- `body_snapshot`
- `why_now`
- `fit_score`
- `risk_score`
- `urgency_score`
- `confidence_score`
- `recommended_angle`
- `recommended_text_short`
- `recommended_text_medium`
- `recommended_text_long`
- `recommended_cta`
- `risk_notes`
- `decision_model`
- `decision_version`
- `status`  
  Values:
  - `new`
  - `reviewed`
  - `approved`
  - `rejected`
  - `posted`
  - `expired`
- `cooldown_until`
- `created_at`
- `updated_at`
- `last_seen_at`

### Add: `scanner_runs`

Recommended fields:

- `id`
- `started_at`
- `finished_at`
- `status`
- `platform`
- `discovered_count`
- `queued_count`
- `error_text`

### Add: `platform_targets`

This table holds configured discovery targets.

Recommended fields:

- `id`
- `platform`
- `target_type`  
  Examples:
  - `subreddit`
  - `search_query`
  - `account`
  - `channel`
  - `video_topic`
- `target_value`
- `is_enabled`
- `priority`
- `notes`

### Optional: `candidate_items`

If you want minimal provenance without building a large archive:

- `id`
- `platform`
- `platform_object_id`
- `parent_target`
- `url`
- `title`
- `body_excerpt`
- `author`
- `score`
- `comment_count`
- `published_at`
- `discovered_at`
- `raw_json` nullable

Keep this table compact and dedupe aggressively.

---

## Decision model

For each candidate, the LLM must return a structured decision object with at least:

- `placement_type`
- `place_here` boolean
- `target_name`
- `target_url`
- `why_this_place`
- `timing_reason`
- `audience_fit`
- `self_promo_risk`
- `recommended_angle`
- `recommended_text_short`
- `recommended_text_medium`
- `recommended_text_long`
- `recommended_cta`
- `moderation_risk_notes`
- `confidence_score`
- `skip_reason` if rejected

### Scoring dimensions

The system should score candidates on:

- **audience fit**
- **timing fit**
- **conversation openness**
- **self-promo risk**
- **platform etiquette fit**
- **expected value**
- **novelty / dedupe distance**

---

## Reddit collection design

## Important operating model

For Reddit, use **your human login in a local browser profile**.

This means the system is not centered on Reddit API credentials.  
Instead, it uses a local Playwright browser session that you initialize manually once and occasionally refresh.

### What you will need to do

#### One-time setup

1. Install Playwright in the project environment.
2. Install the browser binaries.
3. Run a bootstrap script such as:
   - `python scripts/bootstrap_reddit_session.py`
4. A visible Chromium window opens.
5. You log in to Reddit manually.
6. If Reddit asks for 2FA or challenge steps, you complete them manually.
7. Press Enter in the terminal after login is complete.
8. The browser profile is saved locally.

#### Ongoing usage

- The scheduler reuses the saved browser profile.
- The scanner opens subreddit pages and search pages using your stored session.
- If Reddit logs you out or presents a challenge page, the job should stop and emit a clear error.
- You rerun the bootstrap script to refresh the session.

#### Security rules

- Store the browser profile outside git.
- Do not store Reddit password in source files.
- Do not sync the session profile to a public repo or public cloud bucket.
- Use a **dedicated browser profile directory** for this project only.

### What the Reddit scanner should actually do

The scanner should not attempt deep scraping. It should:

- open selected subreddit feeds,
- optionally open selected subreddit searches,
- inspect a small number of fresh posts,
- extract:
  - subreddit
  - post title
  - post URL
  - age
  - score
  - comment count
  - excerpt
  - top comments preview if needed
- pass the candidate to the decision layer.

### Suggested Reddit target types

Support these target configurations:

- `subreddit:new`
- `subreddit:hot`
- `subreddit:search`
- `multi_subreddit`
- `manual_url`

---

## X / Twitter design

Treat X as a second platform.

The first implementation can support:

- public search pages or existing collector path,
- selected account timelines,
- selected search queries.

Focus on:

- identifying posts worth replying under,
- identifying accounts worth monitoring,
- drafting a recommended reply text.

Do **not** make X the hardest dependency in the first pass. Keep the interface abstract enough so the collection mechanism can vary.

---

## YouTube design

Do not implement full YouTube support in the first coding pass.  
Design for it now so the queue schema supports it later.

Target future use cases:

- identify videos whose comments sections contain relevant discussions,
- identify channels worth posting to via comments,
- identify themes worth using in cross-platform content.

---

## File tree changes

Below is the target file structure after modification.

```text
kvasir_marketing/
├─ CLAUDE.md
├─ MODIFICATION_PLAN.md
├─ requirements.txt
├─ config/
│  ├─ sources.yaml
│  ├─ platforms.yaml
│  └─ prompts/
│     ├─ opportunity_classifier.md
│     ├─ recommendation_writer.md
│     └─ platform_style_rules.md
├─ marketing/
│  └─ reports/
├─ runtime/
│  ├─ browser_profiles/
│  │  └─ reddit_profile/
│  ├─ logs/
│  └─ state/
├─ scripts/
│  ├─ bootstrap_reddit_session.py
│  ├─ run_scheduler.sh
│  ├─ run_once.py
│  └─ inspect_queue.py
├─ src/
│  ├─ __init__.py
│  ├─ settings.py
│  ├─ scheduler_entry.py
│  ├─ pipeline.py
│  ├─ db.py
│  ├─ models.py
│  ├─ prompts.py
│  ├─ scoring.py
│  ├─ decisions.py
│  ├─ opportunity_queue.py
│  ├─ render.py
│  ├─ collectors/
│  │  ├─ __init__.py
│  │  ├─ reddit_browser.py
│  │  ├─ twitter.py
│  │  └─ youtube.py
│  ├─ extractors/
│  │  ├─ __init__.py
│  │  ├─ reddit_extract.py
│  │  └─ common.py
│  └─ templates/
│     └─ opportunity_queue.html
├─ templates/
│  └─ opportunity_queue.html
└─ tests/
   ├─ test_db.py
   ├─ test_queue.py
   ├─ test_decisions.py
   └─ test_reddit_extract.py
```

---

## File-by-file implementation plan

## `requirements.txt`

Add the actual runtime requirements, at minimum:

- `playwright`
- `jinja2`
- `pydantic`
- `pyyaml`
- `beautifulsoup4` or `selectolax`
- `tenacity`
- `sqlite-utils` optional
- `pytest`

If Claude API integration already exists elsewhere in your workflow, add only what this repo directly needs.

---

## `config/platforms.yaml`

Add platform-specific configuration.

Suggested structure:

```yaml
scan_interval_minutes: 10

platforms:
  reddit:
    enabled: true
    collector: reddit_browser
    browser_profile_dir: runtime/browser_profiles/reddit_profile
    headless: true
    max_posts_per_target: 12
    targets:
      - type: subreddit:new
        value: chatgpt
      - type: subreddit:new
        value: singularity
      - type: subreddit:search
        value: "books ai"
      - type: subreddit:search
        value: "quiz app"
  twitter:
    enabled: true
    collector: twitter
    max_items_per_target: 10
    targets:
      - type: search
        value: "AI books"
      - type: search
        value: "education startup"
  youtube:
    enabled: false
    collector: youtube
    targets: []
```

---

## `src/models.py`

Define structured models for:

- `CandidateItem`
- `OpportunityDecision`
- `OpportunityQueueItem`
- `ScannerRun`
- `PlatformTarget`

The decision model should be strict enough that Claude output can be validated before insertion.

Recommended enums:

- `Platform`
- `PlacementType`
- `QueueStatus`

---

## `src/db.py`

Responsibilities:

- initialize schema,
- run migrations,
- insert/update candidate items,
- upsert opportunity queue records,
- record scanner runs,
- fetch open queue items,
- mark stale items expired,
- suppress duplicates.

### Important DB rules

- Unique key on `(platform, platform_object_id, placement_type)`
- Cooldown logic to prevent re-adding near-identical items every 10 minutes
- Expire queue items older than configurable TTL unless they were manually reviewed
- Store minimal snapshots for traceability

---

## `src/opportunity_queue.py`

New module.  
Responsibilities:

- dedupe logic,
- scoring normalization,
- queue upsert policy,
- queue status transitions,
- staleness handling.

This module should be the main abstraction around queue behavior instead of scattering queue rules in `db.py`.

---

## `src/scoring.py`

Keep deterministic pre-LLM scoring here.

Possible heuristics:

- subreddit/account/channel weight
- freshness
- thread traction
- text overlap with Quizly/Kvasir topics
- anti-self-promo signals
- duplicate similarity to existing queue items

Output:

- pre-score
- candidate priority
- whether to send to LLM or skip early

---

## `src/decisions.py`

This is the bridge from normalized candidate -> Claude decision.

Responsibilities:

- build prompt input
- call Claude
- validate structured output
- convert to `OpportunityDecision`
- apply fallback defaults on partial LLM failures

The LLM should not decide everything from raw HTML.  
Pass it a compact candidate object.

---

## `src/prompts.py`

Centralize prompt loading and rendering.

Recommended prompt files:

- `config/prompts/opportunity_classifier.md`
- `config/prompts/recommendation_writer.md`
- `config/prompts/platform_style_rules.md`

This allows prompt editing without touching code.

---

## `src/collectors/reddit_browser.py`

This is the core new collector.

Responsibilities:

- launch persistent Playwright context with saved profile,
- verify logged-in state,
- visit configured targets,
- extract candidate post metadata,
- return normalized candidate items.

### Required failure modes

The collector must return explicit errors when:

- browser profile missing
- Reddit session expired
- challenge / CAPTCHA page encountered
- selectors changed enough to break extraction

### Practical extraction scope

Start with:

- title
- URL
- subreddit
- post id if extractable
- age string
- score string
- comments count string
- text excerpt if present

Do not try to parse everything in v1.

---

## `src/extractors/reddit_extract.py`

Keep DOM parsing isolated here.

Responsibilities:

- selectors and fallback selectors,
- page-level extraction helpers,
- conversion to normalized candidate structure.

This reduces breakage when Reddit changes markup.

---

## `src/collectors/twitter.py`

For v1, keep it narrow.

Responsibilities:

- fetch a configured small candidate set,
- normalize into `CandidateItem`,
- provide URLs and excerpt text.

The exact collection method can evolve.  
Keep the interface stable even if implementation changes later.

---

## `src/collectors/youtube.py`

Implement as stub / placeholder initially.

Responsibilities in first pass:

- accept config,
- return empty list,
- preserve interface.

This keeps the architecture ready without bloating phase 1.

---

## `src/pipeline.py`

Refactor this file into a clear orchestration layer.

Recommended flow:

1. load settings
2. initialize DB
3. start scanner run record
4. collect candidates from each enabled platform
5. normalize and pre-score
6. filter obvious skips
7. send remaining candidates to decision layer
8. upsert resulting queue items
9. expire stale queue items
10. render HTML
11. finish scanner run record

Keep `pipeline.py` thin.  
Push platform-specific logic into collectors and queue logic into dedicated modules.

---

## `src/render.py`

The report should no longer look like a generic feed dump.

It should render a **review inbox** with sections such as:

- Reddit comment opportunities
- Reddit native post opportunities
- X reply opportunities
- Paid ad targets
- Monitor only
- Rejected / high-risk items optional

Each card should show:

- platform
- destination
- reason
- scores
- moderation risk
- recommended text
- status
- timestamps

---

## `templates/opportunity_queue.html`

New template.

Important UI blocks:

- top summary counts
- grouped opportunity sections
- queue status badge
- direct link to destination
- short and longer copy variants
- risk notes
- freshness and confidence

Keep it lightweight and readable in a local browser.

---

## `src/scheduler_entry.py`

This should become a clean, non-interactive entrypoint for cron.

Requirements:

- one command runs one full cycle
- writes logs clearly
- exits nonzero on hard failure
- uses lock logic to prevent overlap

### Overlap guard

Because the interval is 10 minutes, add a simple lock:

- file lock, or
- DB lock row.

If a previous run is still active, skip the new run and log it.

---

## `scripts/bootstrap_reddit_session.py`

This script is essential.

Responsibilities:

- launch Playwright in visible mode,
- open Reddit,
- let you log in manually,
- wait for confirmation,
- persist the browser profile,
- optionally validate by opening one target subreddit.

This script should be documented clearly because it is the human-dependent bootstrap step.

---

## `scripts/run_scheduler.sh`

Create a shell script that:

- activates the conda environment,
- changes into repo directory,
- runs `python -m src.scheduler_entry`,
- writes logs to `runtime/logs/`.

Example cron usage:

```bash
*/10 * * * * /path/to/kvasir_marketing/scripts/run_scheduler.sh
```

---

## `scripts/inspect_queue.py`

Useful local inspection helper.

Responsibilities:

- print open queue items,
- filter by platform/status,
- show recent runs,
- help debug without opening HTML.

---

## Scheduler behavior

### Interval

Run once per 10 minutes.

### Rules

- collect only a small number of candidates per target
- dedupe aggressively
- suppress opportunities already reviewed or recently seen
- expire stale opportunities automatically
- do not crash the whole pipeline because one platform failed

### Suggested run policy

- Reddit first
- Twitter second
- YouTube disabled initially
- render even if one platform failed

---

## Opportunity lifecycle

Queue statuses should behave like this:

- `new` -> generated, not reviewed
- `reviewed` -> seen by you
- `approved` -> considered usable
- `rejected` -> explicitly not useful
- `posted` -> already acted on manually
- `expired` -> no longer timely

### Queue rules

- A `posted` item should never be re-opened automatically
- A `rejected` item should obey cooldown before resurfacing
- A `new` item should be updated if the same target becomes more urgent
- A stale `new` item should become `expired`

---

## Reporting design

The rendered HTML should answer these questions immediately:

1. Where should I go right now?
2. What should I say?
3. Why is this a fit?
4. What is the spam / moderation risk?
5. Is this fresh enough to still matter?

### Suggested section order

1. Best immediate reply opportunities
2. Best organic post opportunities
3. Interesting paid-ad targets
4. Monitor-only signals
5. Recent runs / platform health summary

---

## Phase breakdown

## Phase 1 — queue-first refactor

Goal:

- establish queue schema and report shape,
- keep existing collectors functional where possible.

Tasks:

- add models
- add DB schema
- add queue module
- refactor pipeline
- add new renderer/template

Deliverable:

- local HTML report from queue objects

---

## Phase 2 — Reddit browser collector

Goal:

- switch Reddit to human-session browser collection.

Tasks:

- add Playwright dependency
- add bootstrap script
- add collector
- add extractor helpers
- add login/session validation
- update config

Deliverable:

- working local Reddit discovery using saved browser profile

---

## Phase 3 — 10-minute scheduler hardening

Goal:

- make repeated execution safe.

Tasks:

- add lock
- add stale expiration
- add dedupe and cooldown rules
- improve logs

Deliverable:

- stable cron execution every 10 minutes

---

## Phase 4 — improve decision quality

Goal:

- make recommendations more useful.

Tasks:

- tighten prompts
- add richer risk notes
- add short / medium / long text variants
- improve platform style differentiation

Deliverable:

- better recommendation quality and less noisy queue

---

## Phase 5 — extend to X and YouTube

Goal:

- broaden channel coverage without breaking the queue model.

Tasks:

- improve Twitter collector
- keep YouTube as limited first implementation
- ensure UI groups opportunities by platform

Deliverable:

- multi-platform recommendation inbox

---

## Cursor implementation prompts

Below are the first prompts to run in Cursor.

---

### Prompt 1 — repository refactor scaffold

Create the queue-first architecture for the repo.

Tasks:
1. Inspect the existing repository structure and keep all working files that are still useful.
2. Add or update:
   - `src/models.py`
   - `src/db.py`
   - `src/opportunity_queue.py`
   - `src/scoring.py`
   - `src/decisions.py`
   - `src/prompts.py`
   - `src/pipeline.py`
   - `src/render.py`
   - `src/settings.py`
   - `templates/opportunity_queue.html`
3. Introduce the core models:
   - `CandidateItem`
   - `OpportunityDecision`
   - `OpportunityQueueItem`
   - `ScannerRun`
   - `PlatformTarget`
4. Implement SQLite schema creation and migrations for:
   - `scanner_runs`
   - `platform_targets`
   - `candidate_items`
   - `opportunity_queue`
5. Build a queue-first pipeline that:
   - collects candidate items,
   - pre-scores them,
   - passes them to a decision layer,
   - upserts opportunity queue items,
   - renders an HTML report.
6. Keep code modular and typed.
7. Do not implement auto-posting.
8. Add clear docstrings and TODO markers where external integrations are still mocked.

Output:
- working code scaffold
- no placeholder pseudocode in core modules
- app should run locally even if some collectors return empty lists

---

### Prompt 2 — configuration and prompt files

Add configuration and prompt-loading support.

Tasks:
1. Create:
   - `config/platforms.yaml`
   - `config/prompts/opportunity_classifier.md`
   - `config/prompts/recommendation_writer.md`
   - `config/prompts/platform_style_rules.md`
2. Add `src/settings.py` that loads YAML config into structured models.
3. Add `src/prompts.py` that loads prompt files and renders them with variables.
4. Include config for:
   - scan interval of 10 minutes
   - Reddit browser profile path
   - per-platform enable flags
   - per-target limits
5. Include sample targets for Reddit and Twitter.
6. Make the system resilient if YouTube is disabled.

Output:
- clean config loading
- no hardcoded paths except safe defaults
- prompts editable without changing Python code

---

### Prompt 3 — Reddit browser bootstrap and collector

Implement Reddit browser-session support using Playwright.

Tasks:
1. Add `playwright` to requirements and create:
   - `scripts/bootstrap_reddit_session.py`
   - `src/collectors/reddit_browser.py`
   - `src/extractors/reddit_extract.py`
2. The bootstrap script must:
   - launch Chromium in visible mode,
   - use a persistent context,
   - open Reddit,
   - wait for manual login,
   - persist the browser profile,
   - validate login by opening one subreddit page.
3. The collector must:
   - open configured subreddit/search targets,
   - verify that the browser session is authenticated,
   - extract a limited number of fresh posts,
   - normalize them into `CandidateItem`.
4. Handle these failure modes cleanly:
   - missing profile
   - logged out
   - challenge / CAPTCHA
   - selector mismatch
5. Keep selectors isolated inside `src/extractors/reddit_extract.py`.

Output:
- a working local Reddit collector for a saved human session
- no Reddit password stored in code or config

---

### Prompt 4 — scheduler hardening and run scripts

Implement repeated local execution.

Tasks:
1. Update `src/scheduler_entry.py` to run one full scan cycle.
2. Add overlap protection using either:
   - a file lock, or
   - a DB lock row.
3. Create:
   - `scripts/run_scheduler.sh`
   - `scripts/run_once.py`
   - `scripts/inspect_queue.py`
4. Ensure the scheduler:
   - logs start and end,
   - records `scanner_runs`,
   - skips overlapping runs,
   - renders HTML even if one platform fails.
5. Add clear CLI output and nonzero exit codes on hard failures.

Output:
- stable local execution suitable for cron every 10 minutes

---

### Prompt 5 — report UX and recommendation quality

Improve the report so it behaves like a decision inbox.

Tasks:
1. Redesign `templates/opportunity_queue.html` and `src/render.py`.
2. Group results by:
   - best immediate reply opportunities
   - best organic post opportunities
   - paid ad targets
   - monitor only
3. Each card must show:
   - platform
   - destination link
   - fit / risk / urgency / confidence
   - short rationale
   - short / medium / long recommended text
   - moderation risk notes
   - queue status
4. Show a top summary block with counts by platform and placement type.
5. Keep the HTML local, simple, and dependency-light.

Output:
- a readable local review report optimized for action

---

## Acceptance criteria

The implementation is successful when:

1. The repo can run locally on your machine.
2. Reddit scanning works through a manually bootstrapped browser session.
3. The scheduler can run every 10 minutes without overlapping.
4. The output is a queue of actionable opportunities, not a dump of raw posts.
5. Each recommendation includes:
   - where to act,
   - what to say,
   - why it fits,
   - moderation / etiquette risk.
6. The system remains review-first and does not auto-post.

---

## Final recommendation

Implement in this order:

1. queue schema and models
2. pipeline refactor
3. HTML inbox
4. Reddit browser bootstrap + collector
5. scheduler + locks
6. prompt tightening
7. X improvements
8. YouTube later

Do not start with YouTube.  
Do not start with auto-posting.  
Do not overbuild storage for raw source content.

The right v1 is a **small, durable, reviewable opportunity queue**.
