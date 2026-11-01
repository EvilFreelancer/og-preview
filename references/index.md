# Link-preview rules - index

Load only the file for the platform you are fixing or checking - do not read
the whole set. Each file lists what that platform's crawler reads, its layout,
its text budgets and its image limits.

## Shared baseline (applies everywhere)

- Crawlers read `og:*` first. The four required properties: `og:title`,
  `og:type`, `og:image`, `og:url`. Strongly recommended: `og:description`,
  `og:site_name`.
- `og:image` MUST be an absolute `https://` URL. Relative paths, `data:` URIs
  and localhost/private hosts are unusable by real crawlers.
- Recommended image: **1200x630** (1.91:1), JPEG/PNG/WebP, under ~5 MB. Under
  600px wide many platforms degrade to a small thumbnail.
- `og:image:width`/`height`/`alt` structured properties apply to the nearest
  preceding `og:image`; several `og:image` tags are allowed, first wins.
- `<title>` and `<meta name="description">` are the universal fallback - but
  NOT guaranteed on LinkedIn.
- `og:url` is the canonical URL; without it crawlers use the requested URL and
  shares of URL variants split.
- Most platforms cache the first scrape hard: a changed card needs a fresh URL
  or the platform's re-scrape tool.

## Per-platform files

| Platform | File | Reads | Card style | Title budget | Description budget | Image minimum |
|----------|------|-------|------------|--------------|--------------------|---------------|
| Telegram | [platforms/telegram.md](platforms/telegram.md) | OG + title fallback | medium card in message | ~65 | ~200 (3 lines) | ~160px wide or no preview |
| X / Twitter | [platforms/x.md](platforms/x.md) | twitter:* then og:* | summary / summary_large_image | ~70 | ~200 | 300x157 large card |
| Facebook / Messenger | [platforms/facebook.md](platforms/facebook.md) | OG | large card | ~88 | ~200 | 200x200 (1200x630 rec.) |
| Discord | [platforms/discord.md](platforms/discord.md) | OG + twitter:card + theme-color | embed with accent bar | - | ~256 | per card type |
| Slack | [platforms/slack.md](platforms/slack.md) | oEmbed > twitter > OG | unfurl with accent bar | - | - | per card type |
| WhatsApp | [platforms/whatsapp.md](platforms/whatsapp.md) | OG only | rounded card | ~2 lines | domain only | re-hosted, center-safe |
| LinkedIn | [platforms/linkedin.md](platforms/linkedin.md) | OG, poor fallbacks | large card | - | ~150 | 1200x627 rec. |
| Reddit | [platforms/reddit.md](platforms/reddit.md) | OG | image + title + domain | - | none | any landscape |
| iMessage | [platforms/imessage.md](platforms/imessage.md) | OG + apple-touch-icon | card | - | none | - |

## Crawler user-agents (for server-side testing)

- Facebook/Meta: `facebookexternalhit/1.1`, `Facebot`
- X/Twitter: `Twitterbot/1.0`
- Telegram: `TelegramBot (like TwitterBot)`
- Slack: `Slackbot-LinkExpanding`
- Discord: `Discordbot/2.0`
- WhatsApp: `WhatsApp/2.x`
- LinkedIn: `LinkedInBot/1.0`
- Pinterest: `Pinterest/0.2`
- Reddit: `redditbot/1.0`

The script sends a facebookexternalhit-compatible UA to approximate the worst
case. A page that varies HTML per UA should still emit complete OG tags for
every UA above.
