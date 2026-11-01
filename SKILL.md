---
name: og-preview
metadata:
  version: 1.0.0
description: >
  Test Open Graph, Twitter Card and other social-link meta tags fully offline.
  Point it at a URL (localhost works) or an HTML file: it parses the tags and
  renders a self-contained HTML report with mocked link-preview cards for
  Telegram, X/Twitter, Facebook, Discord, Slack, WhatsApp, LinkedIn, Reddit and
  iMessage, plus a findings table of rule violations. No third-party API, no
  external validator - everything runs locally. Use when the user asks to test
  or preview og tags, social cards, link unfurling or how a page looks when
  shared, before deploying.
---

# OG preview

## When this skill applies

The user wants to see how a page's link preview (Open Graph card, Twitter card,
Telegram/Discord/Slack unfurl) will look, or to validate social meta tags -
especially on localhost or a file, where public validators cannot reach.

## Workflow

1. **Run the checker.** Pick the invocation that matches what the user gave:

   ```bash
   # live page, local dev server included
   python3 scripts/og_preview.py http://localhost:3000/blog/post

   # static HTML file; --base makes relative og:image resolvable
   python3 scripts/og_preview.py dist/index.html --base https://example.com/
   ```

   Output: `og-preview.html` (report) in the current directory. Add
   `--json report.json` for machine-readable findings when the fix loop is
   automated. Exit code is 1 when errors are found, 0 otherwise - usable in CI.

2. **Read the findings table first.** Errors (missing `og:title`/`og:image`,
   relative or http image URLs, unreachable image) block correct rendering on
   real platforms; warnings are truncation and size-degradation risks. The
   rules live split by platform under `references/` - consult
   `references/index.md` for the summary table, then open only the files of
   the platforms that flagged findings (`references/platforms/<name>.md`)
   instead of loading every rule.

3. **Show the report.** Open `og-preview.html` for the user (a local preview
   server or the browser tool) so they can compare the nine platform mocks.
   The mocks apply per-platform truncation budgets; they approximate layout,
   not pixel-exact rendering.

4. **Fix and re-run.** Patch the page's `<head>` and re-run until zero errors.
   Typical minimal fix set: `og:title`, `og:description`, `og:site_name`,
   `og:type`, `og:url`, absolute `https://` `og:image` 1200x630 with
   `og:image:width`/`height`/`alt`, `twitter:card=summary_large_image`,
   `theme-color` for Discord/Slack accents.

## Notes

- The only network access is fetching the page itself and its `og:image` for a
  dimension check (`--no-fetch` disables the image fetch). No external
  validators or preview APIs are used - safe for intranet and offline work.
- Mocks cannot reproduce real crawler caches. Remind the user that after
  deploying, Telegram/Facebook cache the first scrape: a changed card needs a
  fresh URL or the platform's re-scrape tool.
