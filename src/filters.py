"""The filter chain. Cheapest disqualifier first, every drop naming its rule.

Order: expiry, annotation vendors, title, seniority, level, experience,
authorisation, location, age.

**Seniority runs after the title rule on purpose.** It drops a posting the
pool admitted, so its count in the run log is the number of relevant roles
excluded for level, and a title the pool never admitted stays a title drop,
which keeps the drop log a clean record of what the pool is missing. The
rule was decided by the operator on 2026-09-17; its words and evidence are in
docs/reference/seniority-exclusions.md, and no record carries it yet.

**Location and age, the operator's decisions of 2026-09-26.** Until then there
was no location filter, the brief having deferred it. D13 drops a posting
only when every place it lists is closed to someone in Pakistan, and keeps
anything unclear. D14 drops a posting more than a week old, which departs
from ADR-0007's recency-as-a-view for the display; the raw layer still keeps
everything fetched. Both lists and the limit live in `config/eligibility.json`
under ADR-0031, and neither decision has a record yet: the architecture
chat's to write.

**The description, the operator's decisions of 2026-10-02.** What
`src/description.py` reads from it reaches three rules. *Experience* drops a
posting that asks for more years than he takes: "3 or 3+ is the max accepted
years", whether required or preferred ("5+ years preferred is already out").
It was deferred by him on 2026-09-17 until filtering read descriptions, with
three years as his reference then. *Authorisation* drops a posting that
requires the right to work, citizenship or residence only in places closed to
him: "work permit of us required". "No visa sponsorship" is not such a
requirement, and is never read: on a role open worldwide it only says no one
will be moved ("i want these kinds of jobs present in table"). *Location*
reads a description saying the role is worked on site as it reads a stated
workplace. All three run after the title and seniority rules, so the title
drop log stays the pool's whole feedback signal, and all three can only drop:
a description that says nothing leaves a posting's verdict as it was. No
record carries them yet: the architecture chat's to write.

*Annotation vendors.* No record carries the list. Three employers are named in
`docs/reference/title-pool.md`, which observes that one census measured 17 of
34 rows as Welo Data, Welocalize and Innodata, and states that the
annotation-vendor rule catches them by employer. Those three are used, sourced
from that line, and the list is marked provisional.

Every drop is logged with the rule that caused it. ADR-0005. For the title rule
the drop log is the only feedback signal that the pool is missing a term, so it
records the title verbatim.
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .normalise import fold

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE_POOL_PATH = os.path.join(REPO_ROOT, "docs", "reference", "title-pool.md")
SENIORITY_PATH = os.path.join(REPO_ROOT, "docs", "reference", "seniority-exclusions.md")
VENDORS_PATH = os.path.join(REPO_ROOT, "docs", "reference", "annotation-vendors.md")

VERDICT_KEEP = "keep"


class FilterError(Exception):
    pass


@dataclass
class Verdict:
    keep: bool
    rule: str = None      # the rule that dropped it, None when kept
    reason: str = None


# ------------------------------------------------------------- title pool
def load_title_pool(path=None):
    """Read the terms and the exempt single tokens from the versioned pool.

    The pool is a file rather than a constant so that changing it is a
    documented act and a historical run is reproducible. ADR-0016."""
    path = path or TITLE_POOL_PATH
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise FilterError("title pool not found at %s" % path)

    exempt = set()
    match = re.search(r"Exempt single tokens:(.+)", text)
    if match:
        exempt = {fold(t) for t in re.findall(r"`([^`]+)`", match.group(1))}

    start = text.find("## Terms")
    if start == -1:
        raise FilterError("title pool has no '## Terms' section")
    end = text.find("## Known behaviour", start)
    section = text[start:end if end != -1 else len(text)]
    terms = [fold(t) for t in re.findall(r"`([^`]+)`", section)]
    terms = [t for t in terms if t]

    if not terms:
        raise FilterError("title pool lists no terms")
    for term in terms:
        if " " not in term and term not in exempt:
            raise FilterError(
                "term %r is a single token and is not on the exempt list. "
                "ADR-0021 requires two words unless exempted, because a bare "
                "token collides." % term)
    return terms, exempt


def load_term_families(path=None):
    """Map each pool term to the role family whose heading it sits under.

    ADR-0038 needs the label and `load_title_pool` discards it: that loader
    reads the whole Terms section and flattens the four `### N. Name`
    headings away, because admission never depended on them. Only the credit
    order did.

    The family is derived, never stored on a row. A term moved to another
    family changes the label on the next projection, which is a
    re-derivation, not a rewrite of an append-only file."""
    path = path or TITLE_POOL_PATH
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise FilterError("title pool not found at %s" % path)
    start = text.find("## Terms")
    if start == -1:
        raise FilterError("title pool has no '## Terms' section")
    end = text.find("## Known behaviour", start)
    section = text[start:end if end != -1 else len(text)]

    # A pool with no family headings at all is a pool without families, which
    # a candidate file being previewed against real postings legitimately is.
    # A pool that has headings and also a term outside them is a structural
    # defect, and that one raises. The distinction matters: the first is a
    # smaller document, the second is a term nobody can name a family for.
    has_headings = bool(re.search(r"^###\s*\d+\.", section, re.MULTILINE))
    if not has_headings:
        return {}

    families = {}
    current = None
    for line in section.splitlines():
        heading = re.match(r"###\s*\d+\.\s*(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip()
            continue
        for term in re.findall(r"`([^`]+)`", line):
            folded = fold(term)
            if not folded:
                continue
            if current is None:
                raise FilterError(
                    "term %r appears in the Terms section before any family "
                    "heading. Every term belongs to exactly one family." % folded)
            families.setdefault(folded, current)
    return families


def load_seniority_words(path=None):
    """Read the excluded senior-level words from their versioned file.

    Only the section headed "Excluded words" is read, so the words the file
    names as deliberately kept can never be excluded by being quoted. Single
    words are the point here, so the pool's two-word rule does not apply."""
    path = path or SENIORITY_PATH
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise FilterError("seniority exclusions not found at %s" % path)
    start = text.find("## Excluded words")
    if start == -1:
        raise FilterError("seniority exclusions have no '## Excluded words' section")
    end = text.find("\n## ", start + 1)
    section = text[start:end if end != -1 else len(text)]
    words = [w for w in (fold(t) for t in re.findall(r"`([^`]+)`", section)) if w]
    if not words:
        raise FilterError("seniority exclusions list no words")
    return words


