#!/usr/bin/env python3
"""
og_preview.py — offline Open Graph / Twitter Card inspector and preview renderer.

Reads a page from a URL (localhost included) or a local HTML file, extracts
Open Graph, Twitter Card and classic meta tags, checks them against per-platform
rules and renders a self-contained HTML report with mocked link-preview cards
for Telegram, X/Twitter, Facebook, Discord, Slack, WhatsApp, LinkedIn, iMessage
and Reddit. No third-party services are involved: the only network call is the
optional fetch of the page itself and of the og:image (for a size check).

Usage:
    og_preview.py https://example.com/page
    og_preview.py http://localhost:3000/blog/post
    og_preview.py dist/index.html --base https://example.com/
    og_preview.py page.html --json report.json --out preview.html

Standard library only.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import ssl
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "og-preview/1.0 (+https://github.com/EvilFreelancer/og-preview) compatible; facebookexternalhit/1.1"

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


class MetaParser(HTMLParser):
    """Collect <meta property/name>, <title> and icon links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[dict[str, str]] = []  # {key, content} in document order
        self.title = ""
        self.favicon = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = a.get("property") or a.get("name") or a.get("itemprop")
            if key and "content" in a:
                self.tags.append({"key": key.strip().lower(), "content": a["content"].strip()})
        elif tag == "title":
            self._in_title = True
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if not self.favicon and ("icon" in rel or rel == "shortcut icon"):
                self.favicon = a.get("href", "")
        elif tag == "html":
            pass

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data

    def get(self, key: str, default: str = "") -> str:
        for t in self.tags:
            if t["key"] == key:
                return t["content"]
        return default

    def get_all(self, key: str) -> list[str]:
        return [t["content"] for t in self.tags if t["key"] == key]


# ---------------------------------------------------------------------------
# Resolved data model
# ---------------------------------------------------------------------------

PLATFORM_ORDER = [
    "telegram",
    "x",
    "facebook",
    "discord",
    "slack",
    "whatsapp",
    "linkedin",
    "reddit",
    "imessage",
]


def truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[: limit - 1].rstrip() + "…", True


def is_local_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    return host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"} or host.endswith(".local") or "." not in host


