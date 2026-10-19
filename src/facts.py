"""Stored rows' derived facts, re-read from their saved postings when the code
or configuration that derives them changes. ADR-0040's and ADR-0058's Changes,
the operator's yes of 2026-10-16 (his option (b) on Brief 12).

**Why.** A row keeps the facts it was given at first sight: the years its
description asks, the levels it states, its place and workplace, the places
a right to work is required in. When the reader or a rule that reads one of
them changes, a row stored before the change keeps facts the new code would
not give it, and today's rules judge it on them. Spreetail's Lever row, first
seen 2026-09-17 with only "Manila", stayed admitted because the source's own
country was not read until 2026-10-02; read again from its saved posting it
carries PH and drops. Of the 130 rows the Senior change's backfill would add,
41 pass only on facts today's reader would not give them.

**How, without rewriting the append-only layers (ADR-0003).** An overlay keyed
by identity: `facts.json` beside the public layers for employer-board rows,
its twin in the private repository for aggregator rows (ADR-0020, ADR-0047).
Each record holds the derived fields only, numbers, configured place names,
flags, stated levels and since 2026-10-19 a label of who reads the
application, what the public layer already carries (ADR-0058).
Every loader that judges stored rows reads the overlay first. The overlay is
a cache, rewritten whole at each re-read, never a record of anything.

**When.** On a change to the files that derive the facts, by a fingerprint
over them: a run whose overlay was read under another fingerprint re-reads
every saved posting before it judges anything. Not every run: the private
full branch is read only then, which is what removes ADR-0040's objection of
2026-10-03. A change to a comment re-reads too, at a minute of runner time
and no Airtable call, which is cheaper than a version someone must remember
to bump.

**A row with no saved posting keeps the facts it stored**: 1,741 of 6,611 on
2026-10-16, first seen before postings were saved in full on 2026-09-26.
"""

import glob
import hashlib
import os
from dataclasses import replace
from datetime import datetime

from . import storage
from .config import is_publishable
from .normalise import dumps, loads, normalise

# The facts a row derives from its posting, and nothing else: its identity,
# title and dates are what it was first seen as, and are never re-read.
DERIVED = ("stated_experience", "stated_levels", "places", "workplace", "required_places",
           "described_workplace", "described", "who_reads")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The code and configuration the derived facts come from.
SOURCES = ("src/description.py", "src/normalise.py", "src/adapters/*.py",
           "config/eligibility.json", "config/who_reads.json")


def fingerprint(root=REPO_ROOT, sources=SOURCES):
    """A hash over the files that derive the facts, each by its path and its
    bytes with line endings made one, so a checkout on another system reads
    the same."""
    digest = hashlib.sha256()
    for pattern in sources:
        for path in sorted(glob.glob(os.path.join(root, pattern))):
            with open(path, "rb") as f:
                body = f.read().replace(b"\r\n", b"\n")
            digest.update(os.path.relpath(path, root).replace(os.sep, "/").encode("utf-8"))
            digest.update(b"\0")
            digest.update(body)
            digest.update(b"\0")
    return digest.hexdigest()[:16]


def envelope(adapter, posting):
    """One saved posting as its adapter's parse expects a response."""
    key = getattr(adapter, "POSTINGS_AT", None)
    return [posting] if key is None else {key: [posting]}


def reread(texts, boards, first_seen, adapters):
    """The derived facts of every posting the saved files hold, by identity,
    as today's adapter and reader give them at its first sight. `texts` are
    the full branch's files; `first_seen` maps an identity to its first sight.
    Returns (records, counts). A posting whose board is no longer configured,
    or that its adapter cannot parse, is counted and left out: its row keeps
    the facts it stored."""
    boards = {b.board_id: b for b in boards}
    records, counts = {}, {"read": 0, "unknown_board": 0, "unparseable": 0}
    for text in texts:
        for entry in loads(text):
            identity = entry.get("identity")
            if not identity or identity in records:
                continue
            board = boards.get(entry.get("board_id"))
            adapter = adapters.get(board.platform) if board else None
            if adapter is None:
                counts["unknown_board"] += 1
                continue
            seen = first_seen.get(identity) or entry.get("fetched_at")
            try:
                parsed = adapter.parse(envelope(adapter, entry.get("posting")), board)
                when = datetime.fromisoformat(seen.replace("Z", "+00:00"))
                rows = normalise(parsed.postings, board, when, seen={identity: seen})
                [row] = [r for r in rows if r.identity == identity]
            except Exception:
                counts["unparseable"] += 1
                continue
            record = {"identity": identity, "source": row.source}
            record.update({name: getattr(row, name) for name in DERIVED})
            records[identity] = record
            counts["read"] += 1
    return records, counts


def write(paths, records, fp):
    """The overlay, split by source class as every layer is: an aggregator's
    facts never reach the public branch (ADR-0020). Each file names the
    fingerprint it was read under."""
    for key, publishable in (("facts", True), ("local_facts", False)):
        rows = [r for _, r in sorted(records.items())
                if is_publishable(r["source"]) == publishable]
        storage.write_atomic(paths[key], dumps({"fingerprint": fp, "records": rows}))


def load(paths):
    """(identity -> record, the fingerprints the files were read under). A
    missing file holds nothing and no fingerprint."""
    records, fps = {}, set()
    for key in ("facts", "local_facts"):
        if not paths.get(key):
            continue
        try:
            with open(paths[key], encoding="utf-8") as f:
                doc = loads(f.read())
        except FileNotFoundError:
            continue
        fps.add(doc.get("fingerprint"))
        for r in doc.get("records") or []:
            records[r["identity"]] = r
    return records, fps


def apply(rows, records):
    """Rows with their derived facts as the overlay gives them; a row the
    overlay does not hold is left as it is."""
    out = []
    for row in rows:
        r = records.get(row.identity)
        out.append(replace(row, **{name: r[name] for name in DERIVED if name in r}) if r else row)
    return out


def applied(rows, paths):
    """`apply` over the overlay on disk: what every loader that judges
    stored rows calls."""
    records, _ = load(paths)
    return apply(rows, records) if records else rows
