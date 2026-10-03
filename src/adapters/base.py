"""What every adapter returns, and the errors it may raise.

An adapter knows one platform's response shape and nothing else. It builds the
URL for a board and turns a decoded payload into `Posting` objects. It does not
fetch, retry, count budget, or decide what to keep: that is the HTTP module's
job and the filter chain's job respectively.

A `Posting` is platform-level, not canonical. It carries the values the
platform actually returned plus where each came from. Mapping onto the one row
shape is the normaliser's job, so that adding a platform never edits the shape.
"""

from dataclasses import dataclass, field
from datetime import datetime

# ADR-0026, as amended 2026-09-16. How a value was obtained. A derived value is
# never indistinguishable from a returned one.
PROVENANCE = frozenset({"payload", "envelope", "slug", "url", "constructed"})


class AdapterError(Exception):
    """The payload is not the shape this adapter was written for.

    Raised for envelope-level surprises, never for one posting missing an
    optional field. A board that changes shape should stop the board, not be
    silently half-parsed. ADR-0018's contract check exists for this class of
    change."""


@dataclass
class Posting:
    """One posting as the platform returned it."""
    external_id: str
    title: str
    url: str
    published_at: datetime          # timezone-aware, UTC
    published_field: str            # the field name it came from, verbatim
    published_raw: object           # the value as returned, for the log
    source: str                     # platform, which names the raw file
    board_id: str
    employer: str = None
    employer_provenance: str = None
    url_provenance: str = "payload"
    location: str = None
    expires_at: str = None      # ISO date or None; read where the platform has one
    # The level the source states, verbatim, where it states one: Himalayas'
    # `seniority`. No employer board gives one (docs/reference/platform-fields.md).
    levels: tuple = None
    # Where the posting is, as the source structures it: a place string per
    # office, a country name, or an ISO 3166 alpha-2 code. The location rule
    # consults them only when the free text names nothing it recognises,
    # and only to close (the operator's go, 2026-10-02).
    places: tuple = None
    # The workplace the source states, verbatim: Lever's `workplaceType`, a
    # Greenhouse board's custom work-type field. Feeds D13's on-site rule.
    workplace: str = None
    # The description's parts as the platform returned them, HTML or text:
    # the normaliser reads them once (src/description.py) and keeps only what
    # they state, never the words. Out of equality and repr, as `raw` is.
    description: tuple = field(default=None, compare=False, repr=False)
    # The posting exactly as the board returned it, description included.
    # Carried, never read: the run saves it to the private store's full
    # branch, and the adapter hands the description to `description` above,
    # so nothing looks inside this (the operator's D11, 2026-09-26:
    # every field a board returns is kept, ADR-0016). Out of equality and
    # repr, so it never changes what two postings compare as or what a log
    # prints.
    raw: dict = field(default=None, compare=False, repr=False)

    def __post_init__(self):
        if self.employer_provenance is not None and self.employer_provenance not in PROVENANCE:
            raise AdapterError("employer provenance %r is not one of %s"
                               % (self.employer_provenance, sorted(PROVENANCE)))
        if self.url_provenance not in PROVENANCE:
            raise AdapterError("url provenance %r is not one of %s"
                               % (self.url_provenance, sorted(PROVENANCE)))
        if self.published_at is not None and self.published_at.tzinfo is None:
            raise AdapterError("published_at for %s is naive; adapters return UTC"
                               % self.external_id)


@dataclass
class ParseResult:
    """Postings that parsed, and the ones that did not.

    Problems are returned rather than raised so one broken posting cannot cost
    a board its other ninety. The run log reports them per board, because a
    silent skip is indistinguishable from a board that shrank."""
    postings: list = field(default_factory=list)
    problems: list = field(default_factory=list)

    def problem(self, external_id, reason):
        self.problems.append({"external_id": external_id, "reason": reason})


def require_absolute(url):
    return isinstance(url, str) and url.lower().startswith(("http://", "https://"))
