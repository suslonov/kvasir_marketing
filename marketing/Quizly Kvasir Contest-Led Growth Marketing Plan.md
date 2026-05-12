# Quizly / Kvasir Contest-Led Growth Marketing Plan — v2

**Version:** 2.0 (May 2026)  
**Based on:** Platform audit of quizly.pub, recent kvasir_proto commits (scenes, readings, echo-contests, share cards), and site analysis.

---

## Executive Summary

Quizly has shipped three distinct contest formats and a new Reading Hall since v1 of this plan. The product is no longer a simple quiz platform — it is a **creator-driven literary AI studio** where users build AI characters, generate short films, and read books inside a live chat environment. The marketing strategy must now reflect this breadth while keeping the entry point simple.

**Core promise (updated):** *"Turn any book into an AI game, a chat character, or a short film — then compete."*

Three contest tracks are live or near-live:

| Track | Page | What users create | AI involvement |
|---|---|---|---|
| **Chat Contest** | `echo-contest.html` | An AI character others can talk to | LLM prompt (game/quiz/discussion/mystery) |
| **Video (Scene) Contest** | `scene-contest.html` | A 2–20 sec AI-generated short video | Runway text-to-video + Flux image generation |
| **Quiz Contest** | `contest.html` | Quiz answers / creative text entries | AI scoring & moderation |

New platform pages that create additional SEO and marketing surface area:

- `scene.html` — watch a scene video (embeddable, shareable)
- `readings.html` / `readings-info.html` / `readings-tag.html` — Reading Hall (structured book reading with integrated echo chats)
- `echo-author.html` — creator profile pages (builds creator community)
- `echo-tag.html` — tag-based discovery (SEO surface)
- `share.html` — dedicated share landing page

**North Star metric (unchanged):** Weekly Contest Participants (unique users who complete or submit an entry).

**New secondary metric:** Weekly AI Creations — unique scenes or echo chat characters published by users. This measures platform stickiness beyond passive participation.

---

## 1. Updated Platform Map

### 1.1 Contest Tracks in Detail

#### Chat Contests (Echo Contests)

Users design an AI character using a system prompt. Character types supported:
- **Quiz Game** — AI tests users on a book
- **Book Discussion** — AI facilitates a literary debate
- **Mystery Adventure** — AI plays a story character
- **Multi-step Game** — progressive narrative game

Once published, any visitor can open a private chat session with the character. The contest judges on engagement quality, creativity, and (for game types) score achieved. The **Define Winner** tab lets admins nominate winners; **Artifact Awards** let the AI character hand out in-game collectibles during chats.

This is the lowest-friction contest for creators: no video production, no coding — just writing a good character prompt. It is the primary onramp for new creators.

**Marketing angle:** *"Write a character. Watch strangers fall into your story."*

#### Video / Scene Contests

Users generate a short AI video (2–20 seconds) tied to a book or lecture. The workflow:
1. Write a scene idea (≤1,000 chars)
2. Select style: Cinematic, Anime, Noir, Storybook, Documentary
3. Select video model (Runway gen4_turbo or similar) and LLM text model
4. Optionally generate a seed image via Flux first (recommended to reduce cost)
5. Optionally add TTS audio mood
6. Generate → Extract frames for title/slide thumbnails → Publish

Published scenes appear on `scene.html` with likes, donations, share button, and a link back to the book series. Winning scenes are embedded permanently on the book/course page.

**Marketing angle:** *"Describe a scene. AI shoots the film."*

#### Quiz / Text Contests

Classic quiz and open-ended text submission contests. Users answer AI-generated questions about a featured book, and the best tie-breaker answer wins. Existing infrastructure; lowest barrier for participants (no creation required).

**Marketing angle:** *"Test your knowledge. Beat the AI."*

### 1.2 Reading Hall

`readings.html` and `readings-info.html` form a structured reading environment where books are presented chapter by chapter with integrated echo chats alongside. This is an entirely new content surface.

**Marketing significance:**
- Creates long-form, returnable content (users come back to finish a book)
- Attaches echo chats organically to the reading experience (cross-sells chat contests)
- High SEO value: each book gets a canonical `/readings-info?id=X` URL indexed by chapter

**Marketing angle:** *"Read the book. Chat with the characters as you go."*

