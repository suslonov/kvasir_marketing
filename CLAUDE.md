# Social Scanner Agent (Kvasir / Quizly Marketing)

## Objective

Build a local, scheduled agent that scans social platforms (primarily Reddit),
identifies high-quality organic marketing opportunities, and produces:

1. A ranked list of threads where Quizly/Kvasir can be mentioned or promoted
2. Suggested ad/comment texts tailored to each thread
3. A local HTML report with actionable recommendations

The system is **assistive**, not autonomous:
- It suggests placements and texts
- It does NOT post automatically

---

## Core principles

### 1. Signal over volume
We are NOT scraping everything.
We are identifying:
- high engagement threads
- relevant intent (learning, books, AI, writing, curiosity)
- contexts where Quizly is a natural fit

### 2. Native tone
Suggestions must:
- feel like a real user comment
- avoid marketing language
- avoid spam patterns

### 3. Platform safety
- No automation for posting
- No evasion techniques
- Respect subreddit rules
- Prefer helpful contribution over promotion

---

## Target domains

Primary:
- Reddit

Secondary (future):
- Hacker News
- Twitter/X (optional, not required)
- niche forums (books, writing, education)

---

## High-value intent patterns

We care about threads like:
- "what should I read"
- "how to learn X"
- "any good resources for..."
- "AI tools for..."
- "interactive learning"
- "book summaries / analysis"
- "recommendations"

We do NOT care about:
- memes
- generic news reposts
- low-effort threads
- unrelated politics

---

## Pipeline overview

1. Collect threads
2. Normalize into schema
3. Filter (keyword + heuristics)
4. Score (engagement + relevance)
5. Claude evaluation:
   - should we engage?
   - how?
   - what to say?
6. Render HTML report

---

## Data model

Each thread must be normalized to:

- id
- platform ("reddit")
- subreddit
- title
- url
- author
- score (upvotes)
- num_comments
- created_at
- content_text
- tags (initial heuristic tags)
- relevance_score (heuristic)
- claude_keep (bool)
- claude_reason
- suggested_angle
- suggested_comment
- suggested_post (longer variant)
- priority_score (0–100)

---

## Reddit collector rules

- Use API (PRAW or direct HTTP JSON endpoints)
- Focus on selected subreddits:
  - r/books
  - r/suggestmeabook
  - r/writing
  - r/learnprogramming
  - r/artificial
  - r/MachineLearning
  - r/ChatGPT
  - r/education
- Sort by:
  - hot
  - new (limited)
- Limit per run:
  - max 50 threads per subreddit

---

## Filtering rules

Initial filter BEFORE Claude:
- must contain at least one include keyword
- must not contain exclude keyword
- min score OR comment threshold:
  - score > 10 OR comments > 5

---

## Claude usage

Claude Sonnet is used ONLY for:
1. relevance decision (keep/drop)
2. engagement strategy
3. generating suggested text

### Required output format (STRICT JSON)

For each item:

```json
{
  "url": "...",
  "keep": true,
  "reason": "...",
  "angle": "...",
  "suggested_comment": "...",
  "suggested_post": "...",
  "priority_score": 0-100
}