def load_annotation_vendors(path=None):
    """The annotation vendors, from their own reference file.

    ADR-0031: a preference is configuration, never a constant in a module.
    This list was a tuple here, marked provisional in a comment, until
    2026-09-17.

    Only the section headed "Vendors" is read. The rest of that file quotes
    file paths and a symbol name in backticks, and a loader that read the
    whole document would silently turn `src/filters.py` into a vendor and
    drop every employer whose name contained it, which is none of them, which
    is exactly how a defect like that survives."""
    path = path or VENDORS_PATH
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise FilterError("annotation vendors not found at %s" % path)
    start = text.find("## Vendors")
    if start == -1:
        raise FilterError("annotation vendors have no '## Vendors' section")
    end = text.find("\n## ", start + 1)
    section = text[start:end if end != -1 else len(text)]
    names = [n for n in (fold(t) for t in re.findall(r"`([^`]+)`", section)) if n]
    if not names:
        raise FilterError("annotation vendors list no names")
    return names


# Loaded once, at import, so a missing or malformed preference file stops the
# program rather than quietly filtering nothing.
ANNOTATION_VENDORS = tuple(load_annotation_vendors())

ELIGIBILITY_PATH = os.path.join(REPO_ROOT, "config", "eligibility.json")
# A part saying any of these is read as unclear, never as closed: "anywhere
# except US" names a closed country and means the opposite.
_NEGATIONS = re.compile(r"\b(except|excluding|excl|outside|not in|other than)\b")
_PARTS = re.compile(r"[;\n|]| / ")
# Words that never restrict where a posting can be done from, removed before a
# place is judged: a time zone, a preference, an office that is optional. The
# operator: "time zone is not an issue". So "Remote (US time zones)" is remote,
# not a United States posting, and "Anywhere (US preferred)" is anywhere. The
# fourth audit's F4 found all three dropped. Bracketed ones are found before
# the fold, which drops brackets; the rest after it, on folded text.
_BRACKETED_QUALIFIER = re.compile(
    r"\([^()]*\b(time ?zones?|hours?|hrs|overlap|preferred|preferably|optional)\b[^()]*\)")
