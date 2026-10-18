"""Hacker News' monthly "Ask HN: Who is hiring?" thread. ADR-0063's second
wave, first: built 2026-10-18 on the operator's word, "building should be
done right now".

Endpoints, Algolia's Hacker News API, keyless, no limit stated (research
0005), two requests a run:

  locator  hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring:
           the `whoishiring` account's newest stories, under `hits`; `follow`
           picks the newest titled "Ask HN: Who is hiring?", since the same
           account posts "Who wants to be hired?" beside it
  thread   hn.algolia.com/api/v1/items/{id}: the thread as one tree, every
           top-level comment a post under `children`, replies under each

Measured over October 2026's thread, 266 posts, on 2026-10-18 (the seat's
report on Brief 15): written by people at the hiring company, 77 giving an
email address; 27 kept by today's rules if read fresh, 16 of them on site.

**A post is free text.** By convention its first line is a header, company,
role, place and terms separated by "|", and the rest is the description.
Read here, provisionally, and held by tests of their own:

  title      the header, whole, up to 200 characters; the title and
             seniority rules read it as they read any title
  employer   the header's first part, any address in it taken out
  location   the header's parts after the first, still separated by "|",
             which the location rule splits on. Company, role and pay are
             parts no place rule can name, so for this source the rule
             leaves them out (`header_place_sources` in
             config/eligibility.json, ADR-0057's row of 2026-10-18)
  workplace  from the header's words: remote wherever "remote" is said and
             not denied, else hybrid, else on site, else nothing. A header
             saying both on site and remote offers a remote option, so it
             reads remote
  link       the post's own page on Hacker News, which names the source
             (ADR-0063); its links to the employer are in the description
  published  the comment's `created_at`, when it was posted
  description  the whole comment, header included

No structured country: a post's place is only what its header says, and
the place rules decide what they can name.
"""

import html
import re
from datetime import datetime

from .base import AdapterError, ParseResult, Posting

PLATFORM = "hackernews"
LOCATOR = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_%s&hitsPerPage=10"
THREAD = "https://hn.algolia.com/api/v1/items/%s"
PAGE = "https://news.ycombinator.com/item?id=%s"

PUBLISHED_FIELD = "created_at"
THREAD_TITLE = re.compile(r"(?i)^\s*ask hn:\s*who is hiring\?")

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints the thread, after the same follow step the run takes; the
# locator's fields are declared too, so a test holds them to the code.
CONSUMED_RESPONSE = ("children", "title")
POSTINGS_AT = "children"
CONSUMED = ("id", PUBLISHED_FIELD, "text")
CONSUMED_LOCATOR = ("hits", "hits.title", "hits.objectID", "hits.created_at_i")

_TAG = re.compile(r"<[^>]+>")
# The first line ends at the first paragraph or line break: Fastly's post of
# October 2026 ran its header into its description with a bare newline.
_PARAGRAPH = re.compile(r"(?i)<p>|<br\s*/?>|\n")
_ADDRESS = re.compile(r"\(\s*(?:https?://|www\.)[^)]*\)|https?://\S+|www\.\S+")
_DASH = re.compile(r"\s[–—-]\s")
_REMOTE = re.compile(r"(?i)\bremote\b")
_NOT_REMOTE = re.compile(r"(?i)\b(?:no|not)\s+remote\b")
_HYBRID = re.compile(r"(?i)\bhybrid\b")
_ON_SITE = re.compile(r"(?i)\bon-?site\b|\bin[- ]person\b|\bin[- ]office\b")
TITLE_LIMIT = 200


def url_for(board):
    return LOCATOR % board.slug


def follow(board, payload):
    """The newest "Who is hiring?" thread among the account's stories, or
    None when there is none, which the parse then refuses."""
    hits = payload.get("hits") if isinstance(payload, dict) else None
    threads = [h for h in hits or [] if isinstance(h, dict)
               and THREAD_TITLE.match(str(h.get("title") or "")) and h.get("objectID")]
    if not threads:
        return None
    newest = max(threads, key=lambda h: h.get("created_at_i") or 0)
    return THREAD % newest["objectID"]


def header_of(text):
    """The post's first line, as plain text."""
    first = _PARAGRAPH.split(text or "", maxsplit=1)[0]
    return " ".join(html.unescape(_TAG.sub(" ", first)).split())


def parts_of(header):
    return [p.strip() for p in header.split("|") if p.strip()]


def employer_of(header):
    parts = parts_of(header)
    first = parts[0] if len(parts) > 1 else _DASH.split(header, maxsplit=1)[0]
    name = " ".join(_ADDRESS.sub(" ", first).split()).strip(" -,")
    return name[:80] or None


def location_of(header):
    parts = parts_of(header)
    return " | ".join(parts[1:]) if len(parts) > 1 else (header or None)


def workplace_of(header):
    if _REMOTE.search(header) and not _NOT_REMOTE.search(header):
        return "remote"
    if _HYBRID.search(header):
        return "hybrid"
    if _ON_SITE.search(header):
        return "on site"
    return None


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def parse(payload, board):
    # A thread naming itself as another, "Who wants to be hired?", is
    # refused. A payload with no title is a saved post the re-read wraps
    # (src/facts.py, `envelope`), and is read.
    title = payload.get("title") if isinstance(payload, dict) else None
    if (not isinstance(payload, dict) or not isinstance(payload.get("children"), list)
            or (title is not None and not THREAD_TITLE.match(str(title)))):
        raise AdapterError("%s: expected a Who is hiring thread with its 'children', got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["children"]:
        if not isinstance(entry, dict):
            result.problem(None, "post is %s, not an object" % type(entry).__name__)
            continue
        text = entry.get("text")
        if not isinstance(text, str) or not text.strip():
            # A deleted or flagged post: no text and no author, nothing to
            # apply to. Not a broken posting, so not a problem.
            continue
        external_id = str(entry.get("id") or "").strip()
        if not external_id:
            result.problem(None, "no id")
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue
        header = header_of(text)
        if not header:
            result.problem(external_id, "no first line to read a title from")
            continue
        employer = employer_of(header)
        result.postings.append(Posting(
            external_id=external_id,
            title=header[:TITLE_LIMIT],
            url=PAGE % external_id,
            published_at=published_at,
            published_field=PUBLISHED_FIELD,
            published_raw=published_raw,
            source=PLATFORM,
            board_id=board.board_id,
            employer=employer,
            employer_provenance="payload" if employer else None,
            url_provenance="constructed",
            location=location_of(header),
            workplace=workplace_of(header),
            description=(text,),
            # The post without its replies: other people's comments are not
            # part of the posting.
            raw={k: v for k, v in entry.items() if k != "children"},
        ))
    return result
