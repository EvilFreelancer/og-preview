# Telegram

## What the crawler reads

- Open Graph `og:*`, falling back to `<title>` and `<meta name="description">`.
- If `og:image` is missing, Telegram may pick an arbitrary `<img>` from the page.
- Crawler UA: `TelegramBot (like TwitterBot)`.

## Card layout

Inline preview under/inside the message: site name (og:site_name or domain),
bold title, description lines, medium-width image.

## Budgets and limits

- Title: ~65 chars safe, then cut.
- Description: ~3 lines, ~200 chars safe.
- Image under ~160px wide often yields NO preview at all.
- Image aspect: landscape preferred; square renders but crops less nicely.

## Gotchas

- Preview is generated server-side once per URL and cached aggressively.
  Changed tags need a new URL (any query param) or the WebPageBot
  (@WebpageBot) refresh.
- Instant View (`tg:iv_*` / `og:` extra fields) is a separate mechanism, not
  needed for a normal link card.
