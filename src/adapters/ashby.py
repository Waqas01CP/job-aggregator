"""Ashby. One adapter serving every Ashby board in the registry, never one
per employer.

Endpoint, Ashby's public job board API, read 2026-10-04 and live on
2026-10-17, no authentication: api.ashbyhq.com/posting-api/job-board/{board},
one request a board, every listed posting with its description, under
`jobs` beside `apiVersion`.

ADR-0059's first wave, fourth, after Manatal, Workable and SmartRecruiters:
the operator's order of 2026-10-09 and his go of 2026-10-17. Two registry
boards, Overjet (Part 3) and deeter-analytics (Part 12), 30 and 3 postings on
2026-10-17.

Fields, measured over those 33 postings on 2026-10-17:

  identity     `id`                 100%, a UUID, the last segment of
               `jobUrl` on 33 of 33
  title        `title`              100%
  link         `jobUrl`             100%, the posting's own page
  publication  `publishedAt`        100%, ISO 8601 with an offset. Ashby
               defines it as when the posting was last published, so a
               republish of the same posting moves it (ADR-0052's row of
               2026-10-09). **The first value is kept by the store, not
               here:** the run appends only identities it has not seen, so a
               posting read again with a later date is never stored again,
               and its row keeps the date its first sight carried. A new
               posting for an old job has a new id and enters as new.
  employer     none. Every key on all 33 was enumerated: no company field,
               the Lever case (ADR-0026), so the board's alias, provenance
               `slug`
  place        `location`, and each of `secondaryLocations`' own
               `location`, one place each, so D13 drops a posting only when
               every place it lists is closed: Overjet's "Egypt" posting
               lists Pakistan second. Their `address.postalAddress
               .addressCountry`, a country's name, not a code, as the
               structured places; absent on 8 of 33 primary addresses, each
               of them "United States, Remote"
  workplace    `workplaceType`: Remote, Hybrid or OnSite, 100%. `isRemote`
               is true on Hybrid postings too, so it is not read
  level        none stated
  description  `descriptionHtml`, in the list itself: no detail request

What today's rules make of the 33, through the real chain on 2026-10-17:
none kept, title 32, seniority 1. Five list Pakistan among their places.
"""

from datetime import datetime, timezone

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "ashby"
BASE = "https://api.ashbyhq.com/posting-api/job-board/%s?includeCompensation=true"

PUBLISHED_FIELD = "publishedAt"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, and tests/test_contract.py holds them to the code.
CONSUMED_RESPONSE = ("jobs",)
POSTINGS_AT = "jobs"
CONSUMED = ("id", "title", "jobUrl", PUBLISHED_FIELD, "location",
            "address", "address.postalAddress", "address.postalAddress.addressCountry",
            "secondaryLocations", "secondaryLocations.location",
            "secondaryLocations.address", "secondaryLocations.address.postalAddress",
            "secondaryLocations.address.postalAddress.addressCountry",
            "workplaceType", "descriptionHtml")


def url_for(board):
    return BASE % board.slug


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None


def _country(entry):
    address = entry.get("address") if isinstance(entry.get("address"), dict) else {}
    postal = address.get("postalAddress") if isinstance(address.get("postalAddress"),
                                                        dict) else {}
    return str(postal.get("addressCountry") or "").strip()


def _places(entry):
    """(the location text, the countries), the posting's own place first and
    each secondary location after it, each named once. The text's places are
    joined by semicolons, which the location rule reads as separate places."""
    located = [entry] + [s for s in (entry.get("secondaryLocations") or [])
                         if isinstance(s, dict)]
    texts, countries = [], []
    for item in located:
        text = str(item.get("location") or "").strip()
        if text and text not in texts:
            texts.append(text)
        country = _country(item)
        if country and country not in countries:
            countries.append(country)
    return "; ".join(texts) or None, tuple(countries) or None


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise AdapterError("%s: expected an object with a 'jobs' list, got %s"
                           % (board.board_id, type(payload).__name__))

    # ADR-0026: derived, expanded through the alias map, absence recorded.
    employer = board.employer_alias or None
    employer_provenance = "slug" if employer else None

    result = ParseResult()
    for entry in payload["jobs"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue
        external_id = str(entry.get("id") or "").strip()
        if not external_id:
            result.problem(None, "no id")
            continue
        title = str(entry.get("title") or "").strip()
        if not title:
            result.problem(external_id, "no title")
            continue
        url = entry.get("jobUrl")
        if not require_absolute(url):
            result.problem(external_id, "jobUrl missing or not absolute: %r" % (url,))
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue
        location, places = _places(entry)
        html = entry.get("descriptionHtml")
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
            employer_provenance=employer_provenance,
            url_provenance="payload",
            location=location,
            places=places,
            workplace=str(entry.get("workplaceType") or "").strip() or None,
            # In the list itself, so read on every sight: an empty tuple is a
            # posting that carried none, never one not read.
            description=(html,) if isinstance(html, str) and html.strip() else (),
            raw=entry,
        ))
    return result