_QUALIFIER = re.compile(
    r"\b(within |in |across |overlapping |overlap with )?(the )?([a-z]+ )?time ?zones?\b"
    r"|\b(est|edt|cst|cdt|mst|mdt|pst|pdt|cet|cest|eet|gmt|bst|ist|aest|sgt|jst|utc)"
    r"( ?[+-] ?\d{1,2}(:?\d\d)?)? (hours?|hrs|time|overlap)\b"
    r"|\b(utc|gmt) ?[+-] ?\d{1,2}(:?\d\d)?\b"
    r"|\b([a-z]+ )?preferred\b"
    r"|\bpreferabl[ey]( in| within)?( the)? [a-z]+\b"
    r"|\b(office|onsite|on site|in office) optional\b")
# "Anywhere in the US" is the US. The open word goes, so the place decides.
_SCOPED_OPEN = re.compile(r"\b(anywhere|worldwide|globally|global) (in|within|across)\b")
# "US only" is a restriction even beside a word that would open it.
_ONLY = re.compile(r"\bonly\b")


@dataclass(frozen=True)
class Eligibility:
    """The operator's D13 and D14, from `config/eligibility.json`: where he
    can work from and how old a posting may be. Every place is a compiled
    whole-word pattern over folded text. And the levels he takes where a
    source states one, folded, with their names as configured."""
    max_age_days: int
    home: tuple
    onsite_home_city: tuple
    onsite_markers: tuple
    open: tuple
    closed: tuple
    remote: tuple = ()
    home_cities: tuple = ()
    home_country_names: tuple = ()
    levels_admitted: tuple = ()
    level_names: tuple = ()
    home_country_codes: tuple = ()
    max_years_experience: int = None


def _words(terms):
    return tuple(re.compile(r"\b%s\b" % re.escape(fold(t))) for t in terms)


