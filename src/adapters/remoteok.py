"""RemoteOK. ADR-0063's second wave, after Jobicy: built 2026-10-18, second
of the other three, its postings naming a recruiter in their process least
often of the three, 8 of 99 (the seat's report on Brief 15).

Endpoint: remoteok.com/api, keyless, one request a run, a top-level array:
its first element a legal notice, then its newest postings, 99 on
2026-10-18, from 2026-08-12 to 10-17. The notice's terms: "Please link back
(with follow, and without nofollow!) to the URL on Remote OK and mention
Remote OK as a source ... If you do not we'll have to suspend API access."
Each row links to its page on Remote OK and names it as its board; the
display's link is a plain one. `apply_url` is Remote OK's own redirect, on
all 99, and is not followed.

Fields, measured over those 99:

  identity     `id`                 100%, a string
  title        `position`           100%
  link         `url`                100%, the posting's page on Remote OK
  publication  `date`               100%, ISO with an offset
  employer     `company`            100%
  place        `location`           52 of 99; empty on 47, which says
               nothing, so the location rule keeps it
  workplace    remote by the feed's own scope
  description  `description`, HTML

Today's rules, read fresh, keep 6 of the 99.
"""

import html
from datetime import datetime

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "remoteok"
BASE = "https://remoteok.com/api"
PUBLISHED_FIELD = "date"
# The legal notice is an element of the array, known by this key.
NOTICE = "legal"

# ADR-0018: what parse() reads, and nothing else. The response is the array.
CONSUMED_RESPONSE = ()
POSTINGS_AT = None
CONSUMED = ("id", "position", "url", PUBLISHED_FIELD, "company", "location", "description",
            NOTICE)


def url_for(board):
    return BASE


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _text(value):
    return " ".join(html.unescape(str(value or "")).split())


def parse(payload, board):
    if not isinstance(payload, list):
        raise AdapterError("%s: expected a top-level array, got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue
        if entry.get(NOTICE) is not None:
            # The terms, not a posting.
            continue
        external_id = str(entry.get("id") or "").strip()
        if not external_id:
            result.problem(None, "no id")
            continue
        title = _text(entry.get("position"))
        if not title:
            result.problem(external_id, "no position")
            continue
        url = entry.get("url")
        if not require_absolute(url):
            result.problem(external_id, "url missing or not absolute: %r" % (url,))
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue
        employer = _text(entry.get("company")) or None
        description = entry.get("description")
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
            workplace="remote",
            description=(description,) if isinstance(description, str) and description.strip()
            else (),
            raw=entry,
        ))
    return result
