# iMessage / Apple Messages

## What the crawler reads

- Open Graph `og:*`, with `<link rel="apple-touch-icon">` as an image
  fallback. Apple's crawler fetches the page like a normal browser.

## Card layout

Bubble preview: image (wide or square), title, domain. No description.

## Budgets and limits

- Title and domain only - keep the title self-sufficient.
- Square images are accepted better here than on most platforms.

## Gotchas

- Rich previews need the page reachable over https.
- If nothing renders, check that the image is a real raster (PNG/JPEG),
  not SVG.
