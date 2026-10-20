"""Startup.jobs, through its keyed API. ADR-0063's Changes of 2026-10-20,
research 0006: built 2026-10-20, measured first through the real chain (the
seat's report on Brief 18): of the 8,225 remote and Pakistani postings of its
last 14 days, today's rules keep 44 dated at their reading and November's 61.

**The keyed API, never the RSS feed.** Its terms forbid copying its content
"(including RSS feeds)", except "content accessed through our API in
accordance with the Startup Jobs API Terms of Service", whose terms permit
"Personal automations, bots, newsletters, and job-search tools that link back
to Startup Jobs". Each row links to the URL the API supplies, its page on
Startup.jobs, and names it as its board. **Its postings are kept past the
seven days its API terms set**, the operator's decision of 2026-10-20, the
one exception to ADR-0063's driver that a source be read under its own
terms; like every source's, a posting is stored once, at first sight, and
never refreshed.

Endpoint: api.startup.jobs/v1/jobs, `Authorization: Bearer <key>`, the key
`STARTUP_JOBS_API_KEY` in the run's environment, never in a URL or a log.
Live jobs of the last 14 days, newest first, up to 50 a page, paged by
`next_cursor` passed as `starting_after` while `has_more`. 20 requests a
minute, so this source is paced at one every 3.5 seconds. A run walks back
only to what is stored, about 12 pages a run at about 585 remote postings a
day (2026-10-20). Without the key the board is not polled and says why; an
ended key answers 401, which fails this source alone.

Two boards, each a query its slug carries, so the query is the
configuration's, never this module's (ADR-0031, ADR-0057), and the
preference audit, which reads a slug as an employer's name, finds none
here: `sj-workplace-<type>`, every job worked that way, the registry's
remote; and `sj-country-<code>`, every job in that country, every
workplace, the registry's the operator's own.

Fields, measured over the 8,225 of 2026-10-20:

  identity     `id`
  title        `title`
  link         `url`, the posting's page on Startup.jobs
  publication  `published_at`, ISO 8601, UTC
  employer     `company.name`
  place        `location`: city, state and country joined, as written;
               `country_code` the source's own country where given, 7,297
               of 8,225 (the United States 4,528)
  workplace    `workplace_type`: remote, hybrid or on-site
  description  `description_html`
"""

import html
from datetime import datetime

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "startupjobs"
BASE = "https://api.startup.jobs/v1/jobs?limit=50"
PUBLISHED_FIELD = "published_at"
# The key, from the run's environment. Never in a URL, a log or a file.
AUTH_ENV = "STARTUP_JOBS_API_KEY"
# Its 20 requests a minute, with room: seconds between this source's requests.
MIN_INTERVAL = 3.5
# Each board's query.
WORKPLACE_SLUG = "sj-workplace-"
COUNTRY_SLUG = "sj-country-"

# ADR-0018: what parse() reads, and nothing else.
CONSUMED_RESPONSE = ("data", "has_more", "next_cursor")
POSTINGS_AT = "data"
CONSUMED = ("id", "title", "url", PUBLISHED_FIELD, "company", "company.name", "location",
            "location.city", "location.state", "location.country", "location.country_code",
            "workplace_type", "description_html")

PAGINATED = True


def url_for(board, cursor=None):
    if board.slug.startswith(WORKPLACE_SLUG) and len(board.slug) > len(WORKPLACE_SLUG):
        query = "workplace_type=%s" % board.slug[len(WORKPLACE_SLUG):]
    elif board.slug.startswith(COUNTRY_SLUG) and len(board.slug) == len(COUNTRY_SLUG) + 2:
        query = "country=%s" % board.slug[len(COUNTRY_SLUG):].upper()
    else:
        raise AdapterError("%s: no Startup.jobs query for slug %r" % (board.board_id, board.slug))
    return "%s&%s%s" % (BASE, query, "&starting_after=%d" % cursor if cursor else "")


def next_cursor(payload):
    if not isinstance(payload, dict) or not payload.get("has_more"):
        return None
    cursor = payload.get("next_cursor")
    return cursor if isinstance(cursor, int) and not isinstance(cursor, bool) else None


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def stop_after(payload, high_water):
    """True when no posting on this page is newer than what is stored."""
    if not high_water or not isinstance(payload, dict):
        return False
    dated = [_parse_time(e.get(PUBLISHED_FIELD)) for e in payload.get("data") or []
             if isinstance(e, dict)]
    dated = [d.isoformat().replace("+00:00", "Z") for d in dated if d is not None]
    return bool(dated) and all(d <= high_water for d in dated)


def _text(value):
    return " ".join(html.unescape(str(value or "")).split())


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise AdapterError("%s: expected an object with a 'data' list, got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["data"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue
        external_id = str(entry.get("id") or "").strip()
        if not external_id:
            result.problem(None, "no id")
            continue
        title = _text(entry.get("title"))
        if not title:
            result.problem(external_id, "no title")
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
        company = entry.get("company") if isinstance(entry.get("company"), dict) else {}
        employer = _text(company.get("name")) or None
        where = entry.get("location") if isinstance(entry.get("location"), dict) else {}
        place = ", ".join(part for part in (_text(where.get("city")),
                                            _text(where.get("state")),
                                            _text(where.get("country"))) if part)
        country = _text(where.get("country_code")).upper()
        description = entry.get("description_html")
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
            location=place or None,
            places=(country,) if len(country) == 2 else None,
            workplace=_text(entry.get("workplace_type")) or None,
            description=(description,) if isinstance(description, str) and description.strip()
            else (),
            raw=entry,
        ))
    return result
