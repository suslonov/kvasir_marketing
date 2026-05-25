# Google SEO — Action Plan
_Last updated 2026-05-20_

---

## Current state

| Metric | 24h (May 19) | change |
|---|---|---|
| Avg position | **4.5** | was 11.9 ✅ |
| Sitemap discovered | **796** | was 0 ✅ |
| Indexed pages | 10 | still declining |

Position jump confirms the sitemap fix worked. Indexed count is still low because the quizly.pub canonical fix hasn't propagated yet (see Bug 1 below).

---

## Why sync.sh didn't propagate the canonical fix

kvasir.pub canonical fixes were written at **11:46** on May 19. quizly.pub files were last touched at **12:04** (from an earlier sync run that day). `sync.sh` only copies source→dest when source is *newer*, so it correctly skipped all five affected files. The fix: apply Bug 1 below to kvasir.pub — that makes kvasir.pub files newer — then re-run `sync.sh` + `deploy.sh`.

---

## Bug 1 — Canonical script must strip extra URL parameters

The current inline script in kvasir.pub uses the full `location.search`, which includes secondary params (`tpl`, `lang`, `course`, `private`). This means `echo-info?param=521&tpl=2&course=216&lang=en` and `echo-info?param=521&tpl=4` each get a unique canonical — producing the 19 "duplicate without user-selected canonical" pages in Search Console.

The canonical must keep **only the primary identifying param**. Replace the current one-liner in kvasir.pub with the correct version per page, then run sync.sh.

**`echo-info.html`, `scene.html`, `echo-tag.html`, `echo.html`** — primary param is `?param=`:
```html
<link rel="canonical" id="canonicalLink">
<script>(function(){var p=new URLSearchParams(location.search).get('param');document.getElementById('canonicalLink').href=location.origin+location.pathname+(p?'?param='+p:'');})();</script>
```

**`contest.html`, `echo-author.html`** — primary param is `?id=`:
```html
<link rel="canonical" id="canonicalLink">
<script>(function(){var p=new URLSearchParams(location.search).get('id');document.getElementById('canonicalLink').href=location.origin+location.pathname+(p?'?id='+p:'');})();</script>
```

---

## Bug 2 — echo-author.js rewrites `?id=` to `?param=` in canonical

`echo-author.html` reads `urlParams.get('id')` so URLs are `echo-author?id=16`. But `echo-author.js` lines 52 and 58 then overwrite the canonical to `echo-author?param=${authorId}`. Google sees two canonical URLs for the same page.

Fix in `kvasir.pub/js/echo-author.js`:
```js
// line 52 — change ?param= to ?id=
if (canonicalEl) canonicalEl.href = `${siteBase}/echo-author?id=${authorId}`;
// line 58
if (ogUrlEl) ogUrlEl.setAttribute('content', `${siteBase}/echo-author?id=${authorId}`);
```

JS files sync automatically (`kvasir.pub/js/` → `quizly.pub/js/` via dir-map).

---

## Bug 3 — Bare URLs indexed as empty shells

`quizly.pub/echo-info` and `quizly.pub/contest` (no params) are in Google's indexed pages list. Users clicking them from search results land on an empty page. This happens because the canonical script, when no param is present, produces a bare URL which Google indexes as valid content.

Add a redirect-to-home **before** the canonical script on each parametrised page in kvasir.pub:

**For `echo-info.html`, `scene.html`, `echo-tag.html`, `echo.html`:**
```html
<script>(function(){if(!new URLSearchParams(location.search).get('param'))window.location.replace('/');})();</script>
<link rel="canonical" id="canonicalLink">
<script>...</script>
```

**For `contest.html`, `echo-author.html`:**
```html
<script>(function(){if(!new URLSearchParams(location.search).get('id'))window.location.replace('/');})();</script>
```

---

## After Bugs 1–3 are fixed: run sync.sh + deploy.sh + resubmit sitemap

Fixing Bug 1 makes kvasir.pub files newer than quizly.pub → sync.sh will propagate all changes correctly. After deploy, resubmit `https://quizly.pub/sitemap.xml` in Search Console.

---

## Issue 4 — Books canonical inconsistency

`quizly.pub/books.html` has `<link rel="canonical" href="https://kvasir.pub/books">` — books canonical to kvasir.pub, but the 704-URL books sitemap is on quizly.pub. Google attributes the reading-info pages to kvasir.pub while they're listed under quizly.pub's sitemap.

Canonical domain assignment:

| Domain | Pages |
|---|---|
| **quizly.pub** | `/` (echoes/index), contests, contest, echo-info, scene, echo-author, echo-tag, echo, about, brief, legal, deck |
| **kvasir.pub** | creator tools, team, index (creator home) |
| **needs decision** | books — quizly.pub sitemap, kvasir.pub canonical |

**Fix:** change `books.html` canonical in both domains to `https://quizly.pub/books`. This aligns books with the sitemap and keeps all user-facing content on one domain.

---

## Issue 5 — Scene video thumbnail is generic

URL Inspection shows `scene?param=1358` uses `og-contests.png` as the video thumbnail instead of the actual scene image. The VideoObject `thumbnailUrl` is sourced from `title_picture_url` in `scene.js` — this field may be null for some scenes, causing Google to fall back to `og:image`.

Two fixes in `scene.js`, in the block that already sets the VideoObject:
1. Guard against null thumbnail — only set VideoObject if `title_picture_url` is present
2. Also update `og:image` dynamically:
```js
const ogImg = document.querySelector('meta[property="og:image"]');
if (ogImg && component_record.title_picture_url) {
  ogImg.setAttribute('content', component_record.title_picture_url);
}
```

---

## P-next — seoSnippet for contest and scene pages

`echo-info.html` already has `<div id="seoSnippet">` and `updateSeoSnippet()` in echo-info.js ✅. The same pattern needs adding to `contest.html` and `scene.html` so Google has unique indexable text on those pages too.

---

## P-next — Landing page keyword text

Not yet done. Expand `landing.hero_tagline` in `en.json` and add one `<p>` after the how-it-works SVG in `echoes.html`. See previous P3 notes.

---

## What to bring next time

After Bugs 1–3 fixed + sync + deploy + sitemap resubmitted (wait ~1 week):

1. **URL Inspection `https://quizly.pub/echo-info?param=273`** — canonical must show `echo-info?param=273` (with param, correct domain).
2. **Indexed pages list** — bare `echo-info` and `contest` should be gone.
3. **"Duplicate without user-selected canonical"** — should drop from 19 toward 0.
4. **Indexed page count** — should start rising as Google re-processes the 61 "crawled not indexed" pages with correct canonicals.
