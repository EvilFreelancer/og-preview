# Discord

## What the crawler reads

- Open Graph `og:*` plus `twitter:card` for layout selection, and
  `<meta name="theme-color" content="#RRGGBB">` for the embed's left border.
- Crawler UA: `Discordbot/2.0`.

## Card layout

Chat embed: colored accent bar on the left, site name line (og:site_name),
title link, description, then the image - wide under `summary_large_image`,
small right-side thumbnail under `summary`.

## Budgets and limits

- Description: ~256 chars.
- Site name comes from `og:site_name`; falls back to domain.
- `theme-color` accent is a nice touch unique to Discord/Slack embeds.

## Gotchas

- oEmbed/JSON endpoints on the page can override all meta-derived fields.
- Image must be a fetchable absolute URL; Discord re-proxies media.
