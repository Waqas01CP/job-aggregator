"""The sweep. ADR-0050's six steps, in the record's order.

1. **Copy.** Every row in `Jobs` with a status and no copy in the matching
   table gets one. What happens to a copy its row's status no longer
   matches is the operator's D12, 2026-09-26:
   - **a cleared status removes nothing**, since a clear is no new
     classification and one stray keystroke makes it;
   - **an `accepted` copy stays** whatever the status becomes, reported, for
     him to remove with `Delete`;
   - **a superseded rejection copy is saved before it goes**: its reason is
     written to `removed_copies.json`, and the copy is deleted only once that
     store holds it, the same write, verify, delete as every other removal.
     ADR-0050 line 71 discarded the reason; the operator's rule is that a
     classification is always saved before it leaves Airtable.
2. **Store, verify, delete from `Jobs`**, fifteen days after `Classified at`.
3. **Delete from the two rejection tables**, fifteen days after `Classified`.
   `accepted` is deleted by no clock. **An `accepted` copy leaves Airtable
   only when the operator sets `Delete` to yes**, and only once its record,
   `Stage` and all, is in `removed_copies.json` and, while its row is still
   in `Jobs`, in the accepted store, both read back from origin. It never
   leaves a store. D12.
4. **Mark what has closed** with `Closed`.
5. **Retire what closed**, fifteen days after `Closed`.
6. **Remove what a rule dropped**, at once. A row the stored layers do not
   hold is not judged by the rules; it is counted.
7. **ADR-0055's clock**: an unreviewed row leaves thirty days after it was
   first seen, with the reason `unreviewed-aged-out`. The number is
   `unreviewed_after_days` in `config/sweep.json`.

**Rows the operator's tool removed leave by the same path.** ADR-0055's tool
writes the store and nothing else; this sweep deletes the row once the store
restored from origin holds it, a day later, as for every other removal.

**Every removal is named in the run log**, by identity, what it left and why,
so an absence can be reconstructed from the logs. An aggregator's identity is
masked there, since the log is public, and named in its private store.

Step 1 runs on every committing run. Steps 2 to 6 are daily: they run
except on the evening slot.

**Write, verify, then delete, and the verify reads what GitHub holds.** A
store is durable only once the workflow has pushed it, after this run ends.
So an outcome written by this run is not yet verified, and its row stays.
The next daily sweep deletes the row only if the store it restored from
origin holds the identity. A push that failed leaves the row where it was,
and the store is written again. No row is deleted on the strength of another
row's success, and none on a write nobody has read back from the branch.
"Origin" holds on a runner, which checks the branch out fresh. A local
committing run restores from the local `data` ref, which can carry commits
never pushed, so there the verify is only as good as that ref (the audit of
2026-09-25, nit 3). The workflow is the only place the sweep is meant to run.

**Routing is exclusive, ADR-0043.** An identity already in one classification
store is never written to another; the row is reported and left.

**Aggregator rows need the private store.** Their outcomes belong there
(ADR-0047). When it could not be restored they are copied, since a copy needs
no store, and otherwise held and counted.

**The pipeline writes none of the operator's fields.** `Status`, the reasons
and `Stage` are read here and never sent; the client refuses them.
"""

from datetime import datetime, timedelta, timezone

from . import storage
from .airtable_sweep import (CLASSIFICATION_TABLES, COPY_FIELDS, DELETE_FIELD, DELETE_YES, JOBS,
                             OPERATOR_FIELD)
from .config import is_publishable
from .dedupe import group
from .filters import apply_chain
from .normalise import Row
from .projection import (REASON_AGED_OUT, REASON_CLOSED, REASON_REGROUPED,
                         REMOVED_UNREVIEWED_STORE, RULE_REASON, latest_reasons, removal_key,
                         returns)

STORE_FOR = {"rejected-not-a-fit": "rejected_not_a_fit.json",
             "rejected-poor-filtering": "rejected_poor_filtering.json",
             "accepted": "accepted.json"}