### 1.3 Creator Profiles and Discovery

`echo-author.html` gives every echo-chat creator a public profile page with their published characters. `echo-tag.html` allows tag-based browsing. These create:
- A creator community layer (bookstagrammers, educators, writers can build audiences)
- SEO landing pages for character/tag combinations (e.g. "Hamlet AI chat")
- Social sharing hooks (creators share their author page)

---

## 2. Revised Marketing Strategy

### 2.1 Three-Track Funnel

The platform now has three distinct user personas, each entering through a different track:

| Persona | Entry Point | Conversion Goal | Retention Hook |
|---|---|---|---|
| **Reader** | Reading Hall → Quiz Contest | Sign up to track reading progress | Weekly featured book; new chapters |
| **Creator** | Echo Contest editor | Publish first AI character | Audience building on author profile |
| **Filmmaker** | Scene Contest editor | Publish first AI video | Credits system; scene featured on book page |

Each track has its own promotional emphasis, but all three share one landing page (the homepage) and one conversion action (Google login).

### 2.2 Homepage Messaging (Updated)

The homepage must reflect the three tracks without overwhelming new visitors. Recommended hero structure:

**Headline:** *"Play, Create, and Win — AI contests for book lovers."*

**Three CTA tiles (below hero):**
1. "Take this week's quiz →" (Reader track, lowest friction)
2. "Design an AI character →" (Creator track)
3. "Generate a scene video →" (Filmmaker track, premium)

**Social proof strip:** Count of active echo chats, scenes published this week, current contest participants.

**Reading Hall teaser:** "Reading [Book Title] now — join 47 readers" with a "Join the reading →" CTA.

### 2.3 Content Calendar by Track

#### Reader Track (Weekly)
- Monday: Announce featured book + quiz contest opens
- Tuesday–Thursday: Daily social snippet (quote + quiz question) with share card
- Friday: "Leaderboard update" post showing top scorers
- Sunday: Winner announced, new book teased

#### Creator Track (Bi-weekly)
- "Character of the Week" spotlight on echo-author profile page
- Tutorial content: "How I built my Hamlet AI in 10 minutes"
- Creator DM campaign: target 20 writers/educators per cycle
- "Public Reading" feature: attach top-performing echo chats to the Reading Hall

#### Filmmaker Track (Monthly, during video contest windows)
- "Scene Drop" announcement with example video (show the AI output)
- Style showcase: one post per style (Cinematic, Anime, Noir, Storybook, Documentary)
- "Behind the scene" post: show the prompt → video pipeline in 30 seconds
- Winning scene embedded on book page (permanent, shareable URL)

### 2.4 Social Platform Strategy

| Platform | Primary Track | Format | Frequency |
|---|---|---|---|
| TikTok / Reels | Filmmaker | 15–30s scene clips + "Created on Quizly" watermark | 3x/week |
| Twitter / X | Reader, Creator | Quiz questions, leaderboard updates, character spotlights | Daily |
| Instagram | All three | Share cards (quiz results, scene thumbnails, character portraits) | 5x/week |
| Reddit | Reader, Creator | r/books, r/suggestmeabook, r/artificial — genuine contributions | 2–3x/week |
| YouTube Shorts | Filmmaker | Scene contest entries repurposed as Shorts | 2x/week |

#### Share Cards (Now Live)

`share-card.js` is implemented. Every contest entry and quiz result should auto-generate a card with:
- Book title + platform logo
- User score or entry preview
- Contest deadline / "Join now" CTA
- quizly.pub URL with UTM parameters

Activate share cards on: quiz completion, scene publish, echo character publish.

### 2.5 SEO Strategy (Updated with New Pages)

New pages create significant organic search surface:

| Page | Target keywords | Volume opportunity |
|---|---|---|
| `readings-info?book=hamlet` | "hamlet read online", "hamlet with commentary" | Medium |
| `echo-tag?tag=shakespeare` | "shakespeare AI chat", "talk to shakespeare character" | Low-medium |
| `scene?id=X` (book-titled) | "hamlet AI video", "pride and prejudice scene" | Low (emerging) |
| `echo-author?id=Y` | Creator name + "AI character" | Branded |
| `contest?id=Z` | "hamlet quiz contest", "book trivia contest" | Medium |

