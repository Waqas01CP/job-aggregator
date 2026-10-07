"""Manatal career pages. One adapter serving every Manatal board in the
registry, never one per employer.

Endpoint: www.careers-page.com/api/v1.0/c/{slug}/jobs/?page={n}, the career
site's own JSON, twenty postings a page with a `next` link. **Manatal does not
document it.** It documents api.careers-page.com/open/v1/career-pages/{slug}/
job-posts, which on 2026-10-04 served five of the nine registry boards (the
other four answered CAREER_PAGE_NOT_FOUND) and gives no working link to a
posting: its id opens a 404, where this endpoint's `hash` opens the posting's
own page. The operator accepted this endpoint for all nine boards on
2026-10-07, on those facts, at about one request per twenty postings.

**No date of any kind.** Measured on 2026-10-04 over 779 postings on the nine
boards, on both endpoints (ADR-0029, research 0005's correction). So a
Manatal posting is never dropped for age, which ADR-0007 already allows, and
it sorts after every dated posting in the display, the operator's rule of
2026-10-07: no job is skipped for lacking a date. The documented endpoint can
filter on a creation date, `created_at__gte`, which brackets the day a
posting was created; it is not read here, since whether creation means
publication is the question ADR-0052 left open for Lever.

**No workplace field.** On-site work reaches D13 only through what the
description says (ADR-0057, ADR-0058).

**Its pages are not stable on every board.** Twenty postings a page,
whatever `page_size` asks. On 2026-10-07 Abacus Consulting's nine pages gave
its 168 postings once each, but on 2026-10-04 ITC Worldwide's 24 pages gave
477 reads of only 338 distinct postings against the 477 its `count` reports:
the order shifts between requests, so a walk repeats some postings and misses
others. A posting repeated within one walk is kept once, here. One missed is
read by a later walk, a delay rather than a loss, since a dateless posting
never ages out, and it cannot be closed for it: closure needs twelve walks in
a row to miss it (ADR-0050).

Fields read, from the 779 postings of 2026-10-04: `id` and `hash` on every
one, `position_name`, `location_display`, `city`, `state`, `country`,
`organization_name` on some boards and absent on others, and `description`,
HTML, handed to the normaliser, which keeps only what it states. The posting
whole goes to the private full branch only (D11).
"""

from urllib.parse import parse_qs, urlparse

from .base import AdapterError, ParseResult, Posting

PLATFORM = "manatal"
BASE = "https://www.careers-page.com/api/v1.0/c/%s/jobs/?page=%d"
JOB_PAGE = "https://www.careers-page.com/%s/job/%s"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, and tests/test_contract.py holds them to the code.
CONSUMED_RESPONSE = ("results", "next")
POSTINGS_AT = "results"
CONSUMED = ("id", "hash", "position_name", "organization_name", "location_display", "city",
            "state", "country", "description")

# Read to the end, every page: with no date, nothing can say where to stop.
# The run's walk takes this as a feed to page through, and ADR-0050's closure
# test counts a walk that reached the end as having looked at every posting.
PAGINATED = True


def url_for(board, cursor=None):
    return BASE % (board.slug, cursor or 1)


def next_cursor(payload):
    """The page `next` names, or None on the last page."""
    link = payload.get("next") if isinstance(payload, dict) else None
    if not link:
        return None
    pages = parse_qs(urlparse(link).query).get("page")
    try:
        return int(pages[0]) if pages else None
    except ValueError:
        return None


def stop_after(payload, high_water):
    """Never: a walk with no dates has no mark to stop at."""
    return False


def _place(entry):
    shown = str(entry.get("location_display") or "").strip()
    if shown:
        return shown
    parts = [str(entry.get(k) or "").strip() for k in ("city", "state", "country")]
    return ", ".join(p for p in parts if p) or None


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise AdapterError("%s: expected an object with a 'results' list, got %s"
                           % (board.board_id, type(payload).__name__))

    result = ParseResult()
    read = set()
    for entry in payload["results"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue

        external_id = entry.get("id")
        external_id = str(external_id) if external_id is not None else None
        if not external_id:
            result.problem(None, "no id")
            continue
        if external_id in read:
            # The same posting on a second page of one walk: the pages shift.
            continue
        read.add(external_id)

        title = str(entry.get("position_name") or "").strip()
        if not title:
            result.problem(external_id, "no position_name")
            continue

        page = str(entry.get("hash") or "").strip()
        if not page:
            result.problem(external_id, "no hash, so no link to the posting")
            continue

        # ADR-0026: the employer as the payload names it, else the board's
        # configured name, else recorded as unresolved.
        employer = str(entry.get("organization_name") or "").strip() or None
        provenance = "payload" if employer else None
        if employer is None and board.employer_alias:
            employer, provenance = board.employer_alias, "slug"

        country = str(entry.get("country") or "").strip()
        result.postings.append(Posting(
            external_id=external_id,
            title=title,
            url=JOB_PAGE % (board.slug, page),
            published_at=None,
            published_field=None,
            published_raw=None,
            source=PLATFORM,
            board_id=board.board_id,
            employer=employer,
            employer_provenance=provenance,
            url_provenance="constructed",
            location=_place(entry),
            places=(country,) if country else None,
            description=(entry.get("description"),),
            raw=entry,
        ))
    return result