def image_size(data: bytes) -> tuple[int, int] | None:
    """Cheap WxH sniffing for PNG/JPEG/GIF/WebP without Pillow."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w, h
        if data[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", data[6:10])
            return w, h
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            if data[12:16] == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                return w & 0x3FFF, h & 0x3FFF
            if data[12:16] == b"VP8X":
                w = int.from_bytes(data[24:27], "little") + 1
                h = int.from_bytes(data[27:30], "little") + 1
                return w, h
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                seg = struct.unpack(">H", data[i + 2 : i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    return w, h
                i += 2 + seg
    except (IndexError, struct.error):
        return None
    return None


def fetch(url: str, timeout: int = 15, max_bytes: int = 8_000_000) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read(max_bytes)


MIME_SNIFF = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"RIFF", "image/webp"),
]


def sniff_mime(data: bytes) -> str:
    for magic, mime in MIME_SNIFF:
        if data[: len(magic)] == magic:
            return mime
    if data[:5].lower().startswith(b"<svg") or b"<svg" in data[:512]:
        return "image/svg+xml"
    return "application/octet-stream"


def data_uri(data: bytes) -> str:
    import base64

    return f"data:{sniff_mime(data)};base64,{base64.b64encode(data).decode()}"


# ---------------------------------------------------------------------------
# Platform rule checks
# ---------------------------------------------------------------------------


def check_common(meta: MetaParser, url: str, image_dims: tuple[int, int] | None, image_ok: bool | None) -> list[dict]:
    warnings: list[dict] = []

    def warn(sev: str, platform: str, msg: str) -> None:
        warnings.append({"severity": sev, "platform": platform, "message": msg})

    title = meta.get("og:title") or meta.title.strip()
    desc = meta.get("og:description") or meta.get("description")
    image = meta.get("og:image") or meta.get("og:image:url")
    site = meta.get("og:site_name")

    if not title:
        warn("error", "all", "No <title> and no og:title — most platforms will show a bare URL.")
    if not desc:
        warn("warn", "all", "No og:description nor meta description — platforms will guess or show nothing.")
    if not image:
        warn("error", "all", "No og:image — the preview will render without an image on most platforms.")
    elif urllib.parse.urlparse(image).scheme not in ("http", "https"):
        warn("error", "all", f"og:image is not an absolute http(s) URL: {image!r}. Crawlers cannot resolve relative paths.")
    if not meta.get("og:url"):
        warn("info", "all", "No og:url — canonical URL is missing; crawlers will use the requested URL.")
    if not site:
        warn("info", "all", "No og:site_name — some platforms show the bare domain instead of a brand name.")
    if not meta.get("og:type"):
        warn("info", "all", "No og:type — defaults to 'website', usually fine.")
    if image and image.startswith("http://"):
        warn("warn", "all", "og:image uses http:// — some clients refuse mixed content; prefer https.")
    if image and is_local_url(image):
        warn("error", "all", "og:image points at localhost/private host — real crawlers cannot fetch it. Fine for local testing only.")
    if url and is_local_url(url):
        warn("info", "all", "Page URL is localhost — previews rendered here are mocks; deploy or tunnel to see real crawlers.")
    if image_ok is False:
        warn("error", "all", f"Could not fetch og:image ({image}) — check the URL and Content-Type.")

    # X / Twitter
    tw_card = meta.get("twitter:card")
    if not tw_card:
        warn("info", "x", "No twitter:card — X falls back to og:* and renders 'summary' (small thumbnail).")
    elif tw_card not in ("summary", "summary_large_image", "player", "app"):
        warn("warn", "x", f"Unknown twitter:card value {tw_card!r}.")
    if tw_card == "summary_large_image" and image_dims and image_dims[0] < 300:
        warn("warn", "x", "summary_large_image needs >=300px wide; image is %dx%d." % image_dims)
    if title and len(title) > 70:
        warn("warn", "x", f"Title {len(title)} chars — X truncates around 70.")

    # Telegram
    if image_dims and image_dims[0] < 160:
        warn("warn", "telegram", "Telegram usually hides previews with images under ~160px wide.")
    if title and len(title) > 65:
        warn("warn", "telegram", f"Title {len(title)} chars — Telegram cuts long titles early.")
    if desc and len(desc) > 200:
        warn("warn", "telegram", f"Description {len(desc)} chars — Telegram shows roughly 3 lines.")

    # Facebook / general OG
    if image_dims:
        w, h = image_dims
        if w < 200 or h < 200:
            warn("warn", "facebook", f"og:image {w}x{h} — Facebook minimum for a large card is 200x200; use 1200x630.")
        elif w < 600:
            warn("info", "facebook", f"og:image {w}x{h} — under 600px wide renders as a small thumbnail.")
    if desc and len(desc) > 200:
        warn("warn", "facebook", f"Description {len(desc)} chars — Facebook cuts around ~200.")

    # Slack/Discord need stable https images too; Discord caps at ~256 chars desc
    if desc and len(desc) > 256:
        warn("info", "discord", "Discord shows ~256 chars of description; yours will be cut.")
    if not meta.get("theme-color"):
        warn("info", "discord", "No <meta name='theme-color'> — Discord uses it for the left border accent.")

    # LinkedIn
    if desc and len(desc) > 150:
        warn("info", "linkedin", "LinkedIn description is cut around ~140-150 chars.")
    if not meta.get("og:title"):
        warn("warn", "linkedin", "LinkedIn reads og:title specifically — <title> fallback is unreliable.")

    return warnings


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

CARD_CSS = """
:root{color-scheme:light dark;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
body{margin:0;padding:24px;background:#f2f3f5;color:#111}
@media(prefers-color-scheme:dark){body{background:#14151a;color:#e8e8ea}}
h1{font-size:20px;margin:0 0 4px}
.sub{opacity:.6;font-size:13px;margin-bottom:24px;word-break:break-all}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px}
section{margin-bottom:8px}
.name{font-size:13px;font-weight:700;opacity:.75;margin:0 0 6px;text-transform:uppercase;letter-spacing:.05em}
.card{border-radius:10px;overflow:hidden;max-width:440px;box-shadow:0 1px 3px rgba(0,0,0,.15);display:flex;flex-direction:column}
.card .img{width:100%;aspect-ratio:1.91/1;object-fit:cover;display:block;background:#c9ced6}
.card.small{flex-direction:row;align-items:stretch}
.card.small .img{width:72px;min-width:72px;aspect-ratio:auto;min-height:72px}
.body{padding:10px 12px;display:flex;flex-direction:column;gap:2px}
.t{font-size:15px;font-weight:600;line-height:1.3}
.d{font-size:13px;opacity:.75;line-height:1.35}
.u{font-size:12px;opacity:.5;margin-top:4px;text-transform:lowercase}
.noimg{display:flex;align-items:center;justify-content:center;font-size:32px;color:#8a93a3}
/* platform skins */
.telegram{background:#fff}.telegram .u{color:#4fa3e3}
.x{background:#fff}.x .t{font-weight:400}
.discord{background:#2b2d31;color:#dbdee1;border-left:4px solid var(--accent,#5865f2);border-radius:4px}
.discord .d{opacity:.85}.discord .u{color:#949ba4}
.slack{background:#fff;border-left:4px solid var(--accent,#611f69);border-radius:4px}
.whatsapp{background:#e7ffd8;border-radius:8px}
.whatsapp .u{color:#34b7f1}
.imessage{background:#fff;border-radius:18px}
.reddit{background:#fff;border-radius:4px;border:1px solid #ccc}
.linkedin{background:#fff}.linkedin .u{text-transform:uppercase}
.facebook{background:#fff}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
th,td{border:1px solid rgba(127,127,127,.35);padding:6px 8px;text-align:left;vertical-align:top}
th{opacity:.7}
.sev-error{color:#c00;font-weight:700}.sev-warn{color:#b8860b;font-weight:700}.sev-info{color:#3574d4;font-weight:700}
.tag{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
@media(prefers-color-scheme:dark){
 .telegram,.x,.slack,.whatsapp,.imessage,.reddit,.linkedin,.facebook{background:#1f2227}
 .whatsapp .u{color:#53bdeb}.card .img{background:#2a2f38}
}
"""


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def card_html(platform: str, *, title: str, desc: str, site: str, domain: str, image: str, small: bool, accent: str = "") -> str:
    style = f' style="--accent:{esc(accent)}"' if accent else ""
    img = (
        f'<img class="img" src="{esc(image)}" alt="">'
        if image
        else '<div class="img noimg">🔗</div>'
    )
    cls = "card small" if small else "card"
    return (
        f'<div class="{esc(platform)} {cls}"{style}>{img}'
        f'<div class="body"><div class="t">{esc(title)}</div>'
        f'<div class="d">{esc(desc)}</div>'
        f'<div class="u">{esc(site or domain)}</div></div></div>'
    )


def render_report(meta: MetaParser, page_url: str, resolved: dict, warnings: list[dict], image_dims, image_ok, image_embed: str = "") -> str:
    title = resolved["title"]
    desc = resolved["desc"]
    image = image_embed or resolved["image"]
    site = resolved["site"]
    domain = urllib.parse.urlparse(page_url or resolved["og_url"]).hostname or ""
    accent = meta.get("theme-color") or ""

    tw_card = meta.get("twitter:card") or "summary"
    tw_small = tw_card != "summary_large_image"
    fb_t, _ = truncate(title, 88)
    fb_d, _ = truncate(desc, 200)
    x_t, _ = truncate(title, 70)
    x_d, _ = truncate(desc, 200)
    tg_t, _ = truncate(title, 65)
    tg_d, _ = truncate(desc, 200)
    li_d, _ = truncate(desc, 150)
    dc_d, _ = truncate(desc, 256)

    cards = [
        ("Telegram", "telegram", card_html("telegram", title=tg_t, desc=tg_d, site=site, domain=domain, image=image, small=False)),
        ("X / Twitter", "x", card_html("x", title=x_t, desc=x_d, site="", domain=domain, image=image, small=tw_small)),
        ("Facebook", "facebook", card_html("facebook", title=fb_t, desc=fb_d, site="", domain=domain, image=image, small=False)),
        ("Discord", "discord", card_html("discord", title=title, desc=dc_d, site=site, domain=domain, image=image, small=False, accent=accent)),
        ("Slack", "slack", card_html("slack", title=title, desc=dc_d, site=site, domain=domain, image=image, small=False, accent=accent)),
        ("WhatsApp", "whatsapp", card_html("whatsapp", title=tg_t, desc=tg_d, site="", domain=domain, image=image, small=False)),
        ("LinkedIn", "linkedin", card_html("linkedin", title=fb_t, desc=li_d, site="", domain=domain, image=image, small=False)),
        ("Reddit", "reddit", card_html("reddit", title=fb_t, desc="", site="", domain=domain, image=image, small=False)),
        ("iMessage", "imessage", card_html("imessage", title=title, desc="", site="", domain=domain, image=image, small=False)),
    ]

    rows = "\n".join(
        f'<tr><td class="sev-{esc(w["severity"])}">{esc(w["severity"])}</td>'
        f'<td>{esc(w["platform"])}</td><td>{esc(w["message"])}</td></tr>'
        for w in warnings
    ) or '<tr><td colspan="3">No issues found.</td></tr>'

    tag_rows = "\n".join(
        f'<tr><td class="tag">{esc(t["key"])}</td><td class="tag">{esc(t["content"])}</td></tr>'
        for t in meta.tags
    )

    img_info = f"{image_dims[0]}x{image_dims[1]}" if image_dims else ("unfetched" if image_ok is None else "fetch failed")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>OG preview — {esc(title or domain)}</title>
<style>{CARD_CSS}</style></head><body>
<h1>Link preview report</h1>
<div class="sub">Source: {esc(page_url or '(file)')} · og:image: {esc(resolved['image'] or 'none')} ({img_info})</div>
<div class="grid">
{''.join(f'<section><p class="name">{esc(n)}</p>{c}</section>' for n, _, c in cards)}
</div>
<h2>Checks</h2>
<table><tr><th>severity</th><th>platform</th><th>finding</th></tr>
{rows}
</table>
<h2>All meta tags</h2>
<table><tr><th>key</th><th>content</th></tr>
{tag_rows}
</table>
</body></html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Offline Open Graph / Twitter Card inspector and preview renderer.")
    ap.add_argument("source", help="URL (http://localhost works) or path to an HTML file")
    ap.add_argument("--base", help="Base URL used to resolve relative og:image when the source is a file")
    ap.add_argument("--out", default="og-preview.html", help="HTML report path (default og-preview.html)")
    ap.add_argument("--json", dest="json_out", help="Also write raw findings as JSON to this path")
    ap.add_argument("--no-fetch", action="store_true", help="Do not fetch og:image for a size check")
    args = ap.parse_args(argv)

    src = args.source
    page_url = ""
    if re.match(r"https?://", src):
        page_url = src
        try:
            raw = fetch(src)
        except (urllib.error.URLError, OSError) as e:
            print(f"error: cannot fetch {src}: {e}", file=sys.stderr)
            return 2
        html_text = raw.decode("utf-8", errors="replace")
    else:
        if not os.path.isfile(src):
            print(f"error: not a file or URL: {src}", file=sys.stderr)
            return 2
        with open(src, "rb") as f:
            html_text = f.read().decode("utf-8", errors="replace")
        page_url = args.base or ""

    meta = MetaParser()
    meta.feed(html_text)

    def resolve(u: str) -> str:
        if not u:
            return u
        if re.match(r"https?://", u):
            return u
        if page_url:
            return urllib.parse.urljoin(page_url, u)
        return u

    resolved = {
        "title": meta.get("og:title") or meta.get("twitter:title") or meta.title.strip(),
        "desc": meta.get("og:description") or meta.get("twitter:description") or meta.get("description"),
        "image": resolve(meta.get("og:image") or meta.get("og:image:url") or meta.get("twitter:image") or meta.get("twitter:image:src")),
        "site": meta.get("og:site_name") or meta.get("application-name"),
        "og_url": meta.get("og:url"),
    }

    image_dims = None
    image_ok = None
    image_embed = ""
    if resolved["image"] and re.match(r"https?://", resolved["image"]) and not args.no_fetch:
        try:
            data = fetch(resolved["image"], timeout=10, max_bytes=4_000_000)
            image_dims = image_size(data)
            image_ok = True
            image_embed = data_uri(data)
        except (urllib.error.URLError, OSError):
            image_ok = False

    warnings = check_common(meta, page_url, image_dims, image_ok)
    report = render_report(meta, page_url, resolved, warnings, image_dims, image_ok, image_embed)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"report: {args.out}")

    if args.json_out:
        findings = {
            "source": src,
            "resolved": resolved,
            "image_dimensions": image_dims,
            "tags": meta.tags,
            "warnings": warnings,
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(findings, f, ensure_ascii=False, indent=2)
        print(f"json: {args.json_out}")

    errors = [w for w in warnings if w["severity"] == "error"]
    warns = [w for w in warnings if w["severity"] == "warn"]
    print(f"checks: {len(errors)} errors, {len(warns)} warnings, {len(warnings) - len(errors) - len(warns)} info")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
