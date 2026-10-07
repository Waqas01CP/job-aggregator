"""The projection: the filtered layer, as the operator reads it in `Jobs`.

ADR-0013: Airtable is a projection of the filtered layer and never the source
of truth. Every run plans the whole layer, so the display converges on what
the current rules admit, and a failed projection is resumable by
construction: the next run plans everything again. Since 2026-10-07 it reads
`Jobs` back and sends only the rows the display does not already show as
they would be sent (`what_differs`, the operator's decision).

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
   measured on a 170-member group. **`removed_unreviewed.json` is read by
   reason** (ADR-0043, 2026-09-28): a row returns only if the reason it left
   was the rules, because only the rules can change their mind. So a row
   stored as `closed`, aged out by ADR-0055's clock or removed by the
   operator's tool stays out, and one a rule dropped comes back when that
   rule admits it again, as ADR-0040 requires. Until 2026-09-30 the store was
   not read at all, and a retired closed row came straight back.
5. **Send** the pipeline-owned fields, ADR-0035's ten and ADR-0038's `Family`,
   through the Airtable client: the groups `Jobs` lacks, and the ones whose
   fields it shows otherwise.
"""

from datetime import datetime, timezone

from . import storage
from .airtable import PIPELINE_FIELDS
from .config import is_publishable
from .dedupe import group
from .filters import apply_chain
from .normalise import Row, loads

# ADR-0043's three classification stores, the only ones the skip reads.
CLASSIFICATION_STORES = ("rejected_not_a_fit.json", "rejected_poor_filtering.json",
                         "accepted.json")
# ADR-0046 step 4's store, read by the skip by reason and never as a whole:
# read whole, a row that fell out on a narrowed rule could never return.
REMOVED_UNREVIEWED_STORE = "removed_unreviewed.json"

# Why a row left the display without a classification. The reasons the rules
# give are "dropped by the <rule> rule", one per rule, built by the sweep.
REASON_CLOSED = "closed"
REASON_REGROUPED = "no longer its group's display row"
REASON_AGED_OUT = "unreviewed-aged-out"        # ADR-0055's clock
REASON_OPERATOR = "operator-removed"           # ADR-0055's tool
RULE_REASON = "dropped by the %s rule"


def returns(reason):
    """Whether a row that left for `reason` may come back to the display.

    ADR-0043's principle: only when the reason it left was the rules,
    because only the rules can change their mind. That covers a rule's drop,
    and the regrouping that follows the rules: a row that stopped being its
    group's display row left because another member now shows the group,
    and reading that record as a judgement would hide the live group with
    it. Any other reason keeps the row out, a reason not yet invented
    included, so a new way of removing a row cannot make one reappear."""
    reason = reason or ""
    return reason == REASON_REGROUPED or (reason.startswith("dropped by the ")
                                          and reason.endswith(" rule"))


def removal_key(identity, reason):
    """The removal store's key: a row can leave more than once, for different
    reasons, when a rule lets it back and something else then removes it."""
    return "%s|%s" % (identity, reason)


def latest_reasons(records):
    """Each identity's latest reason for leaving. Latest by `swept_at`, then
    by position, since the store only appends."""
    latest = {}
    for record in records:
        identity = record.get("identity")
        when = record.get("swept_at") or ""
        if identity not in latest or when >= latest[identity][0]:
            latest[identity] = (when, record.get("reason"))
    return {identity: reason for identity, (_, reason) in latest.items()}


def kept_out(records):
    """The identities whose latest removal keeps them out of the display."""
    return {identity for identity, reason in latest_reasons(records).items()
            if not returns(reason)}


class ProjectionError(Exception):
    pass


def _store_texts(directory, label):
    out = []
    for name in CLASSIFICATION_STORES + (REMOVED_UNREVIEWED_STORE,):
        path = "%s/%s" % (directory, name)
        try:
            with open(path, encoding="utf-8") as f:
                out.append(("%s %s" % (label, name), f.read()))
        except FileNotFoundError:
            out.append(("%s %s" % (label, name), None))
    return out


def public_store_texts(paths):
    """The restored working copies of the public stores. A store the branch
    does not hold yet reads as absent, which is empty."""
    return _store_texts(paths["outcomes_dir"], "public")


def private_store_texts(paths):
    """The working copies of the private repository's stores (ADR-0047),
    restored with the other aggregator files. The caller reads them only
    after a restore that succeeded: before one, an absent file would read as
    an empty store when the truth is unknown."""
    return _store_texts(paths["local_outcomes_dir"], "private")


def identities_in(texts):
    """Every identity the skip keeps out. `texts` is (label, text or None)
    pairs: a classification store's identities all count, and the removal
    store's count by reason. A store this cannot read raises: skipping
    nothing because a store was unreadable would re-surface everything the
    operator ever retired."""
    stored, removals = set(), []
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
            if label.endswith(REMOVED_UNREVIEWED_STORE):
                removals.append(record)
            else:
                stored.add(identity)
    return stored | kept_out(removals)


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
    """The pipeline-owned fields for one display group: ADR-0035's ten and
    ADR-0038's `Family`, the family of the term shown, never of the title.

    **Title and Matched term both come from `title_normalised`.** It is what
    the chain's title rule matches on, so the term shown is the term that
    admitted the row; matching the raw title could name another, or none, on
    a board that puts a city in its titles. And it is what the operator chose
    to read, 2026-09-23: a group gathers every city into Location, so a raw
    title naming one of them misleads. Normalisation only strips a trailing
    " - <city>" equal to the row's own location. The raw title is never lost
    where the pipeline stores anything: the raw and filtered layers on the
    branch keep `title` beside `title_normalised`. `Jobs` shows only the
    normalised one. Aggregator rows keep both in the private repository,
    ADR-0047, from 2026-09-24."""
    rep = g.representative
    term = matcher.match(rep.title_normalised)
    values = {
        "Title": rep.title_normalised,
        "Employer": rep.employer,
        "Location": "\n".join(g.locations),
        "Link": rep.url,
        "Published": airtable_datetime(rep.published_at),
        "First seen": airtable_datetime(rep.first_seen),
        "Order date": airtable_datetime(rep.ordering_date),
        "Board": rep.board_id,
        "Matched term": term,
        "Identity": rep.identity,
        "Family": matcher.family_of(term),
    }
    return {name: values[name] for name in PIPELINE_FIELDS}


