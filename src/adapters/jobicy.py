"""Jobicy. ADR-0063's second wave, after Hacker News: built 2026-10-18, first
of the other three, by its yield (2 a week kept against RemoteOK's 3 a
month and We Work Remotely's 1) and its 71 postings naming a person to
write to (the seat's report on Brief 15).

Endpoint, Jobicy's public Jobs API, keyless: jobicy.com/api/v2/remote-jobs,
1 to 200 a request, newest first, the last 7 days with a 3-hour delay, paged
by `nextCursor` while `hasMore`. Its terms, read 2026-10-18: "Polling a few
times per day is normally sufficient and must not exceed once per hour"; a
pass follows its cursor pages in order; "Do not present Jobicy listings as
your own original job postings or remove source attribution". Two runs a
day, each walking back only to what is stored, keep to them, and each row
links to Jobicy's own page and names it as its board. The employer's own
application link needs a paid key, which the scope floor excludes.

Fields, measured over the 833 postings of 2026-10-12 to 10-18:

  identity     `id`                 100%
  title        `jobTitle`           100%
  link         `url`                100%, the posting's page on Jobicy
  publication  `pubDate`            100%, ISO with an offset
  employer     `companyName`        100%
  place        `jobGeo`             100%, a country, a region or "Anywhere":
               USA 19, UK 8, Canada 7, Anywhere 4 in the first hundred
  workplace    every posting is remote by the feed's own scope
  level        `jobLevel`: Senior, Director, Midweight, or Any, which states
               none; read through the levels that drop
  description  `jobDescription`, HTML

Today's rules, read fresh, keep 2 of the 833.
"""

import html
from datetime import datetime
from urllib.parse import quote

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "jobicy"
BASE = "https://jobicy.com/api/v2/remote-jobs?count=200"
PUBLISHED_FIELD = "pubDate"

# ADR-0018: what parse() reads, and nothing else.
CONSUMED_RESPONSE = ("jobs", "nextCursor", "hasMore")
POSTINGS_AT = "jobs"
CONSUMED = ("id", "jobTitle", "url", PUBLISHED_FIELD, "companyName", "jobGeo", "jobLevel",
            "jobDescription")

# Newest first and paged by cursor, read back to what is stored: one page
# of 200 a run at about 120 postings a day, five on a first walk.
PAGINATED = True
# "Any" is Jobicy's word for no level stated.
NO_LEVEL = "any"


def url_for(board, cursor=None):
    return BASE + ("&cursor=%s" % quote(cursor, safe="") if cursor else "")


def next_cursor(payload):
    if not isinstance(payload, dict) or not payload.get("hasMore"):
        return None
    cursor = payload.get("nextCursor")
    return cursor if isinstance(cursor, str) and cursor else None


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def stop_after(payload, high_water):
    """True when no posting on this page is newer than what is stored, the
    whole page, as Himalayas' walk judges it."""
    if not high_water or not isinstance(payload, dict):
        return False
    dated = [_parse_time(e.get(PUBLISHED_FIELD)) for e in payload.get("jobs") or []
             if isinstance(e, dict)]
    dated = [d.isoformat().replace("+00:00", "Z") for d in dated if d is not None]
    return bool(dated) and all(d <= high_water for d in dated)


def _text(value):
    return " ".join(html.unescape(str(value or "")).split())


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise AdapterError("%s: expected an object with a 'jobs' list, got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["jobs"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue
        external_id = str(entry.get("id") or "").strip()
        if not external_id:
            result.problem(None, "no id")
            continue
        title = _text(entry.get("jobTitle"))
        if not title:
            result.problem(external_id, "no jobTitle")
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
        employer = _text(entry.get("companyName")) or None
        level = _text(entry.get("jobLevel"))
        description = entry.get("jobDescription")
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
            location=_text(entry.get("jobGeo")) or None,
            workplace="remote",
            levels=(level,) if level and level.lower() != NO_LEVEL else None,
            description=(description,) if isinstance(description, str) and description.strip()
            else (),
            raw=entry,
        ))
    return result
