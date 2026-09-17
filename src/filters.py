"""The filter chain. Cheapest disqualifier first, every drop naming its rule.

Order: expiry, stated experience, annotation vendors, title, seniority.

**Seniority runs after the title rule on purpose.** It drops a posting the
pool admitted, so its count in the run log is the number of relevant roles
excluded for level, and a title the pool never admitted stays a title drop,
which keeps the drop log a clean record of what the pool is missing. The
rule was decided by the operator on 2026-09-17; its words and evidence are in
docs/reference/seniority-exclusions.md, and no record carries it yet.

**There is no location filter.** The brief defers it to MVP 2. Location is
recorded on every row and never used to drop, which is why a posting in
"Karachi, Sindh" or "Karachi, Punjab, Pakistan" survives regardless of how the
board spells it. ADR-0001's Confirmation and the architecture document's
component list both still describe a location filter in the chain; neither has
been updated, and that gap is reported rather than resolved here.

**Two rules in the chain have no definition anywhere in the records.**

*Stated experience.* No record names a threshold, and neither Greenhouse nor
Lever returns a structured experience field, so nothing reads one today. The
rule is implemented and disabled: it activates only when a maximum is supplied,
and the run log says it is off. Inventing a threshold would be policy invented
by an implementing session. **Deferred by the operator on 2026-09-17** until
filtering reads descriptions as well as titles, since stated experience lives
in description text; the operator's reference maximum for that time is three
years. Seniority words in titles are a separate matter, raised with the
operator, and are not this rule.

*Annotation vendors.* No record carries the list. Three employers are named in
`docs/reference/title-pool.md`, which observes that one census measured 17 of
34 rows as Welo Data, Welocalize and Innodata, and states that the
annotation-vendor rule catches them by employer. Those three are used, sourced
from that line, and the list is marked provisional.

Every drop is logged with the rule that caused it. ADR-0005. For the title rule
the drop log is the only feedback signal that the pool is missing a term, so it
records the title verbatim.
"""

import os
import re
from dataclasses import dataclass

from .normalise import fold

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE_POOL_PATH = os.path.join(REPO_ROOT, "docs", "reference", "title-pool.md")
SENIORITY_PATH = os.path.join(REPO_ROOT, "docs", "reference", "seniority-exclusions.md")

# Sourced from docs/reference/title-pool.md, "Known behaviour, accepted
# deliberately". PROVISIONAL: no decision record carries this list.
ANNOTATION_VENDORS = ("welo data", "welocalize", "innodata")

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

    def match(self, title):
        """The first term that matches, or None. Returning the term is the
        point: every admission must be explainable by naming one term."""
        folded = fold(title)
        for term, pattern in self.patterns:
            if pattern.search(folded):
                return term
        return None

    def senior_word(self, title):
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


def rule_experience(row, max_years, **kw):
    """Disabled until a threshold exists. See the module docstring."""
    if max_years is None:
        return Verdict(True)
    stated = row.stated_experience
    if stated is None:
        return Verdict(True)
    try:
        years = float(stated)
    except (TypeError, ValueError):
        return Verdict(True)
    if years > max_years:
        return Verdict(False, "experience",
                       "stated experience %s exceeds %s" % (stated, max_years))
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
    word = matcher.senior_word(row.title_normalised)
    if word is not None:
        return Verdict(False, "seniority", "senior-level word %r in title" % word)
    return Verdict(True)


CHAIN = (("expiry", rule_expiry),
         ("experience", rule_experience),
         ("annotation_vendor", rule_annotation_vendor),
         ("title", rule_title),
         ("seniority", rule_seniority))


def apply_chain(rows, now_iso, matcher=None, max_years=None,
                vendors=ANNOTATION_VENDORS):
    """Returns (kept, drops). Each drop names the rule that caused it."""
    matcher = matcher or TitleMatcher()
    kept, drops = [], []
    for row in rows:
        verdict, reason = Verdict(True), None
        for name, rule in CHAIN:
            verdict = rule(row, now_iso=now_iso, matcher=matcher,
                           max_years=max_years, vendors=vendors)
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