def plan(rows, now_iso, matcher, stored, stages=None, retired=None):
    """Stages 2 to 4. Returns the records to send; fills `stages`.

    `retired(group)` says whether a group closed more than ADR-0050's
    fifteen days ago. Such a group is not sent: the sweep has retired its
    row, and ADR-0050 keeps it out "because the closure test still holds".
    Without this it would come straight back, since the filtered layer keeps
    every row it ever admitted."""
    stages = {} if stages is None else stages
    stages["rows_read"] = len(rows)
    kept, _ = apply_chain(rows, now_iso, matcher=matcher)
    admitted = [row for row, _ in kept]
    stages["rows_admitted"] = len(admitted)
    groups = group(admitted)
    stages["groups"] = len(groups)
    send = [g for g in groups if not any(m.identity in stored for m in g.members)]
    stages["groups_skipped_by_store"] = len(groups) - len(send)
    if retired is not None:
        still_open = [g for g in send if not retired(g)]
        stages["groups_retired_closed"] = len(send) - len(still_open)
        send = still_open
    records = [fields_for(g, matcher) for g in send]
    stages["rows_to_send"] = len(records)
    return records


DATE_FIELDS = ("Published", "First seen", "Order date")


def shown_value(name, value):
    """A pipeline field's value as two sides can agree on it: empty as None,
    whatever Airtable omits or returns blank; a date to the millisecond; text
    without the whitespace Airtable may trim."""
    if value is None or value == "":
        return None
    if name in DATE_FIELDS:
        try:
            return airtable_datetime(str(value))
        except ValueError:
            return str(value)
    return value.replace("\r\n", "\n").strip() if isinstance(value, str) else value


def unchanged(record, shown):
    """Whether `Jobs` already shows every pipeline field of `record` as sent."""
    return all(shown_value(name, record.get(name)) == shown_value(name, shown.get(name))
               for name in PIPELINE_FIELDS)


def what_differs(records, displayed, stages):
    """The planned records `Jobs` does not already show as they would be sent.

    **The operator's decision of 2026-10-07: read the display back and send
    only what differs.** ADR-0056 recorded the whole-layer projection's cost,
    one call per ten rows twice a day for ever, and a week measured about 7.5
    new display groups a day, about 230 rows at thirty days, past what a
    month's thousand calls can carry. Reading `Jobs` costs one call per
    hundred rows. It reverses ADR-0004's ruling of 2026-09-23 that the
    projection performs no reads, which he chose knowing it; the principle
    that ruling kept, Airtable never the source of truth, stands, since every
    value sent still comes from the repository and the read decides only
    which rows need sending. What the display lost or had edited by hand is
    sent again, so it heals itself, and a rule change that moves a field
    re-sends that row, as ADR-0040 requires, with no fingerprint of the rules
    to keep.

    An identity the display holds twice is sent, as before, and the upsert
    says what it makes of it."""
    by_identity = {}
    for r in displayed:
        identity = (r.get("fields") or {}).get("Identity")
        if identity:
            by_identity.setdefault(identity, []).append(r["fields"])
    stages["rows_in_base"] = len(displayed)
    new, changed, same = [], [], 0
    for record in records:
        shown = by_identity.get(record["Identity"])
        if not shown:
            new.append(record)
        elif len(shown) == 1 and unchanged(record, shown[0]):
            same += 1
        else:
            changed.append(record)
    stages["rows_unchanged"] = same
    stages["rows_new"] = len(new)
    stages["rows_changed"] = len(changed)
    return new + changed


def project(paths, now_iso, matcher, client, private_texts, stages, public_only=False,
            retired=None, displayed=None):
    """All five stages. `private_texts` are the private repository's copies
    of the same stores, from private_store_texts. `stages` is filled as each
    stage completes, so a failure part way still leaves a count of how far it
    got.

    `displayed()` reads `Jobs` back, for `what_differs`; without it every
    planned record is sent, the whole layer.

    **`public_only`: the private store could not be read.** The operator's
    decision of 2026-09-24, D9: the public rows always update. The aggregator
    rows are withheld, because the private stores that would keep a retired
    one out are unknown, and they are counted so the withholding shows."""
    rows = load_rows(paths)
    if public_only:
        kept = [r for r in rows if is_publishable(r.source)]
        stages["aggregator_rows_withheld"] = len(rows) - len(kept)
        rows, private_texts = kept, []
    stored = identities_in(public_store_texts(paths) + list(private_texts))
    stages["stored_identities"] = len(stored)
    records = plan(rows, now_iso, matcher, stored, stages, retired=retired)
    if displayed is not None:
        records = what_differs(records, displayed(), stages)
    client.upsert(records)
    stages["rows_sent"] = client.rows_sent
    return stages
