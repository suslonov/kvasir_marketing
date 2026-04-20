# Site Evaluation: quizly.pub

## Overall Readiness Score

| Area | Score | Notes |
|------|-------|-------|
| Value Proposition Clarity | 4/10 | Excellent on brief.html, absent on homepage |
| First Impression | 5/10 | Clean design but no context for new visitors |
| SEO Technical | 5/10 | Good basics, but JS-rendered content, no lastmod, query-param URLs |
| Conversion Funnel | 3/10 | No landing page, no onboarding, no email capture |
| Mobile Experience | 7/10 | Good responsive design with mobile tabs |
| Brand Consistency | 3/10 | Kvasir/Quizly/Quizzly confusion throughout |
| Content Quality | 7/10 | Brief page has excellent copywriting |
| Social Proof | 1/10 | No testimonials, no user counts, no reviews |

## Critical Issues

### 1. No Landing Page for New Visitors
The homepage (quizly.pub) IS the app catalog (echoes.html). First-time visitors see "Game and chat with AI. Contests in prompt crafting" with a loading catalog -- no explanation, no hero section, no CTA. The excellent marketing content on `/brief` is buried and unlinked.

### 2. JS-Rendered Homepage = Invisible to Google
The homepage renders all game cards, contests, authors, and tags via JavaScript API calls. Google's crawler sees "Loading..." placeholders. This is the #1 SEO problem.

### 3. Brand Name Chaos
- HTML titles say "Kvasir" on quizly.pub pages
- About page says "Quizzly" (double z)
- OG tags say "Quizly"
- Structured data says "Kvasir"
Google cannot associate these as one brand.

### 4. No Social Proof Anywhere
Zero testimonials, user counts, reviews, or metrics on any page. Visitors have no reason to trust the platform.

### 5. Broken Conversion Funnel
- No email capture mechanism
- No onboarding flow after signup
- Login button is small and easy to miss
- The callout witch (login prompt) only appears on second visit
- brief.html (best marketing page) has no signup CTA

## SEO Issues

- **No `<lastmod>` dates** in any sitemap file
- **Query parameter URLs** (`echo-info?param=273`) instead of clean slugs (`/echo/turing-test`)
- **No `hreflang` tags** despite EN/RU/HE content
- **Logo `<img src="">` on load** -- JS fills it later, crawlers see broken image
- ~67 total indexed URLs across 3 sitemaps (static, contests, echoes)

## What Works Well

- Mobile-responsive with tab-based navigation
- Proper robots.txt blocking admin/editor paths
- Structured data (JSON-LD) present on key pages
- brief.html copywriting is strong and persuasive
- Bilingual support (EN/RU) is a differentiator
- The "callout witch" login nudge on return visits is clever
- Display settings panel lets users customize sections

## Top 10 Recommendations (Priority Order)

1. **Make brief.html content the homepage** or create a hero section on the main page with value prop + featured games before the catalog
2. **Fix brand naming** -- "Quizly" everywhere on quizly.pub, "Kvasir" on kvasir.pub only
3. **Add 2-3 featured games above the fold** with "Play Now" buttons and visual previews
4. **Add `<lastmod>` dates to all sitemaps** and automate regeneration
5. **Add `hreflang` tags** for multilingual pages
6. **Add social proof** -- game play counts, active players, curated user quotes
7. **Pre-render homepage content** or add static HTML fallback for SEO
8. **Add email capture** -- "Get notified about new games" in footer or post-game
9. **Clean up URLs** -- descriptive slugs instead of `?param=` IDs
10. **Fix the deck page for investors** -- add team, metrics, market size, competitive positioning
