"""We Work Remotely. ADR-0063's second wave, last: built 2026-10-19, last of
the other three, by its yield (1 kept of its feed's 88) and its postings
naming a recruiter in their process most often of the three, 31 of 88 (the
seat's report on Brief 15).

Endpoint: weworkremotely.com/remote-jobs.rss, one request a run, RSS, the
newest ten postings of each of its categories, 88 on 2026-10-18 dated
2026-05-20 to 10-18. Its terms: "Anyone can use the feed, all we ask is that
you attribute the links back to We Work Remotely." Each row links to its We
Work Remotely page and names it as its board.

**RSS, not JSON.** The run fetches it as text through the shared client
(`get_text`), and `decode` here turns its items into the payload `parse`
reads, one object an item, so the run, the contract check and the stores
treat it as any other source.

Fields, measured over the 88:

  identity     the last part of `guid`, which is `link` on 88 of 88
  title        `title`, "Company: Role" on 88 of 88; the role
  employer     the title before its first ": "
  link         `link`, the posting's page on We Work Remotely
  publication  `pubDate`, RFC 822
  place        `country` where it names any, each country a place of its
               own: 17 of 88, 11 of them the United States, which the
               region beside them, "Anywhere in the World", does not say.
               Else `region`: "Anywhere in the World" 86 of 88
  workplace    remote by the feed's own scope
  description  `description`, HTML

Today's rules, read fresh, keep 1 of the 88.
"""

import email.utils
import html
import re
import xml.etree.ElementTree as ET

from .base import AdapterError, ParseResult, Posting, require_absolute

PLATFORM = "weworkremotely"
BASE = "https://weworkremotely.com/remote-jobs.rss"
PUBLISHED_FIELD = "pubDate"
FIELDS = ("guid", "title", "link", "pubDate", "region", "country", "state", "category", "type",
          "description")

# ADR-0018: what parse() reads, and nothing else, of the decoded payload.
CONSUMED_RESPONSE = ("items",)
POSTINGS_AT = "items"
CONSUMED = ("guid", "title", "link", PUBLISHED_FIELD, "region", "country", "description")

# A country's flag, two regional indicator letters, which the feed puts
# before each country's name.
_FLAG = re.compile("[\U0001F1E6-\U0001F1FF]")
# The feed lists countries "A, B, and C": split on the commas only, since a
# country's own name may hold "and", "United Kingdom of Great Britain and
# Northern Ireland" among them, and drop the list's last "and".
_COUNTRY_SPLIT = re.compile(r"\s*,\s*")
_LIST_AND = re.compile(r"(?i)^and\s+")


def url_for(board):
    return BASE


def decode(text):
    """The feed's items as objects, each field its text, or raise."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise AdapterError("We Work Remotely's feed is not XML: %s" % e)
    channel = root.find("channel")
    if channel is None:
        raise AdapterError("We Work Remotely's feed has no channel")
    return {"items": [{name: item.findtext(name) for name in FIELDS}
                      for item in channel.findall("item")]}


def _text(value):
    return " ".join(html.unescape(str(value or "")).split())


def place_of(entry):
    """The countries named, one place each, else the region."""
    named = _COUNTRY_SPLIT.split(_text(_FLAG.sub("", entry.get("country") or "")))
    countries = [_LIST_AND.sub("", c).strip() for c in named if c.strip()]
    if countries:
        return "; ".join(countries)
    return _text(entry.get("region")) or None


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value.strip())
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo is not None else None


def parse(payload, board):
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise AdapterError("%s: expected the decoded feed's 'items', got %s"
                           % (board.board_id, type(payload).__name__))
    result = ParseResult()
    for entry in payload["items"]:
        if not isinstance(entry, dict):
            result.problem(None, "item is %s, not an object" % type(entry).__name__)
            continue
        guid = str(entry.get("guid") or "").strip().rstrip("/")
        external_id = guid.rsplit("/", 1)[-1]
        if not external_id:
            result.problem(None, "no guid")
            continue
        heading = _text(entry.get("title"))
        employer, _, role = heading.partition(": ")
        title = role.strip() or heading
        if not title:
            result.problem(external_id, "no title")
            continue
        url = entry.get("link")
        if not require_absolute(url):
            result.problem(external_id, "link missing or not absolute: %r" % (url,))
            continue
        published_raw = entry.get(PUBLISHED_FIELD)
        published_at = _parse_time(published_raw)
        if published_at is None:
            result.problem(external_id, "%s missing or unparseable: %r"
                           % (PUBLISHED_FIELD, published_raw))
            continue
        employer = employer.strip() if role.strip() else ""
        description = entry.get("description")
        result.postings.append(Posting(
            external_id=external_id,
            title=title,
            url=url,
            published_at=published_at,
            published_field=PUBLISHED_FIELD,
            published_raw=published_raw,
            source=PLATFORM,
            board_id=board.board_id,
            employer=employer or None,
            employer_provenance="payload" if employer else None,
            url_provenance="payload",
            location=place_of(entry),
            workplace="remote",
            description=(description,) if isinstance(description, str) and description.strip()
            else (),
            raw=entry,
        ))
    return result