**Action:** Generate SEO-optimized `<title>` and `<meta description>` for each page type using the book/character/tag name. Add structured data (JSON-LD) for contests and videos.

---

## 3. Chat Contest — Detailed Playbook

### 3.1 What Makes a Winning Chat Contest Entry

Users create a character using the echo-contest editor. The best entries share:
- A clear persona (not "AI assistant" but "Inspector Bucket from Bleak House")
- A game mechanic (riddles, scoring, decision trees) or a discussion hook (provocative questions)
- Good first message (the opening line users see before chatting)

**Creator onboarding content needed:**
- 3 example prompts pre-loaded in the editor (Book Discussion, Quiz Game, Mystery Adventure — already in i18n)
- A "prompt guide" page or modal showing what makes a great character
- Featured examples on the contests page with the character's opening line visible before clicking

### 3.2 Chat Contest Launch Sequence

1. **Pre-launch (3 days before):** Announce contest theme (e.g. "Create an AI version of a character from *Hamlet*"). Post example character on social.
2. **Launch:** Open submissions on echo-contest editor. Share creator tutorial. DM 10 relevant creators.
3. **Mid-week:** Feature 2–3 early submissions on social ("Chat with this Hamlet character made by @username"). Drive traffic to the submission's echo-info page.
4. **Voting window (days 5–6):** Readers visit and chat with entries. Board shows live engagement events.
5. **Winner:** Use "Define Winner" tab in echo-info. Announce winner with their author profile link. Winner's character featured on the book's series page permanently.

### 3.3 Artifact Awards as Viral Mechanic

The Artifact Awards system lets AI characters hand out collectibles during chats. This is an underused viral hook:
- Make artifact names book-specific (e.g. "Yorick's Skull" for Hamlet chatters)
- Show artifact collection on user profiles
- "Collect all artifacts from Hamlet characters" creates repeat-visit motivation
- Social post: "I just got the [artifact name] from Quizly's Hamlet contest — can you beat my score?"

---

## 4. Video (Scene) Contest — Detailed Playbook

### 4.1 The Scene Creation Pipeline as Marketing Content

The scene-contest editor is itself a demo-worthy product. The workflow (write idea → AI prepares prompt → generate video) is visually compelling. Make the pipeline the ad:
- Screen-record the 3-step flow (30 seconds)
- Post as TikTok/Reel with voiceover: "I described a scene from *Hamlet*. AI generated this video in 2 minutes."
- End with the actual scene playing

This is the highest-leverage content for filmmaker acquisition. No need for elaborate production — just a clean screen capture of the tool in action.

### 4.2 Style Showcase Campaign

Five styles exist: Cinematic, Anime, Noir, Storybook, Documentary. Run a "Style Week":
- Day 1: Cinematic — "What does Hamlet look like in Hollywood?"
- Day 2: Anime — "Hamlet as a shonen anime"
- Day 3: Noir — "Hamlet as a 1940s detective story"
- Day 4: Storybook — "Hamlet for children"
- Day 5: Documentary — "Hamlet: the untold story"

Each post shows the same prompt rendered in a different style. Highly shareable. Demonstrates AI variety. Drives curiosity and contest entries.

### 4.3 Scene Contest Launch Sequence

1. **Announce (1 week before):** Post the style showcase. "Coming soon: video contest. Create a scene from [Book]. Best video wins and gets featured permanently on the book page."
2. **Launch:** Open scene-contest editor linked from the contest page. Post tutorial (screen-record workflow). Seed 2–3 staff-created example scenes in different styles.
3. **Mid-contest:** Feature community submissions. Boost 1–2 scenes on TikTok ($20 budget). Drive clicks to `scene.html` page.
4. **Frame extraction:** Encourage winners to extract frames — the first frame becomes the book's hero image.
5. **Winner embed:** Winning scene is embedded on the book/series page. Announce with creator attribution + link to their echo-author profile.

### 4.4 Credits System as Acquisition Tool

Video generation costs credits. Use this as a growth lever:
- **Free credits on signup:** New users get enough credits for 2–3 scene generations. No credit card needed.
- **Referral credits:** Invite a friend → both get bonus credits.
- **Contest entry bonus:** Submitting an entry refunds 50% of generation cost (reward participation).
- **Feature credits:** When a scene gets featured on a book page, creator gets a large credit bonus.

