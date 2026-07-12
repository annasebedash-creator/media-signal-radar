import html
import re
import time

import feedparser

from .models import Item

USER_AGENT = (
    "MediaSignalRadar/0.1 (personal portfolio project; RSS headlines only; "
    "+https://github.com/annasebedash-creator/media-signal-radar)"
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean(text):
    """Strip HTML tags/entities and collapse whitespace."""
    text = _TAG_RE.sub(" ", text or "")
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _published_iso(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return ""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", parsed)


def fetch_feed(feed_cfg):
    """Fetch one RSS feed and return its entries as Items.

    Guardrail: only what the feed itself publishes — title, lead, link.
    Article pages are never fetched.
    """
    parsed = feedparser.parse(feed_cfg["url"], agent=USER_AGENT)
    if parsed.get("bozo") and not parsed.entries:
        raise RuntimeError(f"feed unreadable: {parsed.get('bozo_exception')}")

    items = []
    for entry in parsed.entries:
        title = _clean(entry.get("title", ""))
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        items.append(
            Item(
                outlet=feed_cfg["outlet"],
                feed=feed_cfg["name"],
                title=title,
                lead=_clean(entry.get("summary", "") or entry.get("description", "")),
                link=link,
                published=_published_iso(entry),
            )
        )
    return items


def fetch_all(feeds):
    """Fetch every configured feed. Returns (items, per-feed stats).

    A failing feed is recorded in stats but never aborts the run —
    the daily cron must survive a single outlet having a bad day.
    """
    all_items = []
    stats = {}
    for cfg in feeds:
        key = f"{cfg['outlet']} / {cfg['name']}"
        try:
            items = fetch_feed(cfg)
            all_items.extend(items)
            stats[key] = {"ok": True, "items": len(items)}
        except Exception as exc:  # noqa: BLE001 — one bad feed must not kill the run
            stats[key] = {"ok": False, "error": str(exc)}
    return all_items, stats
