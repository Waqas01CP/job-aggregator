"""Greenhouse. One adapter serving nine boards, never one per employer.

Endpoint: boards-api.greenhouse.io/v1/boards/{slug}/jobs

Fields, measured on 1598 postings across nine boards on 2026-09-11, not
re-derived here:

  title            `title`            100%
  employer         `company_name`     100%
  canonical URL    `absolute_url`     100%, all absolute
  location         `location.name`    100%
  publication      `first_published`  100%, ISO-8601 with offset

`?content=true` is never sent. It adds the employer's description text at 9.5
times the payload size, and ADR-0011 keeps description text out of this
repository entirely.

`updated_at` is present and is never used. It is written in bulk, not on edit:
Greenhouse rewrote roughly 265 Speechify postings on each of four dates.
ADR-0018 bars it as a change signal.

`application_deadline` is present on every posting and was null on all 1598.
It is read anyway, because a null field that starts carrying values is exactly
what the expiry filter is for.
"""

from datetime import datetime, timezone

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "greenhouse"
BASE = "https://boards-api.greenhouse.io/v1/boards/%s/jobs"

PUBLISHED_FIELD = "first_published"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, and tests/test_contract.py holds them to the code.
CONSUMED_RESPONSE = ("jobs",)
POSTINGS_AT = "jobs"
CONSUMED = ("id", "title", "absolute_url", PUBLISHED_FIELD, "application_deadline",
            "application_deadline.date", "company_name", "location", "location.name")


def url_for(board):
    return BASE % board.slug


def _parse_iso(value):
    """ISO-8601 with offset, as Greenhouse returns it. Converted to UTC so
    every row in the store is comparable without reading its offset."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise AdapterError(
            "%s: expected an object with a 'jobs' list, got %s"
            % (board.board_id, type(payload).__name__))

    result = ParseResult()
    for entry in payload["jobs"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue

        external_id = entry.get("id")
        external_id = str(external_id) if external_id is not None else None
        if not external_id:
            result.problem(None, "no id")
            continue

        title = (entry.get("title") or "").strip()
        if not title:
            result.problem(external_id, "no title")
            continue

        url = entry.get("absolute_url")
        if not require_absolute(url):
            result.problem(external_id, "absolute_url missing or not absolute: %r" % (url,))
            continue

        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_iso(published_raw)
        if published_at is None:
            result.problem(external_id,
                           "%s missing or unparseable: %r" % (PUBLISHED_FIELD, published_raw))
            continue

        # Null on all 1598 postings measured, and read anyway: the expiry
        # rule exists for the day a board starts populating it.
        expires_at = entry.get("application_deadline") or None
        if isinstance(expires_at, dict):
            expires_at = expires_at.get("date") or None

        employer = (entry.get("company_name") or "").strip() or None
        location = entry.get("location") or {}
        location_name = (location.get("name") or "").strip() if isinstance(location, dict) else None

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
            location=location_name or None,
            expires_at=expires_at,
        ))
    return result
