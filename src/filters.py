"""The filter chain. Cheapest disqualifier first, every drop naming its rule.

Order: expiry, stated experience, annotation vendors, title.

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
by an implementing session.

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
    def __init__(self, path=None):
        self.terms, self.exempt = load_title_pool(path)
        self.patterns = compile_terms(self.terms)

    def match(self, title):
        """The first term that matches, or None. Returning the term is the
        point: every admission must be explainable by naming one term."""
        folded = fold(title)
        for term, pattern in self.patterns:
            if pattern.search(folded):
                return term
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


CHAIN = (("expiry", rule_expiry),
         ("experience", rule_experience),
         ("annotation_vendor", rule_annotation_vendor),
         ("title", rule_title))


def apply_chain(rows, now_iso, matcher=None, max_years=None,
                vendors=ANNOTATION_VENDORS):
    """Returns (kept, drops). Each drop names the rule that caused it."""
    matcher = matcher or TitleMatcher()
    kept, drops = [], []
    for row in rows:
        verdict = Verdict(True)
        for name, rule in CHAIN:
            verdict = rule(row, now_iso=now_iso, matcher=matcher,
                           max_years=max_years, vendors=vendors)
            if not verdict.keep:
                drops.append({"identity": row.identity, "rule": verdict.rule,
                              "reason": verdict.reason, "title": row.title,
                              "employer": row.employer, "board_id": row.board_id})
                break
        if verdict.keep:
            kept.append((row, verdict.reason))
    return kept, drops


def drop_counts(drops):
    """Per rule, for the run log. ADR-0005."""
    counts = {name: 0 for name, _ in CHAIN}
    for d in drops:
        counts[d["rule"]] = counts.get(d["rule"], 0) + 1
    return counts
