"""Two jobs that are easy to confuse, kept apart here.

**Delta detection.** Which rows the raw layer has never recorded, by identity.
ADR-0003 appends only records not previously seen and never rewrites one, so
this is what decides an append.

**Collapsing duplicates.** One job posted to several cities arrives as several
postings with different identities. ADR-0001's key is employer plus title plus
publication date, with the title normalised first per ADR-0027. Twenty to
thirty percent of harvested rows are this, and on Speechify it is ninety-nine:
1086 postings are 8 roles.

The raw layer keeps every posting, because ADR-0001 stores everything fetched
and a collapse is an interpretation. Only the display side sees groups.

Group membership is deterministic. The representative is the earliest by
publication date, then the lowest identity, so two runs over the same data
choose the same row and a diff of the filtered layer means a change.
"""

from dataclasses import dataclass, field

from .normalise import dedupe_key


@dataclass
class Group:
    key: str
    representative: object
    members: list = field(default_factory=list)

    @property
    def locations(self):
        """Every location the role was posted to, sorted so the value is
        stable across runs."""
        return sorted({m.location for m in self.members if m.location})

    @property
    def size(self):
        return len(self.members)


def split_new(rows, seen_identities):
    """(new, already_seen). ADR-0003: only the new ones are appended."""
    seen = set(seen_identities or ())
    new, existing = [], []
    for row in rows:
        (existing if row.identity in seen else new).append(row)
    return new, existing


def _rank(row):
    # Earliest publication first, then identity, so the choice never depends
    # on the order boards happened to answer in.
    return (row.published_at or "", row.identity)


def group(rows):
    """Collapse rows sharing a deduplication key."""
    buckets = {}
    for row in rows:
        buckets.setdefault(dedupe_key(row), []).append(row)

    groups = []
    for key in sorted(buckets):
        members = sorted(buckets[key], key=_rank)
        groups.append(Group(key=key, representative=members[0], members=members))
    return groups


def counts(groups):
    """For the run log: how much the collapse actually did."""
    postings = sum(g.size for g in groups)
    return {
        "postings": postings,
        "groups": len(groups),
        "collapsed": postings - len(groups),
        "largest_group": max((g.size for g in groups), default=0),
    }