Communicate this clearly on the scene-contest editor and the contests page.

---

## 5. Reading Hall — Marketing Integration

### 5.1 Reading Hall as Acquisition Channel

The Reading Hall (`readings.html`) is a natural SEO and direct-traffic entry point for people who want to read books online. Once inside, they encounter:
- Echo chats linked to the book (chat with AI characters)
- Contest banners for active book contests
- "Create your own character for this book" CTA (→ echo-contest editor)

Convert readers into contestants: add a banner at chapter boundaries — "There's an active contest for this book. See entries and compete →"

### 5.2 Public Reading Events

The `echo_info` i18n includes "Public Reading" as a concept. Use this for live events:
- Announce a "Public Reading of [Book]" on a specific date/time
- Readers join the Reading Hall simultaneously
- A featured echo character is active and responding in real-time (or near-real-time)
- Artifacts are awarded during the live session
- Promote via Discord, Reddit r/books, teacher communities

This is a zero-cost community event that drives signups and reading sessions simultaneously.

### 5.3 SEO-Driven Reading Hall Expansion

Each readings-info page should target specific keyword clusters:
- "[Book title] read online free"
- "[Book title] summary by chapter"
- "[Book title] discussion questions"

Add a "Contest for this book" widget to every readings-info page. This cross-links organic search traffic into the contest funnel.

---

## 6. Multi-Language Strategy (en / ru / he)

The platform now supports English, Russian, and Hebrew. This opens three distinct geographic markets:

| Language | Target communities | Contest theme approach |
|---|---|---|
| English | BookTok, r/books, educator networks (US/UK/AU) | Classic English literature (Hamlet, Dickens, Austen) |
| Russian | Russian literature communities, Telegram book groups, VK | Pushkin, Tolstoy, Dostoevsky, Bulgakov |
| Hebrew | Israeli education market, Ben-Gurion era literature | Agnon, Bialik, Alterman; also Torah/Talmud discussion games |

Run the same contest structure in parallel across languages using the i18n system. Russian and Hebrew markets are underserved in the "AI games for books" category — first-mover advantage applies.

**Russian-specific channel:** Telegram. Create a Quizly Telegram channel for each Russian-language contest. Post contest updates, winning scenes (which embed as previews in Telegram), and character spotlights.

---

## 7. Creator Economy Plays

### 7.1 Donation System

The platform supports donations to creators (`donationsContainer`, `buttonDonate`). This enables:
- Creators monetize popular echo characters
- Donation amounts appear publicly ("$47 donated to this creator")
- Creates social proof and incentivizes quality

**Marketing:** Highlight top-earning creator each week ("This week's top Quizly creator earned $X in donations"). This attracts serious creators who want income, not just recognition.

### 7.2 Author Profiles as Creator Pages

`echo-author.html` gives creators a public page with all their published characters. Treat these like creator pages on Patreon/Substack:
- SEO-optimize them (creator name + "AI characters")
- Encourage creators to share their author page link in their social bios
- Feature 3 top creators on the homepage "Creator Spotlight" section each week

### 7.3 Creator Seeding (Updated)

The original plan called for 50 micro-creator DMs. Now target by track:

| Track | Creator type | Platform | Pitch |
|---|---|---|---|
| Chat Contest | Writers, English teachers, book bloggers | Twitter, Substack, YouTube | "Design an AI version of your favorite character and compete" |
| Video Contest | BookTok creators, AI art/video creators | TikTok, Instagram | "Turn your book take into a 10-second AI film" |
| Reading Hall | Book club organizers, educators | Reddit, Facebook groups, Discord | "Run a public reading of [book] on Quizly — free, takes 10 minutes to set up" |

---

## 8. Updated AI-Agent Workflows

All agents operate assistively (human-in-the-loop). Updated to cover new contest tracks:

| Agent | Function | New additions vs. v1 |
|---|---|---|
| **Social Content Agent** | Draft posts per track (quiz, chat, video, reading) | Scene style showcases; creator spotlights; artifact award announcements |
| **SEO Agent** | Generate landing pages for books, characters, tags | `readings-info` pages; `echo-tag` pages; `scene` embed pages |
| **Outreach Agent** | Personalized creator DMs | Separate templates per track (chat/video/reading) |
| **Community Scanner** | Reddit/HN/YouTube scraping for book mentions | Flag threads where scene contest or reading hall would fit |
| **Analytics Agent** | Weekly funnel report | Add scenes-published, echo-chars-published, credits-consumed, donations-collected |

