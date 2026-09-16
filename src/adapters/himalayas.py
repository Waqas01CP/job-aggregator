"""Himalayas. An aggregator feed, not an employer board. ADR-0019.

Browse endpoint only: `himalayas.app/jobs/api?limit=20`, cursor pagination.

The search endpoint is not used and must not be. Measured on 2026-09-16:
`sort=recent` is not ordered by date, breaking at positions 3, 5 and 8 of 13,
and it accepts a `cursor` parameter and silently ignores it, returning a
byte-identical page. Browse is ordered by `pubDate` descending with no
duplicates across 60 postings over three pages.

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

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "himalayas"
SOURCE_CLASS = "aggregator"
BASE = "https://himalayas.app/jobs/api?limit=%d"
PAGE_SIZE = 20

PUBLISHED_FIELD = "pubDate"

# Epoch seconds for plausible posting dates, so a millisecond value cannot
# silently become the year 58000.
_S_MIN = 1_000_000_000      # 2001-09-09
_S_MAX = 4_000_000_000      # 2096-10-02

PAGINATED = True


def url_for(board, cursor=None):
    url = BASE % PAGE_SIZE
    return "%s&cursor=%s" % (url, cursor) if cursor else url


def next_cursor(payload):
    """The cursor for the following page, or None at the end of the feed."""
    return payload.get("nextCursor") if isinstance(payload, dict) else None


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
            location = ", ".join(str(r) for r in restrictions[:3])
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
        ))
    return result


def stop_after(payload, high_water):
    """True when this page has reached postings already stored.

    `high_water` is the newest `pubDate` the pipeline has actually stored, as
    an ISO string, not the previous run's clock. Anchoring on the clock would
    step over postings that reach this feed late, and the feed is known to
    trail by at least 97.7 minutes."""
    if not high_water:
        return False
    for entry in payload.get("jobs", []):
        published = _parse_epoch_s(entry.get(PUBLISHED_FIELD))
        if published is None:
            continue
        if published.isoformat().replace("+00:00", "Z") <= high_water:
            return True
    return False
