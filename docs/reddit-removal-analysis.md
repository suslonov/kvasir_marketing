# Reddit comment removals — what happened and what to do

_Analysis of the posting results in
`Screenshot from 2026-06-28 14-26-38.png` (account `u/Fair-Cauliflower1261`)._

## What the screenshot shows

The account's two comments were both auto-removed:

| Subreddit | Thread | Age | Status | Views |
|---|---|---|---|---|
| r/russian | "What to read in russian as someone who's between b1 and b2 level?" | 1 hr ago | **[Removed by Reddit]** | 1 |
| r/RussianLiterature | "Has anyone read books like 'The Master and Margarita'" | 14 hr ago | **[Removed by Reddit]** | 1 |

Both comments are on-topic and well-targeted (exactly the threads our scanner is
built to find). The problem is **not** topic fit — it's that **Reddit itself
removed them**.

## What "[Removed by Reddit]" means

There are three different removals on Reddit, and they are NOT the same:

1. **"Removed by moderators of r/X"** — a subreddit rule / human or AutoModerator
   action. Subreddit-specific.
2. **"Removed by Reddit"** — Reddit's **site-wide anti-spam / admin systems**
   removed it. This is account- or content-level, across all of Reddit.
3. **Shadowban** — the account can post, sees its own content normally (exactly
   like this screenshot), but **nobody else can see it**. Content silently
   reads as "removed" / gets ~0 views.

We are seeing **#2, and almost certainly #3.** The tells:

- **"Removed by Reddit"** (site-wide), not "by moderators" — on *two different*
  subreddits at once. A genuine rule problem would rarely fire identically on
  both.
- **1 view each.** Real comments, even bad ones, pull more than one view in an
  hour on an active sub. ~1 view = the comment was never actually shown to
  anyone → classic shadowban behaviour.
- **Auto-generated username** (`Fair-Cauliflower1261`) = a fresh account with
  little/no karma and no history. Reddit's spam ML treats brand-new accounts
  that immediately drop links as spam by default.

### Likely root cause

A **new, zero-history account posting promotional links** (and probably the same
domain, `quizly.pub`, more than once) tripped Reddit's spam filter, and the
account is now shadowbanned or heavily filtered. The quality of the *comment
text* is almost irrelevant at this point — the account is the problem, and
possibly the domain.

## How to confirm (do this first, 2 minutes)

1. **Shadowban check:** open `https://www.reddit.com/user/Fair-Cauliflower1261`
   in a **private/incognito window (logged out)**. If the profile or the
   comments are missing/empty when logged out, the account is shadowbanned.
   (Or use a shadowban-checker site.)
2. **Domain check:** from a *different, established* account, try posting a
   `quizly.pub` link in a test comment. If it also vanishes, the **domain**
   is filtered, which is a much bigger problem than one account.
3. **Mod mail:** for the two threads, you can message the subreddit mods to ask
   if they removed it — if they say "we didn't", that confirms it was Reddit,
   not the sub.

## What to do

### Stop the bleeding
- **Do not keep commenting from this account.** More removed posts deepen the
  spam signal and can make a soft filter a hard ban.
- If shadowbanned, you can appeal at r/ShadowBan, but a fresh throwaway is
  usually not worth saving — focus the effort on doing it right next time.

### Fix the account model (this is the real fix)
Reddit promotion only works from accounts that look like real people:

1. **Warm up before promoting.** Age the account (weeks, not hours) and earn
   karma with genuine, **link-free** comments in the target communities first.
   Aim for a few hundred comment karma before any link goes out.
2. **Don't lead with a link from a cold account.** Our drafting guidance says
   "lead with the link" — that's about the *message*, but operationally a new
   account should **mention Quizly by name without a URL** at first, and only
   add links once the account has standing. Earn the right to link.
3. **Respect a promo ratio.** Rule of thumb: **~9 genuinely helpful,
   non-promotional contributions for every 1 that mentions Quizly.** Reddit (and
   mods) tolerate self-promotion only from real participants.
4. **Vary the domain footprint.** Posting the same `quizly.pub` link repeatedly
   across subs is the #1 spam trigger. Space it out, and prefer deep links
   (`/book/<id>`, `/welcome/<id>`) over the bare homepage.
5. **Slow down.** Many comments in a short window from a new account = bot
   pattern. Human cadence: a handful of actions per day, spread out.
6. **Use a real-looking profile.** Custom username, avatar, a little post
   history. The default `Adjective-Noun####` name is itself a weak spam signal.

### Per-subreddit hygiene
- r/russian and r/RussianLiterature both have self-promo rules. Even once the
  account is healthy, read each sub's rules and prefer **value-first** comments
  (actually answer "what to read at B1–B2") with the link as a soft aside, not
  the whole comment.

## Implications for this tool

The scanner is doing its job — it found two well-matched threads. The failure is
in the **execution layer** (account + posting behaviour), which is outside what
the agent controls today. Worth considering:

- Add an **"account warm-up" / link-free mode** to the drafting output: a
  variant that mentions Quizly by name with **no URL**, for use from young
  accounts.
- Track **which suggestions were posted and what happened** (removed / survived /
  upvoted) so we learn which subs and link types are safe.
- Add a **per-domain / per-account rate limiter** to the human workflow
  (e.g., "don't suggest dropping a quizly.pub link in the same sub more than
  once per N days").
- Flag **strict no-promo subs** and high-risk new-account contexts in the report
  so the human posts from a seasoned account there.

## Implemented so far (2026-06-28)

A subreddit **link-posting policy** now drives the recommendations:

- `config/subreddit_policy.yaml` — `link_safe` (URL OK in text), `no_link`
  (name-only, no URL — includes r/russian & r/RussianLiterature), everything
  else `unknown` (defaults to link-free). Plus promo-friendly discovery queries.
- The classifier prompt keeps URLs OUT of comment text for `no_link`/`unknown`
  subs (link stays in `recommended_cta` for the human), and only inlines the
  link in `link_safe` subs.
- Discovery now also searches for promo-tolerant communities and tags each new
  subreddit with a `link_safe` field for human review.

Still to do (human side): account warm-up, karma, cadence, and confirming the
`quizly.pub` domain isn't itself filtered.

> **Bottom line:** the comments weren't bad — the account was. Fix the account
> (warm it up, earn karma, link sparingly, slow down) and confirm the
> `quizly.pub` domain isn't itself filtered before investing more in posting.