---

## 9. Updated KPIs

### North Star
**Weekly Contest Participants** — unique users who complete a quiz, submit a scene, or publish an echo character.

### Track-Specific Metrics

| Metric | Definition | Weekly Target |
|---|---|---|
| Quiz completion rate | Finished ÷ started | ≥ 40% |
| Echo characters published | New characters submitted to a contest | ≥ 10 |
| Echo chat sessions | Unique chats started with contest characters | ≥ 100 |
| Scenes generated | Videos created via scene-contest editor | ≥ 5 |
| Scenes published | Submitted as contest entries | ≥ 3 |
| Reading Hall sessions | Unique visits to readings-info pages | ≥ 200 |
| Share card clicks | Users who shared a result/entry | ≥ 25% of completions |
| Creator profile visits | Visits to echo-author pages | ≥ 50 |
| Signup rate | New accounts ÷ unique participants | ≥ 10% |
| D7 retention | Participants active again within 7 days | ≥ 30% |
| Credits purchased | Revenue transactions | Track weekly |
| Donations received | Donations to creators | Track weekly |

### Dashboard Additions (vs. v1)

- **Creation funnel:** scene-editor-open → idea-saved → generate-clicked → scene-published → contest-submitted
- **Echo character funnel:** editor-open → prompt-written → character-saved → character-published → chats-received
- **Reading Hall funnel:** readings-page-view → chapter-read → echo-chat-opened → contest-banner-clicked
- **Credits flow:** credits-given (signup/referral) → credits-spent (generation) → credits-purchased

---

## 10. Revised Timeline

### Weeks 1–2: Foundation (same as v1, extended)
- Ship homepage with three-track CTA tiles
- Enable share cards on all three contest entry types
- Publish credits-on-signup flow
- Launch first quiz contest (existing)
- Launch first chat contest alongside quiz contest

### Weeks 3–4: Video Track Activation
- Run style showcase campaign (5 posts over 5 days)
- Open first scene-video contest (linked to same book as chat contest)
- Screen-record scene-creation tutorial — post to TikTok
- Seed 2–3 example scenes in different styles

### Weeks 5–6: Reading Hall and Creator Economy
- Feature a "Public Reading" event for the top book
- Promote creator author profiles
- Highlight donation earnings of top creator
- Expand to second book (Russian or Hebrew language market)

### Week 7+: Scale and Repeat
- Run three tracks simultaneously for two different books
- A/B test homepage hero variants
- Launch Telegram channel for Russian-language market
- Negotiate first educator partnership for Reading Hall

---

## 11. Creative Briefs (Updated)

### Chat Contest Brief

- **Theme:** [Book Title] — e.g., *Hamlet: Design Ophelia's AI Ghost*
- **Prompt:** "Create an AI character from [Book]. It can be a quiz master, a storyteller, or a debate partner."
- **Editor link:** `scene-contest.html?contest=[ID]` → No, `echo-contest.html?contest=[ID]`
- **Format:** System prompt + character name + opening message + optional avatar
- **Artifacts:** Name 3 book-specific artifacts the character can award (e.g., "Yorick's Skull", "Denmark Crown", "Poison Vial")
- **Reward:** Featured on book page + author profile spotlight + $50 or credits
- **Success metric:** ≥ 5 chat sessions per submitted character, ≥ 10 characters submitted

### Video (Scene) Contest Brief

- **Theme:** [Book Title] + [Scene moment] — e.g., *Hamlet: The Ghost Scene*
- **Prompt:** "Generate a 5–15 second scene from [Book]. Any style. Best video gets embedded on the book page forever."
- **Recommended workflow:** Generate seed image first → pick from gallery → generate video
- **Styles available:** Cinematic, Anime, Noir, Storybook, Documentary
- **Copyright:** Public-domain books only. User owns AI output; grants Quizly display license.
- **Reward:** Winning scene embedded on book page + $100 + creator profile featured + large credit bonus
- **Success metric:** ≥ 3 scenes submitted, featured scene CTR ≥ 5%

### Reading Hall Event Brief

