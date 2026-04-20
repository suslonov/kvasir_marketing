# Cursor Build Plan — Social Opportunity Scanner for Quizly/Kvasir

## Goal

Build a local agent inside `suslonov/kvasir_marketing` that scans Reddit and other selected communities, identifies promising ad-placement and engagement opportunities for Quizly, drafts candidate ad copy / post copy, and renders the results into a local HTML report.

This is **not** an auto-poster. It is a **scanner + recommender + drafting system** for human review.

Primary model for judgment and drafting: **Claude Sonnet**.

## Why this agent exists

Kvasir/Quizly already has a clear strategic gap: the product exists, but distribution is weak, and the near-term priority is to find one shareable acquisition loop rather than add more features. The repo’s own positioning and promotion documents explicitly frame the problem as lack of distribution, recommend Reddit as a high-priority free channel, and emphasize literary AI / creator-economy positioning instead of generic AI chat. Therefore this agent should focus on **finding real distribution openings** in communities that overlap with books, AI, quizzes, teachers, book clubs, and indie projects.

## What the agent should do

On each run, the agent should:

1. Collect recent posts and threads from a configured set of communities.
2. Normalize and store them locally.
3. Score each opportunity for relevance to Quizly/Kvasir.
4. Ask Claude Sonnet to decide:
   - whether this is a good place to advertise or comment,
   - which product angle fits,
   - whether the opportunity is for a paid ad, a native community post, a comment reply, or “skip”.
5. Draft:
   - recommended ad text,
   - recommended organic post text,
   - recommended comment reply text,
   - risk notes about self-promo / moderator hostility / mismatch.
6. Render a local HTML report with ranked opportunities.
7. Preserve history so repeated runs improve rather than restart from zero.

## Core decision types

For each scanned item, the system should classify into one of these actions:

- `skip`
- `monitor`
- `comment_opportunity`
- `organic_post_opportunity`
- `paid_ad_target`
- `research_only`

This matters because Reddit and similar communities often punish obvious self-promotion, so the agent must distinguish between:

- **native engagement**,
- **ad placement research**,
- **copy ideation**,
- **no-go zones**.

## Product angles the agent should test

The repo’s existing positioning suggests the scanner should not sell Quizly as generic AI chat. It should test several specific angles:

1. **Literary AI games**
   - “AI word games and contests for readers”
2. **Book discussion / AI book club tool**
   - especially for readers, book clubs, teachers
3. **Creator economy for literary prompts and contests**
   - differentiated from pure consumption products
4. **Classic-text grounded AI chats**
   - not just fictional chat, but grounded in source texts
5. **Quiz / challenge angle**
   - “Can you beat the AI on Hamlet / Gatsby / Pride and Prejudice?”
6. **Teacher / homeschool utility**
   - discussion prompts, classroom / club engagement

The agent should learn which angle best matches each community.

## Recommended platforms to scan

### Tier 1 — initial production targets

#### Reddit
Reddit is the best first target because:
- it is already identified in your repo as a high-priority free channel,
- communities are interest-dense,
- opportunities are visible in plain text,
- successful engagement often starts from comments, not ads.

Initial subreddits:

**Books / reading**
- `r/books`
- `r/bookclub`
- `r/suggestmeabook`
- `r/classics`
- `r/literature`
- `r/52book`
- `r/fantasy` (only for specific title/character angles)

**AI / tech**
- `r/ChatGPT`
- `r/artificial`
- `r/LocalLLaMA`
- `r/MachineLearning` (mostly research/infra, likely low direct conversion)
- `r/SideProject`
- `r/IndieHackers` if accessible as a forum mirror elsewhere

**Education / teaching**
- `r/Teachers`
- `r/homeschool`
- `r/Professors` (be cautious)
- `r/EnglishLearning` and related communities only if the angle fits

**Game / quiz adjacent**
- `r/trivia`
- `r/puzzles`
- `r/wordgames`

#### Hacker News
Not as a daily source of ad opportunities, but useful for:
- discovering relevant discussions around AI learning, reading, games, creator tools,
- testing “Show HN” style positioning,
- collecting objections from technical early adopters.

#### Product Hunt
Useful mostly as a launch / campaign timing source, not a daily community response target.
The scanner should monitor:
- similar launches,
- comments on adjacent products,
- launch language that performs well.

### Tier 2 — useful after MVP

#### X/Twitter
Keep in architecture, but secondary for this agent unless you explicitly want social-listening breadth.
Use it mainly to:
- discover discussion themes,
- identify creators / teachers / book influencers,
- collect phrasing that works.
Do not make the MVP depend on it.

