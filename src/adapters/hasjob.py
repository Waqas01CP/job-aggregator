"""Hasjob. ADR-0063's Changes of 2026-10-20, research 0006: built 2026-10-20,
measured first through the real chain (the seat's report on Brief 18): of its
feed's 17 postings, today's rules keep 2 dated at their reading and November's
3, all of them with the employer's own name on the posting.

Endpoint: hasjob.co/feed, one request a run, Atom, its newest postings, 17 on
2026-10-20 dated 2026-09-21 to 10-19. Its terms (/tos) have no clause on
automated reading, and its robots rules bar only its edit, confirm, withdraw
and admin pages. Each row links to the posting's page on Hasjob and names it
as its board.

**Atom, not JSON,** fetched as text through the shared client and decoded
here, as We Work Remotely's RSS is.

**India-centred.** A place is as the poster wrote it, a city or "Anywhere";
the feed states no country, so a city the place rules cannot name keeps its
posting, as everywhere (ADR-0057), and the operator's caution of 2026-10-19
stands against any rule that would drop one unread.

Fields, measured over the 17 of 2026-10-20:

  identity     the last part of `link`'s href, which `id` equals on 17 of 17
  title        `title`
  employer     the first linked name in `content`, the posting's byline,
               on 17 of 17; else None
  link         `link`'s href, the posting's page on Hasjob
  publication  `published`, ISO 8601 with its offset
  place        `location`, "Anywhere" on 4 of 17, an Indian city on 13
  description  `content`, HTML
"""

import html
import re
from datetime import datetime
import xml.etree.ElementTree as ET

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "hasjob"
BASE = "https://hasjob.co/feed"
PUBLISHED_FIELD = "published"
_ATOM = "{http://www.w3.org/2005/Atom}"

# ADR-0018: what parse() reads, and nothing else, of the decoded payload.
CONSUMED_RESPONSE = ("entries",)
POSTINGS_AT = "entries"
CONSUMED = ("title", "link", PUBLISHED_FIELD, "location", "content")
# Read from the feed's XML by `decode`, before there is a payload: the link
# element's `href` attribute, which becomes the entry's `link`. Declared, as
# Hacker News' locator is, and not fingerprinted; the entry's `link` is.
CONSUMED_FEED = ("href",)

# The posting's byline: the employer's name, linked, first in its content.
_BYLINE = re.compile(r"<strong>\s*<a\b[^>]*>([^<]+)</a>")


def url_for(board):
    return BASE


def decode(text):
    """The feed's entries as objects, each field its text, or raise."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise AdapterError("Hasjob's feed is not XML: %s" % e)
    if root.tag != _ATOM + "feed":
        raise AdapterError("Hasjob's feed is not an Atom feed")
    entries = []
    for e in root.findall(_ATOM + "entry"):
        link = e.find(_ATOM + "link")
        entries.append({"id": e.findtext(_ATOM + "id"),
                        "title": e.findtext(_ATOM + "title"),
                        "link": link.attrib.get("href") if link is not None else None,
                        PUBLISHED_FIELD: e.findtext(_ATOM + PUBLISHED_FIELD),
                        "location": e.findtext(_ATOM + "location"),
                        "content": e.findtext(_ATOM + "content")})
    return {"entries": entries}


def _text(value):
    return " ".join(html.unescape(str(value or "")).split())


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise AdapterError("%s: expected the decoded feed's 'entries', got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["entries"]:
        if not isinstance(entry, dict):
            result.problem(None, "entry is %s, not an object" % type(entry).__name__)
            continue
        url = entry.get("link")
        external_id = str(url or "").strip().rstrip("/").rsplit("/", 1)[-1]
        if not require_absolute(url) or not external_id:
            result.problem(None, "link missing or not absolute: %r" % (url,))
            continue
        title = _text(entry.get("title"))
        if not title:
            result.problem(external_id, "no title")
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue
        content = entry.get("content")
        byline = _BYLINE.search(content or "")
        employer = _text(byline.group(1)) if byline else None
        result.postings.append(Posting(
            external_id=external_id,
            title=title,
            url=url,
            published_at=published_at,
            published_field=PUBLISHED_FIELD,
            published_raw=published_raw,
            source=PLATFORM,
            board_id=board.board_id,
            employer=employer,
            employer_provenance="payload" if employer else None,
            url_provenance="payload",
            location=_text(entry.get("location")) or None,
            description=(content,) if isinstance(content, str) and content.strip() else (),
            raw=entry,
        ))
    return result
