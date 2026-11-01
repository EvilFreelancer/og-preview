# X / Twitter

## What the crawler reads

- `twitter:*` tags first, then falls back to `og:*`.
- `twitter:card` selects the layout; without it X renders `summary`.
- Crawler UA: `Twitterbot/1.0`.

## Card types

- `summary` - small square thumbnail beside text.
- `summary_large_image` - big 1.91:1 card, image needs >=300x157,
  recommended 1200x628, <=5 MB.
- `player`, `app` - special cases (video iframe / app store card), rare.

## Budgets and limits

- Title: ~70 chars before truncation.
- Description: ~200 chars; may be omitted entirely in some clients.
- `twitter:site` / `twitter:creator` (`@handle`) - optional attribution.
- `twitter:image` may differ from `og:image`; same absolute-https rule applies.

## Gotchas

- The old Card Validator tool was removed. To see a real render, compose a
  draft tweet with the URL (the card appears in the composer) or rely on this
  skill's mock.
- Robots.txt blocks on `Twitterbot` kill the card silently.