- **Book:** [Public domain title with active echo chats]
- **Format:** Readers follow chapters on `readings-info` page; echo characters are active alongside
- **Duration:** 1-week reading window; live event on day 4
- **Promotion:** Reddit r/books post, Discord book servers, educator email
- **Goal:** ≥ 50 reading sessions, ≥ 20 echo chat interactions during live event
- **Reward:** Top reader (most chapters + most chat interactions) gets platform badge and credit bonus

---

## 12. Legal and Safety (Updated)

All points from v1 carry forward. Additions for new tracks:

**AI-Generated Video:**
- Scenes use public-domain book themes. No copyrighted film clips or music in prompts.
- TTS audio must not mimic specific living people's voices.
- Users grant Quizly a worldwide, nonexclusive license to display, promote, and embed their generated scenes.
- Scenes go through publish-gating (the `publishToggleBtn` is explicit user action, not auto-publish).

**Echo Chat Characters:**
- Characters must not impersonate real living people by name.
- System prompts are reviewed before public visibility (premoderation flag exists in echo-info).
- Artifact names must not contain trademarks or offensive language.
- Chat logs are not stored publicly; only the character prompt is visible to others.

**Reading Hall:**
- Only public-domain texts in the Reading Hall.
- Chapter content attribution required.
- Echo chats linked to readings fall under the same moderation rules as standalone echo chats.

**Credits:**
- Credits are a prepaid service, not a currency. No refunds on consumed credits. Clear price display before generation.
- Generation cost shown explicitly before user clicks "Generate" (`credits_line` i18n string is live).

---

## 13. Checklist (v2)

### Infrastructure (Engineering)
- [ ] Activate share cards on scene publish, echo-char publish, quiz completion
- [ ] Add UTM parameters to all share card URLs
- [ ] Free credits on signup flow (amount TBD)
- [ ] Referral credits link generation
- [ ] Contest-entry credits refund (50% refund on scene submission)
- [ ] Add contest banner to readings-info pages for active contests
- [ ] SEO: `<title>`, `<meta description>`, JSON-LD for all new page types
- [ ] Homepage: three-track CTA tiles + social proof strip

### Content
- [ ] Write 3 example echo-character prompts for Hamlet (Quiz, Discussion, Mystery)
- [ ] Create 5 example scenes (one per style) for Hamlet — staff-generated
- [ ] Screen-record scene-creation tutorial (30 seconds)
- [ ] Publish style showcase campaign posts (5 posts)
- [ ] Set up Telegram channel for Russian-language market

### Outreach
- [ ] 20 creator DMs — chat contest (writers/educators)
- [ ] 20 creator DMs — video contest (BookTok/AI creators)
- [ ] 5 educator/book-club outreach emails — Reading Hall
- [ ] Reddit post: r/books, r/artificial (genuine, helpful framing)

### Operations
- [ ] Configure community scanner for Hamlet + Darwin keywords
- [ ] Schedule weekly analytics digest
- [ ] Set up "Character of the Week" spotlight post template
- [ ] Define artifact names for first chat contest (3 artifacts)
- [ ] Confirm moderation workflow for scenes and echo chats before public launch

---

## 14. Risks and Mitigations (Updated)

| Risk | Likelihood | Mitigation |
|---|---|---|
| Low video contest entries (high barrier) | Medium | Staff-seed 3 examples; show pipeline demo; reduce credits cost for first contest |
| AI-generated videos look low-quality | Medium | Emphasize Storybook/Anime styles (forgiving aesthetics); "lo-fi is the aesthetic" |
| Echo characters feel repetitive or dull | Medium | Publish creator guide; pre-load 3 high-quality example prompts in the editor |
| Reading Hall not discovered organically | High | SEO + Reddit promotion critical; add internal links from all book pages |
| Credits system confuses users | Low-Medium | Show cost clearly before generation; free credits eliminate first-use friction |
| Moderation overhead (scenes + chats) | Medium | Publish-gate flow (manual publish button) ensures no auto-publishing; queue moderation |
| Russian/Hebrew market launch stalls | Low | Start with single contest; Telegram channel is low-cost to set up and test |

---

*This plan supersedes v1. Review and update monthly as new features ship.*

---

## 15. Google Search Visibility — Quick Wins