#### Facebook Groups / Book club communities
Potentially high-value, but technically messy and policy-sensitive. Better as manual research targets later.

#### Discord / Telegram public communities
Good for qualitative research if there are public channels or exported resources, but usually weaker for unattended scraping.

### Tier 3 — optional forums / creator communities
- Lemmy communities related to books / AI / learning
- Indie Hackers public pages
- relevant public blogs with comments
- Goodreads-adjacent public discussions if accessible without abusive scraping

## What to look for

The scanner should not just look for “advertising spaces”. It should detect these opportunity classes:

### 1. Pain / need signals
Examples:
- “How do I make book clubs more engaging?”
- “Any AI tools for literature classes?”
- “Discussion questions for [book]?”
- “How can I get students to read classics?”
- “Is there a quiz / challenge for [book]?”

### 2. Comparative tool requests
Examples:
- “Best AI app for readers?”
- “Alternatives to Character.AI for books?”
- “Tools for book discussion?”

### 3. Viral format openings
Examples:
- daily challenge formats,
- “guess the character / quote / book” threads,
- reading challenge communities,
- screenshot-friendly game mechanics.

### 4. Ad-placement targets
Examples:
- communities that allow promoted posts,
- newsletters or blogs serving readers / teachers / AI hobbyists,
- subreddits whose audience fit suggests Reddit Ads targeting later.

### 5. Language / message mining
The scanner should capture exact phrases users use when they describe their needs, so ad copy uses audience language instead of invented marketing copy.

## What the agent must output for each opportunity

Each item in the report should contain:

- source platform
- community / subreddit / forum name
- thread title
- thread URL
- author
- created time
- score / engagement metrics available
- extracted text snippet
- opportunity type
- relevance score (0–100)
- confidence score (0–100)
- self-promo risk score (0–100)
- suggested audience angle
- suggested action
- short rationale
- one proposed ad text
- one proposed organic post
- one proposed comment reply
- moderation / etiquette notes
- tags

## HTML report structure

The report should be static local HTML, rebuilt each run.

Sections:

1. **Top opportunities today**
2. **Best places for native engagement**
3. **Best places for paid ads / sponsored tests**
4. **High-risk / do not post**
5. **Best-performing message angles**
6. **New communities discovered**
7. **Thread-by-thread opportunity cards**
8. **Archive / history view**

Each opportunity card should show:
- source badge
- community badge
- engagement stats
- opportunity summary
- recommended action
- draft copy blocks
- direct link

Add local filters for:
- platform
- community
- audience angle
- opportunity type
- risk level
- date range

## Recommended architecture

### Principle
Use the same broad pattern as the AI-news scanner:

1. collectors
2. normalizer
3. state store
4. scoring / heuristics
5. Claude decision + drafting
6. HTML renderer

### Suggested project layout inside `kvasir_marketing`

```text
marketing/
  social_scanner/
    README.md
    CLAUDE.md
    requirements.txt
    .env.example
    config/
      sources.yaml
      prompts/
        evaluate_opportunity.txt
        draft_copy.txt
        cluster_themes.txt
    data/
      state.db
      raw/
      rendered/
        social_opportunities.html
      logs/
    src/
      main.py
      scheduler_entry.py
      settings.py
      models.py
      db.py
      pipeline.py
      heuristics.py
      ranking.py
      render.py
      extraction.py
      collectors/
        reddit_api.py
        hn_api.py
        producthunt_scraper.py
        x_listener.py
        generic_rss.py
      claude/
        prompts.py
        evaluate.py
        drafting.py
    templates/
      report.jinja2
    scripts/
      run.sh
      smoke_test.sh
    tests/
      test_reddit_normalization.py
      test_heuristics.py
      test_render.py
```

## Data model

Use SQLite from the start.

Minimum tables:

### `source_items`
Raw normalized social items.
Fields:
- id
- source_id
- platform
- community
- external_id
- title
- url
- author
- created_at
- fetched_at
- score
- comments_count
- body_text
- tags_json
- raw_json
- canonical_hash

### `opportunities`
Claude-reviewed opportunities.
Fields:
- id
- source_item_id
- opportunity_type
- relevance_score
- confidence_score
- self_promo_risk_score
- audience_angle
- recommended_action
- rationale
- ad_text
- organic_post_text
- comment_reply_text
- moderation_notes
- decision_model
- created_at
- updated_at

### `runs`
Track job runs and stats.

### `community_profiles`
Longer-term memory about each community.
Fields:
- community
- platform
- promo_tolerance
- audience_fit
- dominant_topics
- notes
- last_seen_at

## Collector plan

