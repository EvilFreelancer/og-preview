# Facebook / Messenger

## What the crawler reads

- Open Graph `og:*` via the `facebookexternalhit/1.1` / `Facebot` crawler.
- Reference scraper: Meta's Sharing Debugger (developers.facebook.com/tools/debug).

## Card layout

Large card: wide image on top, domain, title, description below (description
often hidden in the mobile feed layout).

## Budgets and limits

- Large card requires >=200x200; >=600x315 for the large layout;
  1200x630 recommended, <=8 MB.
- Title: ~88 chars.
- Description: ~200 chars, and frequently not displayed at all on mobile.

## Gotchas

- Previews are cached hard - a changed `og:image` or title needs a re-scrape
  via the Sharing Debugger.
- `fb:app_id` is optional, only needed for Insights.
