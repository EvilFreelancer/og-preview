# WhatsApp

## What the crawler reads

- Open Graph `og:*` only. Crawler UA: `WhatsApp/2.x`.

## Card layout

Rounded card inside the message: image on top (or small thumb), title
(~2 lines), domain at the bottom. Description is rarely shown.

## Budgets and limits

- Title: ~2 rendered lines (~65 chars safe).
- No reliable description display - keep meaning in the title and image.

## Gotchas

- The image is downloaded and re-hosted; large images get cropped toward
  square-ish aspect in practice - keep important content centered.
- Requires absolute https image URL like everyone else.