def load_eligibility(path=None):
    with open(path or ELIGIBILITY_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    days = raw.get("max_age_days")
    if not isinstance(days, int) or isinstance(days, bool) or days < 1:
        raise FilterError("max_age_days must be a whole number of days, 1 or more")
    lists, names = {}, {}
    for key in ("home", "home_country", "onsite_home_city", "onsite_markers", "remote", "open",
                "closed"):
        value = raw.get(key)
        if not isinstance(value, list) or not value or not all(isinstance(v, str) and v.strip()
                                                               for v in value):
            raise FilterError("%s must be a non-empty list of places" % key)
        lists[key], names[key] = _words(value), tuple(value)
    if any(p.pattern in {q.pattern for q in lists["closed"]} for p in lists["home"]):
        raise FilterError("a home place is also listed as closed")
    country = {p.pattern for p in lists.pop("home_country")}
    if not country <= {p.pattern for p in lists["home"]}:
        raise FilterError("the home country must be one of the home places")
    codes = raw.get("home_country_codes")
    if (not isinstance(codes, list) or not codes
            or not all(isinstance(c, str) and re.fullmatch(r"[A-Z]{2}", c) for c in codes)):
        raise FilterError("home_country_codes must be a non-empty list of ISO 3166 alpha-2 codes")
    levels = raw.get("stated_levels_admitted")
    if not isinstance(levels, list) or not levels or not all(isinstance(v, str) and v.strip()
                                                             for v in levels):
        raise FilterError("stated_levels_admitted must be a non-empty list of levels")
    years = raw.get("max_years_experience")
    if not isinstance(years, int) or isinstance(years, bool) or years < 0:
        raise FilterError("max_years_experience must be a whole number of years, 0 or more")
    return Eligibility(max_age_days=days,
                       home_cities=tuple(p for p in lists["home"] if p.pattern not in country),
                       home_country_names=names["home_country"],
                       levels_admitted=tuple(fold(v) for v in levels),
                       level_names=tuple(levels), home_country_codes=tuple(codes),
                       max_years_experience=years, **lists)


def _qualifiers_removed(part):
    """A location part folded, with what never restricts it taken out."""
    text = fold(_BRACKETED_QUALIFIER.sub(" ", str(part).lower()))
    text = _QUALIFIER.sub(" ", text)
    text = _SCOPED_OPEN.sub(" in ", text)
    return " ".join(text.split())


ELIGIBILITY = load_eligibility()


def classify_place(part, eligibility):
    """One location, alone: "eligible", "closed" or "unclear". The order, each
    step the operator's D13 or its ruling:

    1. Time zones, preferences and optional offices are removed first: they
       never restrict ("time zone is not an issue").
    2. "Except" and its kind make the part unclear, so it is kept.
    3. A home place admits it, unless it is on site in a home city other than
       Karachi with no remote option: "any onsite post besides karachi,
       pakistan are automatically out". "Pakistan (On-site)" names no city,
       so it may be Karachi and is kept.
    4. A closed place beside "only" is closed: "usa only ... out".
    5. Worldwide, or a region that can include Pakistan, admits it, even beside
       closed countries: "US, Canada, Asia" includes him.
    6. A closed place is closed: "Remote, Germany" is Germany's remote.
    7. Remote with nothing closed beside it admits it.
    8. Anything else is unclear, and kept.

    The fourth audit's F4 found the first build dropping seven location
    strings he could take, because it judged a closed name before an open
    one, read "on site" without asking whether a city was named or remote was
    offered, and read a time zone as a country."""
    text = _qualifiers_removed(part)
    if not text:
        return "unclear"

    def names(patterns):
        return any(p.search(text) for p in patterns)
    if _NEGATIONS.search(text):
        return "unclear"
    if names(eligibility.home):
        on_site_elsewhere = (names(eligibility.onsite_markers) and not names(eligibility.remote)
                             and names(eligibility.home_cities)
                             and not names(eligibility.onsite_home_city))
        return "closed" if on_site_elsewhere else "eligible"
    closed = names(eligibility.closed)
    if closed and _ONLY.search(text):
        return "closed"
    if names(eligibility.open):
        return "eligible"
    if closed:
        return "closed"
    if names(eligibility.remote):
        return "eligible"
    return "unclear"


def place_names(phrase, eligibility):
    """The places a description's requirement names, as the configured names
    they match, in order: what a row keeps of it, never the employer's words
    (ADR-0011). Empty when it names none the rule knows, or says "except" or
    its kind, which would turn "anywhere except the US" into the US. Time
    zones and preferences go first, as for a location: "must be located in
    a US time zone" names no place."""
    text = _qualifiers_removed(phrase)
    if not text or _NEGATIONS.search(text):
        return ()
    found = sorted((m.start(), m.group(0)) for p in eligibility.home + eligibility.open
                   + eligibility.closed for m in p.finditer(text))
    names = []
    for _, name in found:
        if name not in names:
            names.append(name)
    return tuple(names)


def compile_terms(terms):
    """Word-boundary patterns with an optional plural suffix on the final word.

    Never a raw substring: `rag` as a substring matches 'sto**rag**e' and turns
    a Storage Engineer into a RAG role. The suffix reaches the term's last word
    only, so `agentic system` matches "Agentic Systems Engineer"."""
    compiled = []
    for term in terms:
        escaped = re.escape(term).replace(r"\ ", " ")
        compiled.append((term, re.compile(r"\b%s(?:e?s)?\b" % escaped)))
    return compiled


class TitleMatcher:
    def __init__(self, path=None, seniority_path=None):
        self.terms, self.exempt = load_title_pool(path)
        self.patterns = compile_terms(self.terms)
        self.seniority_words = load_seniority_words(seniority_path)
        self.seniority_patterns = compile_terms(self.seniority_words)
        self.term_families = load_term_families(path)

    def match(self, title):
        """The first term that matches, or None. Returning the term is the
        point: every admission must be explainable by naming one term."""
        folded = fold(title)
        for term, pattern in self.patterns:
            if pattern.search(folded):
                return term
        return None

    def family_of(self, term):
        """The role family a term belongs to, or None for no term.

        ADR-0038: a lookup, never a judgement. Nothing here reads a title, a
        description or anything but the term the title rule already named."""
        if not term:
            return None
        return self.term_families.get(term)

    def excluded_word(self, title):
        """The first excluded senior-level word in the title, or None."""
        folded = fold(title)
        for word, pattern in self.seniority_patterns:
            if pattern.search(folded):
                return word
        return None


# ----------------------------------------------------------------- rules
def rule_expiry(row, now_iso, **kw):
    """Drop a posting whose expiry has passed.

    Greenhouse returns `application_deadline` on every posting and it was null
    on all 1598 measured. Lever returns no expiry at all. So this rule reads a
    field that is currently always empty, which is the point: a null field that
    starts carrying values is what the rule is for."""
    expires = getattr(row, "expires_at", None)
    if expires and expires < now_iso:
        return Verdict(False, "expiry", "expired at %s" % expires)
    return Verdict(True)


def rule_experience(row, eligibility, **kw):
    """Drop a posting whose description asks for more years of experience
    than the operator takes, under `max_years_experience`: "the most it can
    say is 3+ and not 4+ years". **Any figure over it drops**, a preferred
    one included: "5+ years preferred is already out". A range counts by its
    low end, so "3 to 5 years" is kept. A posting whose description states
    no figure, or a row stored before descriptions were read, is kept."""
    limit = eligibility.max_years_experience
    stated = [y for y in (getattr(row, "stated_experience", None) or [])
              if isinstance(y, int) and not isinstance(y, bool)]
    over = [y for y in stated if limit is not None and y > limit]
    if not over:
        return Verdict(True)
    return Verdict(False, "experience", "the description asks for %d or more years of "
                   "experience; at most %d are admitted" % (max(over), limit))


def rule_authorisation(row, eligibility, **kw):
    """Drop a posting whose description requires the right to work,
    citizenship or residence only in places closed to the operator: his
    "work permit of us required", and "if the job is remote but is us only
    then it should not be shown". As D13 does for a location, **every place
    the requirements name must be closed**: one naming a home place, or a
    region that can include it, keeps the posting, and so does a requirement
    naming no place the rule knows. "No visa sponsorship" is never read as
    one: on a role open worldwide it says only that no one is moved."""
    named = [str(n) for n in (getattr(row, "required_places", None) or []) if str(n).strip()]
    if named and all(classify_place(n, eligibility) == "closed" for n in named):
        return Verdict(False, "authorisation", "the description requires the right to work, "
                       "citizenship or residence in %s, none of them %s"
                       % ("; ".join(named)[:120], " or ".join(eligibility.home_country_names)))
    return Verdict(True)


def rule_annotation_vendor(row, vendors, **kw):
    """Drop task-work vendors by employer.

    The pool deliberately keeps `ai trainer` and `ai evaluator`, which pull
    annotation gig work, and leaves this rule to remove it by employer."""
    if not row.employer:
        return Verdict(True)
    employer = fold(row.employer)
    for vendor in vendors:
        if vendor in employer:
            return Verdict(False, "annotation_vendor", "employer is %s" % row.employer)
    return Verdict(True)


def rule_title(row, matcher=None, **kw):
    """Allowlist only. ADR-0021: admit only a title matching a named term,
    drop everything else, and record the title so the drop log can show which
    terms the pool is missing."""
    term = matcher.match(row.title_normalised)
    if term is None:
        return Verdict(False, "title", "no term matched: %r" % row.title_normalised)
    return Verdict(True, reason="matched %r" % term)


def rule_seniority(row, matcher=None, **kw):
    """Drop an admitted posting whose title carries a senior-level word.
    Decided by the operator on 2026-09-17; see the module docstring."""
    word = matcher.excluded_word(row.title_normalised)
    if word is not None:
        return Verdict(False, "seniority", "senior-level word %r in title" % word)
    return Verdict(True)


def rule_level(row, eligibility, **kw):
    """The level the source states, where it states one: the operator's
    decision of 2026-10-02, for Himalayas, which labels every posting. He
    takes roles up to mid level: "keep till mid", and the levels themselves
    are configuration (ADR-0031).

    **Kept when any level it states is one he takes**, his option A: a role
    labelled both mid and senior is open to a mid-level candidate, and "i do
    not want to miss any". **A posting that states no level is kept**, which
    covers every employer board, and every row stored before this rule.

    The title rule still runs: a title saying "Senior" is dropped there,
    whatever level the source states. The level is not the job type:
    interns, contract, part-time, temporary and volunteer roles are all kept,
    his decision of the same day. Measured on the 809 Himalayas postings
    saved by then: the chain kept 67, and this rule takes 33 of them."""
    stated = [s for s in (getattr(row, "stated_levels", None) or []) if str(s).strip()]
    if not stated or not eligibility.levels_admitted:
        return Verdict(True)
    if any(fold(s) in eligibility.levels_admitted for s in stated):
        return Verdict(True)
    return Verdict(False, "level", "the source states its level as %s, none of them %s"
                   % (" and ".join(stated), " or ".join(eligibility.level_names)))


def rule_location(row, eligibility, **kw):
    """D13, the operator's decision of 2026-09-26: "i do not want any jobs
    shown in the table which i am not eligible to while at the same time i
    do not want to miss any to which i am eligible to".

    A location may list several places, one per line or separated by
    semicolons. **The posting is dropped only when every place it lists is
    closed**: a country other than Pakistan, a region without it, or a
    Pakistan city other than Karachi that says it is on site. No location,
    remote with no country, a region that can include Pakistan, or a place
    this cannot name all keep it: an unrecognised spelling can only let a
    posting through, never lose one."""
    text = getattr(row, "location", None)
    if not text or not str(text).strip():
        return Verdict(True)
    parts = [p for p in _PARTS.split(str(text)) if p.strip()]
    worked = _workplace_words(getattr(row, "workplace", None), eligibility)
    verdicts = [classify_place(_with_workplace(p, worked, eligibility), eligibility)
                for p in parts]
    if parts and all(v == "closed" for v in verdicts):
        # The field, and what was absent from it, as ADR-0041's Confirmation
        # asks. The home country comes from the configuration, so no module
        # names a country (ADR-0031).
        return Verdict(False, "location", "the location field names only places closed to the "
                       "operator, none of them %s or a remote role open to it: %r"
                       % (" or ".join(eligibility.home_country_names),
                          str(text).replace("\n", "; ")[:120]))
    # A description saying the role is worked on site is read as a stated
    # workplace is, when the source states none: a "Lahore, Punjab, Pakistan"
    # posting whose description gives its location as an on-site office is
    # on site outside Karachi, which D13 drops. The source's own field,
    # where it has one, is never overridden by the description.
    described = (None if getattr(row, "workplace", None)
                 else _workplace_words(getattr(row, "described_workplace", None), eligibility))
    if described and parts and all(
            classify_place(_with_workplace(p, described, eligibility), eligibility) == "closed"
            for p in parts):
        return Verdict(False, "location", "the description says the role is worked on site, "
                       "and the location field names only places closed to the operator for "
                       "on-site work: %r" % str(text).replace("\n", "; ")[:120])
    # The text names nothing eligible, and something it cannot place: a city
    # such as "Dallas, TX" or "Manila". Where the source says where the
    # posting is, that decides, and only ever to close: a home place there
    # keeps it, and a source that says nothing leaves today's verdict. The
    # operator's go, 2026-10-02, on 59 saved postings it would close and
    # none it would lose.
    if "eligible" not in verdicts and "unclear" in verdicts:
        places = [str(x) for x in (getattr(row, "places", None) or []) if str(x).strip()]
        if places and all(_classify_structured(x, eligibility) == "closed" for x in places):
            return Verdict(False, "location", "the location field names no place the rule "
                           "knows, and the source places the posting outside %s: %s"
                           % (" or ".join(eligibility.home_country_names),
                              "; ".join(places)[:120]))
    return Verdict(True)


def _workplace_words(workplace, eligibility):
    """The workplace a source states, as the words the place rules read: an
    on-site marker for an on-site or hybrid role, and nothing otherwise.

    **A stated remote workplace adds nothing.** Beside a city the rule cannot
    place, "Manila (remote)" reads as remote with nothing closed beside it,
    which admits it, and the source's own country, the Philippines, would
    never be consulted. The first build did that, and kept 19 remote Lever
    postings in four other countries. A remote role in Pakistan needs no
    help: a home place admits it already."""
    text = fold(workplace or "")
    if not text or any(p.search(text) for p in eligibility.remote):
        return ""
    if any(p.search(text) for p in eligibility.onsite_markers):
        return "on site"
    return ""


def _with_workplace(part, worked, eligibility):
    """A place, with the source's stated workplace beside it when the text
    says neither. So "Lahore, Pakistan" from a board whose field says the
    role is office based reads as on site, and D13's on-site rule applies.
    Text that already says remote or on site is never overridden."""
    if not worked:
        return part
    text = fold(part)
    if any(p.search(text) for p in eligibility.remote + eligibility.onsite_markers):
        return part
    return "%s (%s)" % (part, worked)


def _classify_structured(place, eligibility):
    """A place as a source structures it. An ISO 3166 alpha-2 code is the
    home country's or another's; anything else is read like text."""
    code = str(place).strip()
    if re.fullmatch(r"[A-Z]{2}", code):
        return "eligible" if code in eligibility.home_country_codes else "closed"
    return classify_place(code, eligibility)


def _when(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def rule_age(row, now_iso, eligibility, **kw):
    """D14, the operator's decision of 2026-09-26: "i do not want a job post
    more than a week old".

    **Judged once, at first sight, never again.** The operator's correction
    the same day: a posting published no more than the limit before the
    pipeline first saw it is admitted and then stays, however long it waits
    in the table, because "the fetch will happen daily and i might not see
    the table for a few days then it would mean some posts will be out
    without my knowledge which i do not want". So the age is first seen minus
    published, never the run's clock minus published, and a row re-judged by
    a later projection or sweep gets the same answer every time. A posting
    first seen already older than the limit never enters, a repost carrying
    its original date included.

    Lever's `createdAt` is not proven to mean publication, so a Lever
    posting is never dropped for age: a fresh posting is never lost to a date
    that means something else. A posting with no date is kept."""
    if getattr(row, "published_meaning_unconfirmed", False):
        return Verdict(True)
    seen = _when(getattr(row, "first_seen", None)) or _when(now_iso)
    dated = _when(getattr(row, "ordering_date", None))
    if seen is None or dated is None:
        return Verdict(True)
    if seen - dated <= timedelta(days=eligibility.max_age_days):
        return Verdict(True)
    return Verdict(False, "age", "published %s, more than %d days before it was first seen at %s"
                   % (row.ordering_date, eligibility.max_age_days,
                      getattr(row, "first_seen", None)))


# Experience, authorisation, location and age run last, after the title and
# seniority rules, so their counts in the run log are relevant roles lost to
# what the description asks, to place and to age, and the title rule's drop
# log stays the pool's whole feedback signal. Experience ran second until
# 2026-10-02, when it was never on: moved, it counts relevant roles only.
CHAIN = (("expiry", rule_expiry),
         ("annotation_vendor", rule_annotation_vendor),
         ("title", rule_title),
         ("seniority", rule_seniority),
         ("level", rule_level),
         ("experience", rule_experience),
         ("authorisation", rule_authorisation),
         ("location", rule_location),
         ("age", rule_age))


def apply_chain(rows, now_iso, matcher=None, vendors=ANNOTATION_VENDORS, eligibility=None):
    """Returns (kept, drops). Each drop names the rule that caused it.
    `eligibility` is read at the call, not at import, so a test of another
    mechanism can hold the operator's D13 and D14 aside explicitly."""
    matcher = matcher or TitleMatcher()
    eligibility = eligibility or ELIGIBILITY
    kept, drops = [], []
    for row in rows:
        verdict, reason = Verdict(True), None
        for name, rule in CHAIN:
            verdict = rule(row, now_iso=now_iso, matcher=matcher,
                           vendors=vendors, eligibility=eligibility)
            reason = verdict.reason or reason
            if not verdict.keep:
                drops.append({"identity": row.identity, "rule": verdict.rule,
                              "reason": verdict.reason, "title": row.title,
                              "employer": row.employer, "board_id": row.board_id})
                break
        if verdict.keep:
            # The title rule's "matched <term>" must survive the rules after it.
            kept.append((row, reason))
    return kept, drops


def drop_counts(drops):
    """Per rule, for the run log. ADR-0005."""
    counts = {name: 0 for name, _ in CHAIN}
    for d in drops:
        counts[d["rule"]] = counts.get(d["rule"], 0) + 1
    return counts