### Reddit collector — MVP first
Use the official Reddit API if possible.
The collector should gather from configured subreddits:
- top posts in configurable windows,
- new posts,
- selected comments on promising threads.

Search keywords should include:
- ai book
- book quiz
- literature quiz
- book club tool
- reading discussion questions
- classics discussion
- ai for teachers
- ai classroom reading
- trivia game
- word game
- character chat

Also collect by subreddit without keywords, because many good opportunities are phrased indirectly.

### Hacker News collector
Use available official or simple scrape-friendly endpoints for:
- front page stories in relevant periods,
- search results for terms like books, reading, AI tutor, AI game, edtech, contest, quiz.

### Product Hunt / launch monitor
Do not over-engineer. Start with manual / lightweight scraping of relevant launches, comments, and positioning phrases.

### X listener
Keep the interface in the project, but do not make the MVP depend on it.

## Decision pipeline

### Stage 1 — rules / heuristics
Before spending Claude calls, apply cheap filters:
- duplicate removal
- language filtering
- basic keyword relevance
- obvious no-go communities
- stale threads beyond a configurable age

### Stage 2 — Claude opportunity evaluation
Claude Sonnet receives a compact package:
- title
- body snippet
- community name
- platform
- engagement stats
- known community profile
- product positioning summary

Claude should answer:
- Is this a good place to mention Quizly?
- If yes, in what form?
- Which positioning angle fits?
- How risky is direct promotion?
- What is the best copy draft?

### Stage 3 — community memory update
The system should update per-community profiles over time.
Examples:
- `r/books`: high fit, high promo risk, prefer comments over top-level self-promo
- `r/ChatGPT`: medium fit, moderate promo tolerance if framed as interesting AI project
- `r/Teachers`: fit depends on clear educational value and low hype

## Claude prompt design

You will need at least three prompt types.

### 1. Opportunity evaluation prompt
Input:
- normalized social item
- Quizly positioning summary
- allowed action types

Output JSON:
- keep / skip
- opportunity_type
- relevance_score
- confidence_score
- self_promo_risk_score
- audience_angle
- recommended_action
- rationale
- moderation_notes

### 2. Drafting prompt
Input:
- accepted opportunity
- audience angle
- community norms

Output JSON:
- ad_text_short
- ad_text_long
- organic_post_text
- comment_reply_text
- alt_hooks

### 3. Theme clustering prompt
Input:
- recent accepted opportunities

Output:
- top themes this week
- repeated pain points
- which messages seem most reusable

## Decision rubric for Claude

Claude should score opportunities against this rubric:

### Relevance
Does the thread actually overlap with:
- readers,
- literary discussion,
- AI-enhanced learning,
- creator tools,
- word games,
- quizzes,
- teachers / clubs?

### Actionability
Could you realistically post/comment/advertise there in the next 7 days?

### Promo tolerance
Would a mention of Quizly be welcomed, tolerated, ignored, or punished?

### Message fit
Which of these is the best framing?
- literary AI game
- book discussion tool
- creator contest platform
- classic-text AI chat
- challenge / quiz
- classroom tool

### Timing
Is the thread fresh enough to matter?

## Suggested development phases for Cursor

### Phase 1 — skeleton and local report
Build:
- project structure
- config loading
- SQLite
- basic renderer
- fake sample data pipeline

Success condition:
- one HTML report renders from mock opportunities

### Phase 2 — Reddit MVP
Build:
- Reddit API collector
- normalization
- dedupe
- heuristics
- HTML cards for Reddit opportunities

Success condition:
- one cron-safe local run scans selected subreddits and renders a report

### Phase 3 — Claude evaluation and copy drafting
Build:
- Sonnet evaluation adapter
- strict JSON parsing
- fallback behavior when model fails
- draft copy blocks in output

Success condition:
- each promising thread gets a ranked recommendation and draft texts

### Phase 4 — community memory
Build:
- community profile table
- update logic
- repeated-risk tracking
- reuse of community notes in prompts

Success condition:
- the agent gets better at distinguishing “comment only” vs “do not touch” communities

### Phase 5 — more sources
Add:
- Hacker News
- Product Hunt / adjacent launch sources
- optional X listener
- optional newsletters / blogs / public creator communities

Success condition:
- the report becomes multi-source without breaking the Reddit core

### Phase 6 — campaign layer
Add:
- cluster similar opportunities
- generate campaign recommendations
- identify best reusable copy angles
- produce weekly summary views

## Output modes

The system should produce two reports:

### Daily scanner report
Short horizon. Focus on:
- fresh opportunities
- recommended immediate actions
- draft copy

### Weekly strategy report
Longer horizon. Focus on:
- which communities look best,
- which audience angles are recurring,
- which copy patterns Claude keeps preferring,
- where paid ads might be worth testing.

