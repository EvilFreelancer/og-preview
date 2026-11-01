# og-preview

Test Open Graph, Twitter Card and social-link meta tags **fully offline**. Give
it a URL - `http://localhost:3000` works - or a plain HTML file, and it renders
a self-contained `og-preview.html` report:

- mocked link-preview cards for **Telegram, X/Twitter, Facebook, Discord,
  Slack, WhatsApp, LinkedIn, Reddit and iMessage**, each applying that
  platform's truncation and layout rules;
- a findings table of rule violations (missing tags, relative or `http://`
  images, localhost-only image URLs, wrong image dimensions, truncation risk);
- a full dump of every meta tag found.

No third-party validators, no external API - a single Python script on the
standard library. The only network calls are fetching the page itself (if you
passed a URL) and its `og:image` for a size check (`--no-fetch` skips it).

## Usage

```bash
python3 scripts/og_preview.py http://localhost:3000/blog/post
python3 scripts/og_preview.py https://example.com/page
python3 scripts/og_preview.py dist/index.html --base https://example.com/
python3 scripts/og_preview.py page.html --json report.json --out preview.html
```

Exit code is `1` when errors are found, `0` otherwise - works as a CI gate.

## When to use it

- previewing social cards before deploying a page;
- testing OG tags on a local dev server where public debuggers (Facebook
  Sharing Debugger, LinkedIn Post Inspector) cannot reach;
- a repeatable, scriptable check of meta markup in CI.

For the per-platform rules the checker enforces, see
[references/index.md](references/index.md) - a summary table linking to one
file per platform. A worked example (captured page + rendered report) lives in
[examples/](examples/).

## Install

The repo root is the skill folder: copy or symlink it into your agent's skills
directory (`~/.claude/skills/og-preview`, `~/.cursor/skills/og-preview`,
`~/.agents/skills/og-preview`), or install via the
[rpa-skills](https://github.com/EvilFreelancer/rpa-skills) marketplace.

## Source & attribution

Written for the rpa-skills collection. Rules compiled from the
[Open Graph protocol](https://ogp.me/) spec and platform crawler
documentation. MIT licensed.
