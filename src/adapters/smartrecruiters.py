"""SmartRecruiters. One adapter serving every SmartRecruiters board in the
registry, never one per employer.

Endpoints, SmartRecruiters' public Posting API, read 2026-10-04 and live on
2026-10-15 and 2026-10-17, no authentication for public postings:

  list    api.smartrecruiters.com/v1/companies/{company}/postings, 100 a page,
          `content` beside `totalFound`, `offset` and `limit`
  detail  .../postings/{id}, one posting: its job ad and its own page

**The description is on the detail only**, one request a posting, so the run
asks for it once per posting, ever: when it first sees the posting (ADR-0028,
`Run._fetch_details`). A later run reads the posting from the list alone, its
row already stored; this adapter then reads no description, which the row
records as not read, never as none.

ADR-0059's first wave, third, after Manatal and Workable: the operator's
order of 2026-10-09, SmartRecruiters then Ashby. Two registry boards,
OneScreen and SeekaTechnology, ten postings each on 2026-10-17.

Fields, measured over those twenty postings and two details on 2026-10-17:

  identity     `id`                 100%
  title        `name`               100%
  link         the detail's `postingUrl`; from the list alone, the posting's
               page built from the company and the id, which answered 200
               and named the posting on 2026-10-17
  publication  `releasedDate`       100%. SmartRecruiters' documentation does
               not define it. It did not move on any of nine postings read on
               2026-09-16 and again on 2026-10-17, and the one posting new
               between carried a date between. The operator's decision of
               2026-10-17: trust it as the publication date, so the age rule
               judges it as Workable's and Greenhouse's.
  employer     `company.name`       100%
  place        `location.fullLocation`, and `location.country`, an ISO code
               in lower case
  remote       `location.remote` and `location.hybrid`, booleans; neither
               set says nothing, as Workable's `telecommuting` false does
  level        `experienceLevel.label`: Entry Level, Internship, Mid-Senior
               Level, Executive on these boards; the level rule drops only
               the levels configured above mid
  description  the detail's `jobAd.sections`, four named sections of HTML
"""

from datetime import datetime

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "smartrecruiters"
BASE = "https://api.smartrecruiters.com/v1/companies/%s/postings?limit=100&offset=%d"
DETAIL_URL = "https://api.smartrecruiters.com/v1/companies/%s/postings/%s"
JOB_PAGE = "https://jobs.smartrecruiters.com/%s/%s"

PUBLISHED_FIELD = "releasedDate"

# ADR-0018: what parse() reads, and nothing else. The contract check
# fingerprints exactly these, the detail's as a section of its own, and
# tests/test_contract.py holds them to the code.
CONSUMED_RESPONSE = ("content", "totalFound", "offset")
POSTINGS_AT = "content"
CONSUMED = ("id", "name", PUBLISHED_FIELD, "company", "company.identifier", "company.name",
            "location", "location.fullLocation", "location.city", "location.country",
            "location.remote", "location.hybrid", "experienceLevel", "experienceLevel.label")
CONSUMED_DETAIL = ("postingUrl", "jobAd", "jobAd.sections",
                   "jobAd.sections.companyDescription", "jobAd.sections.companyDescription.text",
                   "jobAd.sections.jobDescription", "jobAd.sections.jobDescription.text",
                   "jobAd.sections.qualifications", "jobAd.sections.qualifications.text",
                   "jobAd.sections.additionalInformation",
                   "jobAd.sections.additionalInformation.text")

# Paged by offset, read to the end: a board lists every open posting, old
# ones included, and ADR-0050's closure test counts a walk that reached the
# end as having looked at every posting. At 100 a page, one request a board.
PAGINATED = True
# The detail phase: Run._fetch_details asks for each new posting's detail.
DETAIL = True


def url_for(board, cursor=None):
    return BASE % (board.slug, cursor or 0)


def next_cursor(payload):
    """The next page's offset, or None once every posting is read."""
    if not isinstance(payload, dict):
        return None
    content = payload.get("content") or []
    try:
        reached = int(payload.get("offset") or 0) + len(content)
        total = int(payload.get("totalFound") or 0)
    except (TypeError, ValueError):
        return None
    return reached if content and reached < total else None


def stop_after(payload, high_water):
    """Never: the walk reads every page, so the closure test can trust it."""
    return False


def detail_url(board, external_id):
    return DETAIL_URL % (board.slug, external_id)


def external_id_of(entry):
    return str(entry.get("id") or "").strip() if isinstance(entry, dict) else ""


def from_detail(detail):
    """What a posting takes from its detail: the two fields parse reads, and
    nothing else, so the saved posting holds the list's fields and these."""
    if not isinstance(detail, dict):
        return {}
    taken = {}
    if "postingUrl" in detail:
        taken["postingUrl"] = detail["postingUrl"]
    if "jobAd" in detail:
        taken["jobAd"] = detail["jobAd"]
    return taken


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _place(location):
    """`fullLocation` with its empty and repeated parts removed: OneScreen's
    "Islamabad,, Islamabad, Pakistan" reads "Islamabad, Pakistan"."""
    parts = []
    for part in str(location.get("fullLocation") or "").split(","):
        part = part.strip()
        if part and part not in parts:
            parts.append(part)
    if parts:
        return ", ".join(parts)
    return str(location.get("city") or "").strip() or None


def _workplace(location):
    if location.get("remote") is True:
        return "remote"
    if location.get("hybrid") is True:
        return "hybrid"
    return None


def _description(entry):
    """The job ad's four sections, in the order the page shows them; None
    when the posting's detail was not read, which is not the same as a
    detail with no text."""
    if "jobAd" not in entry:
        return None
    ad = entry.get("jobAd") if isinstance(entry.get("jobAd"), dict) else {}
    sections = ad.get("sections") if isinstance(ad.get("sections"), dict) else {}
    parts = (sections.get("companyDescription"), sections.get("jobDescription"),
             sections.get("qualifications"), sections.get("additionalInformation"))
    return tuple(p.get("text") for p in parts if isinstance(p, dict))


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
        raise AdapterError("%s: expected an object with a 'content' list, got %s"
                           % (board.board_id, type(payload).__name__))

    result = ParseResult()
    for entry in payload["content"]:
        if not isinstance(entry, dict):
            result.problem(None, "posting is %s, not an object" % type(entry).__name__)
            continue
        external_id = external_id_of(entry)
        if not external_id:
            result.problem(None, "no id")
            continue
        title = str(entry.get("name") or "").strip()
        if not title:
            result.problem(external_id, "no name")
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue

        company = entry.get("company") if isinstance(entry.get("company"), dict) else {}
        # ADR-0026: the posting's own company name, else the board's alias.
        name = str(company.get("name") or "").strip()
        employer, provenance = (name, "payload") if name else (
            (board.employer_alias, "slug") if board.employer_alias else (None, None))
        url = entry.get("postingUrl")
        if require_absolute(url):
            url_provenance = "payload"
        else:
            handle = str(company.get("identifier") or "").strip() or board.slug
            url, url_provenance = JOB_PAGE % (handle, external_id), "constructed"
        location = entry.get("location") if isinstance(entry.get("location"), dict) else {}
        country = str(location.get("country") or "").strip().upper()
        level = entry.get("experienceLevel") if isinstance(entry.get("experienceLevel"),
                                                           dict) else {}
        label = str(level.get("label") or "").strip()
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
            url_provenance=url_provenance,
            location=_place(location),
            places=(country,) if len(country) == 2 else None,
            workplace=_workplace(location),
            levels=(label,) if label else None,
            description=_description(entry),
            raw=entry,
        ))
    return result
