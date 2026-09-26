"""Lever. One adapter serving two boards.

Endpoint: api.lever.co/v0/postings/{slug}?mode=json, a top-level array.

Fields, measured on 48 postings across both boards on 2026-09-11:

  title            `text`                  100%
  canonical URL    `hostedUrl`             100%, all absolute
  location         `categories.location`   100%
  publication      `createdAt`             100%, epoch milliseconds

**Lever returns no employer field.** Every key on all 48 postings was
enumerated and none contains `compan`, `employ` or `org`. The employer is the
configuration slug, which appears in `hostedUrl` on 48 of 48. ADR-0026 requires
it to be derived with recorded provenance and expanded through the alias map,
and requires the absence of an alias to be recorded rather than guessed: a slug
is not a name, and comparing `smart-working-solutions` against "Smart Working
Solutions" as though equivalent would produce silent deduplication misses.

**`createdAt`'s meaning is unproven.** It is the only creation-time field and
nothing is named for publication. It is treated as the publication date and the
row records that the reading is unconfirmed. The pipeline settles this itself:
a posting first seen in a run whose `createdAt` predates the previous run's
clock proves `createdAt` precedes visibility.
"""

from datetime import datetime, timezone

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "lever"
BASE = "https://api.lever.co/v0/postings/%s?mode=json"

PUBLISHED_FIELD = "createdAt"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, and tests/test_contract.py holds them to the code.
# The response is the list of postings itself.
CONSUMED_RESPONSE = ()
POSTINGS_AT = None
CONSUMED = ("id", "text", "hostedUrl", PUBLISHED_FIELD, "categories", "categories.location")

# Recorded on every Lever row. Removed when a second observation settles it.
PUBLISHED_MEANING_UNCONFIRMED = True

# Epoch milliseconds for plausible posting dates. A value outside this range is
# a unit error, most likely seconds mistaken for milliseconds, which would date
# a 2026 posting to 1970 and quietly pass every downstream check.
_MS_MIN = 1_000_000_000_000   # 2001-09-09
_MS_MAX = 4_000_000_000_000   # 2096-10-02


def url_for(board):
    return BASE % board.slug


def _parse_epoch_ms(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not (_MS_MIN <= value <= _MS_MAX):
        return None
    return datetime.fromtimestamp(value / 1000.0, timezone.utc)


def parse(payload, board):
    if not isinstance(payload, list):
        raise AdapterError("%s: expected a top-level array, got %s"
                           % (board.board_id, type(payload).__name__))

    # ADR-0026: derived, expanded through the alias map, absence recorded.
    employer = board.employer_alias or None
    employer_provenance = "slug" if employer else None

    result = ParseResult()
    for entry in payload:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue

        external_id = entry.get("id")
        external_id = str(external_id) if external_id is not None else None
        if not external_id:
            result.problem(None, "no id")
            continue

        title = (entry.get("text") or "").strip()
        if not title:
            result.problem(external_id, "no text (title)")
            continue

        url = entry.get("hostedUrl")
        if not require_absolute(url):
            result.problem(external_id, "hostedUrl missing or not absolute: %r" % (url,))
            continue

        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_epoch_ms(published_raw)
        if published_at is None:
            result.problem(external_id,
                           "%s missing or not plausible epoch ms: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue

        categories = entry.get("categories") or {}
        location = None
        if isinstance(categories, dict):
            location = (categories.get("location") or "").strip() or None

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
            raw=entry,
        ))
    return result
