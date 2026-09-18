"""The priority star: a posting is starred when it shares a named attribute
with a role the operator accepted.

**This is deliberately not similarity matching.** The operator's want, that an
accepted role should raise the priority of later postings resembling it, has
an obvious implementation that ADR-0010 forbids: embed the accepted roles,
embed the candidate, compute a distance, sort. That is a relevance model. It
cannot be explained by naming a rule, and the scope floor exists to keep it
out.

**What is built instead.** Three named attributes, compared for equality:

    employer        the same company is hiring again
    matched term    the same pool term admitted both
    role family     both terms sit under the same heading in the pool

A star names the attribute, the value, and the accepted row it came from. If
a star cannot be read aloud as "starred because the employer matches accepted
row N", it is a model and it does not belong here.

**The line, stated so the next session can see where it was drawn.** No
score. No distance. No embedding. No ranking of one star above another, and
no count of stars used as a rank: ADR-0038 already establishes that ordering
by a derived number is the shape a ranking arrives in. A row is starred or it
is not, and the display still orders by date.

**Nothing here drops a row.** The star is a display annotation. A posting
that resembles nothing accepted is shown exactly as it is today.
"""

from .filters import TitleMatcher
from .normalise import fold

# The named attributes a star may rest on, in the order a reason is reported.
# Adding one is a decision, not a refactor: it widens what "resembles" means.
ATTRIBUTES = ("employer", "matched term", "role family")


def attributes_of(row, matcher):
    """The three comparable attributes of a row, folded for comparison.

    The matched term is recomputed from the title rather than read from the
    row, because the row shape does not carry it: `apply_chain` reports it
    alongside the kept row and the stored record drops it. Recomputing is
    deterministic and uses the same matcher the chain used."""
    term = matcher.match(row.title_normalised)
    return {
        "employer": fold(row.employer) if row.employer else None,
        "matched term": term,
        "role family": matcher.family_of(term),
    }


def star_reasons(row, accepted, matcher=None):
    """Every reason `row` is starred, each naming its attribute and source.

    `accepted` is the accepted outcome store's rows. Returns a list, empty
    when nothing matches, ordered by ATTRIBUTES then by accepted identity, so
    two runs over the same data produce the same reasons in the same order.

    A row never stars itself: an accepted row sharing the candidate's own
    identity is skipped, or re-projecting the accepted store would star every
    row in it for resembling itself."""
    matcher = matcher or TitleMatcher()
    mine = attributes_of(row, matcher)
    reasons = []
    for other in accepted:
        if other.identity == row.identity:
            continue
        theirs = attributes_of(other, matcher)
        for attribute in ATTRIBUTES:
            value = mine.get(attribute)
            if value is not None and value == theirs.get(attribute):
                reasons.append({
                    "attribute": attribute,
                    "value": value,
                    "accepted_identity": other.identity,
                })
    reasons.sort(key=lambda r: (ATTRIBUTES.index(r["attribute"]),
                                r["accepted_identity"]))
    return reasons


def is_starred(row, accepted, matcher=None):
    return bool(star_reasons(row, accepted, matcher))


def explain(reasons):
    """The star as a sentence, which is the test ADR-0010 sets.

    If this cannot be written for a star, the star came from something other
    than a named attribute and is out of scope."""
    return ["starred because %s matches accepted row %s (%s)"
            % (r["attribute"], r["accepted_identity"], r["value"])
            for r in reasons]
