# Promotion Strategy and Agent Recommendations

## Where to Promote (Ranked by ROI for Zero Budget)

### 1. TikTok / BookTok (HIGHEST PRIORITY)
**Why:** 200B+ views on #BookTok. Short AI chat demos have the highest viral potential of any channel. One viral video = thousands of signups.

**Content format:**
- 30-60 sec screen recordings of actual AI book conversations
- "I asked AI about the symbolism in Gatsby and..."
- "POV: You're arguing with AI about whether Heathcliff is a villain"
- "Things AI noticed in Pride and Prejudice that I missed"

**Effort:** 3-5 videos/week, 30 min each. No production quality needed -- authenticity wins on TikTok.

### 2. Reddit
**Where to post:**
- r/books, r/bookclub, r/suggestmeabook -- be helpful for 2-3 weeks before any self-promotion
- r/ChatGPT, r/artificial -- share as "cool AI project"
- r/SideProject -- supportive community for launches
- r/Teachers, r/homeschool -- pitch as educational tool

**Strategy:** Value-first. Answer questions, share reading insights. Link to Quizly only when genuinely relevant (1 in 10 posts max). Build karma first.

### 3. Product Hunt + Hacker News (One-Time Launch)
**When:** After you have 10+ polished book contests and the daily challenge mechanic.
**Product Hunt:** Coordinate 20-30 early supporters to upvote morning of launch.
**Hacker News:** "Show HN: I built an AI that quizzes you on classic literature and argues about the characters."

**Expected:** 100-300 signups in 1-2 days.

### 4. Twitter/X
**Strategy:** Build-in-public approach.
- Share development updates, interesting AI conversation screenshots
- Engage with #BookTwitter, AI Twitter, EdTech Twitter
- Weekly threads: "10 things AI said about [Book] that surprised me"

### 5. Telegram
Already have a channel (t.me/quizly_kvasir). Use it for:
- New contest announcements
- Daily challenge results
- Community building with existing Russian-speaking audience

### 6. Teacher/Book Club Outreach (Direct)
- Email/DM 50+ teachers and book club leaders
- Offer free premium access
- Each brings 10-30 members
- Find them via: r/Teachers, Facebook teacher groups, BookClubs.com, local library contacts

## Agent Infrastructure Recommendations

### Agent 1: Social Media Content Agent
**Purpose:** Generate daily social media content from platform data.
**How it works:**
- Takes a book/game from the platform
- Generates 3-5 TikTok video scripts (screen recording prompts)
- Generates 1 Twitter thread
- Generates 1 Reddit-style discussion post
- Outputs to a content queue for human review before posting

**Implementation:** Python script using Claude API. Input: book title + game description. Output: formatted content for each platform.

### Agent 2: Community Monitoring Agent
**Purpose:** Track mentions and opportunities across platforms.
**How it works:**
- Monitors Reddit (via Reddit API) for posts mentioning: "AI book", "book quiz", "literature quiz", "book club tool", "AI reading"
- Monitors Twitter/X for relevant keywords
- Alerts when there's a good opportunity to comment/engage
- Outputs daily digest of opportunities

**Implementation:** Python script with Reddit API (PRAW) + Twitter API. Runs on cron schedule. Sends digest to Telegram.

### Agent 3: SEO Content Generator
**Purpose:** Generate SEO-optimized pages for high-value search terms.
**How it works:**
- For each book on the platform, generates:
  - "[Book] discussion questions" page
  - "[Book] quiz" landing page
  - "[Book] characters explained" page
- These are static HTML pages that rank for evergreen search terms
- Each page links to the corresponding Quizly game/contest

**Implementation:** Python script using Claude API. Generates HTML files for deployment to S3.

### Agent 4: Outreach Agent
**Purpose:** Find and draft outreach messages to teachers, book club leaders, and micro-influencers.
**How it works:**
- Searches for teacher blogs, book club websites, BookTok creators (1K-50K followers)
- Generates personalized outreach messages mentioning their specific content
- Outputs a spreadsheet of contacts + drafted messages for human review

**Implementation:** Web scraping + Claude API for message generation.

### Agent 5: Analytics Digest Agent
**Purpose:** Weekly summary of key metrics.
**How it works:**
- Pulls data from: Google Search Console, CloudWatch, database (signups, games played)
- Generates weekly markdown report: traffic trends, top-performing games, signup funnel, SEO rankings
- Posts to Telegram channel

**Implementation:** Python script combining GSC API + AWS CloudWatch + MySQL queries.

## Prioritized Agent Build Order

1. **Social Media Content Agent** -- immediate impact, generates daily content
2. **SEO Content Generator** -- compounds over time, set-and-forget
3. **Community Monitoring Agent** -- finds opportunities you'd otherwise miss
4. **Analytics Digest Agent** -- informs strategy decisions
5. **Outreach Agent** -- supports teacher/leader acquisition

## Weekly Promotion Routine (10 hrs/week)

| Day | Activity | Time |
|-----|---------|------|
| Mon | Review agent-generated content, post to TikTok + Twitter | 1.5 hrs |
| Tue | Reddit engagement (answer questions, join discussions) | 2 hrs |
| Wed | Create 2-3 TikTok videos (screen recording + voiceover) | 2 hrs |
| Thu | Teacher/book club outreach (5-10 personalized messages) | 1.5 hrs |
| Fri | Post weekly Twitter thread, schedule weekend content | 1.5 hrs |
| Sat | Write one Reddit post or guest article | 1.5 hrs |

## Success Metrics

Track weekly:
- **Signups** -- the core metric
- **Games played** -- engagement depth
- **Shares** -- viral loop health
- **Google impressions** -- SEO progress (via GSC)
- **Reddit/social mentions** -- community growth
- **Teacher/leader signups** -- multiplier channel
