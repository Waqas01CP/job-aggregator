"""The projection: the filtered layer, as the operator reads it in `Jobs`.

ADR-0013: Airtable is a projection of the filtered layer and never the source
of truth. Every run re-projects the whole layer, so the display converges on
what the current rules admit, and a failed projection is resumable by
construction: the next run sends everything again.

Five stages, each counted, because the display, the store and the chain's
verdicts differ in row count by design and a difference nobody can trace
looks like a bug:

1. **Read** `filtered.json` and the local aggregator copy, as they stand
   after this run's writes and ADR-0030's backfill.
2. **Filter** with the current chain (ADR-0040). The store is never filtered,
   rewritten or pruned; this module only reads it.
3. **Group** with `dedupe.group`, one display row per group (ADR-0037). The
   row carries the representative's identity and every member's location.
4. **Skip** a group when **any member's** identity is in one of the three
   classification stores (ADR-0046, 2026-09-23). Testing the representative
   alone let a classified role come back under the next member's identity:
   measured on a 170-member group. `removed_unreviewed.json` is deliberately
   not read, so a row that fell out on a narrowed rule returns if the rule
   widens again (ADR-0040, ADR-0043).
5. **Send** ADR-0035's ten fields through the Airtable client.
"""

from datetime import datetime, timezone

from . import storage
from .airtable import PIPELINE_FIELDS
from .dedupe import group
from .filters import apply_chain
from .normalise import Row, loads

# ADR-0043's three classification stores, the only ones the skip reads.
CLASSIFICATION_STORES = ("rejected_not_a_fit.json", "rejected_poor_filtering.json",
                         "accepted.json")
# ADR-0046 step 4's store. Named so nothing reads it by accident: the skip must
# not, or a row that fell out could never return.
REMOVED_UNREVIEWED_STORE = "removed_unreviewed.json"


class ProjectionError(Exception):
    pass


def store_paths():
    """Branch-relative paths of the stores the skip reads, the same in the
    public data branch and the private repository (ADR-0047)."""
    return ["%s/%s" % (storage.OUTCOMES_DIR, name) for name in CLASSIFICATION_STORES]


def public_store_texts(paths):
    """The restored working copies of the public stores. A store the branch
    does not hold yet reads as absent, which is empty."""
    out = []
    for name in CLASSIFICATION_STORES:
        path = "%s/%s" % (paths["outcomes_dir"], name)
        try:
            with open(path, encoding="utf-8") as f:
                out.append(("public %s" % name, f.read()))
        except FileNotFoundError:
            out.append(("public %s" % name, None))
    return out


def identities_in(texts):
    """Every identity the given stores hold. `texts` is (label, text or None)
    pairs. A store this cannot read raises: skipping nothing because a store
    was unreadable would re-surface everything the operator ever retired."""
    stored = set()
    for label, text in texts:
        if text is None or not text.strip():
            continue
        records = loads(text)
        if not isinstance(records, list):
            raise ProjectionError("%s does not hold a list of records" % label)
        for record in records:
            identity = record.get("identity") if isinstance(record, dict) else None
            if not identity:
                raise ProjectionError("%s holds a record with no identity" % label)
            stored.add(identity)
    return stored


def load_rows(paths):
    rows = []
    for key in ("filtered", "local_filtered"):
        for record in storage.read_records(paths[key]):
            try:
                rows.append(Row(**record))
            except TypeError as e:
                raise ProjectionError("%s holds a record this code cannot read: %s"
                                      % (paths[key], e))
    return rows


def airtable_datetime(value):
    """UTC to the millisecond. Stored times carry microseconds; the rows
    already in `Jobs test` carry milliseconds, which is what is known to be
    accepted."""
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return "%s.%03dZ" % (dt.strftime("%Y-%m-%dT%H:%M:%S"), dt.microsecond // 1000)


def fields_for(g, matcher):
    """ADR-0035's ten fields for one display group.

    **Title and Matched term both come from `title_normalised`.** It is what
    the chain's title rule matches on, so the term shown is the term that
    admitted the row; matching the raw title could name another, or none, on
    a board that puts a city in its titles. And it is what the operator chose
    to read, 2026-09-23: a group gathers every city into Location, so a raw
    title naming one of them misleads. Normalisation only strips a trailing
    " - <city>" equal to the row's own location. The raw title is never lost:
    every layer stores `title` beside `title_normalised`."""
    rep = g.representative
    values = {
        "Title": rep.title_normalised,
        "Employer": rep.employer,
        "Location": "\n".join(g.locations),
        "Link": rep.url,
        "Published": airtable_datetime(rep.published_at),
        "First seen": airtable_datetime(rep.first_seen),
        "Order date": airtable_datetime(rep.ordering_date),
        "Board": rep.board_id,
        "Matched term": matcher.match(rep.title_normalised),
        "Identity": rep.identity,
    }
    return {name: values[name] for name in PIPELINE_FIELDS}


def plan(rows, now_iso, matcher, stored, stages=None):
    """Stages 2 to 4. Returns the records to send; fills `stages`."""
    stages = {} if stages is None else stages
    stages["rows_read"] = len(rows)
    kept, _ = apply_chain(rows, now_iso, matcher=matcher)
    admitted = [row for row, _ in kept]
    stages["rows_admitted"] = len(admitted)
    groups = group(admitted)
    stages["groups"] = len(groups)
    send = [g for g in groups if not any(m.identity in stored for m in g.members)]
    stages["groups_skipped_by_store"] = len(groups) - len(send)
    records = [fields_for(g, matcher) for g in send]
    stages["rows_to_send"] = len(records)
    return records


def project(paths, now_iso, matcher, client, private_texts, stages):
    """All five stages. `private_texts` are the private repository's copies
    of the same stores. `stages` is filled as each stage completes, so a
    failure part way still leaves a count of how far it got."""
    rows = load_rows(paths)
    stored = identities_in(public_store_texts(paths) + list(private_texts))
    stages["stored_identities"] = len(stored)
    records = plan(rows, now_iso, matcher, stored, stages)
    client.upsert(records)
    stages["rows_sent"] = client.rows_sent
    return stages
