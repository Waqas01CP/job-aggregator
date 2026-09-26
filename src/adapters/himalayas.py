"""Himalayas. An aggregator feed, not an employer board. ADR-0019.

**The search endpoint, filtered to one country**, since 2026-09-26:
`himalayas.app/jobs/api/search?country=<slug>&sort=recent&page=<n>`. The
board's slug is the country, so the board reads `himalayas:pakistan`. The
operator's go that day, after asking "is it not possible that we trim it
beforehand to not fetch a lot?".

**Why search, reversing 2026-09-16.** That measurement rejected search
because `sort=recent` was out of order and a `cursor` was silently ignored.
But the API documents `page` for search, not `cursor`, so the second finding
tested the wrong parameter. Re-measured on 2026-09-26 with `page`:
- three pages, 59 distinct postings, no repeats;
- newest first, except four pinned postings at the top of page one;
- all 59 eligible under the operator's D13, since the country filter keeps
  worldwide postings too;
- 2,965 in total, about 92 new a day.

Browse, the whole feed, spent 25 pages a morning to reach about a third of
Himalayas' 1,600 postings a day, of which 7% are open to Pakistan. Search
reaches all of those in about five pages. D13's location rule still runs
on every row, as a second guard.

**The stop rule looks at the whole page.** A page stops the walk only when
none of its postings is newer than what is stored: the pinned postings at
the top are old, and the old "any posting" rule would have stopped on them
after one page.

Fields, measured on 20 postings:

  title          `title`             100%
  employer       `companyName`       100%
  canonical URL  `applicationLink`   100%, absolute
  publication    `pubDate`           100%, epoch seconds
  expiry         `expiryDate`        100%, epoch seconds

There is no `id`. `guid` is the identifier.

**The stop rule anchors on the newest `pubDate` already stored, never on clock
time.** Browse trails the search endpoint by at least 97.7 minutes, so a
posting can reach this feed after a run with a `pubDate` earlier than that
run's clock. A clock-anchored stop would step over it and never look again.

This adapter paginates, which an employer board does not. It does not fetch:
it builds the URL for a page and reads the cursor out of the response, and the
orchestrator drives the loop through the shared HTTP module.
"""

from datetime import datetime, timezone
from urllib.parse import quote

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "himalayas"
SOURCE_CLASS = "aggregator"
BASE = "https://himalayas.app/jobs/api/search?country=%s&sort=recent&page=%s"
PAGE_SIZE = 20

PUBLISHED_FIELD = "pubDate"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, and tests/test_contract.py holds them to the code.
CONSUMED_RESPONSE = ("jobs", "offset", "limit", "totalCount")
POSTINGS_AT = "jobs"
CONSUMED = ("guid", "title", "applicationLink", PUBLISHED_FIELD, "expiryDate", "companyName",
            "locationRestrictions")

# Epoch seconds for plausible posting dates, so a millisecond value cannot
# silently become the year 58000.
_S_MIN = 1_000_000_000      # 2001-09-09
_S_MAX = 4_000_000_000      # 2096-10-02

PAGINATED = True


def url_for(board, cursor=None):
    """The search for postings open to the board's country; `cursor` is the
    page number, the first page when absent."""
    return BASE % (quote(board.slug), cursor or 1)


def next_cursor(payload):
    """The following page's number, or None past the last. Search pages by
    number: the envelope gives `offset`, `limit` and `totalCount`."""
    if not isinstance(payload, dict):
        return None
    offset, limit, total = payload.get("offset"), payload.get("limit"), payload.get("totalCount")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (offset, limit, total)):
        return None
    if limit <= 0 or offset + limit >= total:
        return None
    return str(offset // limit + 2)


def _parse_epoch_s(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not (_S_MIN <= value <= _S_MAX):
        return None
    return datetime.fromtimestamp(value, timezone.utc)


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise AdapterError("%s: expected an object with a 'jobs' list, got %s"
                           % (board.board_id, type(payload).__name__))

    result = ParseResult()
    for entry in payload["jobs"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue

        guid = entry.get("guid")
        if not guid:
            result.problem(None, "no guid")
            continue

        title = (entry.get("title") or "").strip()
        if not title:
            result.problem(guid, "no title")
            continue

        url = entry.get("applicationLink") or guid
        if not require_absolute(url):
            result.problem(guid, "applicationLink missing or not absolute: %r" % (url,))
            continue

        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_epoch_s(published_raw)
        if published_at is None:
            result.problem(guid, "%s missing or not plausible epoch seconds: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue

        expires = _parse_epoch_s(entry.get("expiryDate"))

        employer = (entry.get("companyName") or "").strip() or None
        restrictions = entry.get("locationRestrictions")
        if isinstance(restrictions, list) and restrictions:
            # Every country, never the first three: D13's location rule keeps
            # a posting that names Pakistan anywhere in its list, 2026-09-26.
            location = ", ".join(str(r) for r in restrictions)
        else:
            # An empty array is not the same as an absent field, and what it
            # means was never established. It is recorded as unstated rather
            # than read as worldwide.
            location = None

        result.postings.append(Posting(
            external_id=str(guid),
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
            location=location,
            expires_at=expires.isoformat().replace("+00:00", "Z") if expires else None,
            raw=entry,
        ))
    return result


def stop_after(payload, high_water):
    """True when no posting on this page is newer than what is stored.

    **The whole page, never one posting.** Search puts pinned postings at the
    top of page one, one of them ten days old on 2026-09-26, and stopping on
    the first old posting would end the walk there. A page whose every
    posting is at or before the mark is past the new ones.

    `high_water` is the newest `pubDate` this board has actually stored, as
    an ISO string, not the previous run's clock, or the age limit when that
    is later: the run passes whichever is. Anchoring on the clock would step
    over postings that reach the feed late, and it is known to trail."""
    if not high_water:
        return False
    dated = [_parse_epoch_s(e.get(PUBLISHED_FIELD)) for e in payload.get("jobs", [])]
    dated = [d.isoformat().replace("+00:00", "Z") for d in dated if d is not None]
    return bool(dated) and all(d <= high_water for d in dated)
