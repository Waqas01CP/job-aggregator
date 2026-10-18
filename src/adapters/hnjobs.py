"""Hacker News' job stories: the posts Y Combinator companies place on its
jobs page. ADR-0063's second wave, with the Who is hiring thread
(src/adapters/hackernews.py), built 2026-10-18.

Endpoint: hn.algolia.com/api/v1/search_by_date?tags=job, keyless, no limit
stated (research 0005), one request a run, the newest hundred under `hits`.
13 job stories in the 30 days to 2026-10-17; 2 kept by today's rules (the
seat's report on Brief 15).

Fields, measured over those 13:

  identity   `objectID`
  title      `title`, a sentence: "Coris (YC S22) Is Hiring Back End Engineer"
  employer   the title before its batch or "is hiring"
  published  `created_at`
  link       the story's own page on Hacker News, which names the source
             (ADR-0063); `url`, the employer's page, is not read
  description `story_text`, which job stories seldom carry: absent, the
             posting carried none
  place      none stated; the title rarely says, so the location rule keeps
             it, as any place it cannot name
"""

import re
from datetime import datetime

from .base import AdapterError, ParseResult, Posting

PLATFORM = "hnjobs"
# The tag is Algolia's, fixed here rather than taken from the board's slug:
# a slug is read as an employer's name, and "job" would name every literal.
BASE = "https://hn.algolia.com/api/v1/search_by_date?tags=job&hitsPerPage=100"
PAGE = "https://news.ycombinator.com/item?id=%s"

PUBLISHED_FIELD = "created_at"

# ADR-0018: what parse() reads, and nothing else.
CONSUMED_RESPONSE = ("hits",)
POSTINGS_AT = "hits"
CONSUMED = ("objectID", "title", PUBLISHED_FIELD, "story_text")

_EMPLOYER = re.compile(r"(?i)^(.+?)\s*(?:\(\s*YC\s+[A-Z]\d{2}\s*\)\s*)?(?:is\s+hiring|hiring)\b")
_YC = re.compile(r"(?i)\s*\(\s*YC\s+[A-Z]\d{2}\s*\)")


def url_for(board):
    return BASE


def employer_of(title):
    m = _EMPLOYER.match(title)
    if not m:
        return None
    name = _YC.sub("", m.group(1)).strip(" -,")
    return name[:80] or None


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("hits"), list):
        raise AdapterError("%s: expected an object with a 'hits' list, got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["hits"]:
        if not isinstance(entry, dict):
            result.problem(None, "story is %s, not an object" % type(entry).__name__)
            continue
        external_id = str(entry.get("objectID") or "").strip()
        if not external_id:
            result.problem(None, "no objectID")
            continue
        title = " ".join(str(entry.get("title") or "").split())
        if not title:
            result.problem(external_id, "no title")
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue
        employer = employer_of(title)
        text = entry.get("story_text")
        result.postings.append(Posting(
            external_id=external_id,
            title=title,
            url=PAGE % external_id,
            published_at=published_at,
            published_field=PUBLISHED_FIELD,
            published_raw=published_raw,
            source=PLATFORM,
            board_id=board.board_id,
            employer=employer,
            employer_provenance="payload" if employer else None,
            url_provenance="constructed",
            description=(text,) if isinstance(text, str) and text.strip() else (),
            raw=entry,
        ))
    return result