REJECTION_TABLES = ("rejected-not-a-fit", "rejected-poor-filtering")
JOBS_FIELDS = COPY_FIELDS + ("Status", "Classified at", "Closed")
# Every copy the sweep removes from a classification table other than by the
# fifteen-day clock, keyed by the copy's own record ID, since one posting can
# be reclassified more than once. Not a classification store: the projection
# never reads it, so nothing in it hides a row. D12.
REMOVED_COPIES_STORE = "removed_copies.json"
# The mark a record carries when the operator's own tool wrote it (ADR-0055).
# Such a classified row or copy leaves at once rather than at fifteen days,
# once the store holding the mark is read back from origin.
REMOVED_BY_OPERATOR = "operator"
# What each classification table is read for. `accepted` is read whole, so a
# copy whose row has left `Jobs` can still be stored from its own fields.
READ_FIELDS = {t: ("Identity", OPERATOR_FIELD[t]) for t in REJECTION_TABLES}
READ_FIELDS["accepted"] = COPY_FIELDS + (OPERATOR_FIELD["accepted"], DELETE_FIELD)


def source_of(identity):
    return identity.split(":", 1)[0] if identity and ":" in identity else None


def parse_time(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def masked(identity):
    """An identity fit for the public run log: an aggregator's is not."""
    return identity if is_publishable(source_of(identity)) else "<aggregator row>"


class Stores:
    """The four stores in both places. `durable` is what the run restored
    from origin, snapshot before this run writes anything: the only thing
    a deletion may be verified against."""

    def __init__(self, paths, private_ok):
        self.dirs = {"public": paths["outcomes_dir"]}
        if private_ok:
            self.dirs["private"] = paths["local_outcomes_dir"]
        names = tuple(STORE_FOR.values()) + (REMOVED_UNREVIEWED_STORE,)
        self.durable = {}
        self.durable_copies = {}
        # The removal store by (identity, reason): a row can leave, return
        # when a rule widens, and leave again for another reason, and the
        # second removal must be written before its row is deleted.
        self.durable_removals = {}
        self.durable_latest = {}
        # Classification records the operator's tool wrote, which let their
        # rows and copies leave before fifteen days.
        self.durable_by_operator = {}
        for where, directory in self.dirs.items():
            for name in names:
                path = "%s/%s" % (directory, name)
                records = storage.read_records(path)
                self.durable[(where, name)] = {r.get("identity") for r in records}
                self.durable_by_operator[(where, name)] = {
                    r.get("identity") for r in records
                    if r.get("removed_by") == REMOVED_BY_OPERATOR}
                if name == REMOVED_UNREVIEWED_STORE:
                    self.durable_removals[where] = {(r.get("identity"), r.get("reason"))
                                                    for r in records}
                    self.durable_latest[where] = latest_reasons(records)
            self.durable_copies[where] = {
                r.get("copy_id") for r in
                storage.read_records("%s/%s" % (directory, REMOVED_COPIES_STORE))}
        self.written = {}

    def where(self, identity):
        """"public", "private", or None when the private store is unavailable."""
        where = "public" if is_publishable(source_of(identity)) else "private"
        return where if where in self.dirs else None

    def durable_has(self, where, name, identity):
        return identity in self.durable.get((where, name), set())

    def durable_removal(self, where, identity, reason):
        """Whether origin's removal store holds this row leaving for this
        reason."""
        return (identity, reason) in self.durable_removals.get(where, set())

    def kept_out_reason(self, where, identity):
        """The reason origin's removal store keeps this row out, or None when
        it holds none, or its latest reason is one the rules may reverse."""
        latest = self.durable_latest.get(where, {})
        if identity not in latest or returns(latest[identity]):
            return None
        return latest[identity]

    def removed_by_operator(self, where, name, identity):
        return identity in self.durable_by_operator.get((where, name), set())

    def exclusivity_violations(self):
        """ADR-0043's invariant, scoped 2026-09-28 to the three outcome
        corpora: no identity in two of them. Not the removal store, and not
        `removed_copies.json`, which D12 writes an `accepted` copy to beside
        the accepted store in the same run, so a check over all five would
        fail on correct behaviour."""
        found = []
        names = list(STORE_FOR.values())
        for where in self.dirs:
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    both = (self.durable.get((where, a), set())
                            & self.durable.get((where, b), set())) - {None}
                    found.extend((identity, a, b) for identity in sorted(both))
        return found

    def classified_elsewhere(self, where, name, identity):
        return [n for n in STORE_FOR.values() if n != name
                and identity in self.durable.get((where, n), set())]

    def copy_saved(self, where, copy_id):
        """Whether the removed-copies store restored from origin holds it."""
        return copy_id in self.durable_copies.get(where, set())

    def write(self, where, name, record, key="identity"):
        path = "%s/%s" % (self.dirs[where], name)
        appended = storage.append_delta(path, [record], key=key)
        key = "%s %s" % (where, name)
        self.written[key] = self.written.get(key, 0) + appended
        return appended


def older_than(value, days, now):
    return bool(value) and parse_time(value) <= now - timedelta(days=days)


def jobs_fields_record(fields):
    """A store record for a row the stored layers do not hold, built from the
    display row itself and marked so."""
    identity = fields.get("Identity")
    return {"identity": identity, "source": source_of(identity),
            "board_id": fields.get("Board"), "title": fields.get("Title"),
            "employer": fields.get("Employer"), "url": fields.get("Link"),
            "location": fields.get("Location"), "from": "display"}


class Sweep:
    def __init__(self, client, paths, now, matcher, closure, config, private_ok):
        self.client = client
        self.paths = paths
        self.now = now
        self.now_iso = now.isoformat().replace("+00:00", "Z")
        self.matcher = matcher
        self.closure = closure
        self.config = config
        self.stores = Stores(paths, private_ok)
        self.report = {"copied": {}, "stale_copies_deleted": {}, "deleted_from_jobs": 0,
                       "copies_deleted": {}, "closed_marked": 0, "closed_cleared": 0,
                       "waiting_for_the_store": 0, "held_private_unavailable": 0,
                       "not_in_the_stored_layers": 0, "kept_after_a_clear": 0,
                       "aged_out": 0, "removals": [], "problems": []}
        self._load_rows()

    # ------------------------------------------------------------- the data
    def _load_rows(self):
        rows = []
        for key in ("filtered", "local_filtered"):
            if key == "local_filtered" and "private" not in self.stores.dirs:
                continue
            rows.extend(Row(**r) for r in storage.read_records(self.paths[key]))
        self.rows = {r.identity: r for r in rows}
        kept, drops = apply_chain(rows, self.now_iso, matcher=self.matcher)
        self.dropped_by = {d["identity"]: d["rule"] for d in drops}
        self.group_of, self.representatives = {}, set()
        for g in group([row for row, _ in kept]):
            self.representatives.add(g.representative.identity)
            for member in g.members:
                self.group_of[member.identity] = g

    def record(self, identity, fields, **outcome):
        row = self.rows.get(identity)
        rec = row.as_record() if row else jobs_fields_record(fields)
        rec.update(outcome)
        rec["swept_at"] = self.now_iso
        return rec

    def copy_record(self, copy, table, why, fields):
        """What `removed_copies.json` keeps of a copy about to leave Airtable:
        the posting, as the stored layers or `fields` give it, and everything
        the operator put on the copy."""
        f = copy["fields"]
        return self.record(f.get("Identity"), fields, copy_id=copy["id"], table=table,
                           reason=f.get(OPERATOR_FIELD[table]), classified=copy.get("createdTime"),
                           why=why)

    def _problem(self, text):
        self.report["problems"].append(text)

    def _bump(self, key, table, n=1):
        self.report[key][table] = self.report[key].get(table, 0) + n

    def _removal(self, identity, table, reason, action):
        """Name one removal in the run log: a store write or a deletion."""
        self.report["removals"].append({"identity": masked(identity), "table": table,
                                        "reason": reason, "action": action})

    # ------------------------------------------------------------------ run
    def run(self, daily, since=None):
        """One sweep. `since` is when the previous copy step ran: a copy-only
        run reads the classification tables only if a status moved after it."""
        self.report["daily"] = daily
        jobs = self.client.list_records(JOBS, JOBS_FIELDS)
        self.report["jobs_rows"] = len(jobs)
        in_jobs = {r["fields"].get("Identity"): r for r in jobs if r["fields"].get("Identity")}
        # `Classified at` moves whenever `Status` does, a clear included, so
        # it says which rows moved. Without a previous run to compare
        # against, every row may have.
        moved = [r for r in jobs if since is not None
                 and (r["fields"].get("Classified at") or "") > since]
        read_tables = daily or since is None or bool(moved)
        self.report["tables_read"] = read_tables
        copies = {t: [] for t in CLASSIFICATION_TABLES}
        if read_tables:
            for t in CLASSIFICATION_TABLES:
                copies[t] = self.client.list_records(t, READ_FIELDS[t])
            self.step1_copy(jobs, in_jobs, copies)
        if daily:
            self.daily(jobs, copies, in_jobs)
            for identity, a, b in self.stores.exclusivity_violations():
                self._problem("%s is in both %s and %s; ADR-0043 allows one"
                              % (masked(identity), a, b))
        self.report["stored_written"] = dict(self.stores.written)
        return self.report

    # --------------------------------------------------------------- step 1
    def step1_copy(self, jobs, in_jobs, copies):
        index = {t: {} for t in CLASSIFICATION_TABLES}
        for t in CLASSIFICATION_TABLES:
            for c in copies[t]:
                index[t].setdefault(c["fields"].get("Identity"), []).append(c)
        self.copy_index = index
        create = {t: [] for t in CLASSIFICATION_TABLES}
        superseded = {t: [] for t in REJECTION_TABLES}
        for r in jobs:
            identity, status = r["fields"].get("Identity"), r["fields"].get("Status")
            if not identity:
                continue
            for t in CLASSIFICATION_TABLES:
                held = index[t].get(identity, [])
                if t == status and not held:
                    create[t].append({name: r["fields"].get(name) for name in COPY_FIELDS})
                elif t == status and len(held) > 1:
                    self._problem("%s has %d copies in %s" % (masked(identity), len(held), t))
                elif t == status or not held:
                    continue
                elif not status:
                    # A clear is no new classification, and one stray
                    # keystroke makes it: nothing is removed (D12).
                    self.report["kept_after_a_clear"] += len(held)
                elif t == "accepted":
                    self._problem("the accepted copy of %s is kept although its status is now %s; "
                                  "set Delete on it to remove it from Airtable"
                                  % (masked(identity), status))
                else:
                    superseded[t].extend((c, r["fields"], status) for c in held)
        for t in REJECTION_TABLES:
            gone = []
            for c, fields, status in superseded[t]:
                where = self.stores.where(fields.get("Identity"))
                if where is None:
                    self.report["held_private_unavailable"] += 1
                elif self.stores.copy_saved(where, c["id"]):
                    gone.append(c["id"])
                else:
                    # Saved first, removed on a later run once origin holds
                    # the record: the reason is the operator's (D12).
                    self.stores.write(where, REMOVED_COPIES_STORE,
                                      self.copy_record(c, t, "superseded: the status is now %s"
                                                       % status, fields), key="copy_id")
                    self.report["waiting_for_the_store"] += 1
            if gone:
                self.client.delete(t, gone)
                self._bump("stale_copies_deleted", t, len(gone))
                removed = set(gone)
                for c in [c for c in copies[t] if c["id"] in removed]:
                    index[t].pop(c["fields"].get("Identity"), None)
                # Out of the run's read too, or step 3 deletes it a second
                # time and the whole daily sweep fails on the unconfirmed
                # delete: the audit of 2026-09-25, F4.
                copies[t][:] = [c for c in copies[t] if c["id"] not in removed]
        for t in CLASSIFICATION_TABLES:
            if create[t]:
                self.client.create_copies(t, create[t])
                self._bump("copied", t, len(create[t]))

    # ----------------------------------------------------------- steps 2-7
    def daily(self, jobs, copies, in_jobs=None):
        days = self.config.retire_after_days
        # (record ID, identity, why): a row can qualify twice, and each
        # deletion is named in the run log.
        delete_jobs, closed_updates = [], []
        in_jobs = in_jobs or {}

        # Step 2: classified rows, fifteen days on, or at once when the
        # operator's tool wrote their outcome (ADR-0055).
        for r in jobs:
            f = r["fields"]
            identity, status = f.get("Identity"), f.get("Status")
            if not identity or status not in STORE_FOR:
                continue
            where, name = self.stores.where(identity), STORE_FOR[status]
            early = where is not None and self.stores.removed_by_operator(where, name, identity)
            if not early and not older_than(f.get("Classified at"), days, self.now):
                continue
            if where is None:
                self.report["held_private_unavailable"] += 1
                continue
            if self.stores.classified_elsewhere(where, name, identity):
                self._problem("%s is already in another classification store; left in Jobs"
                              % masked(identity))
                continue
            why = "classified %s%s" % (status, ", removed by the operator's tool" if early else "")
            if self.stores.durable_has(where, name, identity):
                delete_jobs.append((r["id"], identity, why))
                continue
            held = self.copy_index.get(status, {}).get(identity, [])
            reason = held[0]["fields"].get(OPERATOR_FIELD[status]) if held else None
            self.stores.write(where, name, self.record(identity, f, status=status,
                                                       reason=reason,
                                                       classified_at=f.get("Classified at")))
            self._removal(identity, JOBS, why, "stored")
            self.report["waiting_for_the_store"] += 1

        # Step 3: the rejection tables, fifteen days on, or at once when the
        # operator's tool wrote their outcome. Never `accepted`.
        for t in REJECTION_TABLES:
            gone = []
            for c in copies[t]:
                identity = c["fields"].get("Identity")
                where = self.stores.where(identity)
                early = where is not None and self.stores.removed_by_operator(
                    where, STORE_FOR[t], identity)
                if not early and not older_than(c.get("createdTime"), days, self.now):
                    continue
                if where is None:
                    self.report["held_private_unavailable"] += 1
                elif self.stores.durable_has(where, STORE_FOR[t], identity):
                    gone.append(c["id"])
                    self._removal(identity, t, "removed by the operator's tool" if early
                                  else "%d days after it was classified" % days, "deleted")
                else:
                    self._problem("the %s copy of %s is past %d days but its outcome is not "
                                  "in the store; kept" % (t, masked(identity), days))
            if gone:
                self.client.delete(t, gone)
                self._bump("copies_deleted", t, len(gone))

        # Step 3 for `accepted`: out of Airtable only on the operator's
        # `Delete`, and only once origin holds its record (D12).
        gone = []
        for c in copies["accepted"]:
            f = c["fields"]
            if f.get(DELETE_FIELD) != DELETE_YES:
                continue
            identity = f.get("Identity")
            where = self.stores.where(identity)
            if where is None:
                self.report["held_private_unavailable"] += 1
                continue
            row = in_jobs.get(identity)
            row_accepted = row is not None and row["fields"].get("Status") == "accepted"
            if row_accepted and self.stores.classified_elsewhere(where, STORE_FOR["accepted"],
                                                                 identity):
                self._problem("%s is already in another classification store; its accepted "
                              "copy is kept" % masked(identity))
                continue
            saved = self.stores.copy_saved(where, c["id"])
            stored = not row_accepted or self.stores.durable_has(where, STORE_FOR["accepted"],
                                                                 identity)
            if saved and stored:
                gone.append(c["id"])
                self._removal(identity, "accepted", "the operator marked Delete", "deleted")
                if row_accepted:
                    # Its row goes with it: left alone, step 1 would copy it
                    # straight back.
                    delete_jobs.append((row["id"], identity, "its accepted copy was deleted"))
                continue
            if not saved:
                self.stores.write(where, REMOVED_COPIES_STORE,
                                  self.copy_record(c, "accepted", "the operator marked Delete",
                                                   row["fields"] if row else f), key="copy_id")
            if not stored:
                rf = row["fields"]
                self.stores.write(where, STORE_FOR["accepted"],
                                  self.record(identity, rf, status="accepted",
                                              reason=f.get(OPERATOR_FIELD["accepted"]),
                                              classified_at=rf.get("Classified at")))
            self._removal(identity, "accepted", "the operator marked Delete", "stored")
            self.report["waiting_for_the_store"] += 1
        if gone:
            self.client.delete("accepted", gone)
            self._bump("copies_deleted", "accepted", len(gone))

        # Steps 4 to 7: rows nobody classified.
        for r in jobs:
            f = r["fields"]
            identity = f.get("Identity")
            if not identity or f.get("Status"):
                continue
            where = self.stores.where(identity)
            if where is None:
                self.report["held_private_unavailable"] += 1
                continue
            # Origin already holds a removal that keeps this row out: a
            # closure, the clock or the operator's tool (ADR-0055). It goes
            # now, and no later reason is written over the one that holds.
            kept = self.stores.kept_out_reason(where, identity)
            if kept is not None:
                delete_jobs.append((r["id"], identity, kept))
                continue
            closed, removal = self.judge(identity)
            # Step 4: mark, or clear a mark whose posting came back.
            marked = f.get("Closed")
            if closed and not marked:
                closed_updates.append((r["id"], closed))
                marked = closed
                self.report["closed_marked"] += 1
            elif not closed and marked and removal is None:
                closed_updates.append((r["id"], None))
                marked = None
                self.report["closed_cleared"] += 1
            # Step 5: retire what closed fifteen days ago.
            if marked and older_than(marked + "T00:00:00Z", days, self.now):
                removal = REASON_CLOSED
            # Step 7: ADR-0055's clock, for a row no other reason removes.
            if removal is None and self.aged_out(identity, f):
                removal = REASON_AGED_OUT
                self.report["aged_out"] += 1
            if removal is None:
                continue
            # Store, and delete once origin holds this removal for this reason.
            if self.stores.durable_removal(where, identity, removal):
                delete_jobs.append((r["id"], identity, removal))
                continue
            self.stores.write(where, REMOVED_UNREVIEWED_STORE,
                              self.record(identity, f, reason=removal, closed=marked,
                                          removal=removal_key(identity, removal)),
                              key="removal")
            self._removal(identity, JOBS, removal, "stored")
            self.report["waiting_for_the_store"] += 1

        if closed_updates:
            self.client.set_closed(closed_updates)
        # A row can qualify twice, by its fifteen days and by its accepted
        # copy's `Delete`; Airtable refuses a record named twice in a call.
        once = {}
        for record_id, identity, why in delete_jobs:
            once.setdefault(record_id, (identity, why))
        if once:
            self.client.delete(JOBS, list(once))
            self.report["deleted_from_jobs"] += len(once)
            for identity, why in once.values():
                self._removal(identity, JOBS, why, "deleted")

    def aged_out(self, identity, fields):
        """ADR-0055: first seen more than `unreviewed_after_days` ago. The
        display row's own `First seen`, or the stored row's."""
        first_seen = fields.get("First seen")
        if not first_seen and identity in self.rows:
            first_seen = self.rows[identity].first_seen
        return older_than(first_seen, self.config.unreviewed_after_days, self.now)

    def judge(self, identity):
        """(closed ISO date or None, removal reason or None) for a row
        nobody classified. A closed row is marked, not removed, until it has
        been closed fifteen days."""
        g = self.group_of.get(identity)
        if g is not None:
            if g.representative.identity != identity:
                # The group now shows under another member's identity, so
                # this display row is a duplicate of it.
                return None, REASON_REGROUPED
            return self.closure.group_closed_on(g.members), None
        row = self.rows.get(identity)
        if row is None:
            # Not judged, so not removed: nothing stored can say whether a
            # rule dropped it. The 15 Himalayas rows of 2026-09-24, projected
            # before the private store existed, are the case, and two of them
            # are roles the operator named as ones he had not seen. Counted
            # and left for him; ADR-0050 removes only what the chain drops.
            self.report["not_in_the_stored_layers"] += 1
            return None, None
        rule = self.dropped_by.get(identity)
        if rule == "expiry":
            return self.closure.closed_on(row)[0], None
        return None, RULE_REASON % rule
