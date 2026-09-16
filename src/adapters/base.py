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
