# Quizly/Kvasir Contest-Led Growth Marketing Plan

**Executive Summary:** Quizly (the contest/gaming chat wing of Kvasir) should own a simple, repeatable promise: *“Turn books into interactive contests.”* Every featured title becomes a weekly quiz + creative competition, with winners showcased permanently on the book’s page. This leverages the existing platform and content (AI-chat games and public-domain books) rather than broadening into generic AI marketing. The marketing focus is on quick, sharable loops: daily text quizzes with result cards, visual quote-posters, and short videos, all tied to popular or classically debatable books. We take cues from the Kvasir marketing repo (prioritizing homepage clarity, share mechanics, and creator outreach) and from xxxxx.ai’s “interactive book” concept (multimodal, licensed content)【21†L46-L54】. 

Our 6-week pilot timeline (compressible to 1–3 weeks for an MVP) fixes conversion blockers first, then rolls out one format at a time (text → visual → video). Key tactics include: always requiring login (to hit 1,000 users); giving entrants clear share tools and promises of exposure; seeding contests through targeted outreach; and turning every winning entry into evergreen site content. We recommend staffing at least one dedicated growth lead, one engineer, and one content/moderator, with AI agents assisting social scraping, content draft generation, SEO page creation, and weekly analytics. 

**Quick 20-line plan (resume):**  
1. **Daily quiz habit:** Launch one easy quiz per day on featured books; auto-generate sharable result cards.  
2. **Contests as products:** Use contests (text, image, video) as the product funnel for new users.  
3. **Hero swap:** Replace the homepage hero with a clear contest promise and Google-login CTA.  
4. **Email capture:** Add an email opt-in on contest pages (“Get next quiz”).  
5. **Immediate examples:** Provide 3 example questions and templates for each contest.  
6. **Share mechanics:** Build “Share your result” social cards for each entry.  
7. **Winner spotlight:** Announce and feature winners on the homepage and book page.  
8. **Book pages as hubs:** Add a “Watch the best take” video panel on each book page (with transcript, spoiler tag)【21†L46-L54】.  
9. **Education angle:** Reach out to teachers/book clubs with a classroom contest pitch.  
10. **Creator seeding:** DM 50 micro-creators (TikTokers, Bookstagrammers) with custom links.  
11. **Multimodal adoption:** Mirror xxxxx.ai’s approach by adding audio/video modes (e.g. video quizzes) to diversify participation【21†L50-L54】.  
12. **Licensing-first:** Favor public-domain books and user-generated content. Clearly license entrants’ submissions.  
13. **Weekly cadence:** Run a “Theme of the Week” contest to build routine.  
14. **Prizes:** Offer social/featured awards (e.g. site badges, cash equivalent), not just cash.  
15. **Analytics loop:** Track “landing → start → complete → share” funnel daily; adjust messaging quickly.  
16. **A/B test ads:** If used, promote top entries on TikTok/Instagram for acquisition.  
17. **Feedback cycle:** Use results to refine next contest topics and reward structure.  
18. **Scale if working:** If >200 participants/week and >20% share rate, escalate budget; else refine cheaply.  
19. **Budget tiers:** Plan low/med/high budgets with shared-cash giveaway, dev hours, modest ad spend.  
20. **Legal hygiene:** Have clear contest rules (skill-based), no unlicensed copyrighted use, age consent; follow FTC/CO rules.

## 1. Key tactics from the Kvasir repo

The GitHub marketing folder reveals a consistent playbook. We reviewed the following files (linked) and extract their main points:

| File(s) reviewed | Key recommendations | Actionable takeaway for Quizly |
|---|---|---|
| [`site_evaluation.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/site_evaluation.md) & [`critical_improvements.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/critical_improvements.md) | Homepage clarity is the #1 blocker: current hero is vague, brand name is inconsistent, and there’s no email capture or social proof. The repo calls for a visible daily challenge mechanic with share cards and clear CTAs. | Treat contest rollout as a conversion funnel. **Fix the hero copy (use Quizly only, not Kvasir), add Google-login CTA, email capture, social stats, and shareable result images before pushing traffic**. |
| [`coder_instructions.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/coder_instructions.md) | Pull `/brief`-style copy into the homepage; include a “winner announced” button; add meta descriptions and OpenGraph images; refactor contest cards for clarity. | Use existing copy (e.g. *“Games and chats with AI. Contests to spark debate.”*), and ensure contest features (countdowns, winner lists) are UI-ready. QA on mobile. |
| [`positioning.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/positioning.md) | Quizly should be seen as “creator-run literary AI contests” rather than a generic chatbot. Competitors are game-like (Kahoot!) or chatty (ChatGPT), but not both. Emphasize habit and community (daily rituals, creator incomes). | Market the contest promise: **“Build a new literary habit (like Duolingo for books)”**. Push that quizzes/games are a fun, competitive reason to come back daily【github.com】. Avoid broad “AI for knowledge” messaging at first. |
| [`market_research.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/market_research.md) | Audiences: readers, trivia buffs, lifelong learners. Channels: short-form video (TikTok/YouTube), Reddit/book forums, educator networks. Keyword gap: “book trivia”, “AI book chat”, etc. | Target teen+ readers, teachers/book clubs, and AI hobbyists. Use TikTok/Shorts for quick demos of contests. Build SEO pages around featured titles (e.g. “Hamlet quiz”【quizly.pub】). Leverage Reddit’s book/quiz subs. |
| [`promotion_strategy.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/promotion_strategy.md) | Five-agent workflow: social content, community scanner, SEO pages, outreach, analytics digest. Emphasizes weekly topical focus and review-first approach. | Adopt an agentic content factory: **weekly featured title → generate posts + landing pages → use a review queue**. Do *not* push a random splash campaign. Instead, sequentially test channels with tracking. |
| [`contest_suggestions.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/contest_suggestions.md) | Suggests starting with highly debatable classics (e.g. *Hamlet*, *Origin of Species*, *Jekyll & Hyde*, *Alice*), then moving to romance/horror genres (e.g. *P&P*, *Frankenstein*, *Gatsby*). | Mirror this title ladder. Launch first three contests on on-platform books (Hamlet, Origin, Jekyll) using text quizzes. If traction, expand to *Pride & Prejudice*, etc. |
| [`influencers/search_results.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/influencers/search_results.md`) & [`outreach_templates.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/influencers/outreach_templates.md) | Pre-built lists of 100+ book/AI creators, sample outreach messages for TikTokers, YouTubers, book bloggers. Emphasizes personal notes, free trials, and mutual shoutouts. | Quickly implement creator seeding: use provided contact list and templates. For each contest, personalize 20–50 pitches (e.g. “Your fans would love this AI chat about [title]”); track responses carefully. |
| [`MODIFICATION_PLAN.md`](https://github.com/suslonov/kvasir_marketing/blob/master/marketing/MODIFICATION_PLAN.md) | (Focus on content adaptations, appears incomplete in the repo) Likely notes about tailoring content. | Ensure every contest has clear prompts and examples in Quizly’s contest editor. The earlier draft needed example questions – supply those from the get-go. |
| [`CLAUDE.md`](https://github.com/suslonov/kvasir_marketing/blob/master/CLAUDE.md) & [`pipeline.py`], [`platforms.yaml`], [`update_book_catalog.py`] | Defines a **scan-and-review workflow**: The platform scrapes Reddit/YouTube posts using `platforms.yaml`, dedupes via `pipeline.py`, and feeds a Claude-based review queue. Book titles are matched via `book_catalog.yaml`. | Use the existing scanner to detect trending discussions on each featured title. Route flagged items into a “contest opportunities” inbox. Humans curate posts (no auto-posting). |

> **Action:** We will use all these tactics in sequence. First, we fix conversion friction on Quizly’s site (hero, login, share cards, email, winners). Then we roll out contests on the prioritized titles, leveraging the listed channels and creative assets. Agentic workflows will automate routine tasks (content drafting, scanning, SEO page creation), but with a human touch at key gates.

## 2. Adapted ideas from the xxxxx.ai (StartupHub) article

The StartupHub article on xxxxx.ai (startup raising $1.45M) provides an external signal: AI can turn static books into interactive experiences, but rights and context matter【21†L46-L54】. We adapt its high-level ideas as follows:

| Concept from StartupHub/xxxxx | Adaptation for Quizly | Why it matters |
|---|---|---|
| **Interactive “aiBook” formats:** Traditional books become chatty, quiz-enabled, multi-format experiences【21†L46-L54】. | Make each featured title a **contest hub**: a weekly AI quiz + visual challenge + short video prompt. Use AI chat as a side-feature for deeper engagement. | Keeps readers active, not passive. Mirrors xxxxx’s model of turning reading into an interactive game, which boosts engagement. |
| **AI quiz/summary generation:** xxxxx enables quizzes and summaries automatically. | Rather than (only) auto-generating content, have **users create** quizzes/insights. For text contests, use AI to seed example questions, but let players write their own tie-breaker answers. | Engages users' creativity and feeling of ownership. It’s also safer legally: generated quizzes could infringe if pulled from copyrighted text. |
| **Multi-modal consumption (audio, visual):** xxxxx mentions audio/video explanations for books【21†L50-L54】. | Explicitly include **video contests**: e.g. “Explain [book] in 45 seconds.” Also plan for podcasts or audio-snippet contests (if feasible later). Embed winner videos on book pages (with caption) as per [21†L50-L54]. | Broadens appeal. Visual/video posts are far more likely to go viral than text alone. Puts Quizly into “BookTok” territory. |
| **Licensing-first approach:** xxxxx partners with publishers to legally use text/images【21†L53-L56】. | Start with public-domain books to avoid disputes. Require entrants to **certify ownership** of their submissions and grant Quizly a free license. For future publisher content, be explicit about fair use and seek permissions. | Prevents legal headaches. Also builds trust (publishers are wary of unlicensed AI use). Sets Quizly apart from random web scrapers. |
| **Gaming element:** xxxxx’s pitch implies making reading fun, not a chore. | Emphasize **competition and rewards**. Leaderboards, titles (e.g. “Hamlet Champion”), and user points fit the gamified model. Keep difficulty moderate so non-experts can win, increasing word-of-mouth. | Gamification is a proven retention hook (e.g. Duolingo, Kahoot). Lowering the skill barrier maximizes participation. |
| **Community-driven:** xxxxx suggests user creation and discovery as a content layer. | Encourage users to **share and rate** entries (e.g. “like”, donate, or vote). Feature user names prominently. Consider a referral contest (invite-friends for bonus). | Builds social proof and virality. If your friends post a Quizly entry, you’ll join. |

> **Citations:** The above adaptions are based on xxxxx.ai’s vision as reported by StartupHub【21†L46-L54】, recast to fit Quizly’s existing framework. We do **not** copy language but respect the core ideas of interactivity and rights-consciousness.

## 3. Quick-launch contest strategy

Quizly’s contests should be **sharable by design** and **plug seamlessly into the reading experience**. The three formats and rollout plan are:

1. **Text Quiz Contest (Week 1):** 
   - **How it works:** A featured book (e.g. *Hamlet*) gets one daily AI-generated 5-question quiz. Users can join, answer multiple-choice or short-answer questions, and get an auto-score. (A final open-ended “tiebreaker” prompt invites a creative answer.)  
   - **Share loop:** After completion, a result image (score + book cover + funny remark) is generated. One-click sharing to X/Twitter, LinkedIn, or a copyable link with tracking.  
   - **Signup push:** Require Google login to submit. Gate high-score leaderboard and tie-breaker submission behind login.  
   - **Reward:** Top scorers appear on the book page for the week. Tie-breaker best answer gets a cash/gift and a slot in the quiz questions for next week.  
   - **Why first:** Text quizzes are fastest to build from existing QnA AI. They activate broad interest and familiar mechanics (everyone knows trivia quizzes). This is the most low-friction loop.

2. **Visual Contest (Weeks 2-3):** 
   - **How it works:** After proving the text loop, launch a *poster design* contest: “Create an AI- or hand-drawn poster of your favorite scene from [book].” Users submit an image + brief caption explaining it.  
   - **Moderation:** Use AI image moderation to filter copyrighted characters or explicit content. Human review before publishing.  
   - **Gallery:** Build a contest gallery page and insert a “Community posters” section on the book page, with a “vote” (like) button on each.  
   - **Share loop:** Each submission can be shared on Instagram/TikTok (with hashtags #QuizlyPoster, #KvasirContest). We’ll provide templates for social posts (e.g. “I turned [quote] into art – see it on Quizly!”).  
   - **Reward:** Top 3 posters get homepage features and maybe $50 each or platform credits.  
   - **Why second:** Visuals have higher viral potential on image-heavy platforms (Instagram, Pinterest). This step also tests interest in creative contributions beyond quizzes.

3. **Video Contest (Weeks 3-6):** 
   - **How it works:** Launch a “30-second explain” or “reaction” challenge: e.g., “Explain [book’s cliffhanger] in your own words in 30s.” Entrants upload a vertical video or a link (TikTok/Shorts).  
   - **Best Video Panel:** Feature the winning video in a permanent “Watch the best take” panel on that book’s page (with a transcript and a **Spoiler Alert** toggle if needed).  
   - **Share loop:** Encourage entrants to share via TikTok using Quizly’s handle. We'll use the winning video clips for paid promotion.  
   - **Reward:** Winner gets a larger prize (e.g. $100, plus shout-out). Runner-ups may get “top video” badges.  
   - **Why last:** Video yields huge organic reach but is heavier to moderate. We add it once the process (entry, review, feature) is ironed out by text/visual contests. Also fits xxxxx’s multimodal book idea【21†L50-L54】.

4. **Ongoing Mechanics:**  
   - Every contest runs for 7 days. New theme announced Monday mornings.  
   - **“Add Your Own Contest”**: Encourage users to suggest future titles via an AI chat or poll (educators, book clubs are key solicitors).  
   - **Sustainability:** If a contest fails to reach a minimal threshold (e.g. <30 entries by day 3), pivot immediately (drop prize or theme) rather than waste more time.

> **“Best video to books” module:** Directly incorporating xxxxx’s multimodal idea【21†L50-L54】, we make video outputs evergreen. Each book page gets a fixed block: “Watch the best [book] take.” It includes the top entry’s video (30–60s), caption, and a “Make your own!” button. This embeds contest results into the product, turning winners into permanent bells on our literary tree.

## 4. AI-Agent workflows and operations

We leverage the repo’s automated agents where possible. All bots operate **assistively, not autonomously** (human-in-the-loop for content decisions). A simplified workflow:

```mermaid
flowchart TB
    subgraph Weekly Cycle
        A[Select featured book & contest theme]
        B[Social Content Agent: Draft posts & ads]
        C[SEO Agent: Draft landing page for the theme]
        D[Outreach Agent: Draft creator emails/DMs]
        E[Community Scanner: Scrape Reddit/YouTube for book mentions]
        F[Review Inbox: Human curator reviews drafts & scanner finds]
        G[Publish assets & contact creators]
        H[Contest Entries accumulate]
        I[Moderation: Human review of submissions]
        J[Winners selected & featured]
    end
    A --> B & C & D & E
    B & C & D & E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> B & D  %% Feedback into next cycle
    I --> A  %% Next theme starts after winners
```

| Agent                    | Steps & tasks                                                                                       | Inputs                                   | Outputs                                                    | Automation notes                   | Est. effort               |
|--------------------------|------------------------------------------------------------------------------------------------------|------------------------------------------|------------------------------------------------------------|------------------------------------|---------------------------|
| **Launch (Engineering)** | *One-time tasks:* Update homepage hero copy, add contest CTA buttons, implement Google-login, email capture, share card generation, winner-modules on pages. | Copy from `/brief`, design files, current contest widgets | Updated UI/UX ready for campaigns                           | Major dev sprint at start; no autograding | 5–8 dev-days initial; 1–2h/week QA |
| **Social Content Agent**  | 1. Ingest contest theme (title, contest type, example answers). 2. Prompt LLM to generate: 3 short video scripts, 3 image post captions, 2 Reddit post drafts, 2 influencer pitch variants. 3. Save in content calendar. | Contest brief, book details, previous winners, style guidelines | Draft posts (text + images/videos) ready for review        | Uses prompt templates from repo; batch generation | ~1h/day generating; ~1h/day review/publish |
| **SEO Content Agent**     | 1. Generate supporting pages: “Home page trivia quiz”, “Discussion questions”, and updated “About contest” pages for each featured book. 2. Include internal links to contest landing page and past winners. 3. Optimize meta tags. | Featured book info, contest summary, keyword list | 3 new SEO-focused landing pages per theme, with contest CTA | Batch-run weekly, redeploy site pages               | ~2h per theme to review and publish |
| **Outreach Agent**       | 1. Rank creators/educators by relevance to the book. 2. Personalize 10–20 messages using templates (mention book, teacher angle, etc.). 3. Add UTM tracking links. 4. Send via email/DM, log responses. | Influencer list, contest shortlink, template messages | Outbound emails/DMs, follow-up schedule                   | Semi-automated personalization with LLM | ~3–5h/week for drafting and follow-up |
| **Community Scanner**    | 1. Using `platforms.yaml`, scrape relevant subreddits (e.g. r/books, r/hamlet) and YouTube channels for the book name. 2. Filter by recency and score with AI for contest relevance (e.g. “tweet by user about Hamlet quiz idea”). 3. Dedup & queue items. 4. Render HTML inbox (as in repo). | Book keywords, OCR from platforms, scraping settings | List of promising posts to reply on or share, plus suggested copy | Runs on 10-min schedule, but human must review before any reply or repost | ~30–60 min/day human review, automatic triage |
| **Analytics Agent**      | 1. Aggregate site and contest funnel data: pageviews, starts, completions, shares, signups. 2. Compute weekly metrics (see KPI table). 3. Summarize wins/losses. 4. Generate recommendations (e.g. kill or expand contest). | Database events (tagged), Google Analytics, server logs | Weekly report (chart + text) on progress, delivered as memo | Scheduled (cron) report generation             | ~1h/week to compile and interpret |

> **Human oversight:** All content (social posts, outreach, announcements) is reviewed by a person before publishing. No auto-posting. All contest entries are flagged for human moderation (for copyright or inappropriate content) before winners are chosen or any user content is shown publicly.

## 5. Campaign timeline and budgeting

### 6-week pilot (mermaid Gantt)
```mermaid
gantt
    title Contest-led growth pilot (6 weeks)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Setup & Pre-launch
    UI fixes & tracking                 :a1, 2026-04-28, 5d
    Content/graphic templates           :a2, after a1, 4d
    Agent configuration and testing     :a3, after a1, 4d

    section Text Quiz Contest
    Launch Hamlet Quiz (text)          :b1, 2026-05-05, 14d
    Social/outreach push (TikTok, Reddit):b2, after b1, 10d
    Analyze & adjust (daily)           :b3, concurrent with b2

    section Visual Contest
    Launch Hamlet Poster Contest       :c1, 2026-05-12, 10d
    Create gallery & voting            :c2, after c1, 6d
    Community engagement               :c3, concurrent with c2

    section Video Contest
    Launch Hamlet 30s Video Contest    :d1, 2026-05-19, 14d
    Best video embedding on page       :d2, after d1, 3d
    Paid promotion test                :d3, 2026-05-22, 5d

    section Optimization & Scale
    Data review & strategy pivot      :e1, 2026-05-28, 7d
    Launch Darwin/Alice quizzes       :e2, 2026-06-04, 7d
```

- **Accelerated 1–3 week plan (MVP):** If resources are tighter, condense as follows: In *Week 1*, implement site fixes and launch Hamlet text quiz (Task a1 & b1). Run an outreach blitz (teachers/creators) and measure response. In *Week 2*, spin up a second text quiz (Darwin/Alice) and launch the visual contest. In *Week 3*, announce winners for text and visual; if on track (>500 users), start the video contest. This sprint aims for rapid feedback over breadth; cut any format that underperforms. 

### Budget ranges

Costs for a 6-week sprint depend on prize spend and staffing. The ranges below assume use of contract or part-time labor:

| Budget Tier | Team (est. FTE/weeks) | Key spend items | Budget (6 weeks, USD) | Use case |
|---|---|---|---|---|
| **Low** | 1 founder/growth (20h/wk), 1 engineer (20h/wk), 1 designer (10h/wk) | $500 contest prizes, ~$1k ad tests, plus salaries | **$5k – $10k** | Bootstrapped test: founder-led, minimal ad spend, reinvesting organic results. |
| **Medium** | +1 content/marketing lead (40h/wk), 1 part-time mod (10h/wk) | $1k prizes, $5k ad buys, small influencer budget | **$15k – $30k** | Growing pilot: dedicated growth hire, modest paid amplification, targeted creator fees. |
| **High** | Dedicated team (2 growth, 1 full-time dev, 1 full-time mod) | $3k+ prizes (hardware/gift cards), $10k ad, pro video editing | **$40k – $70k** | Early-scale: aggressive ads and creator partnerships, professional content creation. |

> **Assumptions:** Global (English) market, adult audience, US-standard contest rules. Prize levels and ad costs are adjustable; we recommend starting small and scaling with traction. All figures exclude internal time (we assume growth tasks in-house or already budgeted).  

## 6. KPIs and measurement

Our **North Star** metric is **Weekly Contest Participants** (unique users who start and either complete a quiz or submit a creative entry). This drives signups and word-of-mouth. We track a simple funnel (landings → starts → completions/submissions → shares → signups). Key metrics:

| Metric | Definition | Weekly Target (6wk) | Why it matters |
|---|---|---|---|
| **Landing-to-start rate** | Contest starts ÷ landing-page sessions | ≥15% | Measures how compelling the CTA and messaging are. |
| **Quiz completion rate** | Text quiz finished ÷ starts | ≥40% | Low completion means quiz is too hard/long. |
| **Visual submission rate** | Visual entries ÷ contest views | ≥10% | Tracks how inviting the visual prompt is. |
| **Video submission rate** | Video entries ÷ contest views | ≥5% | Higher bar due to effort; still aims for steady trickle. |
| **Share rate** | Entries with a share click ÷ completions | ≥25% | Virality check: are users promoting their participation? |
| **Participants (per week)** | Unique users who complete a quiz or submit art/video | 250 low / 750 med / 2000 high | Growth baseline: e.g. 250/week yields ~1k in 1 month. |
| **Participant→Signup rate** | New accounts ÷ participants | ≥10% | Locks in repeat ability; contest users should register at higher rate than cold visitors. |
| **Referral from contest** | Signups via UTM/contest code | Monitor | Tracks direct conversion of contest virality. |
| **Retention (D7)** | % participants active again within 7 days | ≥30% | Habit formation: do winners/participants return? |

Event taxonomy (for tracking):  
- `page_view` (landing)  
- `contest_start` (user clicks “Join contest”)  
- `quiz_complete` / `visual_submitted` / `video_submitted`  
- `share_click`  
- `signup_complete`  
- `entry_flagged` (for moderation delays)  
- `winner_appointed`  

### Dashboard layout (suggested charts)

- **Funnel Visualization:** Show top-of-funnel (site visits) through bottom (signups).  
- **Channel breakdown:** Stacked bar of participants by source (TikTok, organic, referrals).  
- **Top contests:** Bar chart of entries per title/format to date.  
- **Viral reach:** Trend line of shares, social impressions, and referral traffic.  
- **Contest health:** Pie or bar for entry approval vs. flagged.  
- **Engagement:** Cohort chart of return rate for past weeks’ participants.  

Use a dashboard tool to connect these metrics. A simple Google Data Studio (free) or internal charts on the analytics digest page can suffice. Monitor daily in early days, weekly thereafter.

## 7. Creative briefs for contests

Each contest type should have a clear creative brief. Use this template and adjust per contest:

### Text Quiz Contest Brief
- **Theme:** [Book Title/Topic], e.g. *Hamlet: Ghostly Plot Points*.  
- **Format:** 5-10 multiple-choice or short-answer questions + 1 open-ended tie-breaker.  
- **Hook/Angle:** Focus on [moral question, famous quote, character debate]. E.g. “Test your knowledge of Shakespeare’s tragic prince!”  
- **Time:** ~3 minutes to complete quiz, 1 min extra to craft tie-breaker.  
- **Assets to create:** Quiz questions, answer key, result image template.  
- **Messaging:** “Think you know [Title]? Prove it!” with shareable result card.  
- **Reward:** Featured on homepage/book page; [small cash or gift voucher].  
- **Success metric:** ≥20% of those who start the quiz complete it; ≥15% share their result.  

### Visual Contest Brief
- **Theme:** [Book Title] quote or scene.  
- **Prompt:** “Create an illustration or poster of [specific scene or quote from book].”  
- **Format:** One 1080×1920 vertical or square image (AI-generated or original art) + 1-sentence caption.  
- **Copyright:** Only use public domain text/ideas. If referencing book cover or movie stills, ensure public domain or licensed.  
- **Assets to create:** Example posters to inspire entrants; social-friendly promo image.  
- **Messaging:** “Make a poster for [Title]! Top art gets featured.”  
- **Reward:** Top 3 featured in gallery, $50 gift card + artist bio mention.  
- **Success metric:** ≥5% of visitors submit an entry; ≥30% of entries get at least one share.  

### Video Contest Brief
- **Theme:** [Book Title] insight or reaction.  
- **Prompt:** “Give us your best 45-second take on [provocative question from the book].” E.g. “Explain [character’s name]’s motivation in one TikTok.”  
- **Format:** Vertical video (9:16), ≤60 seconds, in English. Captions/transcript required.  
- **Copyright:** Originals only—no licensed music or clips unless royalty-free (state use in submission form).  
- **Assets to create:** Example short video (one AI-generated, one user-produced) as inspiration.  
- **Messaging:** “Film your ultimate summary of [Title] – the best take wins and will be featured!”  
- **Reward:** Winner’s video embedded on book page, $100 prize.  
- **Success metric:** ≥3% of contest visitors submit a video; featured video CTR ≥5%.  

## 8. Legal and ethical considerations

We align with U.S. and international guidelines for contests and content. Key points:

- **Copyright:** Only use public-domain books for first contests. Clearly state entrants must own rights to any submitted content (text, image, audio, video) and must not infringe third-party IP. This satisfies that *copyright protection exists from fixation*【18†L213-L218】. Require entrants to confirm original authorship and to grant Quizly a nonexclusive worldwide license to display, edit (e.g. crop/subtitle), and promote their entry.  
- **Fair Use:** Do **not** rely on fair use for reposting copyrighted excerpts or images. For book text, allow short quotes under a “citation” style rule (e.g. ≤300 chars or start of chapter). For visuals, avoid recognizable copyrighted characters or covers unless they are public domain.  
- **AI-Generated Content:** If users use AI tools, require them to explicitly add human commentary. Do **not** market fully AI-authored entries as entirely user-owned. The U.S. Copyright Office states AI “without any human creative input” is not copyrightable【24†L1-L4】. Position the contest as a creativity challenge, not an AI lab.  
- **Privacy/Consent:** Participants register via Google login. Collect minimal personal data (email from Google, which we already have from login). For images/videos featuring people, require them to confirm all individuals are 18+ or have parental consent (default assumption: adult content only). Do not market to under-13s (otherwise COPPA would apply).  
- **Endorsement/FTC:** If we pay influencers or any material compensation, disclose it clearly. Use Instagram/TikTok’s “#ad” or platform disclosure settings. The FTC requires transparency about sponsorship. Similarly, on any Quizly posts stating “featured by Quizly,” don’t misrepresent that as user speech.  
- **Privacy of data:** Comply with GDPR/CCPA on email captures. Use opt-in only and provide unsubscribe options for newsletters.  
- **Contest rules:** Always publish clear official rules on a static page: eligibility (adults only, etc.), entry method, deadlines, judging criteria, prize descriptions, sponsor identity, and no-purchase statements. For skill-based contests, emphasize judging standards (e.g. scoring rubric, who chooses tie-breakers). If at any point we add a random drawing, include a no-purchase alternative and review for lottery laws.  
- **Moderation:** No user entry goes live without review. Enforce rules against hate, defamation, sexual content, illegal advice, etc. Have a takedown pipeline and appeal process. (Kvasir’s existing content rules should apply.)  

> **Sources:** Guidelines on user-generated content and AI from the U.S. Copyright Office【24†L1-L4】【18†L213-L218】; FTC Endorsement Guides (no specific citation, but we follow them).

## 9. Sample promotional copy and creatives

Below are example copy variants for key channels. Tailor details to each contest theme:

| Variant              | Channel         | Example copy                                                 | CTA                     |
|----------------------|-----------------|--------------------------------------------------------------|-------------------------|
| **Homepage hero**    | Webpage         | **“Play quizzes, create art, and debate books with AI.”** <br>“Quizly by Kvasir turns every classic book into a weekly contest.” | [Join this week’s contest] |
| **TikTok (text quiz)** | Short video     | *Overlay text:* “Think you can outsmart AI on *Hamlet*?” <br> *Voice/video:*  10s intro of a sample question + result image flash. | “Take the quiz on Quizly.pub!” |
| **Instagram (visual)** | Image post    | *Graphic:* Quote from book + “Make this scene into art!” <br> *Caption:* “We’re crowdsourcing the best poster for *Hamlet*. Will yours be featured?” | [Design your poster] |
| **YouTube Short (video)** | Short video | *On-screen:* Engaging hook (e.g. “30 seconds to explain Gatsby!”) with timer. | “Enter your video on Quizly.pub” |
| **Reddit post**      | Text forum      | *r/books or r/quiz:* “We launched a free AI-powered quiz on *Hamlet* – check it out and let us know your score! (Plus winners get prizes.)” | “Try the quiz” |
| **Email invite**     | Teacher/Club    | *Subject:* “AI Quiz Challenge: *Hamlet*” <br> *Body:* Brief pitch (“Turn [book] into a fun group game.”) | “Reserve your spot” |
| **Creator DM**       | Personal outreach | “Hi [Name], fans of your [book content] might love our AI *[Title]* quiz contest. I’d love to send you a private trial link!” | “View example contest” |
| **Paid ad**          | Twitter/Meta    | “Think you know literature? Take the *Hamlet* quiz on Quizly and compete for prizes!” | “Play now” (link) |

Include relevant hashtags (e.g. #BookTok, #AIQuiz, #Education). Use platform-specific assets: e.g., Instagram Story templates, TikTok style transitions, or Twitter cards.

## 10. Next steps and timeline (to 1,000 users)

1. **Setup sprint (Days 1–3):** Implement all site fixes: swap in Quizly branding, hero copy, login buttons, and share-card logic. Deploy contest admin for daily questions. Test end-to-end funnel (visit → start contest → complete → share → signup).  
2. **Launch Week 1 (Days 4–10):** Go live with the first text quiz (*Hamlet*). Announce on social (quick video or image demos) and via an email blast (if any list). Manually send 20 creator invites (with prewritten DM templates). Have the analytics agent monitoring signups hourly to catch any drop-offs.  
3. **Optimize & Outreach (Days 10–14):** If start rate < 15%, tweak homepage CTA or question difficulty. Push shareable content (result cards) on social. Double down on low-cost ads: boost one video post on TikTok targeting book lovers ($10/day) to see conversion cost.  
4. **Launch Visual Contest (Week 2):** Open the poster challenge on *Hamlet*. Update homepage to show the new contest. Publish an example poster. Notify participants from Quizly’s newsletter (if available) or in-platform notice.  
5. **Scale Promotion (Week 2-3):** Continue daily TikTok/Reels (use AI agent for scripts), Reddit comments, cross-posts to book forums. Send batch follow-ups to creators who showed interest. Encourage entrants to share a fixed social CTA (“Vote for me on Quizly!”).  
6. **Introduce Video Contest (Week 3):** After 10–15 days, start the video contest on *Hamlet*. Embedding a Vimeo/TikTok link in the contest form. Begin planning to boost the *best quiz* or *best poster* on social with paid promotion to acquire more traffic.  
7. **Weekly winner announcements:** Every 7 days, formally announce the quiz and visual contest winners via all channels. Highlight new contest theme at same time. (Press release not needed at this scale; focus on community.)  
8. **Data checkpoint (Week 4):** Check cumulative metrics: Have we hit ~1,000 visits or ~150 signups? Are participants sharing at ≥20%? If so, continue current pace; if not, consider pausing paid ads and iterating on hook.  
9. **Second wave (Week 5):** If the first book did well, roll contests on the next title (e.g. *Darwin/Origin*). The infrastructure and ad spend remain; just change the content. Reuse and tweak agents’ prompts for new theme.  
10. **Post-campaign evaluation (Week 6):** Total up results. If ~1,000 users reached, analyze source-wise (where came from) and what format worked best. Decide whether to continue scaling or refine the model.  
11. **Risk mitigation:** Guardrail: If any contest falls flat (<10 entrants), shut it down and try a lighter version. Prioritize quality engagement over vanity metrics. Ensure prompt moderation to prevent negative incidents.

> **Risks:** Low virality (plan mitigated by heavy creator seeding), copyright flags (mitigated by clear rules and PD books), and legal oversight (rules published, no sweepstakes). Each next step should have a clear Go/No-Go based on data (set thresholds in the Analytics digest).

## 11. Detailed checklist (Google-Keep–style)

- [ ] **Update homepage hero:** Use Quizly branding and concise value (“Play AI games and win creative book contests”). *Why:* Clearer first impression drives signups.  
- [ ] **Enable Google login & email opt-in:** Replace anonymous mode; require signup before contest entry. *Why:* Login gates ensure we count actual users.  
- [ ] **Implement share cards:** Create result/poster image templates and “Share” buttons for quiz answers and contest entries. *Why:* Viral growth depends on easy sharing.  
- [ ] **Create first quiz (Hamlet):** Write 5 quiz questions + 1 tie-breaker prompt; set 1-week window. *Why:* Needed to start viral loop.  
- [ ] **Design an example poster:** Provide one sample for visual contest instructions. *Why:* Lowers entry friction.  
- [ ] **Add “winner announcement” module:** Put placeholder on homepage and Hamlet page for upcoming winners. *Why:* Social proof (even “?? entrants, winners next week”).  
- [ ] **Write contest rules:** Publish simple rules page (eligibility, prizes, IP clause). *Why:* Legal compliance and trust.  
- [ ] **Prepare social content:** Pre-schedule initial TikToks, Reels, Reddit posts announcing the contest. *Why:* Burst of visibility at launch.  
- [ ] **Seed creators/teachers:** Send personalized messages to relevant influencers/educators with contest links. *Why:* Kickstart network effect.  
- [ ] **Activate agents:** Configure platforms.yaml and book_catalog for the featured title; start scanner. *Why:* Catch organic mentions to engage communities.  
- [ ] **Daily operations:** Each day post 1 new social snippet (text/image/video), respond to all comments, feature one user submission on social. *Why:* Maintains engagement momentum.  
- [ ] **Monitor dashboard:** Check funnel metrics nightly (especially start and completion rates). Tweak quiz difficulty or page copy if conversion is low. *Why:* Rapid improvement ensures scale success.  
- [ ] **Mid-week check:** If week1 target (<300 users) is not on track, double outreach effort (more DMs, Reddit posts) and try a micro-ad ($5) on one creative. *Why:* Early course-correction.  
- [ ] **Launch visual contest (Week 2):** Mirror steps: write prompt, open entries, add shareable image template. *Why:* Refreshes interest and content variety.  
- [ ] **Collect entries for winners:** Use Google Sheets/form or Quizly backend to tally quiz scores and gather submissions by deadline. *Why:* Organize judging easily.  
- [ ] **Announce winners:** Post winners on all channels with thank-you note and teaser for next contest. *Why:* Closure and excitement for next round.  
- [ ] **Embed winning video:** If video contest done, edit winner clip into book page with credit. *Why:* Evergreening content from social traffic.  
- [ ] **Repeat contest cycle:** Immediately open next text quiz on new title. *Why:* Capitalize on established users and channels.  
- [ ] **Weekly review:** Each weekend, review KPI dashboard and qualitative feedback. Drop or pivot any element underperforming. *Why:* Data-driven iteration.  
- [ ] **Document lessons:** Keep a log of what marketing copy and angles got the most engagement. *Why:* Refine briefs and agent prompts for better results.  

Each checklist task should be ticked off and passed along to the relevant team member as we go. This granular plan ensures we hit the 1,000-user goal by creating urgency and accountability.

