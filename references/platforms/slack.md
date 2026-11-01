# Slack

## What the crawler reads

- Priority order: oEmbed, then `twitter:*` card tags, then `og:*`.
- Crawler UA: `Slackbot-LinkExpanding`.

## Card layout

Unfurl under the message: accent bar on the left (from `theme-color`),
site name, bold title, description, image - wide under
`summary_large_image`, ~75px thumbnail otherwise.

## Budgets and limits

- Same truncation character as Discord (~250 chars of description).
- `twitter:card=summary_large_image` is the lever for the wide image.

## Gotchas

- Respects robots.txt; image URL must be reachable without auth.
- Slack caches unfurls per workspace; `chat.unfurl` in its API is for apps,
  not for fixing stale previews.
