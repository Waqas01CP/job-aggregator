"""Python.org's job board. ADR-0063's Changes of 2026-10-20, research 0006:
built 2026-10-20, measured first through the real chain (the seat's report
on Brief 18): of its feed's 20 postings, today's rules keep 7, five roles.

Endpoint: python.org/jobs/feed/rss/, one request a run, RSS, its newest 20
postings. Its robots rules leave /jobs/ open, and its Legal Statements
(2024-12-10) say nothing on automated reading. Each row links to the
posting's page on Python.org and names it as its board.

**RSS, not JSON,** fetched as text through the shared client and decoded
here, as We Work Remotely's is.

**The feed carries no date of any kind**, read 2026-10-20: a posting is
published_at None, so the age rule never drops it and the view orders it
after every dated posting, as Manatal's are (ADR-0007's Changes of
2026-10-07). The operator, 2026-10-20: "also the pythons rss feed would have
the same treatment if it does not have dates."

Fields, measured over the 20 of 2026-10-20:

  identity     the number ending `link`, which `guid` equals on 20 of 20
  title        `title`, "Role, Employer" on 20 of 20; the role
  employer     the title after its last ", ", or the last two parts when
               the last is a company's legal form: "ActivePrime, Inc."
  link         `link`, the posting's page on Python.org
  place        the description's first line, "Remote, Worldwide" or a
               city and country, on 20 of 20; `decode` makes it a field
               of its own, `place`
  description  the description after its first line, HTML
"""

import html
import re
import xml.etree.ElementTree as ET

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "pythonorg"
BASE = "https://www.python.org/jobs/feed/rss/"
FIELDS = ("guid", "title", "link", "description")

# ADR-0018: what parse() reads, and nothing else, of the decoded payload.
CONSUMED_RESPONSE = ("items",)
POSTINGS_AT = "items"
CONSUMED = ("title", "link", "place", "description")

# A company's legal form, which the title puts after a comma of its own.
_LEGAL_FORM = re.compile(r"(?i)^(?:inc|llc|ltd|limited|gmbh|corp|corporation|co|plc|s\.?a|b\.?v"
                         r"|pvt\.? ltd|pte\.? ltd|ag|oy|ab|as|sas|srl)\.?$")
_NUMBER = re.compile(r"/jobs/(\d+)/?$")


def url_for(board):
    return BASE


def decode(text):
    """The feed's items as objects, each field its text, or raise."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise AdapterError("Python.org's feed is not XML: %s" % e)
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("Python.org's feed has no channel")
    items = []
    for item in channel.findall("item"):
        entry = {name: item.findtext(name) for name in FIELDS}
        # The description's first line is the place: kept as a field of its
        # own, so the place is metadata and the description prose alone.
        first, _, rest = str(entry.get("description") or "").partition("\n")
        entry["place"], entry["description"] = first.strip() or None, rest
        items.append(entry)
    return {"items": items}


def _text(value):
    return " ".join(html.unescape(str(value or "")).split())


def split_title(heading):
    """(role, employer) from "Role, Employer", the employer's legal form kept
    with its name; the whole heading and None when it has no comma."""
    parts = heading.split(", ")
    if len(parts) < 2:
        return heading, None
    take = 2 if len(parts) > 2 and _LEGAL_FORM.match(parts[-1].strip()) else 1
    return ", ".join(parts[:-take]).strip(), ", ".join(parts[-take:]).strip()


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise AdapterError("%s: expected the decoded feed's 'items', got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["items"]:
        if not isinstance(entry, dict):
            result.problem(None, "item is %s, not an object" % type(entry).__name__)
            continue
        url = entry.get("link")
        number = _NUMBER.search(str(url or "").strip())
        if not number:
            result.problem(None, "link names no posting: %r" % (url,))
            continue
        external_id = number.group(1)
        if not require_absolute(url):
            result.problem(external_id, "link not absolute: %r" % (url,))
            continue
        role, employer = split_title(_text(entry.get("title")))
        if not role:
            result.problem(external_id, "no title")
            continue
        description = entry.get("description")
        result.postings.append(Posting(
            external_id=external_id,
            title=role,
            url=url,
            published_at=None,
            published_field=None,
            published_raw=None,
            source=PLATFORM,
            board_id=board.board_id,
            employer=employer,
            employer_provenance="payload" if employer else None,
            url_provenance="payload",
            location=_text(entry.get("place")) or None,
            description=(description,) if isinstance(description, str) and description.strip()
            else (),
            raw=entry,
        ))
    return result
