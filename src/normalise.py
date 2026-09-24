"""One row shape for every source.

A `Row` is what the rest of the pipeline sees. Adding a platform adds an
adapter, never a column, which is the point of putting the shape here.

Three things this records that a naive row would lose:

**Where the employer came from.** ADR-0026. Lever returns none, so its rows
carry a value derived from the configuration slug, and `employer_provenance`
says so. A derived value that looked returned would be compared against real
names in deduplication and miss silently.

**Which field supplied the ordering date.** ADR-0007 orders the display by
publication date and falls back to first-seen where there is none. A row that
did not record which it used would let a first-seen fallback be read as a
publication date, which is exactly the error Measure A would then inherit.

**The source.** ADR-0020 routes raw storage by it, one file per source, so a
row's provenance is its filename and no routing bug can misfile it.

The title is normalised per ADR-0027 and the normalised form is stored
*alongside* the original, never replacing it. The display shows what the
employer wrote; the deduplication key uses what we derived.
"""

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

# ADR-0011 fixes what the data branch may hold. Description text is not on the
# list and never reaches a row.
FIELDS = (
    "identity", "source", "board_id", "external_id",
    "employer", "employer_provenance",
    "title", "title_normalised",
    "location",
    "published_at", "published_field", "published_meaning_unconfirmed",
    "first_seen", "ordering_date", "ordering_date_source",
    "url", "url_provenance",
    "stated_experience", "expires_at",
)


class NormaliseError(Exception):
    pass


@dataclass
class Row:
    identity: str
    source: str
    board_id: str
    external_id: str
    title: str
    title_normalised: str
    url: str
    url_provenance: str
    first_seen: str
    ordering_date: str
    ordering_date_source: str          # "publication" or "first_seen"
    employer: str = None
    employer_provenance: str = None
    location: str = None
    published_at: str = None
    published_field: str = None
    published_meaning_unconfirmed: bool = False
    stated_experience: str = None      # no slice platform returns one
    expires_at: str = None             # null on every Greenhouse posting measured

    def as_record(self):
        """The canonical dict. Key order is fixed by FIELDS so two runs that
        change nothing produce a diff containing nothing."""
        d = asdict(self)
        return {k: d[k] for k in FIELDS}


def iso(dt):
    """UTC, microseconds included, always the same spelling."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        raise NormaliseError("refusing to serialise a naive datetime")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------- ADR-0027
def strip_location_suffix(title, location):
    """Remove a trailing separator and the text after it **only when that text
    equals the posting's own location field**. Never on the separator alone.

    Speechify's 1086 postings are 8 titles across 329 locations, and on all
    1074 titles containing " - " the suffix equalled `location.name` exactly.
    A title genuinely containing " - " and not naming a location is left
    intact, which is why the equality test is the rule rather than the
    separator."""
    if not title or not location:
        return title
    suffix = " - " + location.strip()
    if title.endswith(suffix):
        return title[:-len(suffix)].strip()
    return title


NORMALISERS = {"strip_location_suffix": strip_location_suffix}


def normalised_title(posting, board):
    title = posting.title
    for name in board.normalisations:
        fn = NORMALISERS.get(name)
        if fn is None:
            # config.py validates the name, so reaching here means the two
            # lists drifted. Failing loudly beats a silent no-op.
            raise NormaliseError("no normaliser implements %r" % name)
        title = fn(title, posting.location)
    return title


# ------------------------------------------------------------- dedupe key
_PUNCT = re.compile(r"[,()\.:]")
_SEPARATORS = re.compile(r"[-‐‑‒–—_/]")
_SPACE = re.compile(r"\s+")


def strip_latin_marks(text):
    """Remove accents from Latin letters, and only from them.

    "Sênior" reached `Jobs` on 2026-09-24 because "sênior" is not "senior";
    the operator decided accents are stripped before matching. Only a mark
    that follows an ASCII letter is removed, so the marks that carry meaning
    in other scripts, a Japanese voicing mark or a Greek accent, survive.
    Composing again afterwards returns everything else to NFKC, so a string
    with no Latin accent folds exactly as it did before."""
    out = []
    for ch in unicodedata.normalize("NFKD", text):
        if unicodedata.combining(ch) and out and out[-1].isascii():
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def fold(text):
    """Lowercase, separators to spaces, punctuation gone, whitespace collapsed,
    Latin accents removed.

    ADR-0021 specifies this for title matching. The deduplication key uses the
    same fold so that "Senior Engineer" and "senior  engineer" are one key.
    Accent stripping was added 2026-09-24 on the operator's decision, after a
    comparison over 1,458 distinct stored titles changed one verdict, the
    "Sênior" title it was meant to catch, and merged no two dedupe keys."""
    if not text:
        return ""
    text = strip_latin_marks(unicodedata.normalize("NFKC", str(text)))
    text = _SEPARATORS.sub(" ", text.lower())
    text = _PUNCT.sub("", text)
    return _SPACE.sub(" ", text).strip()


def dedupe_key(row):
    """Employer plus title plus publication date. ADR-0001, with the title
    normalised first per ADR-0027.

    Not row identity: twenty to thirty percent of harvested rows are one job
    across several cities, and on Speechify it is ninety-nine percent.

    A row with no employer cannot be compared against one that has a name, so
    its key is scoped to its own board. ADR-0026: a derived employer with no
    alias does not participate in cross-source deduplication."""
    employer = fold(row.employer) if row.employer else "board:" + row.board_id
    date = (row.published_at or "")[:10]
    return "%s|%s|%s" % (employer, fold(row.title_normalised), date)


# --------------------------------------------------------------- normalise
def normalise(postings, board, now, seen=None):
    """Map platform postings onto rows.

    `seen` maps identity to the first-seen timestamp already recorded, so a
    posting observed on an earlier run keeps its original first-seen rather
    than being re-dated on every run."""
    seen = seen or {}
    rows = []
    for p in postings:
        identity = "%s:%s" % (p.source, p.external_id)
        first_seen = seen.get(identity) or iso(now)

        published_at = iso(p.published_at) if p.published_at else None
        if published_at:
            ordering_date, ordering_source = published_at, "publication"
        else:
            # ADR-0007. Recorded, never disguised as a publication date.
            ordering_date, ordering_source = first_seen, "first_seen"

        row = Row(
            identity=identity,
            source=p.source,
            board_id=p.board_id,
            external_id=p.external_id,
            employer=p.employer,
            employer_provenance=p.employer_provenance,
            title=p.title,
            title_normalised=normalised_title(p, board),
            location=p.location,
            published_at=published_at,
            published_field=p.published_field,
            published_meaning_unconfirmed=(p.source == "lever"),
            first_seen=first_seen,
            ordering_date=ordering_date,
            ordering_date_source=ordering_source,
            url=p.url,
            url_provenance=p.url_provenance,
            stated_experience=None,
            expires_at=getattr(p, "expires_at", None),
        )
        rows.append(row)
    return rows


# ------------------------------------------------------------ serialisation
def dumps(records):
    """The one canonical serialisation. Every writer of a file agrees on it,
    so a run that changes nothing produces a diff containing nothing."""
    return json.dumps(records, indent=1, ensure_ascii=False,
                      separators=(",", ": "), sort_keys=False) + "\n"


def loads(text):
    return json.loads(text)