## Guardrails

The agent must not:
- auto-post anywhere,
- spam communities,
- recommend rule-breaking self-promotion,
- treat every mention as an ad opportunity,
- overfit to AI communities and ignore reading communities.

It should explicitly surface:
- uncertainty,
- policy risk,
- whether a better move is a comment, not a post,
- whether the right output is “research only”.

## Metrics to track

Track system metrics:
- sources scanned
- items collected
- opportunities accepted
- communities flagged high-fit
- communities flagged high-risk
- copy drafts generated

Track marketing metrics later, when you connect real outcomes:
- clicks from specific placements
- signups by source/community
- conversion by message angle
- retention by acquisition source

## Implementation notes for Cursor / Claude Code

Create a dedicated `CLAUDE.md` inside `marketing/social_scanner/`.
It should define:
- no auto-posting,
- Python-only implementation,
- SQLite as source of truth,
- static HTML output,
- Reddit-first MVP,
- strict JSON outputs from Claude,
- small incremental edits and focused tests.

Build the system in small prompts:
1. models + db + settings
2. renderer with mock data
3. Reddit collector
4. heuristics
5. Claude evaluator
6. drafting layer
7. scheduler entrypoint
8. weekly report mode

## Suggested first implementation prompt for Cursor

```text
Read this folder's CLAUDE.md and implement the MVP skeleton for a social opportunity scanner.

Requirements:
1. create project structure under marketing/social_scanner/
2. add models.py, settings.py, db.py, render.py, pipeline.py, main.py
3. use SQLite
4. create a static HTML report template
5. render mock opportunity cards from sample data
6. include fields for:
   - platform
   - community
   - title
   - url
   - relevance_score
   - self_promo_risk_score
   - recommended_action
   - ad_text
   - organic_post_text
   - comment_reply_text
7. add focused tests for DB init and HTML rendering

Do not implement real collectors yet.
Keep the code minimal, typed, and cron-safe.
```

## Recommended near-term source priorities

1. Reddit
2. Hacker News
3. Product Hunt / adjacent launch-comment sources
4. optional X listener
5. optional public creator / teacher communities

## Final build principle

This agent should behave less like a “social autoposter” and more like a **market intelligence and copy recommendation system**.

That is the right fit for Quizly at this stage: find where attention already exists, decide where the product actually belongs, and draft channel-specific copy for human use.


# Steps


## 1 — Project skeleton

```text
Read marketing/social_scanner/CLAUDE.md and create the initial project structure.

Create:

marketing/social_scanner/
  src/
    main.py
    pipeline.py
    models.py
    settings.py
  collectors/
    reddit.py
  claude/
    evaluate.py
  render/
    html.py
  tests/
    test_models.py

Implement:
- basic settings loader
- empty pipeline skeleton
- Pydantic models for ThreadItem and ClaudeDecision

Do NOT implement logic yet.
Run minimal tests to confirm imports work.

## 2 - Implement Reddit collector.

Tasks:
1. in collectors/reddit.py:
   - fetch threads using Reddit JSON endpoints (no auth required)
   - support subreddits from config
   - fetch "hot" posts
2. normalize into ThreadItem model
3. include:
   - title
   - url
   - score
   - num_comments
   - subreddit
   - content_text (selftext if present)

4. limit items per subreddit

Add test:
- mock JSON response
- verify normalization

Do NOT add Claude logic yet.

## 3 - Implement filtering and heuristic scoring.

Tasks:
1. create filtering module:
   - keyword include/exclude
   - min score OR comment threshold

2. implement relevance_score:
   formula based on:
   - score
   - comments
   - keyword density

3. integrate into pipeline:
   - collector → filter → scored items

Add tests:
- filtering behavior
- scoring consistency

Keep it simple and deterministic.

## 4 - Implement Claude evaluation layer.

Tasks:
1. create claude/evaluate.py
2. load prompt template
3. send batch of threads to Claude Sonnet
4. parse strict JSON response
5. map results back to items

Add:
- retry logic
- fallback if Claude fails

Test:
- mock Claude response
- validate parsing and mapping

Do NOT over-engineer.

## 5 - Implement HTML output.

Tasks:
1. create render/html.py
2. generate:
   marketing/social_scanner/output/index.html

Structure:
- Top opportunities (sorted by priority_score)
- By subreddit

Each item:
- title
- subreddit
- score/comments
- suggested_comment
- suggested_post
- link

Add:
- minimal CSS
- readable layout
- copy-friendly blocks

Test:
- output file exists
- contains expected sections

No frameworks, just simple HTML.


