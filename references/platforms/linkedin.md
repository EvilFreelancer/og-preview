# LinkedIn

## What the crawler reads

- Open Graph `og:*` specifically: `og:title`, `og:image`, `og:description`,
  `og:url`. The crawler is poor at falling back to `<title>` - emit real OG
  tags. Crawler UA: `LinkedInBot/1.0`.

## Card layout

Post preview: wide image, title, domain.

## Budgets and limits

- Image: 1200x627 recommended.
- Description: cut around ~140-150 chars.
- Title: ~100 chars.

## Gotchas

- Official debugger: LinkedIn Post Inspector.
- First scrape is cached; the Inspector forces a refresh.
