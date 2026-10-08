"""Workable. One adapter serving every Workable board in the registry, never
one per employer.

Endpoint: www.workable.com/api/accounts/{subdomain}?details=true, Workable's
documented public endpoint, read 2026-10-04: no authentication, one request
returning every published job with its description. It answers with a
redirect to apply.workable.com/api/v1/widget/accounts/{subdomain}, which
Workable does not document, and the client follows it within the one
request.

ADR-0059's first wave: Workable second by its own rule, on 2026-10-04 no
posting passing on any of the four platforms but Manatal, the tie broken by
registry boards, six against two each. Four of the six slugs were found
that day by their account's name matching the registry's employer, and the
operator added them to his registry marked unproven.

Fields, measured over 78 postings on six boards on 2026-10-04:

  identity        `shortcode`        100%
  title           `title`            100%
  link            `url`              100%, the job's own page; `application_url`
                                     is its form, the reverse of what the spec
                                     says of the two
  publication     `published_on`     100%, a date without a time, "The
                                     publication date of the job" by the spec
  place           `city`, `state`, `country`, and `locations[].countryCode`
  remote          `telecommuting`    100%, true on 22 of 78
  description     `description`      100%, with `details=true`

`workplace_type`, which the spec documents, appeared on none of the 78, so a
remote role is read from `telecommuting` and an on-site one only from what
the description says. Read anyway, so the day it arrives it is used.
`experience` states a level on some postings ("Entry level", "Mid-Senior
level"); whether the level rule reads it is the operator's, and until he
says, it is not read, as no employer board's level is.
"""

from datetime import datetime, timezone

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "workable"
BASE = "https://www.workable.com/api/accounts/%s?details=true"

PUBLISHED_FIELD = "published_on"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, and tests/test_contract.py holds them to the code.
CONSUMED_RESPONSE = ("jobs", "name")
POSTINGS_AT = "jobs"
CONSUMED = ("shortcode", "title", "url", PUBLISHED_FIELD, "city", "state", "country",
            "locations", "locations.countryCode", "telecommuting", "workplace_type",
            "description")


def url_for(board):
    return BASE % board.slug


def _parse_day(value):
    """A date without a time, as Workable gives it, read as that day's start
    in UTC: the day is all it states."""
    if not isinstance(value, str) or len(value.strip()) != 10:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _workplace(entry):
    stated = str(entry.get("workplace_type") or "").strip()
    if stated:
        return stated
    return "remote" if entry.get("telecommuting") is True else None


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise AdapterError("%s: expected an object with a 'jobs' list, got %s"
                           % (board.board_id, type(payload).__name__))

    # ADR-0026: the account's own name, else the board's configured name.
    account = str(payload.get("name") or "").strip() or None
    employer, provenance = (account, "envelope") if account else (
        (board.employer_alias, "slug") if board.employer_alias else (None, None))

    result = ParseResult()
    for entry in payload["jobs"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue
        external_id = str(entry.get("shortcode") or "").strip()
        if not external_id:
            result.problem(None, "no shortcode")
            continue
        title = str(entry.get("title") or "").strip()
        if not title:
            result.problem(external_id, "no title")
            continue
        url = entry.get("url")
        if not require_absolute(url):
            result.problem(external_id, "url missing or not absolute: %r" % (url,))
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_day(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue

        parts = [str(entry.get(k) or "").strip() for k in ("city", "state", "country")]
        codes = tuple(str(loc.get("countryCode")).strip() for loc in entry.get("locations") or []
                      if isinstance(loc, dict) and str(loc.get("countryCode") or "").strip())
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
            employer_provenance=provenance,
            url_provenance="payload",
            location=", ".join(p for p in parts if p) or None,
            places=codes or None,
            workplace=_workplace(entry),
            description=(entry.get("description"),),
            raw=entry,
        ))
    return result