*(Added May 2026. Reflects updates already applied to HTML/JS.)*

### 15.1 What Was Done (Technical)

All public-facing pages on `quizly.pub` now have consistent `<meta description>`, Open Graph, and Twitter Card tags. Dynamic pages (`echo-info`, `echo-tag`, `echo-author`, `scene`) now update these tags from JS after data loads. `index.html` (kvasir.pub) now has OG tags and a `WebSite` JSON-LD with `SearchAction`. The `contest.html` page already had `Event` + `ItemList` JSON-LD populated dynamically.

### 15.2 Set Up Google Analytics 4 and Search Console

- Create a GA4 property and paste the `gtag.js` snippet into the `<head>` of every HTML page (or a shared include script loaded early). Track `page_view`, `contest_entered`, `echo_chat_started`, `scene_published` as custom events.
- Verify `quizly.pub` and `kvasir.pub` in Google Search Console. Submit the sitemaps (`https://quizly.pub/sitemap.xml`, `https://kvasir.pub/sitemap.xml`). Monitor Core Web Vitals — the AI video pages (scene.html) will load heavy assets and may need lazy loading to pass LCP thresholds.

### 15.3 Add a quizly.pub Sitemap

The current `sitemap.xml` is on `kvasir.pub` only. `quizly.pub` is the primary SEO surface (echoes, contests, echo-info, readings). Generate and host a sitemap at `https://quizly.pub/sitemap.xml` that includes:
- `https://quizly.pub/` (echoes homepage)
- `https://quizly.pub/contests`
- `https://quizly.pub/about`
- All public `echo-info?param=X` URLs (high value — each is a unique indexable page)
- All public `contest?id=X` URLs
- All `echo-tag?param=X` and `echo-author?param=X` pages with canonical URLs

Use a Lambda cron or the existing `sitemap-books.xml` pattern to generate this dynamically.

### 15.4 Target Long-Tail Contest Keywords

Short-head terms ("AI games", "AI chat") are dominated by large players. Focus on long-tail:

| Keyword cluster | Page | Priority |
|---|---|---|
| "[book title] AI chat contest" | `contest?id=X` | High |
| "talk to [character name] AI" | `echo-info?param=X` | High |
| "[book title] quiz online free" | `contest?id=X` | High |
| "AI writing contest free" | `contests` | Medium |
| "[book title] read online with AI" | `readings-info?id=X` | Medium |
| "win prizes AI quiz" | `contests`, `echoes` | Medium |

Write unique `<title>` and `<meta description>` content using these patterns for every public contest and echo-info page — the JS already updates `document.title` dynamically; make the pattern keyword-rich (e.g. `Talk to Hamlet AI — Quizly Chat Contest`).

### 15.5 Create Static Landing Pages for Top Books

Dynamic pages (`echo-info?param=123`) are crawlable but hard to link to naturally. For the 5–10 most popular books on the platform, create static or server-side-rendered landing pages with clean slug URLs:
- `quizly.pub/hamlet` → shows all echo chats, scenes, and active contests for Hamlet
- `quizly.pub/pride-and-prejudice` → same pattern

Each page gets a unique `<h1>`, a descriptive paragraph, and internal links to all echo-info and contest pages. This builds link equity and gives Google a crawlable entry point into the contest/echo graph.

### 15.6 Get Backlinks Through the Existing Content

The best backlinks will come from sources that naturally reference the content:
- **Reddit r/books posts** about a specific book → link to the Quizly reading or contest for that book
- **Creator social bios** → link to their `echo-author` profile page
- **Winning scene embeds** → the scene's `quizly.pub/scene?id=X` URL, shared by creators on TikTok/YouTube descriptions
- **Educator directories** → submit to "free AI tools for teachers" roundups; the Reading Hall + quiz contests are curriculum-adjacent

Backlinks from these sources will be topically relevant (books, education, AI) and signal authority in the keyword clusters above.

### 15.7 Fix robots.txt for quizly.pub

Current `robots.txt` references `https://kvasir.pub/sitemap.xml`. If `quizly.pub` serves the same `robots.txt`, add:
```
Sitemap: https://quizly.pub/sitemap.xml
```
Also confirm that `echo-info`, `echo-tag`, `echo-author`, `contests`, and `scene` are **not** blocked — these are the primary indexable pages.
